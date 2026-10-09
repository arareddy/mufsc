from common import *
from train import train_full
from unlearn import unlearn
from fixedpoint import FixedPointConfig
from accounting import components,counters
from timing import new_timing,totals
from datetime import datetime,timezone
import unittest,time,argparse
CHECKS=[]
class Gate(unittest.TestCase):
 def test_timer_disjointness(self):
  t=new_timing([3,91],2)
  t.update(encoding=1,input_materialization=2,cache_construction=3,shift_bounds=4,phase1_server=5,phase2_server=6,certificate_scan=99,failed_assignment=88,fallback_sunk=77,fallback_rebuild=66)
  t['phase1_client']={3:7,91:8};t['phase2_client_certify']={3:[9,10],91:[11,12]};t['phase2_client_recompute']={3:[13,14],91:[15,16]}
  a=components(t,140)
  assert sum(a['additive'].values())==140 and a['additive']['unattributed']==4
  assert a['additive']['phase2_client_certify']==42 and a['additive']['phase2_client_recompute']==58
  assert a['derived_nonadditive']['refinement_instrumented']==110
  assert totals(t)['certify_total']==42 and totals(t)['recompute_total']==58
 def test_positive_budget_and_ids(self):
  cd={3:np.array([[-2.,0],[-1,0],[0,0],[1,0],[2,1]]),17:np.array([[0.,1],[1,1],[1,2],[2,2]]),91:np.array([[2.,0],[3,1],[4,1]])}
  go={3:np.array([0,0,0,1,1]),17:np.array([0,1,1,1]),91:np.array([0,0,1])}
  for k in (1,3):
   for T in (1,2):
    cfg=FixedPointConfig(12,8)
    before={c:(v.tobytes(),go[c].tobytes()) for c,v in cd.items()}
    checkpoint=train_full(cd,go,10000,k,T,6,fp_cfg=cfg,build_cache=True)
    retained={c:x for c,x in cd.items() if c!=17};groups={c:g for c,g in go.items() if c!=17}
    fresh=train_full(retained,groups,10000,k,T,6,fp_cfg=cfg,build_cache=False)
    assert fresh['client_ids']==[3,91]
    for name,mode in (('direct','none'),('basic','basic'),('runnerup','runnerup')):
     start=time.perf_counter();res=unlearn(checkpoint,{17:np.arange(4)},certificate_mode=mode);elapsed=time.perf_counter()-start
     assert projection(res)==projection(fresh);check_extra(res,fresh)
     comp=components(res['timing'],elapsed);work=counters(res,name,8,T)
     if k==1 and name!='direct':assert work['S']==8*T and not work['threshold_fallback']
     CHECKS.append({'T':T,'k':k,'method':name,'witness':projection(res),'counters':work,'timer_components':comp})
    assert before=={c:(v.tobytes(),go[c].tobytes()) for c,v in cd.items()}
 def test_fallback_accounting(self):
  synthetic={'abandonment_round':0,'diagnostics':[{'round':0,'N':8,'A':8,'P':2,'S':0,'J':6},{'round':1,'N':8,'A':0,'P':0,'S':0,'J':0}]}
  c=counters(synthetic,'basic',8,2);assert c['N']==16 and c['A']==8 and c['P']==2 and c['J']==6 and c['modeled_point_assignments']==22
  c=counters({'abandonment_round':0,'diagnostics':[{'N':8,'A':0,'P':0,'S':0,'J':0}]},'direct',8,1);assert not c['threshold_fallback'] and c['pass_fraction'] is None
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--receipt',default=str(ROOT/'HARNESS_GATE.json'));a=p.parse_args();start=time.perf_counter()
 result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Gate))
 write_json(a.receipt,{'status':'PASS' if result.wasSuccessful() else 'FAIL','created_utc':datetime.now(timezone.utc).isoformat(),'tests_run':result.testsRun,'distinct_fixture_comparisons':len(CHECKS),'checks':CHECKS,'elapsed_seconds':time.perf_counter()-start,'source_hashes':{f:sha256(ROOT/f) for f in ('test_harness.py','accounting.py','common.py')},'canonical_baseline_manifest_sha256':sha256(ROOT/'BASELINE_MANIFEST.json')})
 raise SystemExit(0 if result.wasSuccessful() else 1)
