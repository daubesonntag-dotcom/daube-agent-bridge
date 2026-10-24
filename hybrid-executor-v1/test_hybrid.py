import unittest,tempfile,os,threading,time
from hybrid import Coordinator,run_canary
class HybridTest(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.path=os.path.join(self.tmp.name,"jobs.db");self.c=Coordinator(self.path)
 def tearDown(self):self.c.db.close();self.tmp.cleanup()
 def test_failover(self):
  r=run_canary(os.path.join(self.tmp.name,"canary.db"));self.assertEqual(r["status"],"LOCAL_PASS");self.assertEqual(r["hold_status"],"HOLD")
 def test_duplicate_and_restart(self):
  self.c.submit("x",{"value":1});self.c.submit("x",{"value":2});self.c.db.close();self.c=Coordinator(self.path)
  self.assertIn('"value": 1',self.c.db.execute("SELECT payload FROM jobs WHERE id='x'").fetchone()[0])
 def test_dual_claim(self):
  self.c.submit("race",{"task":"sha256"});out=[];barrier=threading.Barrier(2)
  def task(worker):
   c=Coordinator(self.path);barrier.wait();out.append(c.acquire("race",worker,ttl=2));c.db.close()
  a=threading.Thread(target=task,args=("A",));b=threading.Thread(target=task,args=("B",));a.start();b.start();a.join();b.join()
  self.assertEqual(sum(x is not None for x in out),1)
 def test_stale_fence(self):
  self.c.submit("x",{});a=self.c.acquire("x","A",ttl=.01);time.sleep(.02);b=self.c.acquire("x","B",ttl=2)
  self.assertFalse(self.c.complete("x","A",a,"bad"));self.assertTrue(self.c.complete("x","B",b,"good"))
 def test_retry_limit(self):
  self.c.submit("x",{});self.c.acquire("x","A",ttl=.01);time.sleep(.02);self.c.acquire("x","B",ttl=.01);time.sleep(.02)
  for _ in range(4):self.assertIsNone(self.c.acquire("x","A"))
  self.assertEqual(self.c.snapshot("x")[1],"HOLD")
if __name__=="__main__":unittest.main(verbosity=2)
