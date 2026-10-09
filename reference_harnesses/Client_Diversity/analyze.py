"""Report saved results only; no production numerical modules imported."""
from pathlib import Path
from fractions import Fraction
from collections import defaultdict,Counter
import json,csv,hashlib,statistics as st,math,struct
R=Path(__file__).resolve().parent;RUN=R/'runs/diversity-v1'
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
def table(name,rows):
 with (R/'tables'/name).open('w') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def sd(v):return st.stdev(v) if len(v)>1 else 0.
grid=load(R/'FROZEN_GRID.json')['cases'];select=load(R/'SELECTION.json');raw=[];cases=[];quality=[];setup=[];gate_counts=Counter()
assert load(RUN/'status.json')['status']=='COMPLETE'
for spec in grid:
 batch=RUN/f"{spec['dataset']}_seed{spec['seed']}";d=batch/spec['case_id'];complete=load(d/'complete.json');assert complete['status']=='PASS'
 for file,h in complete['files'].items():assert sha(d/file)==h
 gate=load(d/'gate_model.json');gg=load(d/'gate.json');assert gg['status']=='PASS'
 assert gate['map_version']=='FTF-1' and len(gate['trajectory'])==1 and gate['trajectory'][0]==gate['final_centers'] and gate['per_round_stats']==[]
 a=gate['final_centers'];assert a['shape']==[10,spec['d']] and a['dtype']=='<f8';values=struct.unpack('<'+'d'*(10*spec['d']),bytes.fromhex(a['bytes_hex']));assert all(math.isfinite(x) for x in values) and [x.hex() for x in values]==a['values_hex']
 obs=[json.loads(s) for s in (d/'observations.jsonl').read_text().splitlines()];assert len(obs)==9 and len({(o['method'],o['repetition']) for o in obs})==9
 for o in obs:
  assert o['case_id']==spec['case_id'] and o['seed']==spec['seed'] and o['client']==spec['deleted_client'];p=R/o['output_path'];assert sha(p)==o['output_sha256'] and p.stat().st_size==o['output_bytes'] and load(p)==gate
  assert math.isclose(o['request_e2e_seconds'],sum(o[k] for k in ('request_preparation_seconds','algorithm_seconds','output_seconds')),abs_tol=1e-12)
  assert math.isclose(o['algorithm_seconds'],sum(o['components'].values()),abs_tol=1e-12)
  order=['fresh','direct','fast'];off=(spec['case_index']+o['repetition'])%3;assert o['order']==order[off:]+order[:off] and o['order'][o['position']]==o['method']
  raw.append({k:v for k,v in o.items() if k not in ('roles','order','components')}|{'roles':';'.join(o['roles']),'order':';'.join(o['order']),**{f'component_{k}':v for k,v in o['components'].items()}})
 for m in ('fresh','direct','fast'):assert sorted(o['position'] for o in obs if o['method']==m)==[0,1,2]
 row={'case_id':spec['case_id'],'dataset':spec['dataset'],'client':spec['deleted_client'],'seed':spec['seed'],'roles':';'.join(spec['roles']),'removed_n':spec['removed_n'],'retained_anchors':gg['retained_anchor_slots'],'retained_slices':gg['retained_slices']}
 for m in ('fresh','direct','fast'):
  os=[o for o in obs if o['method']==m];times=[o['request_e2e_seconds']*1000 for o in os]
  for k in ('request_preparation_seconds','algorithm_seconds','output_seconds','request_e2e_seconds'):row[f'{m}_{k}_mean_ms']=st.mean(o[k]*1000 for o in os)
  row[f'{m}_request_sd_ms']=sd(times);row[f'{m}_request_cv']=sd(times)/st.mean(times);row[f'{m}_request_min_ms']=min(times);row[f'{m}_request_max_ms']=max(times)
 row['fresh_fast_ratio']=row['fresh_request_e2e_seconds_mean_ms']/row['fast_request_e2e_seconds_mean_ms'];row['fresh_direct_ratio']=row['fresh_request_e2e_seconds_mean_ms']/row['direct_request_e2e_seconds_mean_ms'];row['direct_fast_ratio']=row['direct_request_e2e_seconds_mean_ms']/row['fast_request_e2e_seconds_mean_ms'];cases.append(row)
 q=load(d/'quality.json');v={k:Fraction(x['numerator'],x['denominator']) for k,x in q['exact'].items()};assert v['Phi']==max(v['Phi_A'],v['Phi_B']) and v['G']==v['Phi_A']+v['Phi_B'];assert q['retained_group_counts']==spec['retained_group_counts'];assert v['pooled_SSE']==sum(n*v[k] for n,k in zip(q['retained_group_counts'],('Phi_A','Phi_B')))
 for k,x in v.items():assert float(x)==q['values'][k]
 quality.append({'case_id':spec['case_id'],'dataset':spec['dataset'],'client':spec['deleted_client'],'seed':spec['seed'],**{k:float(x) for k,x in v.items()},**{k+'_exact':str(x) for k,x in v.items()},'materialization_ms':q['quality_input_materialization_seconds']*1000,'scoring_ms':q['quality_evaluation_seconds']*1000})
 for k in ('model_comparisons','declared_state_comparisons','returned_compact_state_comparisons'):gate_counts[k]+=gg[k]
 for k in ('timed_gate_model_comparisons','timed_declared_state_comparisons','timed_returned_compact_state_comparisons'):gate_counts[k]+=complete[k]
assert len(cases)==30 and len(raw)==270
# Rectangular raw table, preserving component fields specific to each API.
keys=list(dict.fromkeys(k for row in raw for k in row));raw=[{k:row.get(k,'') for k in keys} for row in raw];table('raw_timings.csv',raw);table('cases.csv',cases);table('quality.csv',quality)
summary=[]
for dim in ('all','dataset','client','role','seed','dataset_seed'):
 groups=defaultdict(list)
 for c in cases:
  vals=['all'] if dim=='all' else [c['dataset']] if dim=='dataset' else [f"{c['dataset']}/c{c['client']}"] if dim=='client' else [f"{c['dataset']}/{r}" for r in c['roles'].split(';')] if dim=='role' else [str(c['seed'])] if dim=='seed' else [f"{c['dataset']}/{c['seed']}"]
  for val in vals:groups[val].append(c)
 for val,cs in groups.items():
  r={'dimension':dim,'group':val,'unique_cases':len(cs),'distinct_dataset_clients':len({(c['dataset'],c['client']) for c in cs})}
  for m in ('fresh','direct','fast'):
   for boundary in ('request_e2e_seconds','algorithm_seconds'):
    times=[c[f'{m}_{boundary}_mean_ms'] for c in cs];r[f'{m}_{boundary}_mean_ms']=st.mean(times);r[f'{m}_{boundary}_total_ms']=sum(times)*3
  for a,b in (('fresh','fast'),('fresh','direct'),('direct','fast')):
   ratios=[c[f'{a}_request_e2e_seconds_mean_ms']/c[f'{b}_request_e2e_seconds_mean_ms'] for c in cs];key=a+'_'+b
   r[key+'_total_ratio']=sum(c[f'{a}_request_e2e_seconds_mean_ms'] for c in cs)/sum(c[f'{b}_request_e2e_seconds_mean_ms'] for c in cs)
   r[key+'_paired_mean']=st.mean(ratios);r[key+'_paired_median']=st.median(ratios);r[key+'_paired_sd']=sd(ratios);r[key+'_paired_min']=min(ratios);r[key+'_paired_max']=max(ratios);r[key+'_wins']=sum(x>1 for x in ratios);r[key+'_losses']=sum(x<1 for x in ratios);r[key+'_ties']=sum(x==1 for x in ratios);r[key+'_over10']=sum(x>10 for x in ratios)
  summary.append(r)
table('summary.csv',summary)
comps=[]
for ds in select:
 for method in ('fresh','direct','fast'):
  rr=[r for r in raw if r['dataset']==ds and r['method']==method]
  for key in keys:
   if key.startswith('component_') or key in ('request_preparation_seconds','algorithm_seconds','output_seconds','request_e2e_seconds'):
    v=[r[key]*1000 for r in rr if r[key]!='']
    if v:comps.append({'dataset':ds,'method':method,'component':key,'observations':len(v),'mean_ms':st.mean(v),'sd_ms':sd(v),'min_ms':min(v),'max_ms':max(v)})
table('components.csv',comps)
selrows=[]
for ds,s in select.items():
 for c in s['clients']:
  if c['roles']:selrows.append({'dataset':ds,'client':c['client'],'source_client_id':c['source_client_id'],'roles':';'.join(c['roles']),'size':c['size'],'group0':c['group_counts'][0],'group1':c['group_counts'][1],'group0_fraction':str(Fraction(**c['group0_fraction'])),'remaining0':c['remaining_group_counts'][0],'remaining1':c['remaining_group_counts'][1],'ordered_row_ids_sha256':c['ordered_row_ids_sha256']})
table('selection.csv',selrows)
for b in sorted(RUN.glob('*_seed*')):
 s=load(b/'setup.json');c=load(b/'complete.json');assert c['status']=='PASS' and len(c['case_ids'])==2
 setup.append({'batch':b.name,'load_ms':s['data_load_identity_seconds']*1000,'initial_training_ms':s['original_training_seconds']*1000,'compaction_ms':s['compaction_seconds']*1000,'canonical_pickle_bytes':s['storage']['canonical']['bytes'],'compact_pickle_bytes':s['storage']['compact']['bytes'],'canonical_serialization_ms':s['storage']['canonical']['serialization_seconds']*1000,'compact_serialization_ms':s['storage']['compact']['serialization_seconds']*1000,'batch_wall_seconds':c['batch_wall_seconds']})
table('setup.csv',setup)
logs=[json.loads(x) for x in (RUN/'lock.jsonl').read_text().splitlines()];assert [x['event'] for x in logs]==['waiting','acquired','worker_finished','released']*15 and all(x['returncode']==0 for x in logs if x['event']=='worker_finished')
for file,h in load(R/'COMPLETED_INPUT_BINDINGS.json').items():assert sha(Path(file))==h
assert sha(R/'client_c0.py')==load(R/'SOURCE_VERIFICATION.json')['candidate_sha256']
write(R/'VERIFICATION.json',{'status':'PASS','unique_cases':30,'timed_observations':270,'completed_batches':15,'exact_quality_checks':30,'counts':dict(gate_counts),'complete_input_bindings_unchanged':True,'candidate_unchanged':True,'equal_output_bytes_and_gate_models':True,'balanced_order_and_time_decomposition':True,'all_case_receipt_hashes_valid':True,'lock_batches':15,'scope':'Saved-output and reporting verification; kernel/state equality is asserted by bound worker, not a new independent numerical oracle.'})
write(R/'analysis_summary.json',{'all':summary[0],'datasets':[x for x in summary if x['dimension']=='dataset'],'clients':[x for x in summary if x['dimension']=='client'],'counts':dict(gate_counts),'lock_wait_seconds':sum(x['wait_seconds'] for x in logs if x['event']=='acquired'),'lock_held_seconds':sum(x['held_seconds'] for x in logs if x['event']=='released')})
print(json.dumps(load(R/'analysis_summary.json'),indent=2))
