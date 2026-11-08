from dataclasses import replace
import multiprocessing as mp
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest

from outbox import Outbox, Result, Conflict, classify_legacy_response

OP = 'operation_000001'
MID = 'message_00000001'
PAYLOAD = {'text': 'synthetic offline fixture', 'kind': 'text'}


def bound(message, kind='STORED'):
    return Result(kind, message.principal, message.room,
                  message.client_message_id, message.digest, 'receipt-fixture')


def blocking_worker(directory, started, release, results):
    box = Outbox(directory)
    def transport(message):
        started.set()
        if not release.wait(10):
            raise TimeoutError()
        return bound(message)
    results.put(box.run_once(transport))


def second_worker(directory, results):
    def transport(message):
        raise AssertionError('second worker must not send')
    results.put(Outbox(directory).run_once(transport))


def crashing_worker(directory):
    def transport(message):
        os._exit(17)  # simulates loss after claim, before outcome persistence
    Outbox(directory).run_once(transport)


class OutboxTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name) / 'private'
        self.box = Outbox(self.directory)
        self.enqueue()

    def tearDown(self):
        self.temp.cleanup()

    def enqueue(self, **kwargs):
        values = dict(operation_id=OP, client_message_id=MID,
                      principal='agent:ti', room='room:synthetic', payload=PAYLOAD)
        values.update(kwargs)
        return self.box.enqueue(**values)

    def test_duplicate_enqueue_same_payload(self):
        self.assertEqual(self.enqueue()['attempts'], 0)
        self.assertEqual(self.box.run_once(lambda m: bound(m)), 'STORED')
        self.assertEqual(self.enqueue()['state'], 'STORED')
        self.assertEqual(self.box.run_once(lambda m: self.fail('duplicate send')), 'IDLE')

    def test_conflicting_binding(self):
        for change in ({'payload': {'text': 'changed', 'kind': 'text'}},
                       {'principal': 'agent:other'}, {'room': 'elsewhere'},
                       {'client_message_id': 'different_00001'},
                       {'operation_id': 'different_00001'}, {'max_attempts': 4}):
            with self.subTest(change=change), self.assertRaises(Conflict):
                self.enqueue(**change)

    def test_restart_persistence(self):
        self.box = Outbox(self.directory)
        self.assertEqual(self.box.get(OP)['state'], 'QUEUED')
        self.box.run_once(lambda m: bound(m))
        self.assertEqual(Outbox(self.directory).get(OP)['state'], 'STORED')

    def test_denial_terminal(self):
        self.assertEqual(self.box.run_once(lambda m: Result('DENIED')), 'DENIED')
        self.assertEqual(self.box.run_once(lambda m: self.fail('retry denial')), 'IDLE')
        with self.assertRaises(ValueError):
            self.box.reconcile(OP, lambda m: bound(m, 'NOT_SENT'))
        self.assertEqual(self.box.get(OP)['attempts'], 1)

    def test_legacy_unverified_not_retryable(self):
        for reason in ('SERVICE_IDENTITY_DENIED', 'ACCESS_LOGIN_REDIRECT_BLOCKED',
                       'SERVICE_IDENTITY_NOT_CONFIGURED'):
            self.assertEqual(classify_legacy_response({'status': 'UNVERIFIED',
                'reason': reason, 'safeToRetryWithSameId': True}).kind, 'DENIED')
        self.assertEqual(classify_legacy_response({'status': 'UNVERIFIED',
            'reason': 'TRANSPORT_UNREACHABLE', 'safeToRetryWithSameId': True}).kind, 'UNKNOWN')
        self.assertEqual(classify_legacy_response({'status': 'STORED_BY_SERVER'}).kind, 'UNKNOWN')

    def test_unknown_reconciled_stored(self):
        self.assertEqual(self.box.run_once(lambda m: Result('UNKNOWN')), 'UNCERTAIN')
        self.assertEqual(self.box.run_once(lambda m: self.fail('unsafe retry')), 'IDLE')
        self.assertEqual(self.box.reconcile(OP, lambda m: Result('UNKNOWN')), 'UNCERTAIN')
        self.assertEqual(self.box.reconcile(OP, lambda m: bound(m)), 'STORED')
        self.assertEqual(self.box.get(OP)['attempts'], 1)

    def test_unknown_reconciled_not_sent(self):
        self.box.run_once(lambda m: Result('UNKNOWN'))
        self.assertEqual(self.box.reconcile(OP, lambda m: bound(m, 'NOT_SENT')), 'QUEUED')
        self.assertEqual(self.box.run_once(lambda m: bound(m)), 'STORED')
        self.assertEqual(self.box.get(OP)['attempts'], 2)

    def test_bad_receipt_is_uncertain(self):
        for result in (Result('STORED'), Result('NOT_SENT'), {'status': 'UNVERIFIED'}):
            if self.box.get(OP)['state'] == 'QUEUED':
                actual = self.box.run_once(lambda m: result)
            else:
                actual = self.box.reconcile(OP, lambda m: result)
            self.assertEqual(actual, 'UNCERTAIN')

    def test_each_evidence_binding_mismatch(self):
        self.box.run_once(lambda m: Result('UNKNOWN'))
        for field in ('principal', 'room', 'client_message_id', 'payload_digest', 'receipt'):
            with self.subTest(field=field):
                def verifier(message):
                    return replace(bound(message), **{field: '' if field == 'receipt' else 'wrong'})
                self.assertEqual(self.box.reconcile(OP, verifier), 'UNCERTAIN')
        self.assertEqual(self.box.reconcile(OP, lambda m: bound(m)), 'STORED')

    def test_max_attempts(self):
        for state in ('QUEUED', 'QUEUED', 'EXHAUSTED'):
            self.assertEqual(self.box.run_once(lambda m: bound(m, 'NOT_SENT')), state)
        self.assertEqual(self.box.run_once(lambda m: self.fail('too many attempts')), 'IDLE')
        self.assertEqual(self.box.get(OP)['attempts'], 3)

    def test_last_unknown_cannot_retry_after_reconciliation(self):
        self.box.run_once(lambda m: bound(m, 'NOT_SENT'))
        self.box.run_once(lambda m: bound(m, 'NOT_SENT'))
        self.box.run_once(lambda m: Result('UNKNOWN'))
        self.assertEqual(self.box.reconcile(OP, lambda m: bound(m, 'NOT_SENT')), 'EXHAUSTED')

    def test_exception_is_held_not_logged(self):
        def bad(message):
            raise RuntimeError('synthetic-secret-not-for-storage')
        self.assertEqual(self.box.run_once(bad), 'UNCERTAIN')
        self.assertNotIn(b'synthetic-secret-not-for-storage', self.box.database.read_bytes())

    def test_crash_restart_held(self):
        context = mp.get_context('spawn')
        worker = context.Process(target=crashing_worker, args=(self.directory,))
        worker.start()
        worker.join(10)
        self.assertEqual(worker.exitcode, 17)
        self.assertEqual(self.box.get(OP)['state'], 'IN_FLIGHT')
        restarted = Outbox(self.directory)
        self.assertEqual(restarted.run_once(lambda m: self.fail('crash replay')), 'IDLE')
        self.assertEqual(restarted.get(OP)['state'], 'UNCERTAIN')
        self.assertEqual(restarted.reconcile(OP, lambda m: bound(m)), 'STORED')

    def test_two_process_workers(self):
        context = mp.get_context('spawn')
        started, release, results = context.Event(), context.Event(), context.Queue()
        first = context.Process(target=blocking_worker, args=(self.directory, started, release, results))
        second = context.Process(target=second_worker, args=(self.directory, results))
        first.start()
        try:
            self.assertTrue(started.wait(10))
            second.start()
            self.assertEqual(results.get(timeout=10), 'BUSY')
            self.assertEqual(self.box.reconcile(OP, lambda m: self.fail('active reconcile')), 'BUSY')
            release.set()
            self.assertEqual(results.get(timeout=10), 'STORED')
        finally:
            release.set()
            first.join(10)
            if second.pid:
                second.join(10)
            for worker in (first, second):
                if worker.pid and worker.is_alive():
                    worker.terminate()
                    worker.join()
        self.assertEqual(first.exitcode, 0)
        self.assertEqual(second.exitcode, 0)
        self.assertEqual(self.box.get(OP)['attempts'], 1)

    def test_binding_trigger(self):
        with sqlite3.connect(self.box.database) as db:
            with self.assertRaises(sqlite3.IntegrityError):
                db.execute('UPDATE operations SET room=?', ('changed',))

    def test_unsafe_existing_files_rejected(self):
        for filename in ('outbox.sqlite3', 'worker.lock'):
            for kind in ('fifo', 'public', 'symlink'):
                with self.subTest(filename=filename, kind=kind):
                    directory = Path(self.temp.name) / (filename + kind)
                    directory.mkdir(mode=0o700)
                    target = directory / filename
                    if kind == 'fifo':
                        os.mkfifo(target, 0o600)
                    elif kind == 'symlink':
                        target.symlink_to(self.box.database)
                    else:
                        target.touch(mode=0o644)
                        target.chmod(0o644)
                    with self.assertRaises(ValueError):
                        Outbox(directory)

    def test_payload_rejects_credential_fields(self):
        with self.assertRaises(ValueError):
            self.enqueue(payload={**PAYLOAD, 'clientSecret': 'not-accepted'})


if __name__ == '__main__':
    unittest.main()
