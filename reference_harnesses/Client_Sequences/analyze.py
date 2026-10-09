"""Saved-evidence verification and descriptive tables; no training imports."""
from pathlib import Path
import json,hashlib,csv,statistics,math,struct,argparse
from fractions import Fraction
from collections import Counter
ROOT=Path(__file__).resolve().parent

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def lines(p):return [json.loads(x) for x in p.read_text().splitlines()]
def save(p,value):p.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')
def table(name,rows):
 with (ROOT/'tables'/name).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader()
  for row in rows:w.writerow({k:json.dumps(v,sort_keys=True) if isinstance(v,(dict,list,tuple)) else v for k,v in row.items()})
def validate_model(model,k,d):
 assert model['map_version']=='FTF-1' and model['per_round_stats']==[] and len(model['trajectory'])==1
 assert model['final_centers']==model['trajectory'][0]
 for a in [*model['trajectory'],model['final_centers']]:
  assert a['shape']==[k,d] and a['dtype']=='<f8'
  blob=bytes.fromhex(a['bytes_hex']);assert len(blob)==8*k*d
  values=struct.unpack('<'+'d'*(k*d),blob)
  assert all(math.isfinite(x) for x in values)
  assert [x.hex() for x in values]==a['values_hex']
def main(run_id):
 run=ROOT/'runs'/run_id;assert read(run/'STATUS.json')['status']=='COMPLETE'
 manifest=read(run/'RUN_MANIFEST.json')
 for p,h in manifest['bindings'].items():assert sha(ROOT/p)==h,p
 grid=read(ROOT/'FROZEN_GRID.json');observations=[];checks=[];quality=[];setup=[];paired=[];cumulative=[]
 seen=set();positions=Counter();common_keys=('request_seconds','algorithm_seconds','persistence_seconds','operational_seconds')
 for case in grid['cases']:
  dr=run/case['case_id'];complete=read(dr/'complete.json');assert complete['status']=='PASS' and complete['source_bindings']==manifest['bindings']
  for p,h in complete['artifact_hashes'].items():assert sha(dr/p)==h,(case['case_id'],p)
  obs=lines(dr/'observations.jsonl');audit=lines(dr/'comparisons.jsonl');qrows=read(dr/'quality.json');prep=read(dr/'setup.json')
  assert len(obs)==18 and len(audit)==9 and len(qrows)==3
  by={(r['repetition'],r['step'],r['method']):r for r in obs};assert len(by)==18
  for r in obs:
   key=(case['case_id'],r['repetition'],r['step'],r['method']);assert key not in seen;seen.add(key)
   assert r['dataset']==case['dataset'] and r['seed']==case['seed'] and r['reload_validated']
   step=case['steps'][r['step']-1];assert r['withdrawn_client']==step['client_id']
   order=['fresh','compact'] if (case['case_index']+r['repetition']+r['step']-1)%2==0 else ['compact','fresh']
   assert r['order']==order and r['method']==order[r['position']]
   positions[(r['method'],r['position'])]+=1
   assert abs(r['request_seconds']-sum(r[x] for x in ('request_preparation_seconds','algorithm_seconds','model_output_seconds')))<1e-10
   assert abs(r['persistence_seconds']-sum(r[x] for x in ('serialization_seconds','write_seconds','read_seconds','deserialize_seconds','reload_validation_seconds')))<1e-10
   assert r['operational_seconds']==r['request_seconds']+r['persistence_seconds']
   assert all(r[x]>=0 for x in common_keys)
   path=dr/f'r{r["repetition"]}_s{r["step"]}_{r["method"]}_model.json'
   assert path.stat().st_size==r['model_output_bytes'] and sha(path)==r['model_output_sha256']
   validate_model(read(path),case['k'],grid['sequences'][case['dataset']]['d'])
  for rep in range(3):
   previous_hash=prep['original_state_hash'];previous_persist=None
   for step in case['steps']:
    n=step['step'];f=by[rep,n,'fresh'];c=by[rep,n,'compact']
    assert (dr/f'r{rep}_s{n}_fresh_model.json').read_bytes()==(dr/f'r{rep}_s{n}_compact_model.json').read_bytes()
    a=next(x for x in audit if x['repetition']==rep and x['step']==n)
    assert a['status']=='PASS' and a['input_state_hash']==previous_hash and a['previous_persisted_state_sha256']==previous_persist
    assert a['next_state_hash']==a['fresh_compact_state_hash'] and a['fresh_extra_sha256']==a['compact_extra_sha256']
    assert a['next_persisted_state_sha256']==c['state_sha256'] and a['model_sha256']==f['model_output_sha256']==c['model_output_sha256']
    assert a['next_active_ids']==step['active_client_ids'] and a['group_counts']==step['retained_group_counts']
    assert a['departing_client'] in a['input_active_ids'] and a['departing_client'] not in a['next_active_ids']
    assert sorted(set(a['input_active_ids'])-{a['departing_client']})==a['next_active_ids']
    for key in ('full_model_equal','every_summary_field_equal','ordered_anchor_table_equal','counts_equal','reload_equal','input_state_unchanged','used_reloaded_returned_next_state'):assert a[key] is True
    previous_hash=a['next_state_hash'];previous_persist=a['next_persisted_state_sha256']
  assert sha(dr/'compact_current.pkl')==by[2,3,'compact']['state_sha256']
  assert sha(dr/'fresh_current.json')==by[2,3,'fresh']['state_sha256']
  for n in (1,2,3):
   # Repeat invariance is checked by full output bytes, not rounded summary values.
   assert len({(dr/f'r{rep}_s{n}_fresh_model.json').read_bytes() for rep in range(3)})==1
   row={'dataset':case['dataset'],'seed':case['seed'],'step':n,'withdrawn_client':case['steps'][n-1]['client_id']}
   cum=dict(row)
   for method in ('fresh','compact'):
    for key in common_keys:
     vals=[by[rep,n,method][key] for rep in range(3)]
     row[f'{method}_{key}_mean']=statistics.mean(vals)
     row[f'{method}_{key}_min']=min(vals);row[f'{method}_{key}_max']=max(vals)
     cum[f'{method}_{key}']=statistics.mean([sum(by[rep,j,method][key] for j in range(1,n+1)) for rep in range(3)])
    row[f'{method}_state_bytes']=by[0,n,method]['state_bytes']
    assert len({by[rep,n,method]['state_sha256'] for rep in range(3)})==1
   for key in common_keys:
    row[f'{key}_ratio']=row[f'fresh_{key}_mean']/row[f'compact_{key}_mean']
    cum[f'{key}_ratio']=cum[f'fresh_{key}']/cum[f'compact_{key}']
   row['matched_repeat_ratio_min']=min(by[rep,n,'fresh']['request_seconds']/by[rep,n,'compact']['request_seconds'] for rep in range(3))
   row['matched_repeat_ratio_max']=max(by[rep,n,'fresh']['request_seconds']/by[rep,n,'compact']['request_seconds'] for rep in range(3))
   cum['compact_incremental_setup_operational_seconds']=cum['compact_operational_seconds']+prep['compaction_seconds']
   cum['fresh_common_training_operational_seconds']=cum['fresh_operational_seconds']+prep['initial_training_seconds']
   cum['compact_common_training_operational_seconds']=cum['compact_operational_seconds']+prep['initial_training_seconds']+prep['compaction_seconds']
   paired.append(row);cumulative.append(cum)
  for q in qrows:
   frac={k:Fraction(v['numerator'],v['denominator']) for k,v in q['exact'].items()}
   assert frac['Phi']==max(frac['Phi0'],frac['Phi1']) and frac['G']==frac['Phi0']+frac['Phi1']
   assert q['retained_group_counts']==case['steps'][q['step']-1]['retained_group_counts']
   assert frac['pooled_SSE']==sum(q['retained_group_counts'][g]*frac[f'Phi{g}'] for g in (0,1))
   assert all(float(frac[k])==q['values'][k] for k in frac)
   quality.append({'dataset':case['dataset'],'seed':case['seed'],'step':q['step'],**q['values'],'exact_fractions':q['exact'],'scoring_seconds':q['scoring_seconds']})
  setup.append({'dataset':case['dataset'],'seed':case['seed'],**{k:v for k,v in prep.items() if k not in ('environment','numpy_runtime')},'max_rss_bytes':complete['max_rss_bytes'],'repeat_reset_seconds':complete['repeat_reset_seconds']})
  observations.extend(obs);checks.extend(audit)
 assert len(observations)==270 and len(checks)==135 and len(quality)==45
 assert positions==Counter({('fresh',0):68,('fresh',1):67,('compact',0):67,('compact',1):68})
 summary=[]
 for dataset in ('adult','bank','credit'):
  for n in (1,2,3):
   rows=[r for r in paired if r['dataset']==dataset and r['step']==n];cr=[r for r in cumulative if r['dataset']==dataset and r['step']==n]
   row={'dataset':dataset,'step':n,'seeds':5}
   for method in ('fresh','compact'):
    for key in common_keys:
     row[f'{method}_{key}_mean']=statistics.mean(r[f'{method}_{key}_mean'] for r in rows)
     row[f'{method}_cumulative_{key}_mean']=statistics.mean(r[f'{method}_{key}'] for r in cr)
    row[f'{method}_state_bytes_mean']=statistics.mean(r[f'{method}_state_bytes'] for r in rows)
   for key in common_keys:
    row[f'{key}_ratio']=row[f'fresh_{key}_mean']/row[f'compact_{key}_mean']
    row[f'cumulative_{key}_ratio']=row[f'fresh_cumulative_{key}_mean']/row[f'compact_cumulative_{key}_mean']
    row[f'cumulative_{key}_ratio_seed_min']=min(r[f'{key}_ratio'] for r in cr)
    row[f'cumulative_{key}_ratio_seed_max']=max(r[f'{key}_ratio'] for r in cr)
   summary.append(row)
 (ROOT/'tables').mkdir(exist_ok=True)
 for name,rows in [('observations.csv',observations),('exactness.csv',checks),('quality.csv',quality),('setup.csv',setup),('paired_steps.csv',paired),('cumulative.csv',cumulative),('summary.csv',summary)]:table(name,rows)
 identity=[{'dataset':d,**{k:v for k,v in s.items() if k!='removed_source_rows'}} for d,v in grid['sequences'].items() for s in v['steps']];table('identities.csv',identity)
 locks=lines(run/'lock.jsonl');assert Counter(x['event'] for x in locks)==Counter({x:15 for x in ('waiting','acquired','worker_finished','released')})
 assert all(x['returncode']==0 for x in locks if x['event']=='worker_finished')
 for i in range(15):assert [x['event'] for x in locks[i*4:i*4+4]]==['waiting','acquired','worker_finished','released']
 verification={'status':'PASS','run_id':run_id,'distinct_sequences':15,'distinct_request_cases':45,'timing_repeats_per_sequence':3,'observations':270,'full_indexed_model_comparisons':135,'compact_extra_state_comparison_receipts':135,'serialization_reload_receipts':270,'verified_current_checkpoint_files':30,'exact_fraction_quality_rows':45,'source_binding_files':len(manifest['bindings']),'positions':{str(k):v for k,v in positions.items()},'lock_batches':15,'wait_seconds':sum(x['wait_seconds'] for x in locks if x['event']=='acquired'),'load_average_1min_range':[min(x['load_average'][0] for x in locks if 'load_average' in x),max(x['load_average'][0] for x in locks if 'load_average' in x)],'no_source_or_observation_changes':True,'scope':'Independent saved-model byte/fraction/reporting checker. Compact full-array comparisons executed by the worker; saved digest/chain receipts rechecked here, not an independent numerical oracle.','checked_artifacts':{str(p.relative_to(ROOT)):sha(p) for p in sorted(run.rglob('*')) if p.is_file()},'table_hashes':{p.name:sha(p) for p in sorted((ROOT/'tables').glob('*.csv'))}}
 save(ROOT/'VERIFICATION.json',verification)
 save(ROOT/'SUMMARY.json',{'dataset_steps':summary,'pooled_matched_ratio':sum(r['request_seconds'] for r in observations if r['method']=='fresh')/sum(r['request_seconds'] for r in observations if r['method']=='compact'),'pooled_operational_ratio':sum(r['operational_seconds'] for r in observations if r['method']=='fresh')/sum(r['operational_seconds'] for r in observations if r['method']=='compact'),'pooled_algorithm_ratio':sum(r['algorithm_seconds'] for r in observations if r['method']=='fresh')/sum(r['algorithm_seconds'] for r in observations if r['method']=='compact'),'matched_case_ratio_range':[min(r['request_seconds_ratio'] for r in paired),max(r['request_seconds_ratio'] for r in paired)],'operational_case_ratio_range':[min(r['operational_seconds_ratio'] for r in paired),max(r['operational_seconds_ratio'] for r in paired)]})
 print(json.dumps({k:v for k,v in read(ROOT/'SUMMARY.json').items() if k!='dataset_steps'},indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--run-id',default='sequences-20260926-v1');a=p.parse_args();main(a.run_id)
