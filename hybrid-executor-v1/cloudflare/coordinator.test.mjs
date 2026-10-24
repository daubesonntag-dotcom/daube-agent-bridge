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
function fixture(){const sql=new SqliteAdapter();return {sql,coordinator:new HybridCoordinator({storage:{sql}}, {})}}
async function op(c,path,body={}){const r=await c.fetch(new Request("https://internal.invalid/"+path,{method:"POST",body:JSON.stringify({id:JOB,...body})}));return {status:r.status,body:await r.json()}}
test("B never first-claims",async()=>{const {sql,coordinator:c}=fixture();try{await op(c,"start");const b=await op(c,"claim",{actor:"B"});assert.equal(b.body.claimed,false);assert.equal(b.body.reason,"B_AWAITING_EXPIRED_A");assert.equal((await op(c,"state")).body.job.attempts,0)}finally{sql.close()}});
test("A to B fencing and late completion",async()=>{const {sql,coordinator:c}=fixture();try{await op(c,"start");const a=await op(c,"claim",{actor:"A",ttl:12000});assert.equal(a.body.fence,1);assert.equal((await op(c,"claim",{actor:"B"})).body.claimed,false);sql.exec("UPDATE jobs SET lease_until=? WHERE id=?",Date.now()-1,JOB);const b=await op(c,"claim",{actor:"B",ttl:12000});assert.equal(b.body.fence,2);const digest="1f10541e4f871ae83e5fd21ff9c4c0cffbe406e0b76e302a12fd6ec18b89240c";assert.equal((await op(c,"complete",{actor:"A",fence:1,result:digest})).status,409);assert.equal((await op(c,"complete",{actor:"B",fence:2,result:digest})).body.accepted,true);assert.equal((await op(c,"complete",{actor:"B",fence:2,result:digest})).status,409);const s=(await op(c,"state")).body;assert.equal(s.job.status,"SUCCEEDED");assert.equal(s.job.attempts,2)}finally{sql.close()}});
test("third retry enters HOLD",async()=>{const {sql,coordinator:c}=fixture();try{await op(c,"start");await op(c,"claim",{actor:"A"});sql.exec("UPDATE jobs SET lease_until=? WHERE id=?",Date.now()-1,JOB);await op(c,"claim",{actor:"B"});sql.exec("UPDATE jobs SET lease_until=? WHERE id=?",Date.now()-1,JOB);const h=await op(c,"claim",{actor:"B"});assert.equal(h.body.job.status,"HOLD");assert.equal((await op(c,"claim",{actor:"A"})).body.claimed,false)}finally{sql.close()}});
test("incorrect digest rejected",async()=>{const {sql,coordinator:c}=fixture();try{await op(c,"start");await op(c,"claim",{actor:"A"});assert.equal((await op(c,"complete",{actor:"A",fence:1,result:"wrong"})).status,422)}finally{sql.close()}});
