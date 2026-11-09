import {test} from 'node:test'; import assert from 'node:assert/strict';
import {createConsumer} from './consumer.mjs';
const clientId='8ceae31b13c0a5f495c8374e6a8aced4.access', secret='synthetic-only-not-a-live-secret';
const input={clientMessageId:'12345678-1234-4234-8234-123456789abc',kind:'challenge',text:'Synthetic offline challenge'};
function fixture({caller='approved-test-caller',raw=JSON.stringify({clientId,clientSecret:secret}),mutation={},status=201,grantOverride={}}={}) {
 const calls=[]; const consumer=createConsumer({policy:{actor:'agent:ti',caller:'approved-test-caller',clientId,destination:'https://council.daubesonntag.com/api/agent-chat/rooms/council/messages'},
 verifyCaller:async()=>({caller,actor:'agent:ti',operation:'messenger.send',destination:'https://council.daubesonntag.com/api/agent-chat/rooms/council/messages',...grantOverride}),credentialBinding:{get:async()=>{calls.push('secret');return raw;}},transport:async(url,options)=>{calls.push({url,options});return Response.json({message:{...input,id:'synthetic-stored-001',from:'agent:ti',room:'council',tenantId:'daube',...mutation}},{status});}});return {consumer,calls};
}
test('valid mocked receipt, fixed endpoint and no credential returned',async()=>{const {consumer,calls}=fixture();const r=await consumer.send({},input);assert.equal(r.status,'STORED_BY_SERVER');assert.equal(r.recipientReadVerified,false);assert.equal(calls[1].options.redirect,'error');assert.equal(calls[1].options.headers['CF-Access-Client-Secret'],secret);assert.ok(!JSON.stringify(r).includes(secret));});
test('unauthorized caller never reads credential',async()=>{const {consumer,calls}=fixture({caller:'other'});assert.equal((await consumer.send({},input)).status,'DENIED');assert.equal(calls.length,0);});
test('caller cannot override destination',async()=>{const {consumer,calls}=fixture();assert.equal((await consumer.send({},{...input,destination:'https://evil.invalid'})).status,'INPUT_INVALID');assert.equal(calls.length,0);});
test('wrong credential identity never sends',async()=>{const {consumer,calls}=fixture({raw:JSON.stringify({clientId:'b'.repeat(32)+'.access',clientSecret:secret})});assert.equal((await consumer.send({},input)).status,'CREDENTIAL_IDENTITY_MISMATCH');assert.equal(calls.length,1);});
for(const raw of ['invalid', '{}', 'x'.repeat(8193),`{"clientId":"${clientId}","clientSecret":"${secret}","clientSecret":"${secret}"}`]) test('reject malformed credential '+raw.length,async()=>{const {consumer,calls}=fixture({raw});assert.equal((await consumer.send({},input)).status,'CREDENTIAL_INVALID');assert.equal(calls.length,1);});
for(const mutation of [{from:'agent:daube'},{room:'other'},{tenantId:'other'},{text:'other'},{clientMessageId:'12345678-1234-4234-8234-123456789abd'}]) test('reject receipt mismatch '+Object.keys(mutation)[0],async()=>{const {consumer}=fixture({mutation});assert.equal((await consumer.send({},input)).status,'UNKNOWN_COMMIT');});
test('redirect status is not success',async()=>{const {consumer}=fixture({status:302});assert.equal((await consumer.send({},input)).status,'UNKNOWN_COMMIT');});
test('missing policy cannot create consumer',()=>assert.throws(()=>createConsumer({policy:{}}),/POLICY_INCOMPLETE/));

for (const grantOverride of [{actor:undefined,operation:undefined},{actor:'agent:daube'},{operation:'messenger.read'},{destination:'https://evil.invalid'}]) test('grant scope rejected '+JSON.stringify(grantOverride),async()=>{const {consumer,calls}=fixture({grantOverride});assert.equal((await consumer.send({},input)).status,'DENIED');assert.equal(calls.length,0);});

test('known A id cannot configure B actor',()=>assert.throws(()=>createConsumer({policy:{actor:'agent:daube',clientId,caller:'test'},credentialBinding:{get(){throw Error('must not read');}},verifyCaller:()=>{},transport:()=>{throw Error('must not send');}}),/POLICY_INCOMPLETE/));

// Bridge contract: UUID versions 1..8 and RFC variant 8/9/a/b, case-insensitive.
for (const id of ['synthetic-msg-001', '12345678123442348234123456789abc',
 '12345678-1234-0234-8234-123456789abc', '12345678-1234-9234-8234-123456789abc',
 '12345678-1234-4234-7234-123456789abc', '12345678-1234-4234-c234-123456789abc',
 '12345678-1234-4234-8234-123456789abg', '12345678-1234-4234-8234-123456789abc\n',
 '12345678-1234-4234-8234-123456789ab', '12345678-1234-4234-8234-123456789abcd', 123456789012])
 test('invalid UUID rejected before secret/transport '+JSON.stringify(id),async()=>{
 const {consumer,calls}=fixture(); assert.equal((await consumer.send({},{...input,clientMessageId:id})).status,'INPUT_INVALID'); assert.equal(calls.length,0);
 });
for (const version of '12345678') for (const variant of '89ab') for (const uppercase of [false,true])
 test(`accept UUID version ${version} variant ${variant} uppercase ${uppercase}`,async()=>{
 let id=`12345678-1234-${version}234-${variant}234-123456789abc`; if(uppercase) id=id.toUpperCase();
 const {consumer,calls}=fixture({mutation:{clientMessageId:id}});
 assert.equal((await consumer.send({},{...input,clientMessageId:id})).status,'STORED_BY_SERVER'); assert.equal(calls.length,2);
 });
