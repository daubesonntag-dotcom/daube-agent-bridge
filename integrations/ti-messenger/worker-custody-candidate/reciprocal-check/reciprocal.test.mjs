import {test} from 'node:test'; import assert from 'node:assert/strict';
import {MISSION,challengeText,ackText,checkChallenge,checkAck} from './reciprocal.mjs';
const sourceId='12345678-1234-4234-8234-123456789abc',sourceClient='22345678-1234-4234-8234-123456789abc',ackId='32345678-1234-4234-8234-123456789abc',ackClient='42345678-1234-4234-8234-123456789abc';
function fixture(consumerActor='agent:daube'){const challenge={id:sourceId,clientMessageId:sourceClient,from:consumerActor==='agent:daube'?'agent:ti':'agent:daube',tenantId:'daube',room:'council',kind:'challenge',text:challengeText()};return {consumerActor,observedActor:consumerActor,challenge,expectedSourceId:sourceId,expectedClientMessageId:ackClient,ack:{id:ackId,clientMessageId:ackClient,from:consumerActor,tenantId:'daube',room:'council',kind:'text',text:ackText(sourceId)}};}
for(const actor of ['agent:ti','agent:daube'])test('own and cross check '+actor,()=>{const f=fixture(actor);assert.equal(checkChallenge(f).ok,true);assert.equal(checkAck(f).ok,true);assert.equal(checkAck(JSON.parse(JSON.stringify(f))).ok,true);});
for(const observedActor of ['founder','agent:ti',undefined])test('B rejects wrong observed identity '+observedActor,()=>assert.equal(checkChallenge({...fixture(),observedActor}).ok,false));
for(const field of ['from','tenantId','room','kind','text','clientMessageId','id'])test('challenge invalid '+field,()=>{const f=fixture();f.challenge[field]='wrong';assert.equal(checkChallenge(f).ok,false);assert.equal(checkAck(f).ok,false);});
for(const text of [MISSION,`prefix CHALLENGE ${MISSION}`,`CHALLENGE ${MISSION} extra`,`CHALLENGE ${MISSION}\n`,`CHALLENGE ${MISSION.toUpperCase()}`])test('no substring mission acceptance '+JSON.stringify(text),()=>{const f=fixture();f.challenge.text=text;assert.equal(checkChallenge(f).ok,false);});
for(const field of ['from','tenantId','room','kind','text','clientMessageId','id'])test('new and cold ACK reject '+field,()=>{const f=fixture();f.ack[field]='wrong';assert.equal(checkAck(f).ok,false);assert.equal(checkAck(JSON.parse(JSON.stringify(f))).ok,false);});
for(const bad of [null,123456789012,'synthetic-msg-001',sourceId+'\n','12345678-1234-0234-8234-123456789abc','12345678-1234-4234-c234-123456789abc'])test('strict UUID '+JSON.stringify(bad),()=>{const f=fixture();f.challenge.id=bad;assert.equal(checkChallenge(f).ok,false);assert.throws(()=>ackText(bad));});
test('ACK source must be exact server ID, not client ID',()=>{const f=fixture();f.ack.text=ackText(sourceClient);assert.equal(checkAck(f).ok,false);});
test('same-message replay is not ACK',()=>{const f=fixture();f.ack.id=sourceId;assert.equal(checkAck(f).ok,false);});
test('ACK client ID must be independently correlated',()=>{const f=fixture();f.expectedClientMessageId=sourceClient;assert.equal(checkAck(f).ok,false);});

for(const actor of ['agent:ti','agent:daube']) {
 test('same server UUID with changed case rejected '+actor,()=>{const f=fixture(actor);f.ack.id=sourceId.toUpperCase();assert.equal(checkAck(f).ok,false);});
 test('per-sender identical client UUID accepted '+actor,()=>{const f=fixture(actor);f.challenge.clientMessageId=sourceId;f.ack.clientMessageId=sourceId;f.expectedClientMessageId=sourceId;assert.equal(checkAck(f).ok,true);});
 for(const expectedSourceId of [undefined,ackId,sourceId.toUpperCase()])test('trusted source selection exact '+actor+' '+expectedSourceId,()=>{const f=fixture(actor);f.expectedSourceId=expectedSourceId;assert.equal(checkChallenge(f).ok,false);assert.equal(checkAck(f).ok,false);});
}
