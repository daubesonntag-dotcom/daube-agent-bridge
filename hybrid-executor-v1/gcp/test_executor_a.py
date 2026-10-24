import hashlib, importlib.util, unittest
from pathlib import Path
from unittest.mock import patch

PATH=Path(__file__).with_name("executor-a.py")
SPEC=importlib.util.spec_from_file_location("hybrid_executor_a", PATH)
mod=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)

class GCPCanaryContract(unittest.TestCase):
 def test_id_matches_workers(self):
  expected="CANARY-20261024-FAILOVER-02"
  self.assertEqual(mod.JOB,expected)
  root=Path(__file__).parents[1]/"cloudflare"
  for name in ("coordinator.js","executor-b.js"):
   self.assertIn('const JOB="'+expected+'";',(root/name).read_text())
 def test_claim_no_completion(self):
  with patch.object(mod,"invoke",return_value=(200,{"claimed":True,"fence":1,"job":{"status":"RUNNING","owner":"A"}})) as fn:
   result=mod.run("claim-no-complete")
  fn.assert_called_once_with("claim",{"id":mod.JOB,"actor":"A","ttl":12000})
  self.assertTrue(result["claimed"])
  self.assertEqual(result["fence"],1)
 def test_stale_result_rejected(self):
  with self.assertRaises(ValueError):mod.run("stale-complete")
  with patch.object(mod,"invoke",return_value=(409,{"accepted":False,"job":{"status":"SUCCEEDED","owner":"B","fence":2}})) as fn:
   result=mod.run("stale-complete",1)
  fn.assert_called_once_with("complete",{"id":mod.JOB,"actor":"A","fence":1,"result":hashlib.sha256(b"D-AUBE-CANARY-001").hexdigest()})
  self.assertEqual(result["http"],409)
  self.assertFalse(result["accepted"])
 def test_reject_unknown_modes(self):
  for mode in ("execute-shell","delete","send-email"):
   with self.assertRaises(ValueError):mod.run(mode)
 def test_no_response_secrets(self):
  with patch.object(mod,"invoke",return_value=(401,{"error":"http_error","secret":"do-not-display"})):
   r=mod.run("state")
  self.assertEqual(r["http"],401)
  self.assertNotIn("do-not-display",str(r))

 def test_claim_http_200_without_ownership_cannot_pass(self):
  self.assertFalse(mod.accepted_outcome('claim-no-complete',{'http':200,'claimed':False,'owner':None,'fence':0,'status':'PENDING'}))
  self.assertFalse(mod.accepted_outcome('claim-no-complete',{'http':200,'claimed':True,'owner':'B','fence':1,'status':'RUNNING'}))
  self.assertTrue(mod.accepted_outcome('claim-no-complete',{'http':200,'claimed':True,'owner':'A','fence':1,'status':'RUNNING'}))
 def test_stale_completion_requires_rejection_by_new_owner(self):
  self.assertFalse(mod.accepted_outcome('stale-complete',{'http':200,'accepted':True,'owner':'A','fence':1,'status':'SUCCEEDED'}))
  self.assertFalse(mod.accepted_outcome('stale-complete',{'http':409,'accepted':False,'owner':'A','fence':1,'status':'RUNNING'}))
  self.assertTrue(mod.accepted_outcome('stale-complete',{'http':409,'accepted':False,'owner':'B','fence':2,'status':'SUCCEEDED'}))
 def test_state_requires_existing_job(self):
  self.assertFalse(mod.accepted_outcome('state',{'http':200,'status':None,'owner':None,'fence':0}))
  self.assertTrue(mod.accepted_outcome('state',{'http':200,'status':'PENDING','owner':None,'fence':0}))
