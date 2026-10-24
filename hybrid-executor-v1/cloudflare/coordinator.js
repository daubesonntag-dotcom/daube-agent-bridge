const JOB="CANARY-20261024-FAILOVER-02";
const EXPECTED_DIGEST="1f10541e4f871ae83e5fd21ff9c4c0cffbe406e0b76e302a12fd6ec18b89240c";
const AUD="https://daube-hybrid-staging-v1.spacew039.workers.dev";
const EXPECTED_SUB_SHA256="09d62b4dee9fb0dbe545b52964aaf5eab7e808e85eafe56552b3a2b38abc0e92";
const EXPECTED_INSTANCE_SHA256="ad76e14ffaf12a834cae4385b6dcd726325f3dcfe99e45d35989722711c2656d";
const json=(body,status=200)=>Response.json(body,{status,headers:{"cache-control":"no-store"}});
const digest=async s=>Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256",new TextEncoder().encode(String(s))))).map(x=>x.toString(16).padStart(2,"0")).join("");
const b64=u=>Uint8Array.from(atob(u.replace(/-/g,"+").replace(/_/g,"/")),c=>c.charCodeAt(0));
let keysCache=null,keysExpiry=0;
async function verifyGcpIdentity(req){
 const a=req.headers.get("authorization")||"";
 if(!a.startsWith("Bearer ")||a.length>11000)return false;
 const t=a.slice(7).split(".");
 if(t.length!==3)return false;
 let h,p;
 try{h=JSON.parse(new TextDecoder().decode(b64(t[0])));p=JSON.parse(new TextDecoder().decode(b64(t[1])))}catch{return false}
 if(h.alg!=="RS256"||!h.kid||p.iss!=="https://accounts.google.com"||p.aud!==AUD)return false;
 const now=Math.floor(Date.now()/1000);
 if(!Number.isInteger(p.exp)||p.exp<=now||p.exp>now+3700||!Number.isInteger(p.iat)||p.iat>now+90||p.iat<now-3700)return false;
 if(p.nbf&&p.nbf>now+90)return false;
 if(await digest(p.sub)!==EXPECTED_SUB_SHA256)return false;
 const ce=p.google?.compute_engine;
 if(!ce?.instance_id||await digest(ce.instance_id)!==EXPECTED_INSTANCE_SHA256)return false;
 try{
  if(!keysCache||Date.now()>keysExpiry){
    const res=await fetch("https://www.googleapis.com/oauth2/v3/certs",{signal:AbortSignal.timeout(4000)});
    if(!res.ok)return false;
    const body=await res.json();keysCache=body.keys;keysExpiry=Date.now()+120000;
  }
  const jwk=keysCache.find(k=>k.kid===h.kid&&k.kty==="RSA");
  if(!jwk)return false;
  const key=await crypto.subtle.importKey("jwk",jwk,{name:"RSASSA-PKCS1-v1_5",hash:"SHA-256"},false,["verify"]);
  return await crypto.subtle.verify("RSASSA-PKCS1-v1_5",key,b64(t[2]),new TextEncoder().encode(t[0]+"."+t[1]));
 }catch{return false}
}
export class HybridCoordinator {
 constructor(ctx,env){
  this.ctx=ctx;this.env=env;const s=ctx.storage.sql;
  s.exec("CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY,status TEXT NOT NULL,owner TEXT,fence INTEGER NOT NULL DEFAULT 0,attempts INTEGER NOT NULL DEFAULT 0,lease_until INTEGER NOT NULL DEFAULT 0,result TEXT)");
  s.exec("CREATE TABLE IF NOT EXISTS receipts(seq INTEGER PRIMARY KEY AUTOINCREMENT,job TEXT,actor TEXT,event TEXT,fence INTEGER,at INTEGER)");
 }
 async fetch(req){
  if(req.method!=="POST")return json({error:"method"},405);
  const path=new URL(req.url).pathname;const q=await req.json().catch(()=>({}));
  if(q.id!==JOB)return json({error:"job_allowlist"},403);
  const sql=this.ctx.storage.sql;
  const now=Date.now();
  const read=()=>sql.exec("SELECT * FROM jobs WHERE id=?",JOB).toArray()[0]||null;
  const event=(actor,type,f)=>sql.exec("INSERT INTO receipts(job,actor,event,fence,at) VALUES(?,?,?,?,?)",JOB,actor,type,f,Date.now());
  if(path==="/start"){
   sql.exec("INSERT OR IGNORE INTO jobs(id,status) VALUES(?,'PENDING')",JOB);
   return json({job:read()});
  }
  if(path==="/state"){
   return json({job:read(),receipts:sql.exec("SELECT seq,job,actor,event,fence,at FROM receipts WHERE job=? ORDER BY seq",JOB).toArray()});
  }
  const j=read();if(!j)return json({error:"job_missing"},404);
  if(path==="/claim"){
   if(!["A","B"].includes(q.actor))return json({error:"actor_allowlist"},403);
   if(j.status==="SUCCEEDED"||j.status==="HOLD"||(j.status==="RUNNING"&&j.lease_until>now))return json({claimed:false,job:j});
   // Strict takeover contract: A claims once from PENDING; B can only claim an expired RUNNING lease.
   if(q.actor==="A"&&j.status!=="PENDING")return json({claimed:false,reason:"A_NOT_PENDING",job:j});
   if(q.actor==="B"&&!(j.status==="RUNNING"&&j.lease_until<=now&&(j.owner==="A"||j.owner==="B")))
     return json({claimed:false,reason:"B_AWAITING_EXPIRED_A",job:j});
   if(j.attempts>=2){sql.exec("UPDATE jobs SET status='HOLD' WHERE id=?",JOB);event("system","HOLD",j.fence);return json({claimed:false,job:read()})}
   const fence=j.fence+1;
   const ttl=Math.max(1000,Math.min(30000,Number(q.ttl)||3000));
   sql.exec("UPDATE jobs SET status='RUNNING',owner=?,lease_until=?,fence=?,attempts=attempts+1 WHERE id=?",q.actor,now+ttl,fence,JOB);
   event(q.actor,"ACQUIRED",fence);
   return json({claimed:true,fence,job:read()});
  }
  if(path==="/complete"){
   if(!["A","B"].includes(q.actor))return json({error:"actor_allowlist"},403);
   if(j.status!=="RUNNING"||j.owner!==q.actor||j.fence!==q.fence||j.lease_until<=now){
    event(q.actor,"REJECTED_STALE",Number(q.fence)||0);
    return json({accepted:false,job:j},409);
   }
   if(q.result!==EXPECTED_DIGEST)return json({accepted:false,error:"digest_mismatch"},422);
   sql.exec("UPDATE jobs SET status='SUCCEEDED',result=?,lease_until=0 WHERE id=?",q.result,JOB);
   event(q.actor,"COMPLETED",q.fence);
   return json({accepted:true,job:read()});
  }
  return json({error:"unknown_route"},404);
 }
}
export default {
 async fetch(req,env){
  const path=new URL(req.url).pathname;
  if(path==="/health")return json({service:"daube-hybrid-staging",status:"ready",auth:"gcp-oidc",mode:"canary-only"});
  if(!["/start","/claim","/complete","/state"].includes(path))return json({error:"not_found"},404);
  if(req.method!=="POST")return json({error:"method"},405);
  if(!await verifyGcpIdentity(req))return json({error:"identity_not_authorized"},401);
  const payload=await req.clone().json().catch(()=>({}));
  if((path==="/claim"||path==="/complete")&&payload.actor!=="A")return json({error:"remote_actor_not_A"},403);
  return env.COORDINATOR.get(env.COORDINATOR.idFromName("pilot-v1")).fetch(req);
 }
}