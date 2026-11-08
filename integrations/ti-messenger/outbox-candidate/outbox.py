"""Source-only, POSIX/local-filesystem durable outbox. No network transport."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import stat


@dataclass(frozen=True)
class Message:
    operation_id: str
    client_message_id: str
    principal: str
    room: str
    payload: str  # canonical JSON; no mutable object passed to transport
    max_attempts: int

    @property
    def digest(self):
        return hashlib.sha256(self.payload.encode()).hexdigest()


@dataclass(frozen=True)
class Result:
    # STORED requires matching binding and nonempty receipt. NOT_SENT is a
    # positive guarantee that acceptance did not and cannot later occur.
    kind: str
    principal: str = ''
    room: str = ''
    client_message_id: str = ''
    payload_digest: str = ''
    receipt: str = ''


class Conflict(ValueError):
    pass


class Outbox:
    def __init__(self, directory):
        self.directory = Path(directory).resolve()
        self.directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        info = self.directory.stat()
        if info.st_uid != os.geteuid() or info.st_mode & 0o077:
            raise ValueError('private owned directory required')
        self.database = self.directory / 'outbox.sqlite3'
        self.lock = self.directory / 'worker.lock'
        # This directory must not be writable by untrusted processes. Reject
        # existing symlinks; hostile same-uid mutation is outside the contract.
        for path in (self.database, self.lock):
            if path.is_symlink():
                raise ValueError('symlinks forbidden')
            fd = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
            try:
                info = os.fstat(fd)
                if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid()
                        or info.st_mode & 0o077):
                    raise ValueError('private owned regular files required')
            finally:
                os.close(fd)
        with self._db() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS operations (
                    operation_id TEXT PRIMARY KEY,
                    client_message_id TEXT NOT NULL UNIQUE,
                    principal TEXT NOT NULL, room TEXT NOT NULL,
                    payload TEXT NOT NULL, max_attempts INTEGER NOT NULL,
                    state TEXT NOT NULL DEFAULT 'QUEUED',
                    attempts INTEGER NOT NULL DEFAULT 0,
                    receipt TEXT NOT NULL DEFAULT ''
                );
                CREATE TRIGGER IF NOT EXISTS immutable_binding
                BEFORE UPDATE OF operation_id,client_message_id,principal,room,
                    payload,max_attempts ON operations
                BEGIN SELECT RAISE(ABORT, 'immutable binding'); END;
            ''')

    @contextmanager
    def _db(self):
        db = sqlite3.connect(self.database, timeout=5)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA synchronous=FULL')
        try:
            with db:
                yield db
        finally:
            db.close()

    @contextmanager
    def _worker(self):
        fd = os.open(self.lock, os.O_RDWR | os.O_NOFOLLOW)
        acquired = False
        try:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                acquired = True
            except BlockingIOError:
                pass
            yield acquired
        finally:
            if acquired:
                fcntl.flock(fd, fcntl.LOCK_UN)
            os.close(fd)

    @staticmethod
    def _message(row):
        return Message(*(row[k] for k in Message.__dataclass_fields__))

    def enqueue(self, operation_id, client_message_id, principal, room, payload,
                max_attempts=3):
        for value in (operation_id, client_message_id):
            if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9_-]{12,90}', value):
                raise ValueError('invalid operation/client ID')
        for value in (principal, room):
            if not isinstance(value, str) or not value.strip() or len(value) > 256:
                raise ValueError('invalid binding')
        # Narrow payload contract: authentication/configuration is never stored.
        if (not isinstance(payload, dict) or set(payload) != {'text', 'kind'}
                or not isinstance(payload['text'], str) or not payload['text'].strip()
                or len(payload['text']) > 4000 or payload['kind'] not in ('text', 'challenge')):
            raise ValueError('invalid payload')
        if type(max_attempts) is not int or not 1 <= max_attempts <= 10:
            raise ValueError('invalid attempt bound')
        encoded = json.dumps(payload, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
        message = Message(operation_id, client_message_id, principal, room, encoded, max_attempts)
        with self._db() as db:
            db.execute('BEGIN IMMEDIATE')
            old = db.execute('SELECT * FROM operations WHERE operation_id=? OR client_message_id=?',
                             (operation_id, client_message_id)).fetchall()
            if old:
                if len(old) != 1 or self._message(old[0]) != message:
                    raise Conflict('operation/client ID bound to different content')
            else:
                db.execute('INSERT INTO operations (operation_id,client_message_id,principal,room,payload,max_attempts) VALUES (?,?,?,?,?,?)',
                           tuple(message.__dict__.values()))
        return self.get(operation_id)

    def get(self, operation_id):
        with self._db() as db:
            row = db.execute('SELECT * FROM operations WHERE operation_id=?', (operation_id,)).fetchone()
            return dict(row) if row else None

    @staticmethod
    def _matches(message, result):
        return (isinstance(result, Result) and result.principal == message.principal
                and result.room == message.room
                and result.client_message_id == message.client_message_id
                and result.payload_digest == message.digest)

    def _finish(self, db, row, result):
        message = self._message(row)
        state, receipt = 'UNCERTAIN', ''
        if isinstance(result, Result) and result.kind == 'DENIED':
            state = 'DENIED'
        elif self._matches(message, result):
            if result.kind == 'STORED' and isinstance(result.receipt, str) and 0 < len(result.receipt) <= 256:
                state, receipt = 'STORED', result.receipt
            elif result.kind == 'NOT_SENT':
                state = 'QUEUED' if row['attempts'] < row['max_attempts'] else 'EXHAUSTED'
        db.execute('UPDATE operations SET state=?,receipt=? WHERE operation_id=?',
                   (state, receipt, row['operation_id']))

    def run_once(self, transport):
        """One attempt at most. transport(Message)->Result; never sleeps/retries."""
        with self._worker() as acquired:
            if not acquired:
                return 'BUSY'
            with self._db() as db:
                db.execute('BEGIN IMMEDIATE')
                # Lock proves no cooperating sender is still active. A crash at
                # any point after claim is held, never automatically reclaimed.
                db.execute("UPDATE operations SET state='UNCERTAIN' WHERE state='IN_FLIGHT'")
                row = db.execute("SELECT * FROM operations WHERE state='QUEUED' AND attempts<max_attempts ORDER BY rowid LIMIT 1").fetchone()
                if row is None:
                    return 'IDLE'
                db.execute("UPDATE operations SET state='IN_FLIGHT',attempts=attempts+1 WHERE operation_id=?", (row['operation_id'],))
                row = db.execute('SELECT * FROM operations WHERE operation_id=?', (row['operation_id'],)).fetchone()
            try:
                result = transport(self._message(row))
            except Exception:
                # Never persist exception strings: transport may contain secrets.
                result = Result('UNKNOWN')
            with self._db() as db:
                self._finish(db, row, result)
            return self.get(row['operation_id'])['state']

    def reconcile(self, operation_id, verifier):
        """Explicit trusted verifier(Message)->Result, only for UNCERTAIN.

        A NOT_SENT verdict must prove no delayed acceptance is possible, not
        merely absence from a recent-message page. No timeout unlocks a send.
        """
        with self._worker() as acquired:
            if not acquired:
                return 'BUSY'
            with self._db() as db:
                db.execute("UPDATE operations SET state='UNCERTAIN' WHERE state='IN_FLIGHT'")
                row = db.execute('SELECT * FROM operations WHERE operation_id=?', (operation_id,)).fetchone()
                if row is None or row['state'] != 'UNCERTAIN':
                    raise ValueError('only uncertain operations can be reconciled')
            try:
                result = verifier(self._message(row))
            except Exception:
                result = Result('UNKNOWN')
            with self._db() as db:
                self._finish(db, row, result)
            return self.get(operation_id)['state']


def classify_legacy_response(response):
    """Fail-closed classifier, NOT an executable transport adapter.

    Legacy receipts omit verified room/payload binding. All other results,
    including STORED_BY_SERVER, need independent reconciliation before success.
    """
    if isinstance(response, dict) and (
        response.get('http') in (401, 403)
        or response.get('reason') in {
            'SERVICE_IDENTITY_DENIED', 'ACCESS_LOGIN_REDIRECT_BLOCKED',
            'SERVICE_IDENTITY_NOT_CONFIGURED', 'SURFACE_HOST_MISMATCH',
            'ENDPOINT_NOT_ALLOWLISTED',
        }
    ):
        return Result('DENIED')
    return Result('UNKNOWN')
