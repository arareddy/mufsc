from common import *
from reviewed_benchmark import train,components,quality,state_witness
from client_c0 import compact_checkpoint,delete_clients
from unlearn import unlearn
from datasets import load_dataset
from with_lock import run_locked
from datetime import datetime,timezone
from dataclasses import fields
from fractions import Fraction
import argparse,time,gc,pickle,resource,subprocess,traceback

def bindings():
 return {str(p.relative_to(ROOT)):sha256(p) for p in sorted(ROOT.rglob('*')) if p.is_file() and (p.parent==ROOT and p.name in ('worker.py','PROTOCOL.md','FROZEN_GRID.json','SELECTION.json','client_c0.py','common.py','reviewed_benchmark.py','with_lock.py','SOURCE_VERIFICATION.json','INPUTS.json','IDENTITY_REGISTRY.json') or 'baseline' in p.relative_to(ROOT).parts)}
def compact_hash(s):return object_hash({f.name:getattr(s,f.name) for f in fields(s)})
def check_compact(s,fresh):
 expected=compact_checkpoint(fresh)
 for f in fields(s):
  if f.name!='slice_results':assert getattr(s,f.name)==getattr(expected,f.name),f.name
 # check_extra already compares each retained summary byte/field; compare dataclass canonical values too.
 assert compact_hash(s)==compact_hash(expected)
 return compact_hash(s)
def request(method,cd,go,checkpoint,state,spec,path):
 gc.collect();start=time.perf_counter();c=spec['deleted_client']
 if method=='fresh':args=({j:v for j,v in cd.items() if j!=c},{j:v for j,v in go.items() if j!=c})
 elif method=='direct':args={c:np.arange(len(cd[c]),dtype=np.int64)}
 else:args=[c]
 prepared=time.perf_counter();next_state=None
 if method=='fresh':result=train(*args,spec)
 elif method=='direct':result=unlearn(checkpoint,args,certificate_mode='none')
 else:result,next_state=delete_clients(state,args)
 finished=time.perf_counter()
 encoded=(json.dumps(projection(result),sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode();path.write_bytes(encoded);end=time.perf_counter()
 row={'method':method,'request_preparation_seconds':prepared-start,'algorithm_seconds':finished-prepared,'output_seconds':end-finished,'request_e2e_seconds':end-start,'output_bytes':len(encoded),'output_sha256':hashlib.sha256(encoded).hexdigest(),'components':components(result,method,finished-prepared),'output_path':str(path.relative_to(ROOT))}
 return result,next_state,row

def worker(run,ds,seed):
 batch=ROOT/'runs'/run/f'{ds}_seed{seed}';batch.mkdir(parents=True,exist_ok=False);start_batch=time.perf_counter()
 expected=json.loads((ROOT/'runs'/run/'manifest.json').read_text())['bindings'];assert bindings()==expected
 specs=[s for s in json.loads((ROOT/'FROZEN_GRID.json').read_text())['cases'] if s['dataset']==ds and s['seed']==seed]
 spec=specs[0];begin=time.perf_counter();cd,go,meta=load_dataset(ds,str(DATA),seed=0)
 inp=json.loads((ROOT/'INPUTS.json').read_text())['files'][ds];assert meta['source_sha256']==inp['sha256'] and sha256(inp['identity_path'])==inp['identity_sha256']
 for s in specs:
  c=s['deleted_client'];assert hashlib.sha256(np.asarray(meta['source_record_ids'][c],dtype='<i8').tobytes()).hexdigest()==s['ordered_removed_row_ids_sha256']
  assert len(cd[c])==s['removed_n'] and [int(np.count_nonzero(go[c]==g)) for g in (0,1)]==s['removed_group_counts']
 load=time.perf_counter()-begin;begin=time.perf_counter();checkpoint=train(cd,go,spec,cache=True);training=time.perf_counter()-begin
 begin=time.perf_counter();state=compact_checkpoint(checkpoint);compaction=time.perf_counter()-begin;state_hash=compact_hash(state)
 storage={}
 for label,obj in [('canonical',checkpoint),('compact',state)]:
  begin=time.perf_counter();blob=pickle.dumps(obj,protocol=5);storage[label]={'bytes':len(blob),'serialization_seconds':time.perf_counter()-begin};del blob
 write_json(batch/'setup.json',{'data_load_identity_seconds':load,'original_training_seconds':training,'compaction_seconds':compaction,'storage':storage,'environment':environment_manifest(),'case_count':len(specs),'original_state_sha256':state_hash})
 for spec in specs:
  case=batch/spec['case_id'];case.mkdir();c=spec['deleted_client'];retained={j:v for j,v in cd.items() if j!=c};groups={j:v for j,v in go.items() if j!=c}
  begin=time.perf_counter();fresh=train(retained,groups,spec);direct=unlearn(checkpoint,{c:np.arange(len(cd[c]),dtype=np.int64)},certificate_mode='none');fast,next_state=delete_clients(state,[c])
  for r in (direct,fast):assert projection(r)==projection(fresh);check_extra(r,fresh)
  compact_digest=check_compact(next_state,fresh);gate=projection(fresh);write_json(case/'gate_model.json',gate)
  write_json(case/'gate.json',{'status':'PASS','gate_seconds':time.perf_counter()-begin,'compact_state_sha256':compact_digest,'declared_state_sha256':object_hash(state_witness(fresh)),'retained_anchor_slots':len(fresh['anchor_table']['anchors']),'retained_slices':len(fresh['slice_results']),'retained_clients':len(next_state.client_ids),'retained_group_counts':spec['retained_group_counts'],'model_comparisons':2,'declared_state_comparisons':2,'returned_compact_state_comparisons':1})
  del direct,fast,next_state
  rows=[]
  for rep in range(3):
   canonical=['fresh','direct','fast'];offset=(spec['case_index']+rep)%3;order=canonical[offset:]+canonical[:offset];results={};states={}
   for position,method in enumerate(order):
    result,nxt,row=request(method,cd,go,checkpoint,state,spec,case/f'r{rep}_{method}.json');results[method]=result;states[method]=nxt
    row.update(case_id=spec['case_id'],dataset=ds,seed=seed,client=c,roles=spec['roles'],repetition=rep,position=position,order=order,utc=datetime.now(timezone.utc).isoformat());rows.append(row)
    with (case/'observations.jsonl').open('a') as f:f.write(json.dumps(row,sort_keys=True)+'\n')
   for method,result in results.items():assert projection(result)==gate;check_extra(result,fresh)
   assert check_compact(states['fast'],fresh)==compact_digest
   del results,states
  q=quality(retained,groups,fresh['final_centers'],spec);exact={k:Fraction(v['numerator'],v['denominator']) for k,v in q['exact'].items()};assert exact['Phi']==max(exact['Phi_A'],exact['Phi_B']) and exact['G']==exact['Phi_A']+exact['Phi_B'];write_json(case/'quality.json',q)
  assert compact_hash(state)==state_hash
  write_json(case/'complete.json',{'status':'PASS','case_id':spec['case_id'],'timed_gate_model_comparisons':9,'timed_declared_state_comparisons':9,'timed_returned_compact_state_comparisons':3,'original_state_unmodified':True,'files':{p.name:sha256(p) for p in case.iterdir() if p.is_file()}})
  print(spec['case_id'],'PASS',flush=True)
 assert bindings()==expected
 write_json(batch/'complete.json',{'status':'PASS','case_ids':[s['case_id'] for s in specs],'batch_wall_seconds':time.perf_counter()-start_batch,'max_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'bindings':expected})

def campaign(run):
 directory=ROOT/'runs'/run;directory.mkdir(exist_ok=True);write_json(directory/'manifest.json',{'bindings':bindings(),'run_id':run,'environment':environment_manifest()},immutable=True);start=time.perf_counter();done=[]
 for ds in ('adult','bank','credit'):
  for seed in range(10000,10005):
   batch=directory/f'{ds}_seed{seed}'
   if (batch/'complete.json').exists():assert json.loads((batch/'complete.json').read_text())['bindings']==bindings();done.append(batch.name);continue
   if batch.exists():raise RuntimeError('Incomplete batch retained; diagnose and use a new run ID')
   if time.perf_counter()-start>=5400:break
   rc=run_locked([str(PYTHON),'-B',str(ROOT/'worker.py'),'worker','--run',run,'--dataset',ds,'--seed',str(seed)],directory/'lock.jsonl',timeout=600)
   if rc:write_json(directory/'failure.json',{'batch':batch.name,'returncode':rc});raise SystemExit(rc)
   done.append(batch.name);write_json(directory/'progress.json',{'completed_batches':done,'expected_batches':15})
 write_json(directory/'status.json',{'status':'COMPLETE' if len(done)==15 else 'PARTIAL','completed_batches':done,'elapsed_seconds':time.perf_counter()-start})
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('mode',choices=['run','worker']);p.add_argument('--run',default='diversity-v1');p.add_argument('--dataset');p.add_argument('--seed',type=int);a=p.parse_args()
 if a.mode=='run':campaign(a.run)
 else:worker(a.run,a.dataset,a.seed)
