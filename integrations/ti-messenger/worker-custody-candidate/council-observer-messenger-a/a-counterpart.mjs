import {MISSION,checkChallenge,checkAck} from './reciprocal.mjs';
const A='8ceae31b13c0a5f495c8374e6a8aced4.access';
const ENDPOINT='https://office-origin.daubesonntag.com/api/agent-chat/rooms/council/messages';
const UUID=/^[a-f0-9]{8}-[a-f0-9]{4}-[1-8][a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/i;
async function boundedJSON(response,max=262144){
 if(!response.headers.get('content-type')?.toLowerCase().includes('application/json')||!response.body)throw Error('RESPONSE');
 const reader=response.body.getReader();let n=0;const chunks=[];
 try{for(;;){const {done,value}=await reader.read();if(done)break;n+=value.byteLength;if(n>max)throw Error('SIZE');chunks.push(value);}}
 finally{try{await reader.cancel();}catch{}reader.releaseLock();}
 const bytes=new Uint8Array(n);let offset=0;for(const c of chunks){bytes.set(c,offset);offset+=c.byteLength;}
 return JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes));
}
// Internal factory only. verifyMachine is REQUIRED trusted original-runtime adapter.
export function createACounterpart({verifyMachine,authorize,getCredential,fetchOffice,now=Date.now}={}){
 return Object.freeze({async execute(callerEvidence,scope){
  let dispatched=false;
  try{
   if(typeof verifyMachine!=='function'||typeof authorize!=='function'||typeof getCredential!=='function'||typeof fetchOffice!=='function')return {code:'INTEGRATION_MISSING'};
   if(!scope||Object.keys(scope).sort().join(',')!=='missionId,operation,sourceMessageId'||scope.missionId!==MISSION||!['messenger.read','messenger.ack'].includes(scope.operation)||typeof scope.sourceMessageId!=='string'||scope.sourceMessageId.length!==36||!UUID.test(scope.sourceMessageId))return {code:'SCOPE_INVALID'};
   const selected=Object.freeze({...scope});
   const verified=await verifyMachine(callerEvidence);
   const principal=verified&&Object.freeze({...verified});
   // Caller is the verified dispatcher, NOT actor A. Scoped delegation is checked next.
   if(!principal||principal.clientId!=='36e8f959f2496da9255a16c830571eb7.access'||principal.email!==undefined||!Number.isSafeInteger(principal.expiresAtMs)||principal.expiresAtMs<=now())return {code:'VERIFIED_A_REQUIRED'};
   const required=Object.freeze({...selected,actor:'agent:ti',destination:ENDPOINT});
   const grant=await authorize(principal,required);
   if(!grant||Object.keys(required).some(k=>grant[k]!==required[k])||principal.expiresAtMs<=now())return {code:'ACT_AS_A_GRANT_REQUIRED'};
   const raw=await getCredential();
   if(typeof raw!=='string'||raw.length>8192)return {code:'CREDENTIAL_INVALID'};
   const c=JSON.parse(raw);
   if(!c||Object.keys(c).sort().join(',')!=='clientId,clientSecret'||c.clientId!==A||typeof c.clientSecret!=='string'||! /^[!-~]{16,4096}$/.test(c.clientSecret))return {code:'CREDENTIAL_INVALID'};
   const headers={'CF-Access-Client-Id':c.clientId,'CF-Access-Client-Secret':c.clientSecret};
   const read=async()=>{const res=await fetchOffice(ENDPOINT,{method:'GET',headers:{...headers,accept:'application/json'},redirect:'error',signal:AbortSignal.timeout(6500)});if(res.status!==200)throw Error('READ');const data=await boundedJSON(res);if(data?.authenticatedActor!=='agent:ti'||data.room!=='council'||!Array.isArray(data.messages)||data.messages.length>150)throw Error('ACTOR');return data;};
   const data=await read();
   const findSource=d=>d.messages.find(challenge=>checkChallenge({consumerActor:'agent:ti',observedActor:d.authenticatedActor,challenge,expectedSourceId:selected.sourceMessageId}).ok);
   const source=findSource(data);if(!source)return {code:'B_CHALLENGE_NOT_VERIFIED'};
   const valid=(ack,d,challenge)=>checkAck({consumerActor:'agent:ti',observedActor:d.authenticatedActor,challenge,expectedSourceId:selected.sourceMessageId,ack,expectedClientMessageId:selected.sourceMessageId}).ok;
   const prior=data.messages.find(m=>valid(m,data,source));
   if(prior)return {code:'A_ACK_ALREADY_STORED',ackId:prior.id,peerReadVerified:false};
   if(selected.operation==='messenger.read')return {code:'A_READ_VERIFIED',sourceId:source.id,peerReadVerified:false};
   const checked=checkChallenge({consumerActor:'agent:ti',observedActor:data.authenticatedActor,challenge:source,expectedSourceId:selected.sourceMessageId});
   if(principal.expiresAtMs<=now())return {code:'VERIFIED_A_EXPIRED'};
   dispatched=true;
   const res=await fetchOffice(ENDPOINT,{method:'POST',headers:{...headers,'content-type':'application/json',origin:new URL(ENDPOINT).origin},redirect:'error',signal:AbortSignal.timeout(6500),body:JSON.stringify({text:checked.ackText,kind:'text',clientMessageId:source.id})});
   if(![200,201].includes(res.status))throw Error('POST');const receipt=await boundedJSON(res,16384);
   if(receipt.authenticatedActor!==undefined&&receipt.authenticatedActor!=='agent:ti')throw Error('ACTOR');
   if(!valid(receipt.message,data,source))throw Error('RECEIPT');
   const cold=await read(),coldSource=findSource(cold);if(!coldSource)throw Error('COLD_SOURCE');
   const stored=cold.messages.find(m=>m?.id===receipt.message.id&&valid(m,cold,coldSource));if(!stored)throw Error('COLD_ACK');
   return {code:'A_ACK_STORED_READBACK',sourceId:source.id,ackId:stored.id,peerReadVerified:false};
  }catch{return dispatched?{code:'UNKNOWN_COMMIT',safeToRetry:false}:{code:'A_READ_OR_AUTH_UNVERIFIED'};}
 }});
}
