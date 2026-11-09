// SOURCE-ONLY: no credential binding or deployment authorized by this file.
// Existing SEC04ProbeOnly RPC can call this after separate binding approval.
const MISSION='2fa20aca-bf79-5aa8-9cad-0a22d971ff34';
const ORIGIN='https://remote.daubesonntag.com';
const URL=ORIGIN+'/enterprise/api/owner-ack';
const CLIENT='8ceae31b13c0a5f495c8374e6a8aced4.access';
const hold=code=>({ok:false,code,missionId:MISSION,executed:false});
export async function ownerAck334Transport(env,input,{fetchImpl=fetch}={}){
 if(env.TI_OWNER_ACK_TRANSPORT_ENABLED!=='mission-334-only')return hold('TRANSPORT_DISABLED');
 if(!input||Object.getPrototypeOf(input)!==Object.prototype||Object.keys(input).length!==2||input.missionId!==MISSION||!['readback','accept'].includes(input.action))return hold('SCOPE_DENIED');
 if(typeof env.TI_MESSENGER_CREDENTIAL?.get!=='function')return hold('EXISTING_CREDENTIAL_UNBOUND');
 let credential;try{credential=JSON.parse(await env.TI_MESSENGER_CREDENTIAL.get())}catch{return hold('STORED_CREDENTIAL_FORMAT_UNVERIFIED')}
 // Do not guess an unobserved secret envelope format; fail closed until verified.
 if(credential?.clientId!==CLIENT||typeof credential.clientSecret!=='string'||credential.clientSecret.length<16||credential.clientSecret.length>4096)return hold('STORED_CREDENTIAL_FORMAT_UNVERIFIED');
 const headers={'CF-Access-Client-Id':credential.clientId,'CF-Access-Client-Secret':credential.clientSecret,'content-type':'application/json',origin:ORIGIN};
 const accept=input.action==='accept';
 let response;try{response=await fetchImpl(accept?URL:URL+'?missionId='+MISSION,{method:accept?'POST':'GET',headers,redirect:'error',signal:AbortSignal.timeout(10000),...(accept?{body:JSON.stringify({missionId:MISSION})}:{})})}catch{return hold(accept?'OUTCOME_UNCERTAIN_READBACK_FIRST':'AUTHENTICATED_READBACK_UNAVAILABLE')}
 // Never return response text, request headers, credential, cookies or JWTs.
 if([401,403,302].includes(response.status))return hold('EXISTING_SERVICE_AUTH_DENIED');
 if(response.status===429)return hold('SERVICE_RATE_LIMITED_NO_RETRY');
 if(!String(response.headers.get('content-type')||'').includes('application/json'))return hold(accept?'OUTCOME_UNCERTAIN_READBACK_FIRST':'RESPONSE_UNVERIFIED');
 let result;try{const raw=await response.text();if(raw.length>8192)return hold(accept?'OUTCOME_UNCERTAIN_READBACK_FIRST':'RESPONSE_UNVERIFIED');result=JSON.parse(raw)}catch{return hold(accept?'OUTCOME_UNCERTAIN_READBACK_FIRST':'RESPONSE_UNVERIFIED')}
 if(result.missionId!==MISSION)return hold(accept?'OUTCOME_UNCERTAIN_READBACK_FIRST':'RESPONSE_SCOPE_MISMATCH');
 if(response.status===200&&['queued','running','blocked','done'].includes(result.status)&&result.ok===true&&result.ownerSignatureVerified===true&&/^[a-f0-9]{64}$/.test(result.ownerAckDigest||'')&&['OWNER_ACKED','OWNER_ACK_ALREADY_VERIFIED'].includes(result.code))return {ok:true,code:result.code,missionId:MISSION,ownerAckDigest:result.ownerAckDigest,status:result.status,verification:'ATLAS_REPORTED_REQUIRES_INDEPENDENT_D1_SIGNATURE_READBACK',executed:false};
 return hold(result.code==='PENDING_OWNER_ACK'?'PENDING_OWNER_ACK':'ATLAS_ACK_NOT_VERIFIED');
}
