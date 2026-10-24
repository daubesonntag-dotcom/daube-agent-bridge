
const JOB="CANARY-20261024-FAILOVER-02";
const json=(body)=>new Request("https://internal.daube.invalid/state",{method:"POST",headers:{"content-type":"application/json"},body:JSON.stringify(body)});
async function invoke(stub,path,body){
 const r=await stub.fetch(new Request("https://internal.daube.invalid"+path,{method:"POST",headers:{"content-type":"application/json"},body:JSON.stringify(body)}));
 return {code:r.status,body:await r.json()};
}
async function run(env){
 const stub=env.COORDINATOR.get(env.COORDINATOR.idFromName("pilot-v1"));
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
export default {
 async scheduled(event,env,ctx){ctx.waitUntil(run(env).then(x=>console.log("CANARY_B",JSON.stringify(x))).catch(e=>{console.error("CANARY_B_ERROR",e.name);throw e}))},
 async fetch(req){if(new URL(req.url).pathname==="/health")return Response.json({service:"hybrid-executor-b",access:"scheduled-only",status:"ready"});return new Response("Not found",{status:404})}
}
