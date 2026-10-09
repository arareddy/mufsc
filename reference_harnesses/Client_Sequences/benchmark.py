from common import *
from train import train_full
from fixedpoint import FixedPointConfig,represented_clients
from datasets import load_dataset
from objective import fair_objective
from client_c0 import compact_checkpoint,delete_clients
from service import check_state,persist,state_hash
from with_lock import run_locked
from datetime import datetime,timezone
import argparse,time,gc,pickle,resource,traceback,io,contextlib

CORE=('client_c0.py','common.py','service.py','benchmark.py','with_lock.py','fixtures.py','freeze.py','PROTOCOL.md','FROZEN_GRID.json','BASELINE_MANIFEST.json','INPUTS.json','IDENTITY_REGISTRY.json','INPUT_MANIFEST.json','CORRECTNESS.json')
def bindings():
 out={name:sha256(ROOT/name) for name in CORE}
 out.update({str(p.relative_to(ROOT)):sha256(p) for p in sorted((ROOT/'baseline').rglob('*')) if p.is_file()})
 return out

def train(cd,go,spec,cache=False):
 return train_full(cd,go,spec['seed'],spec['k'],0,spec['L'],gamma=spec['gamma'],fp_cfg=FixedPointConfig(spec['scale_bits'],spec['clip']),anchor_lloyd_iters=spec['anchor_lloyd_iters'],build_cache=cache)

def measured(method,cd,go,current,spec,step,path):
 gc.collect();start=time.perf_counter();c=step['client_id']
 if method=='fresh':
  active=tuple(x for x in current if x!=c)
  assert c in current
  retained={x:cd[x] for x in active};groups={x:go[x] for x in active}
 else:depart=[c]
 prepared=time.perf_counter()
 if method=='fresh':result=train(retained,groups,spec);next_state=active
 else:result,next_state=delete_clients(current,depart)
 finished=time.perf_counter()
 blob=(json.dumps(projection(result),sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
 path.write_bytes(blob);end=time.perf_counter()
 row={'request_preparation_seconds':prepared-start,'algorithm_seconds':finished-prepared,'model_output_seconds':end-finished,'request_seconds':end-start,'model_output_bytes':len(blob),'model_output_sha256':hashlib.sha256(blob).hexdigest()}
 loaded,storage=persist(method,next_state,path.parent/(f'{method}_current.'+('pkl' if method=='compact' else 'json')))
 row.update(storage);row['operational_seconds']=row['request_seconds']+row['persistence_seconds']
 return result,next_state,loaded,row

def quality(cd,go,centers,spec):
 begin=time.perf_counter();fixed,_=represented_clients(cd,FixedPointConfig(spec['scale_bits'],spec['clip']))
 X=np.concatenate([fixed[c] for c in sorted(fixed)]);groups=np.concatenate([go[c] for c in sorted(go)])
 a,b,G,Phi=fair_objective(X,groups,centers,return_exact=True)
 assert Phi==max(a,b) and G==a+b
 ng=[int(np.count_nonzero(groups==g)) for g in (0,1)];pooled=ng[0]*a+ng[1]*b
 return {'exact':{k:{'numerator':v.numerator,'denominator':v.denominator} for k,v in zip(('Phi0','Phi1','G','Phi','pooled_SSE'),(a,b,G,Phi,pooled))},'values':dict(zip(('Phi0','Phi1','G','Phi','pooled_SSE'),map(float,(a,b,G,Phi,pooled)))),'retained_group_counts':ng,'scoring_seconds':time.perf_counter()-begin}

def append(path,value):
 with path.open('a') as f:f.write(json.dumps(jsonable(value),sort_keys=True)+'\n')

def worker(run,spec):
 directory=run/spec['case_id'];directory.mkdir()
 start=time.perf_counter();cd,go,meta=load_dataset(spec['dataset'],str(DATA),seed=0);load=time.perf_counter()-start
 inp=json.loads((ROOT/'INPUTS.json').read_text())['files'][spec['dataset']]
 assert meta['source_sha256']==inp['sha256'] and sha256(inp['identity_path'])==inp['identity_sha256'] and meta['clip']==spec['clip']
 registry=json.loads((ROOT/'IDENTITY_REGISTRY.json').read_text())[spec['dataset']]
 for c in cd:
  assert hashlib.sha256(np.asarray(meta['source_record_ids'][c],dtype='<i8').tobytes()).hexdigest()==registry[str(c)]['ordered_full_row_ids_sha256']
 gc.collect();start=time.perf_counter();checkpoint=train(cd,go,spec,cache=True);initial_train=time.perf_counter()-start
 start=time.perf_counter();original=compact_checkpoint(checkpoint);compaction=time.perf_counter()-start
 start=time.perf_counter();full_blob=pickle.dumps(checkpoint,protocol=5);full_serial=time.perf_counter()-start;full_size=len(full_blob);del full_blob
 start=time.perf_counter();original_blob=pickle.dumps(original,protocol=5);original_serial=time.perf_counter()-start
 original_hash=state_hash(original)
 runtime=io.StringIO()
 with contextlib.redirect_stdout(runtime):np.show_runtime()
 setup={'data_load_identity_seconds':load,'initial_training_seconds':initial_train,'compaction_seconds':compaction,'full_checkpoint_pickle_bytes':full_size,'full_checkpoint_serialization_seconds':full_serial,'original_compact_pickle_bytes':len(original_blob),'original_compact_serialization_seconds':original_serial,'original_state_hash':original_hash,'environment':environment_manifest(),'numpy_runtime':runtime.getvalue()}
 write_json(directory/'setup.json',setup);del checkpoint
 comparisons=[];quality_rows=[];resets=[];all_rows=[]
 for rep in range(3):
  start=time.perf_counter();current=original;fresh_active=tuple(sorted(cd));resets.append(time.perf_counter()-start)
  assert state_hash(current)==original_hash
  previous_persisted_hash=None
  for step in spec['steps']:
   index=step['step']-1;c=step['client_id'];input_state_hash=state_hash(current)
   assert current.client_ids==fresh_active
   before_ids=list(current.client_ids)
   order=('fresh','compact') if (spec['case_index']+rep+index)%2==0 else ('compact','fresh')
   results={};returned={};reloaded={};rows={}
   for position,method in enumerate(order):
    result,new,loaded,row=measured(method,cd,go,current if method=='compact' else fresh_active,spec,step,directory/f'r{rep}_s{step["step"]}_{method}_model.json')
    row.update(dataset=spec['dataset'],seed=spec['seed'],case_id=spec['case_id'],repetition=rep,step=step['step'],method=method,position=position,order=list(order),withdrawn_client=c,utc=datetime.now(timezone.utc).isoformat())
    results[method]=result;returned[method]=new;reloaded[method]=loaded;rows[method]=row
    append(directory/'observations.jsonl',row);all_rows.append(row)
   verify_start=time.perf_counter()
   fresh=results['fresh'];compact=results['compact']
   assert projection(compact)==projection(fresh);check_extra(compact,fresh)
   expected=compact_checkpoint(fresh);check_state(returned['compact'],expected);check_state(reloaded['compact'],expected)
   assert state_hash(current)==input_state_hash
   current=reloaded['compact'];fresh_active=reloaded['fresh']
   assert list(current.client_ids)==step['active_client_ids']==list(fresh_active)
   assert [current.group_sizes[g] for g in (0,1)]==step['retained_group_counts']
   assert [int(x) for x in meta['source_record_ids'][c]]==step['removed_source_rows']
   actual_survivors=np.concatenate([meta['source_record_ids'][x] for x in fresh_active]).astype('<i8')
   assert hashlib.sha256(actual_survivors.tobytes()).hexdigest()==step['retained_ordered_rows_sha256']
   assert sum(len(cd[x]) for x in fresh_active)==step['retained_n']
   extra_keys=('group_sizes','slice_results','anchor_table')
   extra_fresh=object_hash({k:fresh[k] for k in extra_keys});extra_compact=object_hash({k:compact[k] for k in extra_keys});assert extra_fresh==extra_compact
   receipt={'case_id':spec['case_id'],'repetition':rep,'step':step['step'],'status':'PASS','departing_client':c,'input_active_ids':before_ids,'next_active_ids':list(current.client_ids),'input_state_hash':input_state_hash,'previous_persisted_state_sha256':previous_persisted_hash,'next_state_hash':state_hash(current),'fresh_compact_state_hash':state_hash(expected),'next_persisted_state_sha256':rows['compact']['state_sha256'],'fresh_extra_sha256':extra_fresh,'compact_extra_sha256':extra_compact,'full_model_equal':True,'every_summary_field_equal':True,'ordered_anchor_table_equal':True,'counts_equal':True,'reload_equal':True,'input_state_unchanged':True,'used_reloaded_returned_next_state':True,'model_sha256':rows['fresh']['model_output_sha256'],'group_counts':step['retained_group_counts'],'removed_n':step['removed_n'],'retained_n':step['retained_n'],'audit_seconds':time.perf_counter()-verify_start}
   previous_persisted_hash=rows['compact']['state_sha256'];append(directory/'comparisons.jsonl',receipt);comparisons.append(receipt)
   if rep==0:
    q=quality({x:cd[x] for x in fresh_active},{x:go[x] for x in fresh_active},fresh['final_centers'],spec)
    quality_rows.append({'step':step['step'],**q});write_json(directory/'quality.json',quality_rows)
   del results,returned,reloaded,expected
  assert state_hash(original)==original_hash
 write_json(directory/'complete.json',{'status':'PASS','case_id':spec['case_id'],'source_bindings':bindings(),'comparisons':len(comparisons),'observations':len(all_rows),'repetitions':3,'repeat_reset_seconds':resets,'max_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'artifact_hashes':{str(p.name):sha256(p) for p in sorted(directory.iterdir()) if p.is_file()}})
 print(spec['case_id'],'9 sequential comparisons PASS',flush=True)

def campaign(run_id,budget):
 assert Path(run_id).name==run_id
 run=ROOT/'runs'/run_id;run.mkdir(parents=True,exist_ok=True)
 gate=json.loads((ROOT/'CORRECTNESS.json').read_text());assert gate['status']=='PASS'
 for name,hashvalue in gate['source_hashes'].items():assert sha256(ROOT/name)==hashvalue
 write_json(run/'RUN_MANIFEST.json',{'run_id':run_id,'bindings':bindings(),'environment':environment_manifest()},immutable=True)
 start=time.perf_counter();done=[]
 for spec in json.loads((ROOT/'FROZEN_GRID.json').read_text())['cases']:
  path=run/spec['case_id']
  if (path/'complete.json').exists():
   saved=json.loads((path/'complete.json').read_text());assert saved['status']=='PASS' and saved['source_bindings']==bindings();done.append(spec['case_id']);continue
  if path.exists():raise RuntimeError('Incomplete case preserved; use a new attempt, never append a rerun: '+str(path))
  if time.perf_counter()-start>=budget:break
  command=[str(PYTHON),'-B',str(ROOT/'benchmark.py'),'worker','--run-id',run_id,'--case',spec['case_id']]
  rc=run_locked(command,run/'lock.jsonl',timeout=600)
  if rc:
   write_json(run/'FAILURE.json',{'failed_case':spec['case_id'],'returncode':rc,'completed':done});raise SystemExit(rc)
  done.append(spec['case_id']);write_json(run/'PROGRESS.json',{'completed':done,'elapsed_seconds':time.perf_counter()-start})
 write_json(run/'STATUS.json',{'status':'COMPLETE' if len(done)==15 else 'PARTIAL','completed':done,'elapsed_seconds':time.perf_counter()-start})

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('mode',choices=['run','worker']);p.add_argument('--run-id',required=True);p.add_argument('--case');p.add_argument('--budget-seconds',type=int,default=5400);a=p.parse_args()
 if a.mode=='run':campaign(a.run_id,a.budget_seconds)
 else:
  spec=next(x for x in json.loads((ROOT/'FROZEN_GRID.json').read_text())['cases'] if x['case_id']==a.case)
  try:worker(ROOT/'runs'/a.run_id,spec)
  except BaseException:
   error=traceback.format_exc();(ROOT/'runs'/a.run_id/spec['case_id']/'ERROR.txt').write_text(error);raise
