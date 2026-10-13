"""Read-only OSS admission for D'AUBE BRIDGE².

Consumes the EXISTING Capability Scout ranking and pinned source snapshots.
A successful preflight is a sandbox-review packet, NEVER an install, permission,
production approval, release, or payment decision. Founder rights stay reserved.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from .capability_scout import SENSITIVE, scout

EVIDENCE_SCHEMA = 'daube.oss-harvest-evidence.v1'
SCHEMA = 'daube.oss-harvest.v1'
ALLOWED_ACTIONS = frozenset({'research', 'prepare_sandbox'})
# Material and reserved actions cannot be authorized by this module, even with
# a supposed Founder signature or a request from a lower-trust agent.
FOUNDER_RESERVED = frozenset({
    'revoke_founder_access', 'remove_founder', 'change_founder_role',
    'transfer_repo_ownership', 'grant_agent_owner', 'disable_founder_approval',
    'bypass_founder_gate', 'change_governance', 'self_approve_material',
    'merge', 'deploy', 'spend_money', 'register_paid_provider',
    'contact_customer', 'rotate_founder_keys',
})
# Narrowest commercially useful license allowlist for a metadata-level pilot.
REVIEWABLE_LICENSES = frozenset({'MIT', 'Apache-2.0'})
EVIDENCE_FIELDS = frozenset({
    'schema', 'source_revision', 'source_path', 'source_blob_sha',
    'license_path', 'license_blob_sha', 'target_path', 'max_spend_usd',
})
SHA1 = re.compile(r'[0-9a-f]{40}\Z')
SAFE_PART = re.compile(r'[A-Za-z0-9][A-Za-z0-9._-]*\Z')
SAFE_TARGET = re.compile(r'sandbox/oss/[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\Z')
FOUNDER_INSTRUCTION = re.compile(r'(?:remove|demote|disable|bypass|transfer|revoke|lock|grant).{0,60}(?:founder|owner|approval|governance)', re.IGNORECASE)


def _foundation(state: str) -> dict[str, Any]:
    return {
        'schema': SCHEMA,
        'state': state,
        'founder_authority_immutable': True,
        'agent_may_remove_founder': False,
        'agent_may_change_ownership': False,
        'agent_may_self_approve': False,
        'external_action_authorized': False,
        'production_promotion_authorized': False,
        'spend_authorized': False,
        'network_call_made': False,
        'requested_action_performed': False,
        'isolation': 'D_AUBE_ONLY',
        'truth_boundary': (
            'Public OSS metadata and local hashes are research evidence, not '
            'upstream identity, legal clearance, Founder consent or release authority.'
        ),
    }


def _relative_path(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 240:
        raise ValueError(f'{label} must be a short relative path')
    if ('\\' in value or '%' in value or '?' in value or '#' in value
            or value.startswith('/') or '//' in value or ':' in value):
        raise ValueError(f'{label} contains unsafe path syntax')
    parts = value.split('/')
    if any(part in ('.', '..') or not SAFE_PART.fullmatch(part) for part in parts):
        raise ValueError(f'{label} contains unsafe path segments')
    return value


def _target_path(value: Any) -> str:
    if not isinstance(value, str) or not SAFE_TARGET.fullmatch(value):
        raise ValueError('target_path must be one sandbox/oss/<slug> directory')
    if any(term in value for term in (
        'founder', 'owner', 'governance', 'auth', 'secret', 'token',
        'payment', 'billing', 'production', 'amadeli', 'deploy',
    )):
        raise ValueError('target_path cannot be a protected authority destination')
    return value


def _git_blob(data: bytes) -> str:
    return hashlib.sha1(b'blob ' + str(len(data)).encode('ascii') + b'\0' + data).hexdigest()


def _byte_limit(data: Any, label: str, max_bytes: int) -> bytes:
    if type(data) is not bytes or not data or len(data) > max_bytes:
        raise ValueError(f'{label} must be bounded bytes')
    return data


def _source_repo(candidate: dict[str, Any]) -> str:
    if candidate['source_type'] != 'github_repository':
        raise ValueError('Only pinned GitHub repositories have a pilot admission path')
    url = candidate['source_url']
    parsed = urlsplit(url)
    parts = parsed.path.strip('/').split('/')
    if parsed.scheme != 'https' or parsed.netloc != 'github.com' or len(parts) != 2:
        raise ValueError('GitHub repository URL must have owner/repository shape')
    if any(not SAFE_PART.fullmatch(part) for part in parts):
        raise ValueError('GitHub repository name malformed')
    return '/'.join(parts)


def _evidence_shape(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError('evidence must be an object')
    unknown = set(value) - EVIDENCE_FIELDS
    if unknown:
        raise ValueError('unsupported evidence fields: cannot grant new authority')
    if set(value) != EVIDENCE_FIELDS:
        raise ValueError('evidence missing required source/license fields')
    if value['schema'] != EVIDENCE_SCHEMA:
        raise ValueError('unsupported OSS evidence schema')
    for field in ('source_revision', 'source_blob_sha', 'license_blob_sha'):
        if not isinstance(value[field], str) or not SHA1.fullmatch(value[field]):
            raise ValueError(f'{field} must be lowercase Git SHA-1')
    _relative_path(value['source_path'], 'source_path')
    if value['license_path'] != 'LICENSE':
        raise ValueError('license_path must be the reviewed repository-root LICENSE')
    _target_path(value['target_path'])
    if isinstance(value['max_spend_usd'], bool) or value['max_spend_usd'] is None:
        raise ValueError('max_spend_usd must explicitly be zero')
    try:
        amount = Decimal(str(value['max_spend_usd']))
    except (InvalidOperation, ValueError, TypeError) as err:
        raise ValueError('max_spend_usd must explicitly be zero') from err
    if not amount.is_finite() or amount != 0:
        raise ValueError('max_spend_usd must explicitly be zero')
    return value


def assess_harvest(
    snapshot: Any, query: Any, *, action: str, candidate_id: str | None = None,
    evidence: Any = None, source_bytes: bytes | None = None,
    license_bytes: bytes | None = None,
) -> dict[str, Any]:
    """Return a review packet. Never fetch, execute, install, contact, or promote."""
    if not isinstance(action, str):
        raise ValueError('action must be a simple string')
    if action in FOUNDER_RESERVED:
        return _foundation('FOUNDER_ONLY_STOP')
    if action not in ALLOWED_ACTIONS:
        return _foundation('ACTION_NOT_DELEGATED')
    ranked = scout(snapshot, query, limit=25)
    result = _foundation('D0_RESEARCH_PACKET')
    result['existing_scout_state'] = ranked['state']
    candidates = ranked['ranked']
    if not candidates:
        result['state'] = 'NO_MATCH_IN_EXISTING_SCOUT'
        return result
    if candidate_id is not None and (not isinstance(candidate_id, str) or len(candidate_id) > 240):
        raise ValueError('candidate_id malformed')
    candidate = next((item for item in candidates if item['candidate_id'] == candidate_id), None) if candidate_id else candidates[0]
    if candidate is None:
        result['state'] = 'CANDIDATE_NOT_FOUND'
        return result
    result.update({
        'candidate_id': candidate['candidate_id'],
        'source_type': candidate['source_type'],
        'source_revision': candidate['source_revision_reported'],
        'declared_license': candidate['declared_license'],
        'metadata_sha256': candidate['metadata_sha256'],
        'source_provenance_verified': False,
        'license_compliance_verified': False,
        'source_origin_authenticated': False,
    })
    if action == 'research':
        return result
    # In a successful sandbox packet even locally matched bytes are quarantined;
    # only an independent provider/reviewer can validate provenance and license.
    if candidate['source_type'] != 'github_repository' or not candidate['revision_pin_present']:
        result['state'] = 'D1_EVIDENCE_REQUIRED'
        return result
    if candidate['declared_license'] not in REVIEWABLE_LICENSES:
        result['state'] = 'LEGAL_REVIEW_HOLD'
        return result
    if evidence is None:
        result['state'] = 'D1_EVIDENCE_REQUIRED'
        return result
    e = _evidence_shape(evidence)
    if source_bytes is None or license_bytes is None:
        result['state'] = 'D1_EVIDENCE_REQUIRED'
        return result
    src = _byte_limit(source_bytes, 'source_bytes', 131_072)
    lic = _byte_limit(license_bytes, 'license_bytes', 65_536)
    if (e['source_revision'] != candidate['source_revision_reported']
            or _git_blob(src) != e['source_blob_sha']
            or _git_blob(lic) != e['license_blob_sha']):
        result['state'] = 'D1_EVIDENCE_CONFLICT'
        return result
    try:
        source_text = src.decode('utf-8', errors='strict')
        license_str = lic.decode('utf-8', errors='strict')
    except UnicodeDecodeError as exc:
        raise ValueError('source and license must be UTF-8 text') from exc
    if SENSITIVE.search(source_text) or FOUNDER_INSTRUCTION.search(source_text):
        result['state'] = 'SECURITY_REVIEW_HOLD'
        return result
    if candidate['declared_license'] == 'MIT':
        if not (license_str.startswith('MIT License\n')
                and 'Permission is hereby granted, free of charge' in license_str
                and 'THE SOFTWARE IS PROVIDED "AS IS"' in license_str):
            result['state'] = 'LEGAL_REVIEW_HOLD'
            return result
    elif candidate['declared_license'] == 'Apache-2.0':
        if 'Apache License' not in license_str or 'Version 2.0' not in license_str:
            result['state'] = 'LEGAL_REVIEW_HOLD'
            return result
    repo = _source_repo(candidate)
    base = f'https://github.com/{repo}/blob/{e["source_revision"]}/'
    result.update({
        'state': 'D1_SANDBOX_REVIEW_PACKET',
        'source_revision': e['source_revision'],
        'source_url': base + e['source_path'],
        'license_url': base + 'LICENSE',
        'source_git_blob_matched': True,
        'license_git_blob_matched': True,
        'source_sha256': hashlib.sha256(src).hexdigest(),
        'license_sha256': hashlib.sha256(lic).hexdigest(),
        'target_path': e['target_path'],
        'license_notice_must_be_preserved': True,
        'sandbox_execution_authorized': False,
        'source_origin_authenticated': False,
        'license_compliance_verified': False,
        'next_review': 'Independent reviewer verifies original upstream commit, source, license, sandbox tests, ownership and rollback before any code promotion.',
    })
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--index', required=True, type=Path)
    parser.add_argument('--query', required=True)
    parser.add_argument('--action', required=True)
    parser.add_argument('--candidate-id')
    parser.add_argument('--evidence', type=Path)
    parser.add_argument('--source-file', type=Path)
    parser.add_argument('--license-file', type=Path)
    args = parser.parse_args()
    try:
        # Reject hidden filesystem or external paths. Source snapshots live in
        # repo-owned, quarantined examples; the read is bounded and local only.
        repo_root = Path(__file__).resolve().parents[2]
        quarantine = (repo_root / 'examples' / 'oss_harvest').resolve()
        if args.action != 'research' and args.action in ALLOWED_ACTIONS:
            for p in (args.evidence, args.source_file, args.license_file):
                if p is not None and not p.resolve().is_relative_to(quarantine):
                    raise ValueError('source/evidence files must stay in examples/oss_harvest')
        snapshot = json.loads(args.index.read_text(encoding='utf-8'),
                              parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite JSON')))
        evid = (json.loads(args.evidence.read_text(encoding='utf-8')) if args.evidence else None)
        result = assess_harvest(
            snapshot, args.query, action=args.action, candidate_id=args.candidate_id,
            evidence=evid,
            source_bytes=args.source_file.read_bytes() if args.source_file else None,
            license_bytes=args.license_file.read_bytes() if args.license_file else None,
        )
    except (OSError, ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        result = _foundation('BLOCKED')
        result['reason'] = 'Invalid input or unsafe provenance; inspect source files and governance gates.'
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result['state'] in {'D0_RESEARCH_PACKET','D1_SANDBOX_REVIEW_PACKET'} else 2 if result['state'] == 'FOUNDER_ONLY_STOP' else 1


if __name__ == '__main__':
    raise SystemExit(main())
