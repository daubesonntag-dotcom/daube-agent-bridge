import { WorkerEntrypoint } from "cloudflare:workers";
const JOB="CANARY-20261024-FAILOVER-02";
const ALLOWED_OBJECTS=new Set(["pilot-v1"]);
const json=(body)=>new Request("https://internal.daube.invalid/state",{method:"POST",headers:{"content-type":"application/json"},body:JSON.stringify(body)});
async function invoke(stub,path,body){
 const r=await stub.fetch(new Request("https://internal.daube.invalid"+path,{method:"POST",headers:{"content-type":"application/json"},body:JSON.stringify(body)}));
 return {code:r.status,body:await r.json()};
}
async function run(env, objectName){
 if(!ALLOWED_OBJECTS.has(objectName))return {action:"OBJECT_NOT_ALLOWLISTED"};
 const stub=env.COORDINATOR.get(env.COORDINATOR.idFromName(objectName));
 const state=await invoke(stub,"/state",{id:JOB});
 const job=state.body.job;
 if(!job)return {action:"NO_JOB"};
 // B must never become the first claimant; a PENDING job is not evidence of failover.
 if(job.status==="PENDING")return {action:"AWAITING_A"};
 if(job.status==="RUNNING"&&job.owner!=="A"&&job.owner!=="B")return {action:"INVALID_OWNER"};
 if(job.status==="SUCCEEDED"||job.status==="HOLD")return {action:"TERMINAL",status:job.status};
 if(job.status==="RUNNING"&&job.lease_until>Date.now())return {action:"LEASE_ACTIVE"};
 const claim=await invoke(stub,"/claim",{id:JOB,actor:"B",ttl:12000});
 if(!claim.body.claimed)return {action:"NOT_CLAIMED",status:claim.body?.job?.status};
 const b=new TextEncoder().encode("D-AUBE-CANARY-001");
 const digest=[...new Uint8Array(await crypto.subtle.digest("SHA-256",b))].map(x=>x.toString(16).padStart(2,"0")).join("");
 const completion=await invoke(stub,"/complete",{id:JOB,actor:"B",fence:claim.body.fence,result:digest});
 return {action:"EXECUTED",accepted:completion.body.accepted===true,fence:claim.body.fence};
}
export default class ExecutorB extends WorkerEntrypoint {
 // This method can only be invoked by a Worker with a Cloudflare Service Binding.
 async runCanary(id,objectName){
  if(id!==JOB)return {action:"JOB_NOT_ALLOWLISTED"};
  if(!ALLOWED_OBJECTS.has(objectName))return {action:"OBJECT_NOT_ALLOWLISTED"};
  return run(this.env,objectName);
 }
 async fetch(req){
  if(new URL(req.url).pathname==="/health")return Response.json({service:"hybrid-executor-b",access:"binding-rpc-only",status:"ready"});
  return new Response("Not found",{status:404});
 }
}
