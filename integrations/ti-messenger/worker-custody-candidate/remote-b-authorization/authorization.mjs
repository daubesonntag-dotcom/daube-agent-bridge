// Pure decision over a caller-injected trusted current grant reader. No grant issuance/storage.
const B='6120a6eb353588180a8f8c8ca93a39a1.access';
const ISSUER='https://jolly-mode-075c.cloudflareaccess.com';
const AUD='b61023883a77fc3f61dac058d317cdfdb771c4ffd3d8e81c3cea75c435130883';
const MISSION='2fa20aca-bf79-5aa8-9cad-0a22d971ff34';
const ENDPOINT='https://office-origin.daubesonntag.com/api/agent-chat/rooms/council/messages';
const uuid=x=>typeof x==='string'&&x.length===36&&/^[a-f0-9]{8}-[a-f0-9]{4}-[1-8][a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/i.test(x);
const keys=(x,wanted)=>x&&typeof x==='object'&&!Array.isArray(x)&&Object.keys(x).sort().join(',')===wanted.split(',').sort().join(',');
const revision=x=>typeof x==='string'&&/^[A-Za-z0-9_-]{1,96}$/.test(x);
export function createAuthorizeRemoteB({readCurrentGrant,now=Date.now}={}) {
  // Missing policy source is an executable deny-all callback, never an implicit grant.
  return async function authorizeRemoteB(principal,scope) {
    try {
      const time=now();
      if(!Number.isSafeInteger(time)||typeof readCurrentGrant!=='function')return null;
      if(!principal||principal.verification!=='ACCESS_JWT_RS256_VERIFIED'||principal.clientId!==B||
         principal.issuer!==ISSUER||principal.audience!==AUD||principal.email!==undefined||
         typeof principal.verifiedAssertion!=='string'||!principal.verifiedAssertion||
         !Number.isSafeInteger(principal.expiresAtMs)||principal.expiresAtMs<=time)return null;
      if(!keys(scope,'actor,missionId,sourceMessageId,operation,destination')||scope.actor!=='agent:daube'||
         scope.missionId!==MISSION||scope.destination!==ENDPOINT||!uuid(scope.sourceMessageId)||
         !['messenger.read','messenger.ack'].includes(scope.operation))return null;
      // Copy primitives before the first await; never hand assertion/credential to policy seam.
      const selected=Object.freeze({...scope});const identityExpiry=principal.expiresAtMs;
      const request=Object.freeze({subjectClientId:B,...selected,room:'council',tenantId:'daube'});
      const snapshot=await readCurrentGrant(request);
      const checkedAt=now();
      if(!Number.isSafeInteger(checkedAt)||checkedAt<time||identityExpiry<=checkedAt||
         !keys(snapshot,'grant,currentVersion,currentFence')||!revision(snapshot.currentVersion)||!revision(snapshot.currentFence))return null;
      const g=snapshot.grant;
      if(!keys(g,'subjectClientId,actor,missionId,sourceMessageId,operation,destination,room,tenantId,notBeforeMs,expiresAtMs,revoked,version,fence')||
         g.revoked!==false||!Number.isSafeInteger(g.notBeforeMs)||!Number.isSafeInteger(g.expiresAtMs)||
         g.notBeforeMs>checkedAt||g.expiresAtMs<=checkedAt||g.expiresAtMs<=g.notBeforeMs||
         g.version!==snapshot.currentVersion||g.fence!==snapshot.currentFence||
         Object.keys(request).some(key=>g[key]!==request[key]))return null;
      return selected;
    } catch { return null; }
  };
}
