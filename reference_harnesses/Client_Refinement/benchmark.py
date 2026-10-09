"""Fixed matched-budget canonical replay experiment; no compact C0 path."""
from common import *
from train import train_full
from unlearn import unlearn
from fixedpoint import FixedPointConfig
from datasets import load_dataset
from accounting import components,counters
from with_lock import run_locked
from datetime import datetime,timezone
from fractions import Fraction
import argparse,time,gc,pickle,resource,traceback,subprocess
METHODS=('fresh','direct','basic','runnerup')
MODES={'direct':'none','basic':'basic','runnerup':'runnerup'}
BOUND=('benchmark.py','accounting.py','common.py','with_lock.py','test_harness.py','HARNESS_GATE.json','PROTOCOL.md','FROZEN_GRID.json','BASELINE_MANIFEST.json','INPUTS.json','IDENTITY_REGISTRY.json','QUALITY_REFERENCE_MANIFEST.json','C0_PRESERVATION.json')

def bindings():
 out={f:sha256(ROOT/f) for f in BOUND}
 for p in sorted((ROOT/'baseline').rglob('*.py')):out[str(p.relative_to(ROOT))]=sha256(p)
 return out

def train(cd,go,spec,cache=False):
 return train_full(cd,go,spec['seed'],spec['k'],spec['T'],spec['L'],gamma=spec['gamma'],fp_cfg=FixedPointConfig(spec['scale_bits'],spec['clip']),anchor_lloyd_iters=spec['anchor_lloyd_iters'],build_cache=cache)

def measured_request(method,cd,go,checkpoint,spec,path):
 gc.collect();start=time.perf_counter();departed=spec['deleted_client']
 if method=='fresh':args=({c:x for c,x in cd.items() if c!=departed},{c:g for c,g in go.items() if c!=departed})
 else:args={departed:np.arange(len(cd[departed]),dtype=np.int64)}
 prepared=time.perf_counter()
 result=train(*args,spec) if method=='fresh' else unlearn(checkpoint,args,certificate_mode=MODES[method])
 finished=time.perf_counter()
 payload=projection(result)
 encoded=(json.dumps(payload,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
 path.write_bytes(encoded);end=time.perf_counter()
 obs={'method':method,'algorithm_seconds':finished-prepared,'request_preparation_seconds':prepared-start,'output_seconds':end-finished,'request_e2e_seconds':end-start,'output_sha256':hashlib.sha256(encoded).hexdigest(),'output_bytes':len(encoded),'timing_primitives':jsonable(result['timing']),'components':components(result['timing'],finished-prepared),'work':counters(result,method,spec['n']-spec['removed_n'],spec['T'])}
 return result,payload,obs

def worker(run,spec):
 d=run/spec['case_id'];d.mkdir(parents=True,exist_ok=False)
 started=datetime.now(timezone.utc).isoformat();start=time.perf_counter()
 cd,go,meta=load_dataset(spec['dataset'],str(DATA),seed=spec['dataset_selection_seed'])
 load_seconds=time.perf_counter()-start;start=time.perf_counter()
 accepted=json.loads((ROOT/'INPUTS.json').read_text())['files'][spec['dataset']]
 assert meta['source_sha256']==accepted['sha256'] and meta['clip']==spec['clip'] and meta['d']==spec['d']
 registry=json.loads((ROOT/'IDENTITY_REGISTRY.json').read_text())[spec['dataset']]
 for c in cd:
  r=registry[str(c)];assert meta['source_client_ids'][c]==r['source_client_id'] and len(cd[c])==r['row_count']
  assert hashlib.sha256(np.asarray(meta['source_record_ids'][c],dtype='<i8').tobytes()).hexdigest()==r['ordered_full_row_ids_sha256']
 assert meta['source_client_ids'][spec['deleted_client']]==spec['source_client_id']
 assert meta['source_record_ids'][spec['deleted_client']].tolist()==spec['removed_source_rows']
 assert sum(len(x) for x in cd.values())==spec['n']
 identity_seconds=time.perf_counter()-start
 ref=json.loads((ROOT/'QUALITY_REFERENCE_MANIFEST.json').read_text())['cases'][spec['parent_case_id']]
 start=time.perf_counter();qpath=Path(ref['path']);assert sha256(qpath)==ref['sha256'];old_rows=json.loads(qpath.read_text());reference_load=time.perf_counter()-start
 start=time.perf_counter();matched=next(q for q in old_rows if q['T']==spec['T']);old_witness=matched['model_witness']
 assert object_hash(old_witness)==ref['budgets'][str(spec['T'])]['full_witness_sha256']
 e={k:Fraction(v['numerator'],v['denominator']) for k,v in matched['quality']['exact'].items()}
 assert e['Phi']==max(e['Phi_A'],e['Phi_B']) and e['G']==e['Phi_A']+e['Phi_B']
 ng=matched['quality']['retained_group_counts'];assert ng==spec['retained_group_counts'];assert e['pooled_SSE']==ng[0]*e['Phi_A']+ng[1]*e['Phi_B']
 reference_verify=time.perf_counter()-start
 gc.collect();start=time.perf_counter();checkpoint=train(cd,go,spec,cache=True);setup_seconds=time.perf_counter()-start
 start=time.perf_counter();blob=pickle.dumps(checkpoint,protocol=5);storage=len(blob);serialization=time.perf_counter()-start;del blob
 setup={'canonical_original_training_seconds':setup_seconds,'checkpoint_pickle_bytes':storage,'checkpoint_serialization_seconds':serialization,'checkpoint_primitives':jsonable(checkpoint['timing']),'checkpoint_components':components(checkpoint['timing'],setup_seconds),'input_load_verify_seconds':load_seconds,'identity_verification_seconds':identity_seconds,'quality_reference_load_seconds':reference_load,'quality_reference_verify_seconds':reference_verify,'new_quality_scoring_seconds':0.0,'quality_reused_from':str(qpath),'quality_reference_sha256':ref['sha256'],'environment':environment_manifest()}
 write_json(d/'preparation.json',setup)
 reference=None;workref={};comparisons=0;verification_seconds=0;orders=[]
 for rep in range(4):
  offset=(spec['setting_index']+rep)%4;order=METHODS[offset:]+METHODS[:offset];orders.append(order);results={};payloads={}
  for pos,method in enumerate(order):
   result,payload,obs=measured_request(method,cd,go,checkpoint,spec,d/f'rep{rep}_{method}_model.json')
   obs.update(case_id=spec['case_id'],parent_case_id=spec['parent_case_id'],dataset=spec['dataset'],seed=spec['seed'],T=spec['T'],repetition=rep,position=pos,order=order,observed_utc=datetime.now(timezone.utc).isoformat())
   results[method]=result;payloads[method]=payload
   with (d/'observations.jsonl').open('a') as f:f.write(json.dumps(obs,sort_keys=True)+'\n')
  start=time.perf_counter();fresh=payloads['fresh'];assert fresh==old_witness,'historical complete quality witness mismatch'
  if reference is None:reference=fresh
  assert fresh==reference
  for method in METHODS:
   assert payloads[method]==fresh,(spec['case_id'],rep,method,'full indexed trajectory/stats')
   if method!='fresh':check_extra(results[method],results['fresh']);comparisons+=1
   work=counters(results[method],method,spec['n']-spec['removed_n'],spec['T'])
   if rep==0:workref[method]=work
   else:assert work==workref[method]
  verification_seconds+=time.perf_counter()-start
  del results,payloads
 receipt={'status':'PASS','case_id':spec['case_id'],'T':spec['T'],'distinct_methods':4,'distinct_replay_comparisons':3,'repeated_replay_comparisons':comparisons,'timing_observations':16,'full_witness_sha256':object_hash(reference),'historical_complete_witness_equal':True,'quality_reference_sha256':ref['sha256'],'reference_model_path':'rep0_fresh_model.json','observations_sha256':sha256(d/'observations.jsonl'),'verification_seconds':verification_seconds,'unique_work_counters':workref,'started_utc':started,'ended_utc':datetime.now(timezone.utc).isoformat(),'max_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'source_bindings':bindings()}
 write_json(d/'complete.json',receipt);print(spec['case_id'],'PASS',flush=True)

def campaign(run_id,budget):
 if Path(run_id).name!=run_id:raise ValueError('simple fresh run ID required')
 gate=json.loads((ROOT/'HARNESS_GATE.json').read_text());assert gate['status']=='PASS'
 for f,h in gate['source_hashes'].items():assert sha256(ROOT/f)==h
 assert gate['canonical_baseline_manifest_sha256']==sha256(ROOT/'BASELINE_MANIFEST.json')
 run=ROOT/'runs'/run_id;run.mkdir(parents=True,exist_ok=True)
 write_json(run/'run_manifest.json',{'run_id':run_id,'source_bindings':bindings(),'environment':environment_manifest(),'methods':METHODS,'repetitions':4,'contract':'Resident request matched-budget canonical learner, full indexed trajectory/stat output; no compact positive-T method.'},immutable=True)
 specs=json.loads((ROOT/'FROZEN_GRID.json').read_text())['cases'];start=time.perf_counter();done=[]
 for spec in specs:
  d=run/spec['case_id'];receipt=d/'complete.json'
  if receipt.exists():
   r=json.loads(receipt.read_text());assert r['status']=='PASS' and r['source_bindings']==bindings();done.append(spec['case_id']);continue
  if d.exists():raise RuntimeError('Incomplete attempt preserved; diagnose and explicitly record new attempt rather than overwrite: '+str(d))
  if time.perf_counter()-start>=budget:break
  command=[str(PYTHON),'-B',str(ROOT/'benchmark.py'),'worker','--run-id',run_id,'--case',spec['case_id']]
  try:rc=run_locked(command,run/'lock.jsonl',timeout=600)
  except Exception as error:
   write_json(run/'failure.json',{'case':spec['case_id'],'error':repr(error),'completed':done});raise
  if rc:
   write_json(run/'failure.json',{'case':spec['case_id'],'returncode':rc,'completed':done});raise SystemExit(rc)
  done.append(spec['case_id']);write_json(run/'progress.json',{'completed':done,'elapsed_seconds':time.perf_counter()-start})
 write_json(run/'status.json',{'status':'COMPLETE' if len(done)==30 else 'PARTIAL','completed':done,'elapsed_seconds':time.perf_counter()-start})

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('mode',choices=['run','worker']);p.add_argument('--run-id',default='client-refinement-20260926-v1');p.add_argument('--case');p.add_argument('--budget-seconds',type=int,default=5400);a=p.parse_args()
 if a.mode=='run':campaign(a.run_id,a.budget_seconds)
 else:worker(ROOT/'runs'/a.run_id,next(s for s in json.loads((ROOT/'FROZEN_GRID.json').read_text())['cases'] if s['case_id']==a.case))
