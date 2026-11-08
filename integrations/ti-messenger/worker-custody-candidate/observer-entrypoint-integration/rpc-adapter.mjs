import {createConsumer} from './consumer.mjs';
import {createACounterpart} from './a-counterpart.mjs';
import {MISSION,challengeText} from './reciprocal.mjs';
export const DISPATCHER='36e8f959f2496da9255a16c830571eb7.access';
const A='8ceae31b13c0a5f495c8374e6a8aced4.access';
const URL='https://office-origin.daubesonntag.com/api/agent-chat/rooms/council/messages';
const uuid=x=>typeof x==='string'&&x.length===36&&/^[a-f0-9]{8}-[a-f0-9]{4}-[1-8][a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/i.test(x);
// Local integration seam; verifier MUST independently verify the original signed proof
// at Observer, including signature, issuer/audience, expiry and machine-only claims.
// Neither a Council-supplied decoded principal nor service-binding access is proof.
export function createMessengerARPC({verifySignedProof,issuer,audience,authorize,getCredential,fetchOffice,now=Date.now}={}){
 async function call(operation,input){
  try{
   if(typeof verifySignedProof!=='function'||!issuer||!audience||typeof authorize!=='function'||typeof getCredential!=='function'||typeof fetchOffice!=='function')return {code:'INTEGRATION_MISSING'};
   const needsId=operation!=='messenger.status';
   const keys=needsId?'missionId,proof,sourceMessageId':'missionId,proof';
   if(!input||Object.keys(input).sort().join(',')!==keys||input.missionId!==MISSION||typeof input.proof!=='string'||!input.proof||input.proof.length>16384||(needsId&&!uuid(input.sourceMessageId)))return {code:'SCOPE_INVALID'};
   const proof=input.proof,sourceMessageId=input.sourceMessageId;
   // Snapshot verified scalars, never return proof or verifier errors.
   const p=await verifySignedProof(proof,{issuer,audience});
   if(!p||p.clientId!==DISPATCHER||p.issuer!==issuer||p.audience!==audience||p.email!==undefined||p.actor!==undefined||!Number.isSafeInteger(p.expiresAtMs)||p.expiresAtMs<=now())return {code:'DISPATCHER_UNVERIFIED'};
   const principal=Object.freeze({clientId:p.clientId,issuer:p.issuer,audience:p.audience,expiresAtMs:p.expiresAtMs});
   const scope=Object.freeze({actor:'agent:ti',caller:DISPATCHER,operation,missionId:MISSION,tenantId:'daube',room:'council',destination:URL,...(needsId?{sourceMessageId}:{})});
   const grant=await authorize(principal,scope);
   if(!grant||Object.keys(scope).some(k=>grant[k]!==scope[k])||principal.expiresAtMs<=now())return {code:'ACT_AS_A_GRANT_REQUIRED'};
   // Credential/JWKS awaits must not admit a new Office request after expiry.
   const guardedFetch=(...args)=>{if(principal.expiresAtMs<=now())throw Error('DISPATCHER_EXPIRED');return fetchOffice(...args);};
   if(['messenger.read','messenger.ack'].includes(operation)){
    const a=createACounterpart({verifyMachine:async()=>principal,authorize:async(_,required)=>{if(principal.expiresAtMs<=now())return null;return required;},getCredential,fetchOffice:guardedFetch,now});
    return await a.execute(null,{missionId:MISSION,sourceMessageId,operation});
   }
   const consumer=createConsumer({policy:{actor:'agent:ti',clientId:A,caller:DISPATCHER,destination:URL},credentialBinding:{get:getCredential},transport:guardedFetch,verifyCaller:async()=>principal.expiresAtMs>now()?{caller:DISPATCHER,actor:'agent:ti',destination:URL,operation:operation==='messenger.status'?'messenger.read':'messenger.send'}:null});
   if(operation==='messenger.status')return await consumer.status(null);
   return await consumer.send(null,{text:challengeText(),kind:'challenge',clientMessageId:sourceMessageId});
  }catch{return {code:'AUTH_OR_INTEGRATION_UNVERIFIED'};}
 }
 return Object.freeze({messengerAStatus:input=>call('messenger.status',input),messengerARead:input=>call('messenger.read',input),messengerASendChallenge:input=>call('messenger.sendChallenge',input),messengerAAck:input=>call('messenger.ack',input)});
}
