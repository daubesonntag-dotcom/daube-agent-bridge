#!/usr/bin/env python3
"""GCP canary client: no remote commands, no service-account key export."""
import json,urllib.request,urllib.error,urllib.parse,hashlib,argparse,sys
BASE='https://daube-hybrid-staging-v1.spacew039.workers.dev'
JOB='CANARY-20261024-FAILOVER-02'
IDENTITY='http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/identity'
def invoke(route,payload):
 if route not in ('start','state','claim','complete'):raise ValueError('route_disallowed')
 query=urllib.parse.urlencode({'audience':BASE,'format':'full'})
 meta=urllib.request.Request(IDENTITY+'?'+query,headers={'Metadata-Flavor':'Google'})
 with urllib.request.urlopen(meta,timeout=4) as res: token=res.read(11000).decode('ascii')
 if len(token.split('.'))!=3:raise ValueError('identity_invalid')
 req=urllib.request.Request(BASE+'/'+route,data=json.dumps(payload).encode(),method='POST',
   headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'})
 try:
  with urllib.request.urlopen(req,timeout=9) as res:return res.status,json.load(res)
 except urllib.error.HTTPError as err:return err.code,{'error':'http_error'}
def run(mode,fence=None):
 if mode=='start':code,response=invoke('start',{'id':JOB})
 elif mode=='state':code,response=invoke('state',{'id':JOB})
 elif mode=='claim-no-complete':code,response=invoke('claim',{'id':JOB,'actor':'A','ttl':12000})
 elif mode=='stale-complete':
  if fence is None or fence<1:raise ValueError('missing_fence')
  value=hashlib.sha256(b'D-AUBE-CANARY-001').hexdigest()
  code,response=invoke('complete',{'id':JOB,'actor':'A','fence':fence,'result':value})
 else:raise ValueError('mode_disallowed')
 job=response.get('job') or {}
 return {'http':code,'mode':mode,'job':JOB,'status':job.get('status'),'owner':job.get('owner'),
         'fence':response.get('fence',job.get('fence')),'claimed':response.get('claimed'),
         'accepted':response.get('accepted'),'events':[r.get('event') for r in response.get('receipts',[])]}
def accepted_outcome(mode,out):
 if out.get('http') is None:return False
 if mode=='start':
  return out.get('http')==200 and out.get('status')=='PENDING' and out.get('owner') is None and out.get('fence')==0
 if mode=='state':
  return out.get('http')==200 and out.get('status') in ('PENDING','RUNNING','SUCCEEDED','HOLD')
 if mode=='claim-no-complete':
  return (out.get('http')==200 and out.get('claimed') is True
   and out.get('owner')=='A' and out.get('status')=='RUNNING' and out.get('fence')==1)
 if mode=='stale-complete':
  return (out.get('http')==409 and out.get('accepted') is False
   and out.get('owner')=='B' and out.get('status')=='SUCCEEDED'
   and isinstance(out.get('fence'),int) and out['fence']>=2)
 return False
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('mode',choices=['start','state','claim-no-complete','stale-complete']);p.add_argument('--fence',type=int)
 args=p.parse_args()
 try:out=run(args.mode,args.fence);print(json.dumps(out));sys.exit(0 if accepted_outcome(args.mode,out) else 2)
 except Exception as err:print(json.dumps({'status':'HOLD','type':type(err).__name__}));sys.exit(2)