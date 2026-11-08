/**
 * D'AUBE ONE-PROGRAM — bounded Office Messenger B reader/ACK (candidate only).
 * Integrate ONLY behind the EXISTING Remote Worker verified Access auth.
 * Never return or log the original Cloudflare Secrets Store value.
 * No scheduler, agent impersonation, mission signing, grant/lease or new store.
 */
import {MISSION, checkChallenge, checkAck} from './reciprocal.mjs';
const ENDPOINT = 'https://office-origin.daubesonntag.com/api/agent-chat/rooms/council/messages';
const ID_B = '6120a6eb353588180a8f8c8ca93a39a1.access';
const UUID = /^[a-f0-9]{8}-[a-f0-9]{4}-[1-8][a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/i;
const FOUNDERS = new Set(['founder@daubesonntag.com', 'spacew039@gmail.com', 'yninguyen006@gmail.com']);
const HEADERS = {'cache-control':'no-store','x-content-type-options':'nosniff','x-robots-tag':'noindex','referrer-policy':'no-referrer'};
const reply = (status, code, rest={}) => Response.json({schema:'daube.remote.messenger-b-v1',code,actor:'agent:daube',missionId:MISSION,
  originalAReadVerified:false,originalBStoredVerified:false,reciprocalAReadVerified:false,missionOwnerSigned:false,grantIssued:false,leaseIssued:false,checkerAdmitted:false,...rest},
  {status,headers:HEADERS});
async function boundedJSON(res,max=262144){
  if(!String(res.headers.get('content-type')||'').toLowerCase().includes('application/json'))throw Error('TYPE');
  if(!res.body)throw Error('BODY');
  const reader=res.body.getReader();let n=0,blocks=[];
  try{for(;;){let {done,value}=await reader.read();if(done)break;if(!(value instanceof Uint8Array)|| (n+=value.byteLength)>max)throw Error('SIZE');blocks.push(value)}}
  finally{try{await reader.cancel()}catch{}reader.releaseLock()}
  const b=new Uint8Array(n);let i=0;for(const chunk of blocks){b.set(chunk,i);i+=chunk.byteLength}
  return JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(b));
}
async function bodyJSON(request){
  const length=request.headers.get('content-length');
  if(length!==null&&(!/^\d+$/.test(length)||Number(length)>512))return null;
  if(!request.body)return null;
  const reader=request.body.getReader();let n=0,parts=[];
  try{for(;;){const {done,value}=await reader.read();if(done)break;if(!(value instanceof Uint8Array)||(n+=value.byteLength)>512)return null;parts.push(value)}}
  finally{try{await reader.cancel()}catch{}reader.releaseLock()}
  const b=new Uint8Array(n);let i=0;for(const part of parts){b.set(part,i);i+=part.length}
  try{return JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(b))}catch{return null}
}
/** Request-side identity must come from Remote's verified JWT, never from user JSON. */
export function createRemoteMessengerBHandler({fetchOffice=fetch,getCredential,authorize=async()=>null}={}){
  if(typeof fetchOffice!=='function'||typeof getCredential!=='function')throw TypeError('TRUSTED_INTEGRATION_REQUIRED');
  return async function handle(request,verifiedPrincipal){
    const url=new URL(request.url);
    if(url.protocol!=='https:'||url.hostname!=='remote.daubesonntag.com'||url.port||url.hash||url.pathname!=='/workspace/api/agent-chat/b/ack')return reply(404,'ROUTE_DENIED');
    if(!['GET','POST'].includes(request.method))return reply(405,'METHOD_DENIED');
    // Trusted verifier output only: never construct this context from request JSON/headers.
    const machine=verifiedPrincipal?.verification==='ACCESS_JWT_RS256_VERIFIED' &&
      verifiedPrincipal.clientId===ID_B && verifiedPrincipal.issuer==='https://jolly-mode-075c.cloudflareaccess.com' &&
      verifiedPrincipal.audience==='b61023883a77fc3f61dac058d317cdfdb771c4ffd3d8e81c3cea75c435130883' &&
      Number.isFinite(verifiedPrincipal.expiresAtMs) && verifiedPrincipal.expiresAtMs>Date.now() &&
      typeof verifiedPrincipal.verifiedAssertion==='string' && verifiedPrincipal.verifiedAssertion.length>0 &&
      verifiedPrincipal.email===undefined;
    const human=verifiedPrincipal && verifiedPrincipal.verification===undefined && verifiedPrincipal.clientId===undefined &&
      verifiedPrincipal.verifiedAssertion===undefined && verifiedPrincipal.isMachine!==true &&
      typeof verifiedPrincipal.email==='string' && FOUNDERS.has(verifiedPrincipal.email.toLowerCase());
    if(!machine&&!human)return reply(403,'VERIFIED_B_OR_DELEGATED_HUMAN_REQUIRED');
    let sourceId;
    if(request.method==='GET'){
      if(url.searchParams.size!==1||url.searchParams.getAll('sourceMessageId').length!==1)return reply(400,'REQUEST_INVALID');
      sourceId=url.searchParams.get('sourceMessageId');
    }else{
      if(url.search||request.headers.get('origin')!==url.origin||
        !/^application\/json(?:;\s*charset=utf-8)?$/i.test(request.headers.get('content-type')||''))return reply(400,'POST_SCOPE_DENIED');
      let input=await bodyJSON(request);
      if(!input||typeof input!=='object'||Array.isArray(input)||
        Object.keys(input).sort().join(',')!=='missionId,sourceMessageId'||input.missionId!==MISSION)return reply(400,'REQUEST_INVALID');
      sourceId=input.sourceMessageId;
    }
    if(typeof sourceId!=='string'||sourceId.length!==36||!UUID.test(sourceId))return reply(400,'SOURCE_ID_INVALID');
    // Verified human email is necessary but never sufficient to act as B.
    const scope=Object.freeze({actor:'agent:daube',missionId:MISSION,sourceMessageId:sourceId,
      operation:request.method==='POST'?'messenger.ack':'messenger.read',destination:ENDPOINT});
    try {
      const grant=await authorize(verifiedPrincipal,scope);
      if(!grant || Object.keys(scope).some(k=>grant[k]!==scope[k]))return reply(403,'ACT_AS_B_GRANT_REQUIRED');
    } catch { return reply(403,'ACT_AS_B_GRANT_REQUIRED'); }
    let auth;
    try{
      const raw=await getCredential();
      if(typeof raw!=='string'||raw.length>8192)throw Error('FORMAT');
      const c=JSON.parse(raw);
      if(!c||typeof c!=='object'||Array.isArray(c)||Object.keys(c).sort().join(',')!=='clientId,clientSecret'||
         c.clientId!==ID_B||typeof c.clientSecret!=='string'||c.clientSecret.length<16||c.clientSecret.length>4096||/[\x00-\x20\x7f]/.test(c.clientSecret))throw Error('CUSTODY');
      auth={'CF-Access-Client-Id':c.clientId,'CF-Access-Client-Secret':c.clientSecret};
    }catch{return reply(503,'B_CREDENTIAL_NOT_VERIFIED')}
    const read=async()=>{
      const r=await fetchOffice(ENDPOINT,{method:'GET',headers:{...auth,accept:'application/json'},redirect:'error',signal:AbortSignal.timeout(6500)});
      if(r.status!==200)throw Error('GET_STATUS');
      const d=await boundedJSON(r);
      if(d?.room!=='council'||d.authenticatedActor!=='agent:daube'||!Array.isArray(d.messages)||d.messages.length>150)throw Error('B_ACTOR_NOT_VERIFIED');
      return d;
    };
    let observed;
    try{observed=await read()}catch{return reply(502,'B_READ_UNVERIFIED')}
    const messages=observed.messages;
    const original=messages.find(m=>checkChallenge({consumerActor:'agent:daube',observedActor:observed.authenticatedActor,
      challenge:m,expectedSourceId:sourceId}).ok);
    if(!original)return reply(404,'ORIGINAL_A_CHALLENGE_NOT_FOUND');
    const checked=checkChallenge({consumerActor:'agent:daube',observedActor:observed.authenticatedActor,
      challenge:original,expectedSourceId:sourceId});
    const text=checked.ackText;
    const validatesAck=(ack,observedActor,challenge=original)=>checkAck({consumerActor:'agent:daube',observedActor,
      challenge,expectedSourceId:sourceId,ack,expectedClientMessageId:sourceId}).ok;
    const prior=messages.find(m=>validatesAck(m,observed.authenticatedActor));
    if(prior)return reply(200,'B_ACK_ALREADY_STORED',{originalAReadVerified:true,originalBStoredVerified:true,sourceMessageId:sourceId,ackMessageId:prior.id});
    if(request.method==='GET')return reply(200,'B_READ_VERIFIED',{originalAReadVerified:true,sourceMessageId:sourceId});
    // Deterministic clientMessageId is the original server UUID; Office per-sender idempotency guards replays.
    const body=JSON.stringify({text,kind:'text',clientMessageId:sourceId});
    let result;
    try{
      const r=await fetchOffice(ENDPOINT,{method:'POST',headers:{...auth,'content-type':'application/json',origin:new URL(ENDPOINT).origin},redirect:'error',signal:AbortSignal.timeout(6500),body});
      if(r.status!==200&&r.status!==201)return reply(502,'UNKNOWN_COMMIT',{safeToRetry:false,originalAReadVerified:true});
      result=await boundedJSON(r,16384);
      if(result?.authenticatedActor!==undefined&&result.authenticatedActor!=='agent:daube')throw Error('B_ACTOR_ECHO');
      const m=result?.message;
      if(!validatesAck(m,observed.authenticatedActor))throw Error('RECEIPT_SCOPE');
    }catch{return reply(502,'UNKNOWN_COMMIT',{safeToRetry:false,originalAReadVerified:true})}
    try{
      const refreshed=await read();
      const coldSource=refreshed.messages.find(m=>checkChallenge({consumerActor:'agent:daube',observedActor:refreshed.authenticatedActor,challenge:m,expectedSourceId:sourceId}).ok);
      if(!coldSource)throw Error('COLD_SOURCE_MISS');
      const stored=refreshed.messages.find(m=>m?.id===result.message.id&&validatesAck(m,refreshed.authenticatedActor,coldSource));
      if(!stored)throw Error('COLD_READ_MISS');
      return reply(200,'B_ACK_STORED_READBACK',{originalAReadVerified:true,originalBStoredVerified:true,sourceMessageId:sourceId,ackMessageId:stored.id});
    }catch{return reply(502,'UNKNOWN_COMMIT',{safeToRetry:false,originalAReadVerified:true})}
  };
}

