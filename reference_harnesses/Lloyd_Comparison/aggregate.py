from common import *
from fractions import Fraction as F
import csv,math,datetime
from collections import defaultdict
OUT=W/'tables';OUT.mkdir(exist_ok=True)
def csvout(n,rr):
 if not rr:return
 with (OUT/n).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rr[0]));w.writeheader();w.writerows(rr)
def field(r,k,v):r[k+'_exact']=str(v) if v is not None else '';r[k]=float(v) if v is not None else ''
def stats(vals):
 valid=[v for v in vals if v is not None];n=len(valid);mean=sum(valid,F(0))/n if n else None;var=sum(((v-mean)**2 for v in valid),F(0))/(n-1) if n>1 else None;r=dict(n=n,undefined=len(vals)-n)
 for k,v in [('mean',mean),('sample_variance',var),('min',min(valid) if n else None),('max',max(valid) if n else None)]:field(r,k,v)
 r['sample_sd']=math.sqrt(float(var)) if var is not None else '';return r
verify_sources();assert load(W/'PROGRESS.json')['status']=='COMPLETE'
assert load(W/'PROTOCOL_FREEZE.json')['bindings']==bindings()
for r in load(W/'INPUT_MANIFEST.json')['files']:
 p=Path(r['path']);assert sha(p)==r['sha256'] and p.stat().st_mtime_ns==r['mtime_ns'] and p.stat().st_size==r['bytes']
rows=[];raw={};receipts=[];ambiguous=0;metricnames=['Phi_A','Phi_B','Phi','G','population_average','pooled_SSE']
for c in load(W/'FROZEN_GRID.json')['cases']:
 p=W/'runs/matched-start-v1'/c['case_id'];r=load(p/'complete.json');assert r['status']=='PASS' and r['source_bindings']==bindings() and sha(p/'outputs.json')==r['output_sha256'];x=load(p/'outputs.json');receipts.append(r)
 assert x['counts']==c['counts'] and x['retained_identity_sha256']==c['retained_identity_sha256']
 assert x['methods']['fair']['witness']['trajectory'][0]==x['methods']['lloyd']['witness']['trajectory'][0]
 assert x['methods']['fair']['witness']['per_round_stats'][0]==x['methods']['lloyd']['witness']['per_round_stats'][0]
 for method,result in x['methods'].items():
  assert len(result['witness']['trajectory'])==3 and len(result['witness']['per_round_stats'])==2 and len(result['quality'])==3
  for T,q in enumerate(result['quality']):
   v={k:F(s) for k,s in q['exact'].items()};assert v['Phi']==max(v['Phi_A'],v['Phi_B']) and v['G']==v['Phi_A']+v['Phi_B']
   assert v['pooled_SSE']==sum(n*v[k] for n,k in zip(c['counts'],['Phi_A','Phi_B'])) and v['population_average']==v['pooled_SSE']/sum(c['counts'])
   key=c['population'],c['dataset'],c['seed'],method,T;assert key not in raw;raw[key]=v
   rr=dict(case_id=c['case_id'],population=c['population'],dataset=c['dataset'],seed=c['seed'],method=method,T=T,n0=c['counts'][0],n1=c['counts'][1],retained_identity_sha256=c['retained_identity_sha256'],output_sha256=r['output_sha256'],ambiguous_rows=q['verification']['ambiguous_rows'])
   for k in metricnames:field(rr,k,v[k])
   rows.append(rr)
   if method=='fair' or T>0:ambiguous+=q['verification']['ambiguous_rows']
assert len(rows)==180
csvout('quality.csv',rows)
summary=[];paired=[];pairedsummary=[];changes=[];changessummary=[];meanmax=[]
for pop in ['record','client']:
 for ds in ['adult','bank','credit']:
  for method in ['fair','lloyd']:
   for T in range(3):
    for k in metricnames:summary.append(dict(population=pop,dataset=ds,method=method,T=T,metric=k,**stats([raw[pop,ds,seed,method,T][k] for seed in range(10000,10005)])))
    vals=[raw[pop,ds,seed,method,T] for seed in range(10000,10005)];mm=sum(v['Phi'] for v in vals)/5;mg=max(sum(v[k] for v in vals)/5 for k in ['Phi_A','Phi_B']);r=dict(population=pop,dataset=ds,method=method,T=T)
    for k,v in [('mean_seed_max',mm),('max_group_mean',mg),('difference',mm-mg)]:field(r,k,v)
    meanmax.append(r)
   for seed in range(10000,10005):
    for a,b in [(0,1),(1,2),(0,2)]:
     for k in metricnames:
      va,vb=raw[pop,ds,seed,method,a][k],raw[pop,ds,seed,method,b][k];r=dict(population=pop,dataset=ds,seed=seed,method=method,T_from=a,T_to=b,metric=k)
      for name,v in [('before',va),('after',vb),('change',vb-va),('relative_change',(vb-va)/va if va else None)]:field(r,name,v)
      r['relative_status']='defined' if va else 'undefined_zero_before';changes.append(r)
  for T in range(3):
   for k in metricnames:
    these=[]
    for seed in range(10000,10005):
     a,b=raw[pop,ds,seed,'fair',T][k],raw[pop,ds,seed,'lloyd',T][k];r=dict(population=pop,dataset=ds,seed=seed,T=T,metric=k)
     for name,v in [('fair',a),('lloyd',b),('fair_minus_lloyd',a-b),('relative_difference',(a-b)/b if b else None)]:field(r,name,v)
     r['relative_status']='defined' if b else 'undefined_zero_lloyd';paired.append(r);these.append(r)
    r=dict(population=pop,dataset=ds,T=T,metric=k,seeds=5,fair_lower=sum(F(x['fair_minus_lloyd_exact'])<0 for x in these),fair_higher=sum(F(x['fair_minus_lloyd_exact'])>0 for x in these),ties=sum(F(x['fair_minus_lloyd_exact'])==0 for x in these))
    for fld in ['fair_minus_lloyd','relative_difference']:
     for name,v in stats([F(x[fld+'_exact']) if x[fld+'_exact'] else None for x in these]).items():r[fld+'_'+name]=v
    pairedsummary.append(r)
for pop in ['record','client']:
 for ds in ['adult','bank','credit']:
  for method in ['fair','lloyd']:
   for a,b in [(0,1),(1,2),(0,2)]:
    for k in metricnames:
     rr=[r for r in changes if (r['population'],r['dataset'],r['method'],r['T_from'],r['T_to'],r['metric'])==(pop,ds,method,a,b,k)];vv=[F(r['change_exact']) for r in rr];r=dict(population=pop,dataset=ds,method=method,T_from=a,T_to=b,metric=k,decreases=sum(v<0 for v in vv),increases=sum(v>0 for v in vv),ties=sum(v==0 for v in vv))
     for fld in ['change','relative_change']:
      for name,v in stats([F(x[fld+'_exact']) if x[fld+'_exact'] else None for x in rr]).items():r[fld+'_'+name]=v
     changessummary.append(r)
csvout('summary.csv',summary);csvout('paired_methods.csv',paired);csvout('paired_methods_summary.csv',pairedsummary);csvout('within_method_changes.csv',changes);csvout('within_method_summary.csv',changessummary);csvout('mean_vs_max.csv',meanmax)
# All positive costs relative to the alternative or prior budget remain explicit.
csvout('fair_higher_than_lloyd.csv',[r for r in paired if F(r['fair_minus_lloyd_exact'])>0]);csvout('step_increases.csv',[r for r in changes if F(r['change_exact'])>0])
comparison={}
for T in [1,2]:
 comparison[str(T)]={}
 for k in metricnames:
  pp=[r for r in paired if r['T']==T and r['metric']==k]
  comparison[str(T)][k]=dict(fair_lower=sum(F(r['fair_minus_lloyd_exact'])<0 for r in pp),fair_higher=sum(F(r['fair_minus_lloyd_exact'])>0 for r in pp),ties=sum(F(r['fair_minus_lloyd_exact'])==0 for r in pp))
receipt=dict(status='PASS',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),cases=len(receipts),method_budget_rows=len(rows),fresh_fair_witnesses_reproduced=sum(r['fair_saved_witnesses_reproduced'] for r in receipts),saved_fair_objectives_recomputed=sum(r['fair_saved_objectives_recomputed'] for r in receipts),independent_objective_checks=sum(r['independent_canonical_score_crosschecks'] for r in receipts),independent_full_label_checks=sum(r['independent_canonical_label_crosschecks'] for r in receipts),total_ambiguous_point_evaluations=ambiguous,inputs_unchanged=len(load(W/'INPUT_MANIFEST.json')['files']),source_files_unchanged=len(load(W/'SOURCE_MANIFEST.json')['files']),fixture_status=load(W/'fixtures/results.json')['status'],comparisons=comparison,step_increase_counts={m:{k:sum(r['method']==m and r['metric']==k and r['T_from']+1==r['T_to'] and F(r['change_exact'])>0 for r in changes) for k in metricnames} for m in ['fair','lloyd']},paired_metric_rows=len(paired),within_method_metric_rows=len(changes),exclusions=[],unresolved_correctness=[],scope='New full-population recomputation and independently written scoring; canonical trajectory kernels and Python/NumPy runtime shared as documented',reporting_script_sha256=sha(Path(__file__)))
dump(W/'VERIFICATION.json',receipt);print(json.dumps(receipt,indent=2))
