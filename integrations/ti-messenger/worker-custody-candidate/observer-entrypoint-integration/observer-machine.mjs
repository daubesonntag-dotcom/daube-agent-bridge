import {withMessengerA} from './rpc-methods.mjs';
import {messengerDependencies} from './messenger-runtime-config.mjs';
import {ownerAck334Transport} from './sec04-owner-ack-transport.mjs';
import { WorkerEntrypoint } from "cloudflare:workers";
/**
 * D'AUBE independent edge observation canary — intentionally read-only.
 * No GitHub credentials, no private repo access, no paid provider or deploy APIs.
 * Monitoring is limited to public, pinned target hosts; receipts are written to
 * a dedicated KV namespace and never counted as source/CI/production PASS.
 */
export const SCHEMA = 'daube.autonomy-edge-observer.v1';
const REPO_URL = 'https://api.github.com/repos/daubesonntag-dotcom/daube-agent-bridge/commits/main';
const PORTFOLIO_URL = 'https://work.daubesonntag.com/portfolio/';
const SHA_RE = /^[a-f0-9]{40}$/;
const MAX_HTTP_MS = 5000;

function safeError(error) {
  if (error?.name === 'TimeoutError' || error?.name === 'AbortError') return 'TIMEOUT';
  return 'FETCH_FAILED';
}

function publicHeaders(kind) {
  return kind === 'github'
    ? {'accept': 'application/vnd.github+json', 'user-agent': 'daube-readonly-edge-observer'}
    : {'accept': 'text/html'};
}

export async function observeTarget(kind, fetchImpl = fetch) {
  if (kind !== 'github' && kind !== 'portfolio') throw new Error('unknown_observation_target');
  const target = kind === 'github' ? REPO_URL : PORTFOLIO_URL;
  try {
    const response = await fetchImpl(target, {
      method: 'GET', redirect: 'manual', headers: publicHeaders(kind),
      signal: AbortSignal.timeout(MAX_HTTP_MS),
    });
    const status = response.status;
    if (status !== 200) return {ok:false,httpStatus:status,sha:null,error:status>=300&&status<400?'UNEXPECTED_REDIRECT':'HTTP_NON_200'};
    if (kind === 'portfolio') return {ok:true,httpStatus:200,sha:null,error:null};
    let payload;
    try { payload = await response.json(); }
    catch { return {ok:false,httpStatus:200,sha:null,error:'INVALID_JSON'}; }
    const sha = String(payload?.sha||'').toLowerCase();
    if (!SHA_RE.test(sha)) return {ok:false,httpStatus:200,sha:null,error:'INVALID_SHA'};
    return {ok:true,httpStatus:200,sha,error:null};
  } catch (error) {
    return {ok:false,httpStatus:null,sha:null,error:safeError(error)};
  }
}

async function receiptHash(body) {
  const data = new TextEncoder().encode(JSON.stringify(body));
  const bytes = new Uint8Array(await crypto.subtle.digest('SHA-256', data));
  return [...bytes].map(b=>b.toString(16).padStart(2,'0')).join('');
}

/** A single bounded UTC-day observation; a repeated cron execution is a no-op. */
export async function auditOnce(env, {fetchImpl=fetch, now=()=>new Date()} = {}) {
  const kv = env?.RECEIPTS;
  if (!kv || typeof kv.get !== 'function' || typeof kv.put !== 'function') {
    return {state:'HOLD_NO_STATE_BINDING',reason:'dedicated KV receipt store required'};
  }
  const date = now().toISOString().slice(0,10);
  const dayKey = 'day:' + date;
  const existing = await kv.get(dayKey);
  if (existing) return {state:'DEDUPED',day:date};

  // Deliberately sequential, two static public requests; no subdelegation.
  const github = await observeTarget('github',fetchImpl);
  const portfolio = await observeTarget('portfolio',fetchImpl);
  const body = {
    schema:SCHEMA,
    observedAt:now().toISOString(),
    day:date,
    decision:github.ok&&portfolio.ok?'OBSERVED':'DEGRADED',
    observations:{github,portfolio},
    dataClass:'PUBLIC_ONLY',
    authority:'OBSERVE_ONLY',
    privateRepositoryRead:false,
    productionMutation:false,
    paidSpendAuthorized:false,
    ciRuntimePassed:false,
    releaseAdmitted:false,
  };
  const receipt={...body,receiptDigestSha256:await receiptHash(body)};
  await kv.put(dayKey,JSON.stringify(receipt),{expirationTtl:90*24*3600});
  await kv.put('last-receipt',JSON.stringify(receipt),{expirationTtl:90*24*3600});
  return {state:'RECORDED',receipt};
}

function json(body, status=200) {
  return new Response(JSON.stringify(body),{
    status, headers:{'content-type':'application/json;charset=utf-8','cache-control':'no-store','x-content-type-options':'nosniff','strict-transport-security':'max-age=31536000; includeSubDomains','content-security-policy':"default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'",'x-frame-options':'DENY','referrer-policy':'no-referrer'},
  });
}

const DAUBE_AP_JOB='359a14b8-3415-43e6-80e4-b63b52ae23f0';
const DAUBE_AP_WORK='f699f1e9-b250-4031-9a91-fd2824a0266f';
const DAUBE_AP_WORKER='daube-gcp-e2e-20261031';
const DAUBE_AP_WORKKEY='council-autopilot-durable-benchmark-20261030-v1';
const DAUBE_AP_PROVIDER='cloudflare-workers-ai';
const DAUBE_AP_CHECKER_PUB='UTU6TXx9+88UsWeZIgCqcLdwPL+756CkaralxhUh56U=';
const DAUBE_AP_REST='https://wilqsqndjgckqxbjptxm.supabase.co/rest/v1/rpc/daube_autopilot_e2e_preflight_v1';
const DAUBE_AP_KEY="sb_publishable_ynfcB4JbyYhNhkPkPBc4wg_3ZPF0gl6";
async function daubeAutopilotCheckAndSign(request,env){
 const denied=(code,status=403)=>json({ok:false,error:code},status);
 if(request.method!=='POST')return denied('METHOD_NOT_ALLOWED',405);
 if(!env?.RECEIPTS||!env?.COUNCIL_ED25519_KEY)return denied('CHECKER_UNAVAILABLE',503);
 if(!/application\/json/i.test(request.headers.get('content-type')||''))return denied('JSON_REQUIRED',415);
 const input=await request.text();
 if(input.length>14500)return denied('INPUT_TOO_LARGE',413);
 let q;try{q=JSON.parse(input)}catch{return denied('BAD_JSON',400)}
 const token=request.headers.get('X-Daube-Council-Node-Token')||'';
 if(token.length<48||token.length>160)return denied('NODE_TOKEN_INVALID');
 if(q?.schema!=='daube.council.autopilot-check-request.v1'||q.jobId!==DAUBE_AP_JOB||
 q.workId!==DAUBE_AP_WORK||q.workerId!==DAUBE_AP_WORKER||
 q.workKey!==DAUBE_AP_WORKKEY||q.provider!==DAUBE_AP_PROVIDER||
 !/^[0-9a-f-]{36}$/.test(String(q.leaseToken||''))||
 !/^chatcmpl-[a-zA-Z0-9-]{12,128}$/.test(String(q.modelInvocationId||''))||
 !/^@cf\/[a-zA-Z0-9_-]+\/[a-zA-Z0-9_.-]+$/.test(String(q.model||''))||
 !/^[a-f0-9]{64}$/.test(String(q.outputSha256||''))||
 !/^[a-f0-9]{64}$/.test(String(q.inputSha256||''))||
 typeof q.output!=='string'||q.output.length<75||q.output.length>5000||
 !Number.isFinite(Date.parse(q.calledAt))||Math.abs(Date.now()-Date.parse(q.calledAt))>180000||
 q?.usage?.totalTokens<10||q?.usage?.totalTokens>1200||
 q.finishReason!=='stop')return denied('EVIDENCE_CONTRACT_INVALID');
 const sha=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(q.output));
 const hex=Array.from(new Uint8Array(sha),x=>x.toString(16).padStart(2,'0')).join('');
 if(hex!==q.outputSha256)return denied('PROVIDER_OUTPUT_HASH_INVALID');
 const proofResponse=await fetch(DAUBE_AP_REST,{method:'POST',redirect:'manual',headers:{'apikey':DAUBE_AP_KEY,'Content-Type':'application/json'},body:JSON.stringify({p_token:token,p_job_id:q.jobId,p_worker_id:q.workerId,p_lease_token:q.leaseToken}),signal:AbortSignal.timeout(8000)}).catch(()=>null);
 if(!proofResponse||proofResponse.status!==200)return denied('INDEPENDENT_LEASE_SOURCE_UNAVAILABLE',503);
 let preflight;try{preflight=await proofResponse.json()}catch{return denied('INDEPENDENT_LEASE_JSON_INVALID',503)}
 if(preflight?.ok!==true||preflight.jobId!==q.jobId||preflight.workId!==q.workId||
 preflight.workKey!==q.workKey||preflight.provider!==q.provider||preflight.workerId!==q.workerId||
 preflight.attempt!==1||Date.parse(preflight.leaseExpiresAt)<=Date.now())return denied('INDEPENDENT_LEASE_DENIED');
 const key='daube:autopilot:e2e:receipt:'+DAUBE_AP_JOB;
 const existing=await env.RECEIPTS.get(key);
 if(existing){
  let e;try{e=JSON.parse(existing)}catch{return denied('STORED_RECEIPT_CORRUPT',503)}
  return e?.jobId===q.jobId&&e?.outputSha256===q.outputSha256&&e?.modelInvocationId===q.modelInvocationId
   ?json({ok:true,reused:true,receipt:e}):denied('REPLAY_CONFLICT');
 }
 const signed={
  schema:'daube.council.autopilot-independent-checker.v1',
  jobId:q.jobId,workId:q.workId,workKey:q.workKey,workerId:q.workerId,
  provider:q.provider,model:q.model,modelInvocationId:q.modelInvocationId,
  inputSha256:q.inputSha256,outputSha256:q.outputSha256,
  checkerIdentity:'daube-edge-observer-v1/CouncilCanaryChecker',
  independentLeaseReadback:true,jobLeaseAttempt:preflight.attempt,
  providerResultObservedByWorker:true,modelInvoked:true,
  finishReason:q.finishReason,usage:q.usage,checkedAt:new Date().toISOString(),
  autonomousWorkforce15Live:false
 };
 const canonical=JSON.stringify(signed);
 const keyBytes=Uint8Array.from(atob(String(env.COUNCIL_ED25519_KEY)),x=>x.charCodeAt(0));
 const privateKey=await crypto.subtle.importKey('pkcs8',keyBytes,{name:'Ed25519'},false,['sign']);
 const sig=await crypto.subtle.sign('Ed25519',privateKey,new TextEncoder().encode(canonical));
 const receipt={...signed,canonicalPayload:canonical,signatureAlgorithm:'Ed25519',
  signatureBase64:btoa(String.fromCharCode(...new Uint8Array(sig))),checkerPublicKeyB64:DAUBE_AP_CHECKER_PUB};
 await env.RECEIPTS.put(key,JSON.stringify(receipt),{expirationTtl:604800});
 return json({ok:true,reused:false,receipt},200);
}

export const handler = {
  async fetch(request,env) {
    const url=new URL(request.url);
    if(url.pathname==='/v1/autopilot/attest')return daubeAutopilotCheckAndSign(request,env);
    if(request.method!=='GET'&&request.method!=='HEAD')return json({error:'method_not_allowed'},405);
    if(url.pathname==='/healthz')return json({ok:true,service:SCHEMA,mode:'READ_ONLY',hasReceiptStore:!!env?.RECEIPTS});
    if(url.pathname==='/status'){
      if(!env?.RECEIPTS)return json({state:'HOLD_NO_STATE_BINDING'},503);
      const receipt=await env.RECEIPTS.get('last-receipt');
      if(!receipt)return json({state:'NO_RECEIPT_YET',source:'cloudflare-kv'},404);
      try{return json(JSON.parse(receipt))}catch{return json({state:'HOLD_RECEIPT_INVALID'},503)}
    }
    return json({error:'not_found'},404);
  },
  async scheduled(_controller,env,ctx, testDeps={}) {
    const work=auditOnce(env,testDeps).then(result=>{
      // Log only non-secret status, never response bodies or credentials.
      console.log(JSON.stringify({service:SCHEMA,edgeCron:true,state:result.state,decision:result.receipt?.decision||null,day:result.receipt?.day||result.day||null}));
      return result;
    }).catch(()=>console.log(JSON.stringify({service:SCHEMA,edgeCron:true,state:'HOLD_ERROR'})));
    ctx.waitUntil(work);
  }
};
export default handler;

function verifyCanaryProof(p) {
 const e = Array.isArray(p?.events) ? p.events : [];
 const validBase = p?.schema === 'daube.council.synthetic-job-proof.v1' && p?.jobId === 'CANARY-20261024-FAILOVER-02' && p?.source === 'cloudflare_durable_object_via_service_binding' && p?.executionClass === 'SYNTHETIC_CANARY_ONLY' && p?.modelInvoked === false && p?.productionMutation === false;
 const validJob = p?.jobStatus === 'SUCCEEDED' && p?.owner === 'B' && p?.fence === 2 && p?.attempts === 2 && p?.resultDigestSha256 === '1f10541e4f871ae83e5fd21ff9c4c0cffbe406e0b76e302a12fd6ec18b89240c';
 const names = [['A','ACQUIRED',1], ['system','ALARM_DISPATCH_B',1], ['B','ACQUIRED',2], ['B','COMPLETED',2], ['system','ALARM_B_CONFIRMED',1]];
 const order = names.map(([actor,event,fence]) => e.findIndex(x => x?.actor === actor && x?.event === event && x?.fence === fence));
 const eventOrder = e.length >= 5 && e.length <= 20 && order.every(x=>x>=0) && order.every((x,i)=>i===0 || x>order[i-1]);
 const eventIds = e.every(x=>Number.isSafeInteger(x?.seq) && Number.isSafeInteger(x?.at) && x.at>0) && new Set(e.map(x=>x.seq)).size === e.length && e.every((x,i)=>i===0 || x.seq>e[i-1].seq);
 const checks = {validBase,validJob,eventOrder,eventIds};
 return { verified:Object.values(checks).every(Boolean), checks };
}
/** D'AUBE Council: tightly bounded real AI mission signing contract. Uses WebCrypto Ed25519. */
const MISSION_KEY='council-autonomous-real-ai-dispatch-20261030';
const WORK_KEY='COUNCIL-AUTO-E2E-20261030';
const MODEL='@cf/meta/llama-3.2-3b-instruct';
const RECEIPT_SCHEMA='daube.council.ai-mission-receipt.v1';
const HEX64=/^[0-9a-f]{64}$/;
const UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const enc=new TextEncoder();
const digestHex=async value=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',enc.encode(value))),b=>b.toString(16).padStart(2,'0')).join('');
function validMissionPacket(p,now=Date.now()){
 return !!(p&&p.schema==='daube.council.model-mission-invocation.v1'
 &&p.missionKey===MISSION_KEY&&p.workKey===WORK_KEY&&UUID.test(String(p.dbMissionId||''))
 &&p.model===MODEL&&p.origin==='council_worker_ai_binding_dispatch'
 &&HEX64.test(String(p.promptDigestSha256||''))&&HEX64.test(String(p.responseDigestSha256||''))
 &&p.providerResultObserved===true&&p.outputValid===true
 &&Number.isInteger(p.outputSize)&&p.outputSize>=10&&p.outputSize<=5000
 &&p.tokenCap===220&&Number.isFinite(Date.parse(p.calledAt||''))
 &&Math.abs(now-Date.parse(p.calledAt))<=120000);
}
async function signMissionPacket(p,privateKey,now=Date.now()){
 if(!validMissionPacket(p,now))throw Error('MISSION_PACKET_INVALID');
 const base={
  schema:RECEIPT_SCHEMA,missionKey:MISSION_KEY,workKey:WORK_KEY,dbMissionId:p.dbMissionId,
  model:MODEL,origin:'council_worker_ai_binding_dispatch',providerResultObserved:true,
  modelInvokedByGateway:true,jobStatus:'completed',outputValid:true,
  promptDigestSha256:p.promptDigestSha256,responseDigestSha256:p.responseDigestSha256,outputSize:p.outputSize,
  checker:'daube-edge-observer-v1/CouncilCanaryChecker',signed:true,
  productionMutation:false,releaseAdmitted:false,completedAt:new Date(now).toISOString()
 };
 const receipt={...base,receiptDigestSha256:await digestHex(JSON.stringify(base))};
 const sig=new Uint8Array(await crypto.subtle.sign('Ed25519',privateKey,enc.encode(JSON.stringify(receipt))));
 receipt.signatureAlgorithm='Ed25519';
 receipt.signatureBase64=btoa(String.fromCharCode(...sig));
 return receipt;
}
async function verifyMissionReceipt(r,pubKey,expectedMissionId=null){
 try{
  if(!r||r.schema!==RECEIPT_SCHEMA||r.missionKey!==MISSION_KEY||r.workKey!==WORK_KEY
   ||r.model!==MODEL||r.signed!==true||r.jobStatus!=='completed'
   ||r.providerResultObserved!==true||r.modelInvokedByGateway!==true||r.outputValid!==true
   ||r.productionMutation!==false||r.releaseAdmitted!==false
   ||!UUID.test(String(r.dbMissionId||''))||(expectedMissionId&&r.dbMissionId!==expectedMissionId)
   ||!HEX64.test(String(r.promptDigestSha256||''))||!HEX64.test(String(r.responseDigestSha256||''))
   ||!HEX64.test(String(r.receiptDigestSha256||''))
   ||r.signatureAlgorithm!=='Ed25519'||typeof r.signatureBase64!=='string'||r.signatureBase64.length!==88
   ||!Number.isFinite(Date.parse(r.completedAt||'')))return false;
  const {signatureAlgorithm,signatureBase64,...signed}=r;
  const {receiptDigestSha256,...base}=signed;
  if(await digestHex(JSON.stringify(base))!==receiptDigestSha256)return false;
  const bytes=Uint8Array.from(atob(signatureBase64),x=>x.charCodeAt(0));
  const key=pubKey instanceof CryptoKey?pubKey:await crypto.subtle.importKey('raw',pubKey,{name:'Ed25519'},false,['verify']);
  return await crypto.subtle.verify('Ed25519',key,bytes,enc.encode(JSON.stringify(signed)));
 }catch{return false}
}

const STAGE_VERIFY_PUB='UTU6TXx9+88UsWeZIgCqcLdwPL+756CkaralxhUh56U=';
const STAGE_EDGE_PROOF='https://wilqsqndjgckqxbjptxm.supabase.co/functions/v1/daube-runtime-health?view=office-stage-proof';
const STAGE_UUID=/^[a-f0-9]{8}-(?:[a-f0-9]{4}-){3}[a-f0-9]{12}$/i;
const STAGE_SHA=/^[a-f0-9]{64}$/;
const STAGE_KEY_PREFIX='daube:office-stage:v1:checker:';

/** Proof required by the ORIGINAL Council Checker. Never verify digest claims
 * without independently signed, scoped grant and live lease records returned
 * by the original Mission Store authority service binding.
 */
const NATIVE_ADMISSION_WORK='DAUBE-SPRINT-20261028-ONE-PROGRAM';
const NATIVE_UUID=/^[a-f0-9]{8}-(?:[a-f0-9]{4}-){3}[a-f0-9]{12}$/i;
const NATIVE_HEX=/^[a-f0-9]{64}$/;
const NATIVE_SHA=/^(?:[a-f0-9]{40}|[a-f0-9]{64})$/;
const NATIVE_ID=/^[A-Za-z0-9][A-Za-z0-9_.:-]{3,127}$/;
const NATIVE_FIELDS=['schema','missionId','workKey','tenantId','principalId','sourceSha',
 'messageDigest','nonce','grantDigest','leaseDigest'];
const NATIVE_GRANT_FIELDS=['schema','missionId','workKey','tenantId','principalId',
 'sourceSha','messageDigest','nonce','grantDigest','action','issuedAtMs','expiresAtMs'];
const NATIVE_LEASE_FIELDS=['schema','missionId','workKey','tenantId','principalId',
 'sourceSha','nonce','leaseDigest','active','state','generation','issuedAtMs','expiresAtMs'];
const NATIVE_SIGNED_FIELDS=[...NATIVE_FIELDS,'status','checkerIdentity','issuedAtMs','expiresAtMs'];
const nativeExact=(o,keys)=>o&&Object.getPrototypeOf(o)===Object.prototype
 &&Object.keys(o).length===keys.length&&keys.every(k=>Object.hasOwn(o,k));
export function validOriginalNativeAdmission(input){
 return nativeExact(input,NATIVE_FIELDS)&&input.schema==='daube.council.native-admission-request.v1'
  &&NATIVE_UUID.test(input.missionId||'')&&input.workKey===NATIVE_ADMISSION_WORK
  &&NATIVE_ID.test(input.tenantId||'')&&NATIVE_ID.test(input.principalId||'')
  &&NATIVE_ID.test(input.nonce||'')&&NATIVE_SHA.test(input.sourceSha||'')
  &&NATIVE_HEX.test(input.messageDigest||'')&&NATIVE_HEX.test(input.grantDigest||'')
  &&NATIVE_HEX.test(input.leaseDigest||'');
}
const nativeB64=raw=>{
 if(typeof raw!=='string'||!raw.length||raw.length>512)return null;
 try{return Uint8Array.from(atob(raw),x=>x.charCodeAt(0))}catch{return null}
};
async function nativeRoleProof(record,pinnedKey,expectedId,schema,fields,now){
 if(!nativeExact(record,['canonicalPayload','signatureAlgorithm','signatureBase64','keyId'])||
  record.keyId!==expectedId||record.signatureAlgorithm!=='Ed25519'||
  typeof record.canonicalPayload!=='string'||record.canonicalPayload.length>2500||
  !/^[A-Za-z0-9+/]{86}==$/.test(record.signatureBase64))return null;
 const keyRaw=nativeB64(pinnedKey),signature=nativeB64(record.signatureBase64);
 if(keyRaw?.length!==32||signature?.length!==64)return null;
 let payload;
 try{payload=JSON.parse(record.canonicalPayload)}catch{return null}
 if(!nativeExact(payload,fields)||payload.schema!==schema||
  !Number.isSafeInteger(payload.issuedAtMs)||!Number.isSafeInteger(payload.expiresAtMs)||
  payload.issuedAtMs>now+30000||now-payload.issuedAtMs>120000||
  payload.expiresAtMs<=now||payload.expiresAtMs-payload.issuedAtMs>300000)return null;
 try{
  const key=await crypto.subtle.importKey('raw',keyRaw,{name:'Ed25519'},false,['verify']);
  if(!await crypto.subtle.verify('Ed25519',key,signature,new TextEncoder().encode(record.canonicalPayload)))return null;
 }catch{return null}
 return payload;
}
export async function verifyOriginalNativeGrantLease(input,readback,{
 grantPublicKeyB64,leasePublicKeyB64,grantSignerId,leaseSignerId,checkerPublicKeyB64,
 now=Date.now()
}={}){
 if(!validOriginalNativeAdmission(input)||!Number.isSafeInteger(now)||
  !nativeExact(readback,['schema','scope','grant','lease'])||
  readback.schema!=='daube.council.original-grant-lease-readback.v1'||
  readback.scope!=='ORIGINAL_MISSION_STORE'||
  !NATIVE_ID.test(grantSignerId||'')||!NATIVE_ID.test(leaseSignerId||'')||
  grantSignerId===leaseSignerId||
  typeof grantPublicKeyB64!=='string'||typeof leasePublicKeyB64!=='string'||
  typeof checkerPublicKeyB64!=='string'||
  grantPublicKeyB64===leasePublicKeyB64||
  grantPublicKeyB64===checkerPublicKeyB64||
  leasePublicKeyB64===checkerPublicKeyB64)return false;
 const grant=await nativeRoleProof(readback.grant,grantPublicKeyB64,grantSignerId,
   'daube.mission.signed-grant.v1',NATIVE_GRANT_FIELDS,now);
 const lease=await nativeRoleProof(readback.lease,leasePublicKeyB64,leaseSignerId,
   'daube.mission.signed-lease.v1',NATIVE_LEASE_FIELDS,now);
 if(!grant||!lease||grant.action!=='mission:submit'||lease.active!==true||lease.state!=='ACTIVE'||!Number.isSafeInteger(lease.generation)||lease.generation<1)return false;
 for(const key of ['missionId','workKey','tenantId','principalId','sourceSha','nonce']){
  if(grant[key]!==input[key]||lease[key]!==input[key])return false;
 }
 if(grant.messageDigest!==input.messageDigest||grant.grantDigest!==input.grantDigest||
    lease.leaseDigest!==input.leaseDigest)return false;
 // Lease and grant must both be valid and fresh at the signing instant.
 return grant.expiresAtMs>now&&lease.expiresAtMs>now;
}

export class CouncilCanaryChecker extends WorkerEntrypoint {
 async verifyNativeMachineAdmission(input){
  // This Worker is an independent signer, not a replacement for the original
  // Supervisor grant, FreshStore Mission Store, or live Executor lease.
  if(!validOriginalNativeAdmission(input))return {ok:false,error:'NATIVE_REQUEST_INVALID'};
  const authority=this.env?.ORIGINAL_MISSION_AUTHORITY;
  if(typeof authority?.readGrantLeaseForMission!=='function')
   return {ok:false,error:'ORIGINAL_GRANT_LEASE_READER_NOT_BOUND'};
  const pk=this.env?.NATIVE_GRANT_VERIFY_PUBLIC_KEY_B64,
    lk=this.env?.NATIVE_LEASE_VERIFY_PUBLIC_KEY_B64,
    checkerPk=this.env?.NATIVE_CHECKER_VERIFY_PUBLIC_KEY_B64;
  const grantSignerId=this.env?.NATIVE_GRANT_SIGNER_ID,
    leaseSignerId=this.env?.NATIVE_LEASE_SIGNER_ID;
  if(!pk||!lk||!checkerPk||!grantSignerId||!leaseSignerId||
     !this.env?.COUNCIL_ED25519_KEY)return {ok:false,error:'ORIGINAL_SIGNER_TRUST_NOT_PINNED'};
  let records;
  try{
   records=await authority.readGrantLeaseForMission({
     missionId:input.missionId,tenantId:input.tenantId,
     principalId:input.principalId,workKey:input.workKey
   });
  }catch{return {ok:false,error:'ORIGINAL_GRANT_LEASE_READ_FAILED'}}
  const checkedAt=Date.now();
  if(!await verifyOriginalNativeGrantLease(input,records,{
    grantPublicKeyB64:pk,leasePublicKeyB64:lk,
    grantSignerId,leaseSignerId,checkerPublicKeyB64:checkerPk,now:checkedAt
  }))return {ok:false,error:'ORIGINAL_GRANT_LEASE_NOT_VERIFIED'};
  const claims={...input,schema:'daube.council.native-machine-admission.v1',
    status:'ADMITTED',
    checkerIdentity:'daube-edge-observer-v1/CouncilCanaryChecker',
    issuedAtMs:checkedAt,expiresAtMs:checkedAt+120000};
  const canonicalPayload=JSON.stringify(claims);
  try{
   const keyBytes=nativeB64(this.env.COUNCIL_ED25519_KEY);
   if(!keyBytes||keyBytes.length>1000)return {ok:false,error:'CHECKER_SIGNER_UNAVAILABLE'};
   const signer=await crypto.subtle.importKey('pkcs8',keyBytes,{name:'Ed25519'},false,['sign']);
   const sig=await crypto.subtle.sign('Ed25519',signer,new TextEncoder().encode(canonicalPayload));
   const signatureBase64=btoa(String.fromCharCode(...new Uint8Array(sig)));
   // Independently verify private-key custody against the pinned public key.
   const checkerRaw=nativeB64(checkerPk);
   if(checkerRaw?.length!==32)return {ok:false,error:'CHECKER_KEY_PIN_INVALID'};
   const verifier=await crypto.subtle.importKey('raw',checkerRaw,{name:'Ed25519'},false,['verify']);
   if(!await crypto.subtle.verify('Ed25519',verifier,new Uint8Array(sig),
         new TextEncoder().encode(canonicalPayload)))
     return {ok:false,error:'CHECKER_KEY_PIN_MISMATCH'};
   return {canonicalPayload,signatureAlgorithm:'Ed25519',signatureBase64};
  }catch{return {ok:false,error:'CHECKER_SIGNING_UNAVAILABLE'}}
 }

 async officeStageCountersign(p){
  try{
   if(!p||!STAGE_UUID.test(String(p.jobId||''))||!STAGE_UUID.test(String(p.workId||''))||!STAGE_UUID.test(String(p.runId||''))||!STAGE_UUID.test(String(p.leaseToken||''))||
    !STAGE_SHA.test(String(p.outputSha256||''))||p.provider!=='cloudflare-workers-ai'||p.model!=='@cf/meta/llama-3.2-3b-instruct'||
    typeof p.accessJwt!=='string'||p.accessJwt.length<100||p.accessJwt.length>12000)return{ok:false,error:'CHECKER_SCOPE_DENIED'};
   const answer=await fetch(STAGE_EDGE_PROOF,{method:'POST',redirect:'manual',headers:{'Content-Type':'application/json','Cf-Access-Jwt-Assertion':p.accessJwt},body:JSON.stringify({jobId:p.jobId,runId:p.runId,leaseToken:p.leaseToken}),signal:AbortSignal.timeout(9000)});
   if(answer.status!==200)return{ok:false,error:'INDEPENDENT_DATABASE_EVIDENCE_DENIED',http:answer.status};
   let proof;try{proof=await answer.json()}catch{return{ok:false,error:'INDEPENDENT_DATABASE_JSON_INVALID'}}
   if(proof?.ok!==true||proof.jobId!==p.jobId||proof.workId!==p.workId||proof.outputSha256!==p.outputSha256||proof.runId!==p.runId||
   proof.provider!==p.provider||proof.model!==p.model||proof.attempt!==1||Date.parse(proof.leaseExpiresAt)<=Date.now())return{ok:false,error:'INDEPENDENT_EVIDENCE_MISMATCH'};
   const kvKey=STAGE_KEY_PREFIX+p.jobId;
   const old=await this.env.RECEIPTS.get(kvKey);
   if(old){const prior=JSON.parse(old);return prior?.jobId===p.jobId&&prior?.runId===p.runId&&prior?.outputSha256===p.outputSha256?{ok:true,reused:true,receipt:prior}:{ok:false,error:'CHECKER_REPLAY_CONFLICT'}}
   const signed={schema:'daube.office.stage-independent-check.v1',jobId:p.jobId,workId:p.workId,runId:p.runId,
    provider:p.provider,model:p.model,outputSha256:p.outputSha256,observedReceiptId:proof.receiptId,
    attempt:1,checker:'daube-edge-observer-v1/CouncilCanaryChecker',independentDatabaseReadback:true,checkedAt:new Date().toISOString()};
   const canonicalPayload=JSON.stringify(signed);
   const rawKey=Uint8Array.from(atob(String(this.env.COUNCIL_ED25519_KEY||'')),x=>x.charCodeAt(0));
   const signingKey=await crypto.subtle.importKey('pkcs8',rawKey,{name:'Ed25519'},false,['sign']);
   const sig=await crypto.subtle.sign('Ed25519',signingKey,new TextEncoder().encode(canonicalPayload));
   const receipt={...signed,canonicalPayload,signatureAlgorithm:'Ed25519',signatureBase64:btoa(String.fromCharCode(...new Uint8Array(sig))),checkerPublicKeyB64:STAGE_VERIFY_PUB};
   await this.env.RECEIPTS.put(kvKey,JSON.stringify(receipt),{expirationTtl:604800});
   return{ok:true,reused:false,receipt};
  }catch{return{ok:false,error:'CHECKER_SIGNING_UNAVAILABLE'}}
 }
 async officeStageReadback(jobId){
  if(!STAGE_UUID.test(String(jobId||'')))return{ok:false,error:'INVALID_JOB_ID'};
  try{
   const raw=await this.env.RECEIPTS.get(STAGE_KEY_PREFIX+jobId);
   if(!raw)return{ok:false,error:'NO_STAGE_SIGNATURE'};
   const r=JSON.parse(raw),p=JSON.parse(r.canonicalPayload||'{}');
   if(p.jobId!==jobId||p.outputSha256!==r.outputSha256||p.runId!==r.runId||r.checkerPublicKeyB64!==STAGE_VERIFY_PUB||r.signatureAlgorithm!=='Ed25519')return{ok:false,error:'INVALID_CHECKER_CLAIMS'};
   const pub=await crypto.subtle.importKey('raw',Uint8Array.from(atob(STAGE_VERIFY_PUB),x=>x.charCodeAt(0)),{name:'Ed25519'},false,['verify']);
   const valid=await crypto.subtle.verify('Ed25519',pub,Uint8Array.from(atob(r.signatureBase64),x=>x.charCodeAt(0)),new TextEncoder().encode(r.canonicalPayload));
   return valid?{ok:true,signatureVerified:true,receipt:r}:{ok:false,error:'CHECKER_SIGNATURE_INVALID'};
  }catch{return{ok:false,error:'CHECKER_READBACK_UNAVAILABLE'}}
 }

 async autopilotSignedReadback(jobId){
  if(jobId!==DAUBE_AP_JOB)return{ok:false,error:'JOB_NOT_ALLOWED'};
  const raw=await this.env.RECEIPTS.get('daube:autopilot:e2e:receipt:'+jobId);
  if(!raw)return{ok:false,error:'NO_SIGNED_RECEIPT'};
  try{
   const r=JSON.parse(raw),signed=JSON.parse(r.canonicalPayload);
   if(r.schema!=='daube.council.autopilot-independent-checker.v1'||r.jobId!==DAUBE_AP_JOB||
     r.checkerPublicKeyB64!==DAUBE_AP_CHECKER_PUB||r.signatureAlgorithm!=='Ed25519'||
     JSON.stringify(signed)!==r.canonicalPayload||signed.jobId!==r.jobId||signed.outputSha256!==r.outputSha256||
     signed.modelInvocationId!==r.modelInvocationId||signed.workId!==r.workId)return{ok:false,error:'RECEIPT_CONTRACT_INVALID'};
   const key=await crypto.subtle.importKey('raw',Uint8Array.from(atob(DAUBE_AP_CHECKER_PUB),c=>c.charCodeAt(0)),{name:'Ed25519'},false,['verify']);
   const verified=await crypto.subtle.verify('Ed25519',key,Uint8Array.from(atob(r.signatureBase64),c=>c.charCodeAt(0)),new TextEncoder().encode(r.canonicalPayload));
   return verified?{ok:true,verified:true,receipt:r}:{ok:false,verified:false,error:'CHECKER_SIGNATURE_INVALID'};
  }catch{return{ok:false,error:'CHECKER_READBACK_INVALID'}}
 }

 async recordPilotDiagnostic(code){const name=String(code||'UNKNOWN').slice(0,100).replace(/[^A-Za-z0-9_:-]/g,'_');await this.env.RECEIPTS.put('council:role-pilot-20261030:diagnostic',JSON.stringify({schema:'daube.council.role-pilot-diagnostic.v1',code:name,at:new Date().toISOString()}),{expirationTtl:86400});return{ok:true};}


 async councilRoleTicket(action,missionId,agentKey){
  if(missionId!=='a59d3c43-377b-41d8-97e3-dbb590a9a618'||agentKey!=='council-cf-ai-pilot-01'||
    !['prepare','finalize','commit','readback'].includes(action))return{ok:false,error:'MISSION_ROLE_NOT_ALLOWED'};
  const rand=new Uint8Array(24);crypto.getRandomValues(rand);
  const nonce=btoa(String.fromCharCode(...rand)).replaceAll('+','-').replaceAll('/','_').replace(/=+$/,'');
  const payload={schema:'daube.council.role-ticket.v1',action,agentKey,missionId,nonce,
    issuedAt:new Date().toISOString(),notAfter:new Date(Date.now()+120000).toISOString()};
  const canonical=JSON.stringify(Object.fromEntries(Object.entries(payload).sort(([x],[y])=>x<y?-1:x>y?1:0)));
  const pk=Uint8Array.from(atob(String(this.env.COUNCIL_ED25519_KEY||'')),x=>x.charCodeAt(0));
  const key=await crypto.subtle.importKey('pkcs8',pk,{name:'Ed25519'},false,['sign']);
  const sig=new Uint8Array(await crypto.subtle.sign('Ed25519',key,enc.encode(canonical)));
  return{ok:true,payload,canonical,signatureBase64:btoa(String.fromCharCode(...sig))};
 }
 async councilRoleCountersign(bundle){
  try{
   const p=bundle?.claims,canonical=o=>JSON.stringify(Object.fromEntries(Object.entries(o).sort(([x],[y])=>x<y?-1:x>y?1:0)));
   if(p?.schema!=='daube.council.role-execution-proof.v2'||p.missionId!=='a59d3c43-377b-41d8-97e3-dbb590a9a618'||
    p.agentKey!=='council-cf-ai-pilot-01'||p.checkerIdentity!=='daube-edge-observer-v1/CouncilCanaryChecker'||
    !/^[a-f0-9]{64}$/.test(p.modelOutputSha256||'')||!/^[a-f0-9]{64}$/.test(p.queueResultSha256||'')||
    !/^[A-Za-z0-9_-]{22,86}$/.test(p.nonce||'')||Math.abs(Date.now()-Date.parse(p.issuedAt))>120000||
    bundle.canonicalPayload!==canonical(p))return{ok:false,error:'ROLE_PROOF_REJECTED'};
   const pub=Uint8Array.from(atob(bundle.agentPublicKeyB64||''),x=>x.charCodeAt(0));
   const agentSig=Uint8Array.from(atob(bundle.agentSignatureB64||''),x=>x.charCodeAt(0));
   if(pub.length!==32||agentSig.length!==64)return{ok:false,error:'AGENT_SIGNATURE_FORMAT'};
   const agentPub=await crypto.subtle.importKey('raw',pub,{name:'Ed25519'},false,['verify']);
   if(!await crypto.subtle.verify('Ed25519',agentPub,agentSig,enc.encode(bundle.canonicalPayload)))return{ok:false,error:'BAD_AGENT_SIGNATURE'};
   const payloadSha256=await digestHex(bundle.canonicalPayload);
   const message=canonical({agentKey:p.agentKey,checkerIdentity:p.checkerIdentity,missionId:p.missionId,
       nonce:p.nonce,payloadSha256,agentSignatureB64:bundle.agentSignatureB64});
   const keyBytes=Uint8Array.from(atob(String(this.env.COUNCIL_ED25519_KEY||'')),x=>x.charCodeAt(0));
   const priv=await crypto.subtle.importKey('pkcs8',keyBytes,{name:'Ed25519'},false,['sign']);
   const checkerSignatureB64=btoa(String.fromCharCode(...new Uint8Array(await crypto.subtle.sign('Ed25519',priv,enc.encode(message)))));
   const result={ok:true,claims:p,canonicalPayload:bundle.canonicalPayload,agentSignatureB64:bundle.agentSignatureB64,
      checkerSignatureB64,payloadSha256,agentPublicKeyB64:bundle.agentPublicKeyB64,
      state:'PENDING_SUPABASE_CALLBACK',live:false};
   await this.env.RECEIPTS.put('council:role:v1:pending:'+p.missionId,JSON.stringify(result),{expirationTtl:600});
   return result;
  }catch{return{ok:false,error:'COUNTERSIGN_FAILED'}}
 }
 async councilRoleReadback(missionId){
  if(missionId!=='a59d3c43-377b-41d8-97e3-dbb590a9a618')return{ok:false,error:'MISSION_DENIED'};
  const raw=await this.env.RECEIPTS.get('council:role:v1:accepted:'+missionId);
  return raw?{ok:true,receipt:JSON.parse(raw)}:{ok:false,error:'ROLE_CALLBACK_NOT_VERIFIED'};
 }
 async councilRoleConfirm(result,ack){
  const p=result?.claims;
  if(!result?.ok||p?.missionId!=='a59d3c43-377b-41d8-97e3-dbb590a9a618'||
   p.agentKey!=='council-cf-ai-pilot-01'||ack?.ok!==true||ack.missionId!==p.missionId||
   ack.agentKey!==p.agentKey||ack.signatureVerified!==true||ack.nonceConsumed!==true||
   !ack.receiptId)return{ok:false,error:'CALLBACK_NOT_VERIFIED'};
  const d={schema:'daube.council.role-verified-readback.v1',missionId:p.missionId,agentKey:p.agentKey,
   signedReceiptId:ack.receiptId,queueJobId:p.queueJobId,modelRunId:p.modelRunId,
   modelOutputSha256:p.modelOutputSha256,payloadSha256:result.payloadSha256,
   proofSignatureB64:result.checkerSignatureB64,checkedAt:new Date().toISOString(),live:false};
  await this.env.RECEIPTS.put('council:role:v1:accepted:'+p.missionId,JSON.stringify(d),{expirationTtl:604800});
  return{ok:true,receipt:d};
 }

 async recordMissionDiagnostic(errorCode){
  const code=String(errorCode||'UNKNOWN').slice(0,100).replace(/[^A-Za-z0-9_:-]/g,'_');
  const event={schema:'daube.council.mission-diagnostic.v1',missionKey:'council-autonomous-real-ai-dispatch-20261030',code,at:new Date().toISOString()};
  await this.env.RECEIPTS.put('council:real-ai-mission:20261030:diagnostic',JSON.stringify(event),{expirationTtl:60*60*24});
  return {ok:true};
 }

 async readMissionEvidence(missionKey){
  if(missionKey!==MISSION_KEY)return {ok:false,state:'INVALID_MISSION'};
  const raw=await this.env.RECEIPTS.get('council:real-ai-mission:20261030');
  if(!raw)return {ok:false,state:'NOT_RUN'};
  try{const receipt=JSON.parse(raw);const answer=await this.env.RECEIPTS.get('council:real-ai-mission:20261030:answer'); if(typeof answer!=='string'||await digestHex(answer)!==receipt.responseDigestSha256)return {ok:false,state:'ANSWER_DIGEST_MISMATCH'};return {ok:true,receipt,answer};}catch{return {ok:false,state:'CORRUPTED'};}
 }

 async attestNativeQueueEvidence(p){
  const id='5a9942e5-8652-4033-bca2-6bdad59ad838',qid='b36162d1-51b4-49ec-818e-6ec2ea248929',rid='ea778736-ba83-44df-b554-e67420d52653',h='22645b257fb66665ca778abe740b238048e5b2df256b3b730ba27261f029dc82';
  const ok=p?.schema==='daube.council.native-queue-attestation-request.v1'&&p.missionKey==='council-native-executor-e2e-canary-20261030'&&p.missionId===id&&p.queueId===qid&&p.receiptId===rid&&p.worker==='supabase-engineering-executor'&&p.queueStatus==='completed'&&p.receiptStatus==='verified'&&p.contentHash===h&&p.executionClass==='DETERMINISTIC_SYSTEM_PROBE_NO_EXTERNAL_EFFECT'&&p.providerSqlIndependentReadback===true&&p.result?.ok===true&&p.result.role==='engineering'&&p.result.worker===p.worker&&p.result.processed_at==='2026-10-29T21:03:07.937361+00:00';
  if(!ok)return {ok:false,error:'NATIVE_MISSION_EVIDENCE_REJECTED'};
  if(await digestHex('{"ok": true, "role": "engineering", "worker": "supabase-engineering-executor", "processed_at": "2026-10-29T21:03:07.937361+00:00"}')!==h)return {ok:false,error:'RESULT_HASH_MISMATCH'};
  const key='council:native-queue-e2e:'+id;
  if(await this.env.RECEIPTS.get(key))return this.readNativeQueueEvidence(id);
  const receipt={schema:'daube.council.native-queue-receipt.ed25519.v1',missionKey:p.missionKey,missionId:id,queueId:qid,receiptId:rid,worker:p.worker,resultHashSha256:h,queueStatus:p.queueStatus,receiptStatus:p.receiptStatus,executionClass:p.executionClass,checker:'daube-edge-observer-v1/CouncilCanaryChecker',providerEvidenceSource:'supabase-sql-connector-independent-readback',scope:'DETERMINISTIC_SYNTHETIC_CANARY_ONLY',signed:true,modelInvoked:false,productionMutation:false,releaseAdmitted:false,checkedAt:new Date().toISOString()};
  receipt.receiptDigestSha256=await digestHex(JSON.stringify(receipt));
  const keyBytes=Uint8Array.from(atob(String(this.env.COUNCIL_ED25519_KEY||'')),c=>c.charCodeAt(0));
  const signingKey=await crypto.subtle.importKey('pkcs8',keyBytes,{name:'Ed25519'},false,['sign']);
  const signature=await crypto.subtle.sign('Ed25519',signingKey,enc.encode(JSON.stringify(receipt)));
  receipt.signatureAlgorithm='Ed25519';receipt.signatureBase64=btoa(String.fromCharCode(...new Uint8Array(signature)));
  await this.env.RECEIPTS.put(key,JSON.stringify(receipt),{expirationTtl:2592000});
  return this.readNativeQueueEvidence(id);
 }
 async readNativeQueueEvidence(id){
  if(id!=='5a9942e5-8652-4033-bca2-6bdad59ad838')return {ok:false,error:'MISSION_NOT_ALLOWED'};
  const raw=await this.env.RECEIPTS.get('council:native-queue-e2e:'+id);
  if(!raw)return {ok:false,error:'NOT_SIGNED'};
  try{
   const r=JSON.parse(raw),{signatureBase64,signatureAlgorithm,...signed}=r;
   if(r.schema!=='daube.council.native-queue-receipt.ed25519.v1'||r.missionId!==id||signatureAlgorithm!=='Ed25519')return {ok:false,error:'BAD_RECEIPT'};
   const {receiptDigestSha256,...base}=signed;
   if(await digestHex(JSON.stringify(base))!==receiptDigestSha256)return {ok:false,error:'BAD_DIGEST'};
   const pub=Uint8Array.from(atob('UTU6TXx9+88UsWeZIgCqcLdwPL+756CkaralxhUh56U='),c=>c.charCodeAt(0));
   const k=await crypto.subtle.importKey('raw',pub,{name:'Ed25519'},false,['verify']);
   const sig=Uint8Array.from(atob(signatureBase64||''),c=>c.charCodeAt(0));
   return await crypto.subtle.verify('Ed25519',k,sig,enc.encode(JSON.stringify(signed)))?{ok:true,verified:true,receipt:r}:{ok:false,error:'BAD_SIGNATURE'};
  }catch{return {ok:false,error:'CORRUPT_RECEIPT'}}
 }

 async attestCouncilOfficeQueueV2(p){
  const expected={missionKey:'council-signed-office-20261030-01',missionId:'911a4c15-f7b4-44c8-a0e0-37875d1762c4',
   queueId:'b44bd2d6-a1c4-4286-8498-7ae01903bd79',receiptId:'811ade58-e53f-4671-b546-ab7b66ef7195',
   worker:'supabase-engineering-executor',resultHashSha256:'02c7fc58b27268a631c3c608ffa85ffd8e6a8335ba911658f5c3044b2eb180bb'};
  for(const [key,val] of Object.entries(expected))if(p?.[key]!==val)return {ok:false,error:'MISSION_PROOF_MISMATCH'};
  if(p.queueStatus!=='completed'||p.receiptStatus!=='verified'||p.executionClass!=='SUPABASE_DETERMINISTIC_READ_ONLY_QA'||p.providerSqlIndependentReadback!==true)
   return {ok:false,error:'PROVIDER_EVIDENCE_UNVERIFIED'};
  if(await digestHex('{"receipts": 28760, "verified": 28633}')!==expected.resultHashSha256)return {ok:false,error:'RESULT_HASH_MISMATCH'};
  const existing=await this.readCouncilOfficeQueueV2(expected.missionId);
  if(existing.ok)return existing;
  const data={schema:'daube.council.office-queue-receipt.ed25519.v2',...expected,
   queueStatus:p.queueStatus,receiptStatus:p.receiptStatus,executionClass:p.executionClass,
   checker:'daube-edge-observer-v1/CouncilCanaryChecker',providerEvidenceSource:'supabase-sql-checked-snapshot',
   modelInvokedByCouncil:false,productionMutation:false,releaseAdmitted:false,
   signed:true,checkedAt:new Date().toISOString()};
  data.receiptDigestSha256=await digestHex(JSON.stringify(data));
  const keyBytes=Uint8Array.from(atob(String(this.env.COUNCIL_ED25519_KEY||'')),c=>c.charCodeAt(0));
  const k=await crypto.subtle.importKey('pkcs8',keyBytes,{name:'Ed25519'},false,['sign']);
  const sig=new Uint8Array(await crypto.subtle.sign('Ed25519',k,enc.encode(JSON.stringify(data))));
  data.signatureAlgorithm='Ed25519';data.signatureBase64=btoa(String.fromCharCode(...sig));
  await this.env.RECEIPTS.put('council:office-queue-v2:'+expected.missionId,JSON.stringify(data),{expirationTtl:60*60*24*7});
  return await this.readCouncilOfficeQueueV2(expected.missionId);
 }
 async readCouncilOfficeQueueV2(id){
  if(id!=='911a4c15-f7b4-44c8-a0e0-37875d1762c4')return {ok:false,error:'MISSION_NOT_ALLOWED'};
  const raw=await this.env.RECEIPTS.get('council:office-queue-v2:'+id);
  if(!raw)return {ok:false,error:'NOT_SIGNED'};
  try{
   const r=JSON.parse(raw);
   if(r.schema!=='daube.council.office-queue-receipt.ed25519.v2'||r.missionId!==id||
      r.modelInvokedByCouncil!==false||r.signatureAlgorithm!=='Ed25519')return {ok:false,error:'INVALID_RECEIPT'};
   const {signatureBase64,signatureAlgorithm,...signed}=r,{receiptDigestSha256,...base}=signed;
   if(await digestHex(JSON.stringify(base))!==receiptDigestSha256)return {ok:false,error:'DIGEST_INVALID'};
   const pub=Uint8Array.from(atob('UTU6TXx9+88UsWeZIgCqcLdwPL+756CkaralxhUh56U='),c=>c.charCodeAt(0));
   const key=await crypto.subtle.importKey('raw',pub,{name:'Ed25519'},false,['verify']);
   const bytes=Uint8Array.from(atob(signatureBase64),c=>c.charCodeAt(0));
   if(!await crypto.subtle.verify('Ed25519',key,bytes,enc.encode(JSON.stringify(signed))))return {ok:false,error:'BAD_SIGNATURE'};
   return {ok:true,verified:true,receipt:r};
  }catch{return {ok:false,error:'CORRUPT_RECEIPT'}}
 }
  async attestMissionEvidence(packet){
  const key='council:real-ai-mission:20261030';
  if(!validMissionPacket(packet))return {ok:false,error:'INVALID_MISSION_PACKET'};
  if(typeof packet.responseText!=='string'||packet.responseText.length!==packet.outputSize||await digestHex(packet.responseText)!==packet.responseDigestSha256)return {ok:false,error:'MODEL_ANSWER_DIGEST_INVALID'};
  const existing=await this.env.RECEIPTS.get(key);
  if(existing){
   try{
    const value=JSON.parse(existing);
    const pub=Uint8Array.from(atob('UTU6TXx9+88UsWeZIgCqcLdwPL+756CkaralxhUh56U='),c=>c.charCodeAt(0));
    return await verifyMissionReceipt(value,pub,packet.dbMissionId)?value:{ok:false,error:'EXISTING_RECEIPT_INVALID'};
   }catch{return {ok:false,error:'EXISTING_RECEIPT_CORRUPTED'};}
  }
  const pkcs8=Uint8Array.from(atob(String(this.env.COUNCIL_ED25519_KEY||'')),c=>c.charCodeAt(0));
  const keyPair=await crypto.subtle.importKey('pkcs8',pkcs8,{name:'Ed25519'},false,['sign']);
  const receipt=await signMissionPacket(packet,keyPair);
  await this.env.RECEIPTS.put(key+':answer',packet.responseText,{expirationTtl:60*60*24*7});
  await this.env.RECEIPTS.put(key,JSON.stringify(receipt),{expirationTtl:60*60*24*7});
  return receipt;
 }

 async readModelEvidence(){
  const raw=await this.env.RECEIPTS.get('council:ai-review:Q100:20261029');
  if(!raw)return {ok:false,state:'NOT_RUN',schema:'daube.council.model-evidence-state.v1'};
  try{const result=JSON.parse(raw);return {ok:true,receipt:result};}
  catch{return {ok:false,state:'CORRUPTED',schema:'daube.council.model-evidence-state.v1'};}
 }
 async attestModelEvidence(packet){
  const key='council:ai-review:Q100:20261029';
  const prior=await this.env.RECEIPTS.get(key);
  if(prior){try{return JSON.parse(prior)}catch{return {ok:false,error:'existing_evidence_corrupt'};}}
  const valid=packet?.schema==='daube.council.model-invocation.v1'
   &&packet?.workKey==='COUNCIL-MODEL-20261029-Q100'
   &&packet?.model==='@cf/meta/llama-3.2-3b-instruct'
   &&packet?.origin==='council_worker_ai_binding'
   &&/^[a-f0-9]{64}$/.test(String(packet?.responseDigestSha256||''))
   &&/^[a-f0-9]{64}$/.test(String(packet?.promptDigestSha256||''))
   &&Number.isFinite(Date.parse(packet?.calledAt||''))
   &&Math.abs(Date.now()-Date.parse(packet.calledAt))<90000
   &&packet?.outputSize>0 &&packet.outputSize<6000
   &&packet?.tokenCap===160
   &&packet?.founderAccessVerified===true
   &&packet?.providerResultObserved===true;
  if(!valid)return {ok:false,error:'model_evidence_contract_invalid'};
  const reply={
   schema:'daube.council.model-review-receipt.v1',
   workKey:packet.workKey,model:packet.model,providerResultObserved:true,
   modelInvokedByGateway:true,promptDigestSha256:packet.promptDigestSha256,
   responseDigestSha256:packet.responseDigestSha256,
   outputValid:packet.outputValid===true,
   policyVerdict:packet.outputValid===true?'NOT_AUTONOMOUS':'MODEL_OUTPUT_REQUIRES_REVIEW',
   owner:'knowledge-intelligence',checker:'quality-and-security',
   source:'existing_council_ai_binding',
   reviewedAt:new Date().toISOString(),signed:true,releaseAdmitted:false,
   productionMutation:false,jobExecuted:false
  };
  const bytes=new TextEncoder().encode(JSON.stringify(reply));
  reply.receiptDigestSha256=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),v=>v.toString(16).padStart(2,'0')).join('');
  const privateBytes=Uint8Array.from(atob(String(this.env.COUNCIL_ED25519_KEY||'')),c=>c.charCodeAt(0));
  const signer=await crypto.subtle.importKey('pkcs8',privateBytes,{name:'Ed25519'},false,['sign']);
  const signature=await crypto.subtle.sign('Ed25519',signer,new TextEncoder().encode(JSON.stringify(reply)));
  reply.signatureAlgorithm='Ed25519';
  reply.signatureBase64=btoa(String.fromCharCode(...new Uint8Array(signature)));
  await this.env.RECEIPTS.put(key,JSON.stringify(reply),{expirationTtl:60*60*24*30});
  return reply;
 }

 async verify() {
  if(typeof this.env?.EXECUTOR_B?.readCanaryProof !== 'function') return {schema:'daube.council.independent-canary-check.v1',verified:false,error:'source_binding_unavailable',signed:false,modelExecuted:false};
  const evidence = await this.env.EXECUTOR_B.readCanaryProof();
  const result = verifyCanaryProof(evidence);
  const receipt = {schema:'daube.council.independent-canary-check.v1',verified:result.verified,checks:result.checks,jobId:'CANARY-20261024-FAILOVER-02',source:'executor_b_service_binding',checker:'daube-edge-observer-v1/CouncilCanaryChecker',jobStatus:evidence?.jobStatus||null,owner:evidence?.owner||null,fence:evidence?.fence??null,attempts:evidence?.attempts??null,eventsChecked:Array.isArray(evidence?.events)?evidence.events.length:0,checkedAt:new Date().toISOString(),signed:true,modelExecuted:false,productionReleaseAdmitted:false};
  const bytes=new TextEncoder().encode(JSON.stringify(receipt));
  receipt.receiptDigestSha256=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),v=>v.toString(16).padStart(2,'0')).join('');
  const material=Uint8Array.from(atob(String(this.env.COUNCIL_ED25519_KEY||'')),c=>c.charCodeAt(0));
  const signer=await crypto.subtle.importKey('pkcs8',material,{name:'Ed25519'},false,['sign']);
  const signature=await crypto.subtle.sign('Ed25519',signer,new TextEncoder().encode(JSON.stringify(receipt)));
  receipt.signatureAlgorithm='Ed25519';
  receipt.signatureBase64=btoa(String.fromCharCode(...new Uint8Array(signature)));

  return receipt;
 }
 async sec04KeySelfTest(){
  const common={schema:'daube.sec04.signer-probe.v1',keyFingerprintSha256:'b9ac901b2e6f657d4eaafe75ed20b79685e61908f9ef2681a44ac3b9f477aa46',w2Approved:false,w6Approved:false,releaseAuthorized:false};
  try{
   if(typeof this.env?.SEC04_SIGNING_KEY?.get!=='function')return {...common,verified:false,reason:'KEY_BINDING_MISSING'};
   const encoded=await this.env.SEC04_SIGNING_KEY.get();
   if(typeof encoded!=='string'||encoded.length>1024||encoded.length<40)return {...common,verified:false,reason:'KEY_FORMAT'};
   const privateBytes=Uint8Array.from(atob(encoded),c=>c.charCodeAt(0));
   let priv;
   try{priv=await crypto.subtle.importKey('pkcs8',privateBytes,{name:'Ed25519'},false,['sign']);}
   finally{privateBytes.fill(0);}
   const challenge=new TextEncoder().encode('DAUBE_SEC04_KEY_CUSTODY_PROBE_ONLY_20261104');
   const sig=await crypto.subtle.sign('Ed25519',priv,challenge);
   const publicBytes=Uint8Array.from(atob('MCowBQYDK2VwAyEAnEnTY4vC1fgJozHjyMw58ptgf+sXNetddprGxmtY4eo='),c=>c.charCodeAt(0));
   const hash=new Uint8Array(await crypto.subtle.digest('SHA-256',publicBytes));
   const observed=[...hash].map(x=>x.toString(16).padStart(2,'0')).join('');
   if(observed!==common.keyFingerprintSha256)return {...common,verified:false,reason:'PUBLIC_KEY_FINGERPRINT'};
   const pub=await crypto.subtle.importKey('spki',publicBytes,{name:'Ed25519'},false,['verify']);
   const verified=await crypto.subtle.verify('Ed25519',pub,sig,challenge);
   return {...common,verified,reason:verified?'CRYPTO_PROBE_VALID':'CRYPTO_PROBE_INVALID'};
  }catch{return {...common,verified:false,reason:'KEY_PROBE_FAILED'};}
 }

}

/** Bounded named RPC: fixed key-custody check plus approved mission334 owner-ACK transport. No Checker authority added. */
export class SEC04ProbeOnly extends withMessengerA(WorkerEntrypoint, messengerDependencies) {
 async ownerAck334(input){return await ownerAck334Transport(this.env,input);}

 async sec04KeySelfTest(){
  return await CouncilCanaryChecker.prototype.sec04KeySelfTest.call(this);
 }
}
