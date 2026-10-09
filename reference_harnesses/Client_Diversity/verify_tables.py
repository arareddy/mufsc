"""Independent table audit; standard library, no learner/report imports."""
from pathlib import Path
from fractions import Fraction
from collections import defaultdict,Counter
import csv,json,math,hashlib,statistics
R=Path(__file__).resolve().parent
load=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
raw=[json.loads(line) for p in (R/'runs/diversity-v1').glob('*/*/observations.jsonl') for line in p.read_text().splitlines()]
assert len(raw)==270
by_case=defaultdict(list)
for r in raw:by_case[r['case_id']].append(r)
assert len(by_case)==30
checked=0
def eq(actual,expected):
 global checked
 assert math.isclose(float(actual),float(expected),rel_tol=1e-12,abs_tol=1e-10),(actual,expected)
 checked+=1
for r in csv.DictReader((R/'tables/summary.csv').open()):
 dim,key=r['dimension'],r['group'];chosen=[]
 for cid,obs in by_case.items():
  o=obs[0]
  include=dim=='all' or dim=='dataset' and key==o['dataset'] or dim=='client' and key==f"{o['dataset']}/c{o['client']}" or dim=='role' and key.split('/')[0]==o['dataset'] and key.split('/')[1] in o['roles'] or dim=='seed' and key==str(o['seed']) or dim=='dataset_seed' and key==f"{o['dataset']}/{o['seed']}"
  if include:chosen.append(obs)
 eq(r['unique_cases'],len(chosen));eq(r['distinct_dataset_clients'],len({(x[0]['dataset'],x[0]['client']) for x in chosen}))
 means={m:[math.fsum(o['request_e2e_seconds'] for o in obs if o['method']==m)/3 for obs in chosen] for m in ('fresh','direct','fast')}
 for method in means:
  for boundary in ('request_e2e_seconds','algorithm_seconds'):
   vals=[o[boundary] for obs in chosen for o in obs if o['method']==method];eq(r[f'{method}_{boundary}_total_ms'],math.fsum(vals)*1000);eq(r[f'{method}_{boundary}_mean_ms'],math.fsum(vals)*1000/len(vals))
 for a,b in (('fresh','fast'),('fresh','direct'),('direct','fast')):
  vals=[x/y for x,y in zip(means[a],means[b])];p=a+'_'+b
  exp={'total_ratio':math.fsum(means[a])/math.fsum(means[b]),'paired_mean':statistics.mean(vals),'paired_median':statistics.median(vals),'paired_sd':statistics.stdev(vals) if len(vals)>1 else 0,'paired_min':min(vals),'paired_max':max(vals),'wins':sum(x>1 for x in vals),'losses':sum(x<1 for x in vals),'ties':sum(x==1 for x in vals),'over10':sum(x>10 for x in vals)}
  for k,v in exp.items():eq(r[p+'_'+k],v)
for r in csv.DictReader((R/'tables/components.csv').open()):
 vals=[]
 for o in raw:
  if o['dataset']==r['dataset'] and o['method']==r['method']:
   k=r['component'];v=o['components'].get(k.removeprefix('component_')) if k.startswith('component_') else o[k]
   if v is not None:vals.append(v*1000)
 for k,v in {'observations':len(vals),'mean_ms':statistics.mean(vals),'sd_ms':statistics.stdev(vals),'min_ms':min(vals),'max_ms':max(vals)}.items():eq(r[k],v)
for r in csv.DictReader((R/'tables/cases.csv').open()):
 obs=by_case[r['case_id']]
 for method in ('fresh','direct','fast'):
  rows=[o for o in obs if o['method']==method];v=[o['request_e2e_seconds']*1000 for o in rows]
  for k in ('request_preparation_seconds','algorithm_seconds','output_seconds','request_e2e_seconds'):eq(r[f'{method}_{k}_mean_ms'],statistics.mean(o[k]*1000 for o in rows))
  for k,e in {'sd_ms':statistics.stdev(v),'cv':statistics.stdev(v)/statistics.mean(v),'min_ms':min(v),'max_ms':max(v)}.items():eq(r[f'{method}_request_{k}'],e)
 for a,b in (('fresh','fast'),('fresh','direct'),('direct','fast')):eq(r[f'{a}_{b}_ratio'],math.fsum(o['request_e2e_seconds'] for o in obs if o['method']==a)/math.fsum(o['request_e2e_seconds'] for o in obs if o['method']==b))
 gate=load(next((R/'runs/diversity-v1').glob('*/'+r['case_id']+'/gate.json')));assert gate['retained_anchor_slots']==(380 if r['dataset']=='bank' else 1980)
selections=load(R/'SELECTION.json')
for ds,s in selections.items():
 valid=[c for c in s['clients'] if min(c['remaining_group_counts'])>0];sizes=sorted(c['size'] for c in valid);n=len(sizes);median2=sizes[(n-1)//2]+sizes[n//2];frac=lambda c:Fraction(c['group_counts'][0],c['size'])
 rules={'smallest':lambda c:(c['size'],c['client']),'median_size':lambda c:(abs(2*c['size']-median2),c['client']),'largest':lambda c:(-c['size'],c['client']),'min_group0_fraction':lambda c:(frac(c),c['client']),'max_group0_fraction':lambda c:(-frac(c),c['client']),'min_surviving_smaller_group':lambda c:(min(c['remaining_group_counts']),c['client'])}
 assert {role:min(valid,key=key)['client'] for role,key in rules.items()}==s['roles']
 assert len(set(s['roles'].values()))==2 and len(valid)==len(s['clients'])
 assert sorted(Counter(c['size'] for c in valid).values())==[1,len(valid)-1]
for name,h in load(R/'runs/diversity-v1/manifest.json')['bindings'].items():assert sha(R/name)==h
(R/'TABLE_VERIFICATION.json').write_text(json.dumps({'status':'PASS','independent_summary_case_component_numeric_fields':checked,'selection_recomputed_from_all_original_metadata':True,'source_protocol_grid_bindings_unchanged':True,'raw_observations':270,'independent_import_scope':'Python standard library only; raw JSON read directly, no production or reporting code imported'},indent=2)+'\n')
print('PASS:',checked,'independently recomputed numeric fields; selection and frozen bindings verified.')
