import {DISPATCHER} from './rpc-adapter.mjs';
export const ISSUER='https://jolly-mode-075c.cloudflareaccess.com';
export const AUDIENCE='3ae2b154dac34ab91f643fcb55512f138a1fdc1bd31294837a6ce64d66f18739';
const bytes=s=>{if(typeof s!=='string'||!/^[A-Za-z0-9_-]+$/.test(s))throw Error();return Uint8Array.from(atob(s.replace(/-/g,'+').replace(/_/g,'/')+'='.repeat((4-s.length%4)%4)),c=>c.charCodeAt(0));};
// Existing team's RS256/JWKS pattern. Trust owner must confirm Council uses this issuer.
// Inject only approved cert fetch; there is deliberately no ambient fetch default.
export function createDispatcherVerifier({fetchCerts,now=Date.now}={}){
 return async(token,pins)=>{
  try{
   if(typeof fetchCerts!=='function'||pins?.issuer!==ISSUER||pins?.audience!==AUDIENCE||typeof token!=='string'||token.length>14000)return null;
   const parts=token.split('.');if(parts.length!==3)return null;
   const parse=s=>JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes(s)));
   const h=parse(parts[0]),p=parse(parts[1]),t=Math.floor(now()/1000);
   if(h.alg!=='RS256'||typeof h.kid!=='string'||!h.kid||h.kid.length>256||h.crit!==undefined||p.iss!==ISSUER||!(Array.isArray(p.aud)?p.aud.includes(AUDIENCE):p.aud===AUDIENCE)||p.type!=='app'||p.sub!==''||Object.hasOwn(p,'email')||p.common_name!==DISPATCHER||!Number.isSafeInteger(p.exp)||p.exp<=t||p.exp>t+31*86400||['nbf','iat'].some(k=>p[k]!==undefined&&(!Number.isSafeInteger(p[k])||p[k]>t+30)))return null;
   const res=await fetchCerts(ISSUER+'/cdn-cgi/access/certs',{redirect:'error',signal:AbortSignal.timeout(4000)});
   if(res.status!==200||!res.body)return null;
   const r=res.body.getReader();let n=0,all=[];try{for(;;){const v=await r.read();if(v.done)break;n+=v.value.length;if(n>65536)return null;all.push(v.value);}}finally{await r.cancel();r.releaseLock();}
   const b=new Uint8Array(n);let offset=0;for(const c of all){b.set(c,offset);offset+=c.length;}
   const jwks=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(b));if(!Array.isArray(jwks.keys)||jwks.keys.length>25)return null;
   const matches=jwks.keys.filter(k=>k.kid===h.kid&&k.kty==='RSA'&&(k.alg===undefined||k.alg==='RS256')&&(k.use===undefined||k.use==='sig'));if(matches.length!==1)return null;
   const key=await crypto.subtle.importKey('jwk',matches[0],{name:'RSASSA-PKCS1-v1_5',hash:'SHA-256'},false,['verify']);
   if(!await crypto.subtle.verify('RSASSA-PKCS1-v1_5',key,bytes(parts[2]),new TextEncoder().encode(parts[0]+'.'+parts[1]))||p.exp*1000<=now())return null;
   return {clientId:p.common_name,issuer:p.iss,audience:AUDIENCE,expiresAtMs:p.exp*1000};
  }catch{return null;}
 };
}
