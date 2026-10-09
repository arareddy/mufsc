"""Independent saved-fraction analysis. Standard library only; never imports training."""
import csv,json,hashlib,struct,math,datetime,traceback
from pathlib import Path
from fractions import Fraction as F
from collections import defaultdict
W=Path(__file__).resolve().parent;A=Path('study://Round_Budgets');B=Path('study://Client_Deletion')
OUT=W/'tables';OUT.mkdir(exist_ok=True)
def load(p):return json.loads(p.read_text())
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def objsha(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def table(name,rows):
 assert rows
 with (OUT/name).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def frac(x):
 assert type(x['numerator']) is int and type(x['denominator']) is int and x['denominator']>0
 return F(x['numerator'],x['denominator'])
def addfrac(r,k,v):
 r[k+'_exact']=str(v) if v is not None else '';r[k]=float(v) if v is not None else ''
def derive(q,counts):
 v={k:frac(q['exact'][k]) for k in ['Phi_A','Phi_B','Phi','G']}
 assert all(x>=0 for x in v.values())
 assert v['Phi']==max(v['Phi_A'],v['Phi_B'])
 assert v['G']==v['Phi_A']+v['Phi_B']
 floats=q.get('values',q)
 assert all(floats[k]==float(x) for k,x in v.items())
 assert min(counts)>0
 v['pooled_SSE']=sum(F(n)*v[k] for n,k in zip(counts,['Phi_A','Phi_B']))
 if 'pooled_SSE' in q['exact']:assert v['pooled_SSE']==frac(q['exact']['pooled_SSE']) and floats['pooled_SSE']==float(v['pooled_SSE'])
 v['population_average']=v['pooled_SSE']/sum(counts)
 v['absolute_group_gap']=abs(v['Phi_A']-v['Phi_B'])
 lo=min(v['Phi_A'],v['Phi_B']);v['max_min_group_ratio']=v['Phi']/lo if lo else None
 return v

def witness(w,T,k,d,counts):
 assert len(w['trajectory'])==T+1 and len(w['per_round_stats'])==T and w['final_centers']==w['trajectory'][-1]
 for arr in w['trajectory']:
  assert arr['shape']==[k,d] and arr['dtype']=='<f8'
  b=bytes.fromhex(arr['bytes_hex']);vals=struct.unpack('<'+'d'*(k*d),b)
  assert all(math.isfinite(v) for v in vals)
  assert list(map(float.hex,vals))==arr['values_hex']
 for s in w['per_round_stats']:
  N=s['N'];assert [sum(g) for g in N]==counts
  assert all(type(n) is int and n>=0 for g in N for n in g)

def main():
 frozen=load(W/'INPUT_MANIFEST.json');pf=load(W/'PROTOCOL_FREEZE.json')
 assert sha(W/'PROTOCOL.md')==pf['protocol_sha256']==frozen['protocol_sha256']
 assert sha(W/'INPUT_MANIFEST.json')==pf['input_manifest_sha256']
 for f in frozen['files']:
  p=Path(f['path']);s=p.stat();assert (s.st_size,s.st_mtime_ns,sha(p))==(f['bytes'],f['mtime_ns'],f['sha256']),str(p)
 ah=load(A/'baseline_manifest.json');bh=load(B/'BASELINE_MANIFEST.json');source_checks=0
 for name,h in ah['files'].items():
  assert h==bh['files'][name]['sha256']
  for p in [A/'source'/name,B/'baseline'/name,Path(bh['files'][name]['source'])]:assert sha(p)==h;source_checks+=1
 identities={};inputs=load(B/'INPUTS.json')['files'];registry=load(B/'IDENTITY_REGISTRY.json')
 for ds,v in inputs.items():
  assert sha(Path(v['path']))==v['sha256'];p=Path(v['identity_path']);assert sha(p)==v['identity_sha256'];ident=load(p);identities[ds]=ident
  allids=[i for a in ident['source_record_ids'].values() for i in a];assert len(allids)==len(set(allids))==v['n']
  assert ident['source_sha256']==v['sha256']
  for c,ids in ident['source_record_ids'].items():
   rec=registry[ds][c];assert rec['row_count']==len(ids) and rec['source_client_id']==ident['source_client_ids'][c]
   assert rec['ordered_full_row_ids_sha256']==hashlib.sha256(struct.pack('<'+'q'*len(ids),*ids)).hexdigest()
 rows=[];idrows=[];checks=[];casevals={};prefix_checks=0
 def emit(pop,ds,seed,T,counts,vals,path,identity_hash):
  key=(pop,ds,seed,T);assert key not in casevals;casevals[key]=vals
  row=dict(population=pop,dataset=ds,seed=seed,T=T,n_group0=counts[0],n_group1=counts[1],retained_n=sum(counts),source_path=str(path),source_sha256=sha(path),retained_identity_sha256=identity_hash)
  for k,v in vals.items():addfrac(row,k,v)
  row['ratio_status']='defined' if vals['max_min_group_ratio'] is not None else 'undefined_zero_minimum'
  row['worst_group']='tie' if vals['Phi_A']==vals['Phi_B'] else ('0' if vals['Phi_A']>vals['Phi_B'] else '1')
  rows.append(row)
 for inp in load(A/'input_manifest.json'):
  ds=inp['dataset'];seed=inp['settings']['seed'];meta=inp['meta'];req=load(Path(inp['request']));ident=identities[ds]
  assert sha(Path(inp['input']))==inp['input_sha256'] and sha(Path(inp['request']))==inp['request_sha256']
  for k in ['source_record_ids','source_client_ids','source_sha256','group_counts']:assert meta[k]==ident[k]
  removed=[];retained=[]
  for c in sorted(meta['source_record_ids'],key=int):
   ids=meta['source_record_ids'][c];rm=req['removed'].get(c,[]);assert len(rm)==len(set(rm))
   for i in rm:
    v=ids[i];removed.append(dict(client_id=int(c),local_row=i,processed_full_row=v,source_client_id=meta['source_client_ids'][c],stable_record_id=f"{meta['source_sha256']}:full-row:{v}"))
   retained.extend([int(c),i,v] for i,v in enumerate(ids) if i not in set(rm))
  assert removed==req['removed_source_records'] and objsha(removed)==req['removal_source_identity_hash']
  assert len(removed)==inp['removed'] and len(retained)==inp['n']-inp['removed']
  root=A/'runs'/(A/'RUN_ID').read_text().strip();r1=root/f'{ds}_s{seed}_T1';counts=[sum(x) for x in load(r1/'gate_fresh.witness.json')['per_round_stats'][0]['N']]
  orig=[sum(x) for x in load(r1/'checkpoint.witness.json')['per_round_stats'][0]['N']]
  assert orig==[meta['group_counts'][str(g)] for g in (0,1)] and sum(counts)==len(retained)
  assert all(0<=o-n<=inp['removed'] for o,n in zip(orig,counts))
  rh=objsha(retained);idrows.append(dict(population='record',dataset=ds,seed=seed,original_n=inp['n'],removed_n=len(removed),retained_n=sum(counts),n_group0=counts[0],n_group1=counts[1],removed_group0=orig[0]-counts[0],removed_group1=orig[1]-counts[1],retained_identity_sha256=rh,removed_identity_sha256=objsha(removed)))
  trajs=[]
  for T in range(3):
   r=root/f'{ds}_s{seed}_T{T}';receipt=load(r/'complete.json');assert receipt['status']=='PASS';fresh=load(r/'gate_fresh.witness.json');witness(fresh,T,10,inp['d'],counts);trajs.append(fresh)
   q=load(r/'gate_fresh.json')['quality'];values=derive(q,counts)
   for m in ['fresh','none','basic','runnerup']:
    p=r/f'gate_{m}.json';wp=r/f'gate_{m}.witness.json';g=load(p)
    assert receipt['files'][p.name]==sha(p) and receipt['files'][wp.name]==sha(wp)
    assert g['dataset']==ds and g['seed']==seed and g['T']==T and g['method']==m
    assert g['witness_sha256']==sha(wp) and load(wp)==fresh and derive(g['quality'],counts)==values
    checks.append(dict(population='record',dataset=ds,seed=seed,T=T,method=m,exact_definitions=True,counts=True,same_budget_model_equal=True))
   emit('record',ds,seed,T,counts,values,r/'gate_fresh.json',rh)
  for T in (0,1):
   assert trajs[T]['trajectory']==trajs[2]['trajectory'][:T+1] and trajs[T]['per_round_stats']==trajs[2]['per_round_stats'][:T];prefix_checks+=1
 for case in load(B/'FROZEN_GRID.json')['cases']:
  ds=case['dataset'];seed=case['seed'];c=str(case['deleted_client']);ident=identities[ds];counts=case['retained_group_counts'];orig=inputs[ds]['group_counts']
  assert not case['excluded'] and case['removed_source_rows']==ident['source_record_ids'][c]
  assert [o-r for o,r in zip(orig,case['removed_group_counts'])]==counts and sum(counts)==case['n']-case['removed_n']
  assert len(case['removed_source_rows'])==case['removed_n']==registry[ds][c]['row_count']
  retained=[[int(cid),i,v] for cid in sorted(ident['source_record_ids'],key=int) if cid!=c for i,v in enumerate(ident['source_record_ids'][cid])];rh=objsha(retained)
  r=B/'runs/client-c0-20260926-v1/quality'/case['case_id'];core=B/'runs/client-c0-20260926-v1/core'/case['case_id'];receipt=load(r/'complete.json');cp=load(core/'complete.json')
  assert receipt['status']==cp['status']=='PASS' and receipt['same_population_as_core']
  assert receipt['quality_sha256']==sha(r/'quality.json') and cp['extra_state_witness_sha256']==sha(core/'extra_state_witness.json')
  for rr in [receipt,cp]:
   for n,h in rr['source_bindings'].items():assert sha(B/n)==h
  assert [load(core/'extra_state_witness.json')['group_sizes'][str(g)] for g in (0,1)]==counts
  qrows=load(r/'quality.json');assert [q['T'] for q in qrows]==[0,1,2]
  assert qrows[0]['model_witness']==load(core/'rep0_fresh_model.json')==cp['full_model_witness']
  idrows.append(dict(population='client',dataset=ds,seed=seed,original_n=case['n'],removed_n=case['removed_n'],retained_n=sum(counts),n_group0=counts[0],n_group1=counts[1],removed_group0=case['removed_group_counts'][0],removed_group1=case['removed_group_counts'][1],retained_identity_sha256=rh,removed_identity_sha256=objsha(case['removed_source_rows'])))
  for q in qrows:
   T=q['T'];assert q['quality']['retained_group_counts']==counts;witness(q['model_witness'],T,10,case['d'],counts)
   assert q['model_witness']['trajectory']==qrows[2]['model_witness']['trajectory'][:T+1]
   assert q['model_witness']['per_round_stats']==qrows[2]['model_witness']['per_round_stats'][:T]
   prefix_checks+=T<2
   vals=derive(q['quality'],counts);emit('client',ds,seed,T,counts,vals,r/'quality.json',rh)
   checks.append(dict(population='client',dataset=ds,seed=seed,T=T,method='fresh_quality',exact_definitions=True,counts=True,same_budget_model_equal='T0_core_link' if T==0 else 'quality_reference_only'))
 assert len(rows)==90 and len(idrows)==30 and len(checks)==225
 # Compare completed rounded reporting tables as a secondary sanity check, never a source of arithmetic.
 bcsv=list(csv.DictReader((B/'tables/quality.csv').open()));assert len(bcsv)==45
 for r in bcsv:
  vals=casevals['client',r['dataset'],int(r['seed']),int(r['T'])]
  assert all(float(r[k])==float(vals[k]) for k in ['Phi_A','Phi_B','Phi','G','pooled_SSE'])
 table('case_quality.csv',rows);table('identity_counts.csv',idrows);table('definition_checks.csv',checks)
 groups=[]
 for r in rows:
  for g,k in enumerate(['Phi_A','Phi_B']):groups.append({**{k:r[k] for k in ['population','dataset','seed','T']},'group':g,'n_group':r[f'n_group{g}'],'cost_exact':r[k+'_exact'],'cost':r[k]})
 table('group_costs.csv',groups)
 summaries=[];aggregation=[];paired=[];trans=[]
 metrics=list(next(iter(casevals.values())))
 for pop in ['record','client']:
  for ds in ['adult','bank','credit']:
   for T in range(3):
    vv=[casevals[pop,ds,s,T] for s in range(10000,10005)]
    for k in metrics:
     xs=[v[k] for v in vv if v[k] is not None];r=dict(population=pop,dataset=ds,T=T,metric=k,seeds=5,defined_n=len(xs),undefined_n=5-len(xs));mean=sum(xs,F(0))/len(xs) if xs else None;var=sum(((x-mean)**2 for x in xs),F(0))/(len(xs)-1) if len(xs)>1 else None
     for n,v in [('mean',mean),('sample_variance',var),('min',min(xs) if xs else None),('max',max(xs) if xs else None)]:addfrac(r,n,v)
     r['sample_sd']=math.sqrt(float(var)) if var is not None else '';summaries.append(r)
    mm=sum((v['Phi'] for v in vv),F(0))/5;mg=max(sum((v[g] for v in vv),F(0))/5 for g in ['Phi_A','Phi_B']);r=dict(population=pop,dataset=ds,T=T)
    for n,v in [('mean_of_seed_maxima',mm),('max_of_group_seed_means',mg),('difference',mm-mg)]:addfrac(r,n,v)
    r.update(group0_worst_seeds=sum(v['Phi_A']>v['Phi_B'] for v in vv),group1_worst_seeds=sum(v['Phi_B']>v['Phi_A'] for v in vv),tie_seeds=sum(v['Phi_A']==v['Phi_B'] for v in vv));aggregation.append(r)
   for seed in range(10000,10005):
    for t0,t1 in [(0,1),(1,2),(0,2)]:
     before=casevals[pop,ds,seed,t0];after=casevals[pop,ds,seed,t1];key=dict(population=pop,dataset=ds,seed=seed,T_from=t0,T_to=t1)
     tr={**key,'Phi_decreases':after['Phi']<before['Phi'],'group0_increases':after['Phi_A']>before['Phi_A'],'group1_increases':after['Phi_B']>before['Phi_B']}
     tr['any_group_increase_while_Phi_decreases']=tr['Phi_decreases'] and (tr['group0_increases'] or tr['group1_increases']);trans.append(tr)
     for k in metrics:
      a,b=before[k],after[k];delta=b-a if a is not None and b is not None else None;relative=-delta/a if delta is not None and a!=0 else None;r={**key,'metric':k}
      for n,v in [('before',a),('after',b),('change',delta),('relative_decrease',relative)]:addfrac(r,n,v)
      r['relative_status']='defined' if relative is not None else ('undefined_zero_before' if a==0 else 'undefined_input');paired.append(r)
 assert len(trans)==90 and len(groups)==180
 table('summary.csv',summaries);table('mean_vs_max.csv',aggregation);table('paired_changes.csv',paired);table('transition_checks.csv',trans)
 pairsummary=[]
 for pop in ['record','client']:
  for ds in ['adult','bank','credit']:
   for a,b in [(0,1),(1,2),(0,2)]:
    for k in metrics:
     pp=[r for r in paired if (r['population'],r['dataset'],r['T_from'],r['T_to'],r['metric'])==(pop,ds,a,b,k)];r=dict(population=pop,dataset=ds,T_from=a,T_to=b,metric=k,seeds=5)
     for field in ['change','relative_decrease']:
      xs=[F(p[field+'_exact']) for p in pp if p[field+'_exact']!=''];r[field+'_defined_n']=len(xs)
      for label,val in [('mean',sum(xs,F(0))/len(xs) if xs else None),('min',min(xs) if xs else None),('max',max(xs) if xs else None)]:addfrac(r,field+'_'+label,val)
      r[field+'_sample_sd']=math.sqrt(float(sum(((x-sum(xs,F(0))/len(xs))**2 for x in xs),F(0))/(len(xs)-1))) if len(xs)>1 else ''
     r['decreases']=sum(F(p['change_exact'])<0 for p in pp if p['change_exact']!='');r['increases']=sum(F(p['change_exact'])>0 for p in pp if p['change_exact']!='');r['ties']=sum(F(p['change_exact'])==0 for p in pp if p['change_exact']!='');pairsummary.append(r)
 table('paired_summary.csv',pairsummary)
 events=[t for t in trans if t['any_group_increase_while_Phi_decreases']]
 # Purposeful exact fixtures for known aggregation hazards.
 assert (max(F(10),F(0))+max(F(0),F(10)))/2==10 and max(F(5),F(5))==5
 assert (F(1)*2+F(9)*4)/10==F(19,5) and F(2)+F(4)==6 and max(F(2),F(4))==4
 fixtureq={'exact':{k:{'numerator':v,'denominator':1} for k,v in dict(Phi_A=0,Phi_B=0,Phi=0,G=0).items()},'values':dict(Phi_A=0.,Phi_B=0.,Phi=0.,G=0.)}
 assert derive(fixtureq,[1,9])['max_min_group_ratio'] is None
 fixtures=['mean_of_maxima_distinct_from_max_of_means','unequal_count_weighting','zero_denominator_undefined']
 bad=json.loads(json.dumps(fixtureq));bad['exact']['Phi']['numerator']=1
 try:derive(bad,[1,9])
 except AssertionError:fixtures.append('incorrect_Phi_rejected')
 else:raise AssertionError('bad Phi accepted')
 receipt=dict(status='PASS',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),analysis_sha256=sha(Path(__file__)),protocol_sha256=pf['protocol_sha256'],input_manifest_sha256=pf['input_manifest_sha256'],frozen_files_hash_size_mtime_verified=len(frozen['files']),source_copy_checks=source_checks,unique_quality_rows=len(rows),group_rows=len(groups),scientific_seed_cases=30,seeds_per_population_dataset=5,record_gate_quality_model_checks=180,client_quality_checks=45,client_T0_core_links=15,prefix_checks=prefix_checks,paired_transitions=len(trans),all_transitions_Phi_strictly_decreases=all(t['Phi_decreases'] for t in trans),group_increase_events=events,distinct_cases_with_event=len(set((t['population'],t['dataset'],t['seed']) for t in events)),undefined_observed_group_ratios=sum(r['ratio_status']!='defined' for r in rows),mean_vs_max_nonzero_rows=sum(r['difference']!=0 for r in aggregation),fixtures=fixtures,new_training_runs=0,new_timing_observations=0,exclusions=[],limitations=['Exact scoring fractions are verified and recombined, not independently rescored from raw coordinates.','A group counts come from saved positive-T N witnesses; input pickle contents are hash-bound but not unpickled.','B group counts are cross-bound among frozen grid, saved core state and quality witnesses; original raw provenance is not recreated.','Existing source review and past arithmetic gates remain historical; this analysis does not re-prove numerical kernels.'])
 dump(W/'VERIFICATION.json',receipt)
 print(json.dumps({k:v for k,v in receipt.items() if k not in ['limitations','fixtures']},indent=2))
if __name__=='__main__':
 try:main()
 except BaseException as e:
  with (W/'FAILURES.jsonl').open('a') as f:f.write(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),error=repr(e),traceback=traceback.format_exc()))+'\n')
  raise
