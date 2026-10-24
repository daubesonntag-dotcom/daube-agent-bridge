import { test } from "node:test";
import assert from "node:assert/strict";
import { DatabaseSync } from "node:sqlite";
import { HybridCoordinator } from "./coordinator.js";
const JOB="CANARY-20261024-FAILOVER-02";
class SqliteAdapter {
 constructor(){this.db=new DatabaseSync(":memory:")}
 exec(query,...args){let s=this.db.prepare(query);if(/^\s*SELECT\b/i.test(query))return {toArray:()=>s.all(...args)};s.run(...args);return {toArray:()=>[]}}
 close(){this.db.close()}
}
function fixture(){const sql=new SqliteAdapter();const alarms=[];const storage={sql,setAlarm:async time=>{alarms.push(time)}};return {sql,alarms,coordinator:new HybridCoordinator({storage}, {})}}
async function op(c,path,body={}){const r=await c.fetch(new Request("https://internal.invalid/"+path,{method:"POST",body:JSON.stringify({id:JOB,...body})}));return {status:r.status,body:await r.json()}}
test("B never first-claims",async()=>{const {sql,coordinator:c}=fixture();try{await op(c,"start");const b=await op(c,"claim",{actor:"B"});assert.equal(b.body.claimed,false);assert.equal(b.body.reason,"B_AWAITING_EXPIRED_A");assert.equal((await op(c,"state")).body.job.attempts,0)}finally{sql.close()}});
test("A to B fencing and late completion",async()=>{const {sql,coordinator:c}=fixture();try{await op(c,"start");const a=await op(c,"claim",{actor:"A",ttl:12000});assert.equal(a.body.fence,1);assert.equal((await op(c,"claim",{actor:"B"})).body.claimed,false);sql.exec("UPDATE jobs SET lease_until=? WHERE id=?",Date.now()-1,JOB);const b=await op(c,"claim",{actor:"B",ttl:12000});assert.equal(b.body.fence,2);const digest="1f10541e4f871ae83e5fd21ff9c4c0cffbe406e0b76e302a12fd6ec18b89240c";assert.equal((await op(c,"complete",{actor:"A",fence:1,result:digest})).status,409);assert.equal((await op(c,"complete",{actor:"B",fence:2,result:digest})).body.accepted,true);assert.equal((await op(c,"complete",{actor:"B",fence:2,result:digest})).status,409);const s=(await op(c,"state")).body;assert.equal(s.job.status,"SUCCEEDED");assert.equal(s.job.attempts,2)}finally{sql.close()}});
test("third retry enters HOLD",async()=>{const {sql,coordinator:c}=fixture();try{await op(c,"start");await op(c,"claim",{actor:"A"});sql.exec("UPDATE jobs SET lease_until=? WHERE id=?",Date.now()-1,JOB);await op(c,"claim",{actor:"B"});sql.exec("UPDATE jobs SET lease_until=? WHERE id=?",Date.now()-1,JOB);const h=await op(c,"claim",{actor:"B"});assert.equal(h.body.job.status,"HOLD");assert.equal((await op(c,"claim",{actor:"A"})).body.claimed,false)}finally{sql.close()}});
test("incorrect digest rejected",async()=>{const {sql,coordinator:c}=fixture();try{await op(c,"start");await op(c,"claim",{actor:"A"});assert.equal((await op(c,"complete",{actor:"A",fence:1,result:"wrong"})).status,422)}finally{sql.close()}});

test("A claim arms lease alarm, but B cannot first claim",async()=>{
 const {sql,alarms,coordinator:c}=fixture();try{
  await op(c,"start");await op(c,"claim",{actor:"B"});
  assert.equal(alarms.length,0);
  const a=await op(c,"claim",{actor:"A",ttl:12000});
  assert.equal(a.body.fence,1);assert.equal(alarms.length,1);
  assert.ok(alarms[0]>Date.now());
 }finally{sql.close()}
});
test("alarm dispatch to internal B RPC completes after expired A lease",async()=>{
 const {sql,coordinator:c}=fixture();try{
  await op(c,"start");await op(c,"claim",{actor:"A",ttl:12000});
  sql.exec("UPDATE jobs SET lease_until=? WHERE id=?",Date.now()-1,JOB);
  let dispatched=0;
  c.env.EXECUTOR_B={runCanary:async id=>{
   assert.equal(id,JOB);dispatched++;
   const b=await op(c,"claim",{actor:"B",ttl:12000});
   assert.equal(b.body.fence,2);
   const digest="1f10541e4f871ae83e5fd21ff9c4c0cffbe406e0b76e302a12fd6ec18b89240c";
   const done=await op(c,"complete",{actor:"B",fence:2,result:digest});
   return {action:"EXECUTED",accepted:done.body.accepted};
  }};
  await c.alarm();await c.alarm();
  assert.equal(dispatched,1);
  const state=(await op(c,"state")).body;
  assert.equal(state.job.owner,"B");assert.equal(state.job.status,"SUCCEEDED");
  assert.deepEqual(state.receipts.filter(x=>x.actor!=="system").map(x=>x.event),["ACQUIRED","ACQUIRED","COMPLETED"]);
 }finally{sql.close()}
});
test("failed B binding dispatch stops after two attempts, never loops",async()=>{
 const {sql,alarms,coordinator:c}=fixture();try{
  await op(c,"start");await op(c,"claim",{actor:"A",ttl:12000});
  sql.exec("UPDATE jobs SET lease_until=? WHERE id=?",Date.now()-1,JOB);
  let tries=0;c.env.EXECUTOR_B={runCanary:async()=>{tries++;throw Error("transient")}};
  await c.alarm();await c.alarm();await c.alarm();
  assert.equal(tries,2);
  assert.equal((await op(c,"state")).body.job.status,"HOLD");
  assert.equal(sql.exec("SELECT tries FROM alarm_dispatches WHERE job=?",JOB).toArray()[0].tries,2);
  assert.ok(alarms.length<=2);
 }finally{sql.close()}
});
test("expired B lease is terminal HOLD",async()=>{
 const {sql,coordinator:c}=fixture();try{
  await op(c,"start");await op(c,"claim",{actor:"A",ttl:12000});
  sql.exec("UPDATE jobs SET lease_until=? WHERE id=?",Date.now()-1,JOB);
  await op(c,"claim",{actor:"B",ttl:12000});
  sql.exec("UPDATE jobs SET lease_until=? WHERE id=?",Date.now()-1,JOB);
  await c.alarm();await c.alarm();
  assert.equal((await op(c,"state")).body.job.status,"HOLD");
 }finally{sql.close()}
});
