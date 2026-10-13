"""D'AUBE BRIDGE² offline capability scout for skill, MCP, A2A and OSS metadata.

This deliberately does not crawl, connect, install, execute, qualify practitioners,
or provide evidence of an external agent's identity or a commercial outcome.
External records are untrusted discovery hints and are never instructions.
"""
from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

SCHEMA = 'daube.capability-scout.v1'
MAX_SNAPSHOT_BYTES = 350_000
MAX_CANDIDATES = 100
KNOWN_KINDS = frozenset({'agent_skill','mcp_registry','a2a_agent_card','github_repository'})
SENSITIVE = re.compile(
    r'(?:\bBearer\s+\S+|\bsk-[A-Za-z0-9_-]{14,}|\bgh[pousr]_[A-Za-z0-9]{15,}'
    r'|\b[\w.%+-]+@[\w.-]+\.[A-Za-z]{2,}\b|-----BEGIN\s+[^-]+PRIVATE KEY-----)',
    flags=re.IGNORECASE,
)

# Versioned, deliberately narrow routing hints; these are not certifications.
DOMAINS: dict[str, tuple[str, ...]] = {
    'ai-interoperability': ('ai','agent','a2a','mcp','llm','rag','agent card','skills','model','orchestration','ai agents','tác nhân'),
    'software-qa': ('qa','testing','test','kiểm thử','smoke','regression','bug','pytest','playwright','pull request','github pr','quality assurance'),
    'frontend-ux': ('ui','ux','frontend','front-end','landing page','react','figma','responsive','accessibility','giao diện','trải nghiệm','thiết kế giao diện'),
    'backend-integrations': ('backend','back-end','api','webhook','database','postgres','fastapi','python','integration','tích hợp','kết nối'),
    'devops-cloud': ('devops','cloud','cicd','ci/cd','deployment','deploy','docker','kubernetes','infrastructure','hạ tầng','observability'),
    'security-privacy': ('security','privacy','bảo mật','an toàn','owasp','red team','redteam','authentication','pentest','detection','security audit'),
    'data-analytics': ('data','analytics','dashboard','sql','kpi','forecast','bi','dữ liệu','phân tích','báo cáo','thống kê'),
    'visual-design': ('design','illustration','graphic','illustrator','typography','poster','brand design','visual','mỹ thuật','thiết kế đồ họa'),
    'marketing-growth': ('marketing','seo','growth','copywriting','landing page','conversion','chuyển đổi','content','social','tiếp thị','quảng cáo','tối ưu'),
    'sales-revops': ('sales','revenue','crm','lead','prospecting','pipeline','retention','doanh thu','bán hàng','khách hàng','revops','quote'),
    'project-management': ('project','roadmap','timeline','planning','project management','milestone','gantt','schedule','prd','spec','spec-driven','sdd','specification','lập kế hoạch','quản lý dự án','tiến độ','deadline'),
    'localization-writing': ('translation','localization','translate','subtitle','transcription','copywriting','writing','document','dịch thuật','ngôn ngữ','phụ đề','biên tập'),
    'commerce-finance': ('payment','invoice','financial','accounting','profit','cashflow','cash flow','commerce','thu tiền','thanh toán','lợi nhuận','hóa đơn'),
    'legal-compliance': ('legal','compliance','tax','gdpr','privacy law','contract','regulation','luật','thuế','hợp đồng','pháp lý','tuân thủ'),
}
REVENUE_DIRECT = frozenset({'software-qa','frontend-ux','backend-integrations','devops-cloud','ai-interoperability','data-analytics','visual-design','marketing-growth','sales-revops','project-management','localization-writing','commerce-finance'})


def _json_bytes(value: Any) -> bytes:
    try:
        raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')
    except (ValueError, TypeError, RecursionError) as exc:
        raise ValueError('snapshot must be finite JSON') from exc
    if len(raw) > MAX_SNAPSHOT_BYTES:
        raise ValueError('snapshot exceeds bounded discovery size')
    return raw


def _clean(value: Any, field: str, *, limit: int = 4096) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValueError(f'{field} must be a nonempty bounded string')
    if any(unicodedata.category(c).startswith('C') and c not in '\n\t' for c in value):
        raise ValueError(f'{field} contains control or formatting characters')
    if field in {'candidate name','source URL','candidate identifier'} and any(ord(c)<32 or ord(c)==127 for c in value):
        raise ValueError(f'{field} contains unsafe control characters')
    if field in {'candidate name','source URL','candidate identifier'} and SENSITIVE.search(value):
        raise ValueError(f'{field} contains sensitive text')
    return value.strip()


def _url(value: Any, field: str) -> str:
    if not isinstance(value, str) or value != value.strip():
        raise ValueError(f'{field} requires no surrounding whitespace')
    value = _clean(value, field, limit=2048)
    if value != value.strip() or '\\' in value or any(ord(c) < 32 for c in value):
        raise ValueError(f'{field} must be a canonical URL')
    try:
        parsed = urlsplit(value)
        host = parsed.hostname
        port = parsed.port
    except ValueError as exc:
        raise ValueError(f'{field} malformed') from exc
    if parsed.scheme != 'https' or parsed.username is not None or parsed.password is not None:
        raise ValueError(f'{field} must use credential-free HTTPS')
    if parsed.query or parsed.fragment or not parsed.path.startswith('/'):
        raise ValueError(f'{field} must have absolute path and no query/fragment')
    if not isinstance(host, str) or not re.fullmatch(r'[a-z0-9.-]+', host):
        raise ValueError(f'{field} host is invalid')
    if host.lower() != host or host.endswith('.') or '..' in host or '.' not in host:
        raise ValueError(f'{field} hostname must be public canonical DNS')
    if host.endswith(('.local','.test','.invalid','.localhost','.internal')) or port not in (None,443):
        raise ValueError(f'{field} cannot use local hosts/nondefault ports')
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        raise ValueError(f'{field} cannot target an IP literal')
    if parsed.netloc not in (host,host+':443'):
        raise ValueError(f'{field} must have canonical authority')
    return value


def _timestamp(value: Any) -> str:
    text = _clean(value, 'observed_at', limit=48)
    try:
        dt = datetime.fromisoformat(text.replace('Z','+00:00'))
    except ValueError as exc:
        raise ValueError('observed_at must be an ISO 8601 timestamp') from exc
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError('observed_at requires a timezone offset')
    return text


def _txt(value: Any, label: str, *, default: str = '') -> str:
    if value is None:
        return default
    return _clean(value, label)


def _keywords(text: str) -> set[str]:
    normalized = unicodedata.normalize('NFKC',text).casefold()
    return {domain for domain, keys in DOMAINS.items() if any(
        re.search(r'(?<!\w)'+re.escape(key)+r'(?!\w)', normalized, flags=re.UNICODE)
        for key in keys
    )}


def _tokens(text: str) -> set[str]:
    return {word for word in re.findall(r'[^\W_]+',unicodedata.normalize('NFKC',text).casefold()) if len(word)>=3}


def _metadata(record: Any) -> dict[str, Any]:
    if not isinstance(record, dict):
        raise ValueError('candidate record must be a JSON object')
    kind = record.get('source_type')
    if not isinstance(kind,str) or kind not in KNOWN_KINDS:
        raise ValueError('unsupported source_type')
    revision = record.get('source_revision')
    if revision is not None and (kind not in {'github_repository','agent_skill'}
            or not isinstance(revision,str)
            or re.fullmatch(r'[0-9a-f]{40}',revision) is None):
        raise ValueError('source_revision must be an exact lowercase Git SHA-1')
    source_url = _url(record.get('source_url'),'source URL')
    seen_at = _timestamp(record.get('observed_at'))
    payload = record.get('payload')
    if not isinstance(payload,dict):
        raise ValueError('source payload must be an object')
    host = urlsplit(source_url).hostname
    version: str | None = None
    license_id: str | None = None
    extra_fields: list[str] = []
    remote_auth = False
    registry_state = None
    if kind=='mcp_registry':
        if host!='registry.modelcontextprotocol.io':
            raise ValueError('MCP registry records require the official registry source')
        server = payload.get('server')
        if not isinstance(server,dict):
            raise ValueError('MCP registry server is missing')
        name = _clean(server.get('name'),'candidate name',limit=200)
        description = _txt(server.get('description'),'candidate description')
        version = _txt(server.get('version'),'source version',default='') or None
        stateinfo = payload.get('_meta') or {}
        if not isinstance(stateinfo,dict):
            raise ValueError('registry metadata must be an object')
        official = stateinfo.get('io.modelcontextprotocol.registry/official') or {}
        if not isinstance(official,dict):
            raise ValueError('registry official metadata must be an object')
        registry_state = official.get('status')
        if registry_state not in (None,'active','deprecated','deleted'):
            raise ValueError('unknown MCP server status')
        remotes=server.get('remotes') or []
        if not isinstance(remotes,list) or len(remotes)>20:
            raise ValueError('MCP remotes must be bounded array')
        for remote in remotes:
            if not isinstance(remote,dict):
                raise ValueError('MCP remote must be object')
            headers=remote.get('headers') or []
            if not isinstance(headers,list) or len(headers)>30:
                raise ValueError('MCP remote headers malformed')
            for header in headers:
                if not isinstance(header,dict):
                    raise ValueError('MCP remote header must be an object')
                if header.get('isSecret') is True or str(header.get('name','')).casefold()=='authorization':
                    remote_auth=True
    elif kind=='agent_skill':
        if host not in {'github.com','raw.githubusercontent.com'}:
            raise ValueError('skill source must be a reviewable GitHub reference')
        if revision is not None and host=='github.com':
            m = re.search(r'/blob/([0-9a-f]{40})/',urlsplit(source_url).path)
            if not m or m.group(1)!=revision:
                raise ValueError('skill source revision does not match pinned URL')
        name = _clean(payload.get('name'),'candidate name',limit=64)
        if re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',name) is None:
            raise ValueError('agent skill name must match portable slug format')
        description=_txt(payload.get('description'),'candidate description')
        license_id=payload.get('license')
        meta=payload.get('metadata') or {}
        if not isinstance(meta,dict):
            raise ValueError('skill metadata must be an object')
        version = _txt(meta.get('version'),'source version',default='') or None
    elif kind=='a2a_agent_card':
        if urlsplit(source_url).path not in ('/.well-known/agent-card.json','/.well-known/agent.json'):
            raise ValueError('A2A source is not a well-known discovery path')
        name = _clean(payload.get('name'),'candidate name',limit=128)
        description=_txt(payload.get('description'),'candidate description')
        version = _txt(payload.get('version'),'source version',default='') or None
        skills=payload.get('skills')
        if not isinstance(skills,list) or not 0<len(skills)<=64:
            raise ValueError('A2A skills are required')
        interfaces=payload.get('supportedInterfaces')
        if not isinstance(interfaces,list) or not 0<len(interfaces)<=8:
            raise ValueError('A2A interfaces must be bounded and nonempty')
        for item in interfaces:
            if not isinstance(item,dict) or item.get('protocolVersion')!='1.0':
                raise ValueError('A2A 1.0 interface expected')
            binding=item.get('protocolBinding')
            if not isinstance(binding,str) or binding not in {'HTTP+JSON','JSONRPC'}:
                raise ValueError('A2A binding not admitted for offline BRIDGE2 discovery')
            endpoint=_url(item.get('url'),'A2A endpoint')
            if urlsplit(endpoint).hostname!=host:
                raise ValueError('discovery host and endpoint host must match')
        for skill in skills:
            if not isinstance(skill,dict):
                raise ValueError('A2A skill must be an object')
            extra_fields.extend([_txt(skill.get(k),'A2A skill '+k) for k in ('id','name','description')])
            tags=skill.get('tags') or []
            if not isinstance(tags,list) or len(tags)>32:
                raise ValueError('A2A tags malformed')
            extra_fields.extend(_clean(tag,'A2A tag',limit=80) for tag in tags)
    else:
        if host!='github.com':
            raise ValueError('GitHub repo requires github.com source')
        name = _clean(payload.get('full_name'),'candidate name',limit=200)
        description=_txt(payload.get('description'),'candidate description')
        url = payload.get('html_url')
        if url is not None and _url(url,'GitHub repository URL')!=source_url:
            raise ValueError('GitHub repo URL conflicts with provenance')
        topics=payload.get('topics') or []
        if not isinstance(topics,list) or len(topics)>40:
            raise ValueError('GitHub topics malformed')
        extra_fields.extend(_clean(tag,'GitHub topic',limit=80) for tag in topics)
        version=_txt(payload.get('version'),'source version',default='') or None
        license_value=payload.get('license')
        if license_value is not None:
            if not isinstance(license_value,dict):
                raise ValueError('GitHub license must be an object')
            license_id=license_value.get('spdx_id')
    if license_id is not None:
        license_id=_clean(license_id,'declared license',limit=120)
        if license_id in ('NOASSERTION','none','None'):
            license_id=None
    corpus=' '.join([name,description,*extra_fields])
    return {'source_type':kind,'source_url':source_url,'observed_at':seen_at,
            'name':name,'source_version':version,'source_revision':revision,'declared_license':license_id,
            'domains':_keywords(corpus),'tokens':_tokens(corpus),
            'remote_auth_required_or_possible':remote_auth,
            'registry_status_reported':registry_state,
            'id':kind+':'+name.casefold(),
            'metadata_digest':hashlib.sha256(_json_bytes(payload)).hexdigest()}


def scout(snapshot: Any, query: Any, *, limit: int = 8) -> dict[str, Any]:
    """Rank untrusted specialist capabilities for review, never perform actions."""
    if type(limit) is not int or not 1<=limit<=25:
        raise ValueError('limit must be integer from 1 to 25')
    query=_clean(query,'task query',limit=1000)
    if SENSITIVE.search(query):
        raise ValueError('task query contains possible personal data or secrets')
    if not isinstance(snapshot,dict):
        raise ValueError('snapshot must be an object')
    _json_bytes(snapshot)
    if snapshot.get('schema')!=SCHEMA:
        raise ValueError('unsupported scout schema')
    entries=snapshot.get('entries')
    if not isinstance(entries,list) or len(entries)>MAX_CANDIDATES:
        raise ValueError('entries must be a bounded array')
    normalized=[];identities=set();excluded_count=0
    for item in entries:
        cand=_metadata(item)
        identity=cand['id']
        if identity in identities:
            raise ValueError('duplicate candidate identity')
        identities.add(identity)
        if cand['registry_status_reported'] in ('deleted','deprecated'):
            excluded_count+=1
            continue
        normalized.append(cand)
    requested=_keywords(query)
    ranked=[]
    query_tokens=_tokens(query)
    for item in normalized:
        shared=requested & item['domains']
        if not shared: continue
        overlap=min(8,len(query_tokens & item['tokens']))
        score=min(100,30*len(shared)+4*overlap)
        ranked.append({
            'candidate_id':item['id'], 'name':item['name'], 'source_type':item['source_type'],
            'source_url':item['source_url'],'observed_at':item['observed_at'],
            'source_version_reported':item['source_version'],
            'source_revision_reported':item['source_revision'],
            'revision_pin_present':item['source_revision'] is not None,
            'metadata_sha256':item['metadata_digest'],
            'matched_domains':sorted(shared),'relevance_score_hint':score,
            'declared_license':item['declared_license'],'license_status':'REVIEW_REQUIRED',
            'license_verified':False,'source_provenance_verified':False,
            'peer_identity_verified':False,'remote_auth_required_or_possible':item['remote_auth_required_or_possible'],
            'admission':'SOURCE_REVIEW_ONLY','execution_authorized':False,
            'research_next_step':'Verify original pinned source, license and scope before sandbox benchmark',
        })
    ranked.sort(key=lambda x:(-x['relevance_score_hint'],x['candidate_id']))
    if not requested:
        state='NO_GROUNDED_DOMAIN'
    elif not ranked:
        state='NO_RELEVANT_CANDIDATE'
    else:
        state='RESEARCH_ONLY'
    return {
        'schema':SCHEMA,'state':state,
        'query_sha256':hashlib.sha256(query.encode('utf-8')).hexdigest(),
        'requested_domains':sorted(requested),
        'candidate_count':len(entries),'excluded_count':excluded_count,
        'low_relevance_count':len(normalized)-len(ranked),
        'ranked':ranked[:limit],
        'ranked_result_total':len(ranked),
        'unknown_or_unmatched':state!='RESEARCH_ONLY',
        'requires_professional_review':'legal-compliance' in requested,
        'external_action_authorized':False,'autonomous_install_authorized':False,
        'settled_revenue_proven':False,
        'truth_boundary':'Public metadata is untrusted research. No installed skill, licensed reuse, expertise, identity, live API, provider auth, client access or income is proven.',
    }


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--index',required=True,type=Path,help='Local curated public metadata snapshot JSON')
    parser.add_argument('--query',required=True,help='Non-sensitive task summary; never echoed in output')
    parser.add_argument('--limit',type=int,default=8)
    args=parser.parse_args()
    try:
        raw=args.index.read_bytes()
        if len(raw)>MAX_SNAPSHOT_BYTES:
            raise ValueError('snapshot exceeds bounded discovery size')
        snapshot=json.loads(raw.decode('utf-8'),parse_constant=lambda _:(lambda: (_ for _ in ()).throw(ValueError('nonfinite JSON')))())
        result=scout(snapshot,args.query,limit=args.limit)
    except (OSError,ValueError,UnicodeDecodeError,RecursionError) as exc:
        print(json.dumps({'state':'BLOCKED','reason':str(exc)},ensure_ascii=False))
        return 2
    print(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True))
    return 0

if __name__=='__main__':
    raise SystemExit(main())
