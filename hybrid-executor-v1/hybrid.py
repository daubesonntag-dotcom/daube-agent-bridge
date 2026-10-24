"""Offline reference canary. Never run production jobs from this module."""
import sqlite3,time,hashlib,json,tempfile
from pathlib import Path
SCHEMA="""CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY,payload TEXT NOT NULL,status TEXT NOT NULL,owner TEXT,lease_until REAL NOT NULL DEFAULT 0,fence INTEGER NOT NULL DEFAULT 0,attempts INTEGER NOT NULL DEFAULT 0,result TEXT,reason TEXT);CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY AUTOINCREMENT,job_id TEXT,worker TEXT,event TEXT,fence INTEGER,at REAL);"""
class Coordinator:
 def __init__(self,path):
  self.db=sqlite3.connect(path,timeout=5,isolation_level=None)
  self.db.executescript(SCHEMA)
 def event(self,j,w,e,f):
  self.db.execute("INSERT INTO events(job_id,worker,event,fence,at) VALUES(?,?,?,?,?)",(j,w,e,f,time.time()))
 def submit(self,j,payload):
  self.db.execute("INSERT OR IGNORE INTO jobs(id,payload,status) VALUES(?,?,?)",(j,json.dumps(payload,sort_keys=True),"PENDING"))
 def acquire(self,j,worker,ttl=30,max_attempts=2):
  if ttl<=0 or max_attempts<1:raise ValueError("invalid lease policy")
  now=time.time();self.db.execute("BEGIN IMMEDIATE")
  try:
   row=self.db.execute("SELECT status,lease_until,fence,attempts FROM jobs WHERE id=?",(j,)).fetchone()
   if not row:self.db.execute("COMMIT");return None
   status,expires,fence,attempts=row
   if status in ("SUCCEEDED","HOLD") or (status=="RUNNING" and expires>now):
    self.db.execute("COMMIT");return None
   if attempts>=max_attempts:
    self.db.execute("UPDATE jobs SET status='HOLD',reason='MAX_ATTEMPTS' WHERE id=?",(j,));self.db.execute("COMMIT");return None
   self.db.execute("UPDATE jobs SET status='RUNNING',owner=?,lease_until=?,fence=?,attempts=attempts+1 WHERE id=?",(worker,now+ttl,fence+1,j))
   self.db.execute("COMMIT");self.event(j,worker,"ACQUIRED",fence+1);return fence+1
  except BaseException:
   self.db.execute("ROLLBACK");raise
 def complete(self,j,worker,fence,result):
  updated=self.db.execute("UPDATE jobs SET status='SUCCEEDED',result=?,lease_until=0 WHERE id=? AND owner=? AND fence=? AND status='RUNNING' AND lease_until>?",(result,j,worker,fence,time.time()))
  self.event(j,worker,"COMPLETED" if updated.rowcount else "REJECTED_STALE",fence)
  return bool(updated.rowcount)
 def snapshot(self,j):return self.db.execute("SELECT id,status,owner,fence,attempts,result,reason FROM jobs WHERE id=?",(j,)).fetchone()
def run_canary(path):
 c=Coordinator(path);payload={"task":"sha256","input":"D-AUBE-CANARY-001"};j="canary-001";c.submit(j,payload)
 a=c.acquire(j,"A",ttl=.04);assert a==1
 time.sleep(.06)
 b=c.acquire(j,"B",ttl=5);assert b==2
 result=hashlib.sha256(payload["input"].encode()).hexdigest()
 assert not c.complete(j,"A",a,"wrong")
 assert c.complete(j,"B",b,result)
 assert c.acquire(j,"A") is None
 snap=c.snapshot(j);assert snap[1]=="SUCCEEDED" and snap[2]=="B" and snap[4]==2
 hold="hold-001";c.submit(hold,payload);c.acquire(hold,"A",ttl=.01);time.sleep(.02);c.acquire(hold,"B",ttl=.01);time.sleep(.02)
 assert c.acquire(hold,"A") is None and c.snapshot(hold)[1]=="HOLD"
 return {"status":"LOCAL_PASS","remote_status":"HOLD","canary":snap,"hold_status":c.snapshot(hold)[1]}
if __name__=="__main__":
 print(json.dumps(run_canary(str(Path(tempfile.mkdtemp())/"jobs.sqlite")),indent=2))
