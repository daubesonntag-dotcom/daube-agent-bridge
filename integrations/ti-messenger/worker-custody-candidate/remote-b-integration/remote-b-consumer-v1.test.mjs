import test from 'node:test';
import assert from 'node:assert/strict';
import {createRemoteMessengerBHandler} from './remote-b-consumer-v1.mjs';
const MISSION='2fa20aca-bf79-5aa8-9cad-0a22d971ff34';
const A='11111111-1111-4111-8111-111111111111',B='22222222-2222-4222-8222-222222222222';
const ROOT='https://remote.daubesonntag.com/workspace/api/agent-chat/b/ack';
const PRINCIPAL={verification:'ACCESS_JWT_RS256_VERIFIED',clientId:'6120a6eb353588180a8f8c8ca93a39a1.access',issuer:'https://jolly-mode-075c.cloudflareaccess.com',audience:'b61023883a77fc3f61dac058d317cdfdb771c4ffd3d8e81c3cea75c435130883',expiresAtMs:Date.now()+60000,verifiedAssertion:'SYNTHETIC_NOT_A_JWT'};
const CRED=JSON.stringify({clientId:'6120a6eb353588180a8f8c8ca93a39a1.access',clientSecret:'synthetic-no-live-secret-123456'});
const msg={id:A,from:'agent:ti',room:'council',tenantId:'daube',kind:'challenge',text:'CHALLENGE '+MISSION,clientMessageId:A};
const ack={id:B,from:'agent:daube',room:'council',tenantId:'daube',kind:'text',text:'ACK '+A,clientMessageId:A};
const req=(method='GET',sourceId=A,more={})=>new Request(method==='GET'?ROOT+'?sourceMessageId='+sourceId:ROOT,{method,headers:method==='POST'?{'content-type':'application/json',origin:'https://remote.daubesonntag.com'}:{},...(method==='POST'?{body:JSON.stringify({missionId:MISSION,sourceMessageId:sourceId})}:{}),...more});
function setup({sources=[msg],postMode='ok',badActor=false}={}){
 let secretRead=0,getCalls=0,postCalls=0;
 const handler=createRemoteMessengerBHandler({authorize:async(_,scope)=>({...scope}),getCredential:async()=>{secretRead++;return CRED},fetchOffice:async(_,opts)=>{
   if(opts.method==='GET'){getCalls++;return Response.json({room:'council',authenticatedActor:badActor?'founder@daubesonntag.com':'agent:daube',messages:sources});}
   postCalls++;
   if(postMode==='timeout')throw Error('synthetic-transport-failure');
   if(postMode==='badReceipt')return Response.json({message:{...ack,from:'agent:ti'}},{status:201});
   sources.push(ack);
   return Response.json({message:ack,authenticatedActor:'agent:daube'},{status:201});
 }});
 return {handler,calls:()=>({secretRead,getCalls,postCalls})};
}
test('unauthenticated and wrong principal blocked before reading credential or HTTP',async()=>{
 const {handler,calls}=setup();for(const p of [null,{email:'unlisted@example.com'},{email:'founder@daubesonntag.com',isMachine:true}]){
  const x=await handler(req(),p);assert.equal(x.status,403);assert.equal((await x.json()).code,'VERIFIED_B_MACHINE_REQUIRED');
 }assert.deepEqual(calls(),{secretRead:0,getCalls:0,postCalls:0});
});
test('non-UUID source and other mission fail before credential read',async()=>{
 const {handler,calls}=setup();let x=await handler(req('GET','synthetic-id'),PRINCIPAL);assert.equal(x.status,400);
 let y=await handler(req('POST',A,{body:JSON.stringify({missionId:'wrong',sourceMessageId:A})}),PRINCIPAL);assert.equal(y.status,400);
 assert.equal(calls().secretRead,0);
});
test('GET proves recipient B read of original Ti A challenge, not ACK/mission',async()=>{
 let {handler,calls}=setup();const x=await handler(req(),PRINCIPAL);const j=await x.json();assert.equal(x.status,200);assert.equal(j.code,'B_READ_VERIFIED');assert.equal(j.originalAReadVerified,true);assert.equal(j.originalBStoredVerified,false);assert.equal(j.reciprocalAReadVerified,false);assert.equal(j.grantIssued,false);assert.equal(calls().postCalls,0);
});
test('GET fails closed when backend principal echo is Founder',async()=>{
 let {handler}=setup({badActor:true});const x=await handler(req(),PRINCIPAL);assert.equal((await x.json()).code,'B_READ_UNVERIFIED');
});
test('POST sends only verified B ACK and cold reads it; remains no A reciprocal receipt',async()=>{
 let {handler,calls}=setup();const x=await handler(req('POST'),PRINCIPAL);const j=await x.json();assert.equal(x.status,200);assert.equal(j.code,'B_ACK_STORED_READBACK');assert.equal(j.originalAReadVerified,true);assert.equal(j.originalBStoredVerified,true);assert.equal(j.reciprocalAReadVerified,false);assert.equal(calls().postCalls,1);assert.equal(calls().getCalls,2);
});
test('retry with same source ID checks existing B ACK and does not POST again',async()=>{
 let {handler,calls}=setup({sources:[msg,ack]});const x=await handler(req('POST'),PRINCIPAL);assert.equal((await x.json()).code,'B_ACK_ALREADY_STORED');assert.equal(calls().postCalls,0);
});
test('unknown commit on transport failure never retries',async()=>{
 let {handler,calls}=setup({postMode:'timeout'});const x=await handler(req('POST'),PRINCIPAL),j=await x.json();assert.equal(j.code,'UNKNOWN_COMMIT');assert.equal(j.safeToRetry,false);assert.equal(calls().postCalls,1);
});
test('forged POST receipt remains UNKNOWN_COMMIT',async()=>{
 let {handler}=setup({postMode:'badReceipt'});const x=await handler(req('POST'),PRINCIPAL);assert.equal((await x.json()).code,'UNKNOWN_COMMIT');
});
test('missing A challenge never sends ACK',async()=>{
 let {handler,calls}=setup({sources:[]});const x=await handler(req('POST'),PRINCIPAL);assert.equal((await x.json()).code,'ORIGINAL_A_CHALLENGE_NOT_FOUND');assert.equal(calls().postCalls,0);
});

