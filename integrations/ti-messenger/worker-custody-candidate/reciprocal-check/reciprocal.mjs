// Opt-in pure validators. No authentication, I/O, persistent ledger or automatic ACK.
export const MISSION = '2fa20aca-bf79-5aa8-9cad-0a22d971ff34';
const uuid = x => typeof x === 'string' && x.length === 36 && /^[a-f0-9]{8}-[a-f0-9]{4}-[1-8][a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/i.test(x);
const opposite = actor => actor === 'agent:ti' ? 'agent:daube' : actor === 'agent:daube' ? 'agent:ti' : null;
export const challengeText = () => `CHALLENGE ${MISSION}`;
function message(m, actor, kind, text) {
  return !!m && typeof m === 'object' && !Array.isArray(m) &&
    m.from === actor && m.room === 'council' && m.tenantId === 'daube' &&
    m.kind === kind && m.text === text && uuid(m.id) && uuid(m.clientMessageId);
}
export function ackText(sourceId) {
  if (!uuid(sourceId)) throw new Error('SOURCE_ID_INVALID');
  return `ACK ${sourceId}`;
}
export function checkChallenge({consumerActor, observedActor, challenge, expectedSourceId}={}) {
  const sourceActor = opposite(consumerActor);
  if (!sourceActor || observedActor !== consumerActor) return {ok:false,reason:'CONSUMER_IDENTITY_MISMATCH'};
  if (!uuid(expectedSourceId) || !message(challenge, sourceActor, 'challenge', challengeText()) || challenge.id !== expectedSourceId) return {ok:false,reason:'CHALLENGE_INVALID'};
  return {ok:true,sourceActor,consumerActor,sourceId:challenge.id,ackText:ackText(challenge.id)};
}
export function checkAck({consumerActor, observedActor, challenge, ack, expectedClientMessageId, expectedSourceId}={}) {
  const checked=checkChallenge({consumerActor,observedActor,challenge,expectedSourceId});
  if (!checked.ok) return checked;
  // Both a new receipt and a cold/prior ACK use this identical strict path.
  if (!uuid(expectedClientMessageId) || !message(ack,consumerActor,'text',checked.ackText) ||
      ack.clientMessageId !== expectedClientMessageId || ack.id.toLowerCase() === challenge.id.toLowerCase()) return {ok:false,reason:'ACK_INVALID'};
  return {ok:true,sourceId:checked.sourceId,ackId:ack.id,consumerActor,missionId:MISSION};
}
