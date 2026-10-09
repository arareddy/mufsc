"""Verify full saved outputs and produce unique-setting and repetition tables."""
from common import *
from fractions import Fraction
import csv,statistics,math,argparse
from datetime import datetime,timezone
OLD=Path('study://Client_Deletion')
METHODS=('fresh','direct','basic','runnerup')

def save_csv(path,rows):
 fields=list(dict.fromkeys(k for r in rows for k in r))
 with Path(path).open('w',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)
def avg(x):return statistics.mean(x)
def stdev(x):return statistics.stdev(x) if len(x)>1 else 0

def main(run_id):
 run=ROOT/'runs'/run_id;out=ROOT/'tables';out.mkdir(exist_ok=True)
 manifest=json.loads((run/'run_manifest.json').read_text());specs=json.loads((ROOT/'FROZEN_GRID.json').read_text())['cases']
 raw=[];cases=[];paired=[];repeat_pairs=[];workrows=[];rounds=[];setups=[];verification=[];missing=[]
 for s in specs:
  d=run/s['case_id']
  if not (d/'complete.json').exists():missing.append(s['case_id']);continue
  receipt=json.loads((d/'complete.json').read_text());assert receipt['status']=='PASS' and receipt['source_bindings']==manifest['source_bindings']
  assert sha256(d/'observations.jsonl')==receipt['observations_sha256']
  obs=[json.loads(line) for line in (d/'observations.jsonl').read_text().splitlines()];assert len(obs)==16 and len({(r['repetition'],r['method']) for r in obs})==16
  witness=None
  for r in obs:
   p=d/f"rep{r['repetition']}_{r['method']}_model.json";assert sha256(p)==r['output_sha256'] and p.stat().st_size==r['output_bytes']
   w=json.loads(p.read_text())
   if witness is None:witness=w
   assert w==witness and object_hash(w)==receipt['full_witness_sha256']
   assert len(w['trajectory'])==s['T']+1 and len(w['per_round_stats'])==s['T']
   assert math.isclose(sum(r['components']['additive'].values()),r['algorithm_seconds'],abs_tol=1e-10)
   assert math.isclose(r['algorithm_seconds']+r['request_preparation_seconds']+r['output_seconds'],r['request_e2e_seconds'],abs_tol=1e-10)
   assert r['work']==receipt['unique_work_counters'][r['method']]
   flat={k:v for k,v in r.items() if k not in ('components','timing_primitives','work','order')};flat['order']='/'.join(r['order'])
   for group,fields in r['components'].items():flat.update({f'{group}_{k}_seconds':v for k,v in fields.items()})
   flat.update({f'work_{k}':v for k,v in r['work'].items() if k!='rounds'});raw.append(flat)
  ref=json.loads((ROOT/'QUALITY_REFERENCE_MANIFEST.json').read_text())['cases'][s['parent_case_id']]
  assert sha256(Path(ref['path']))==ref['sha256']
  historical=next(q for q in json.loads(Path(ref['path']).read_text()) if q['T']==s['T'])
  assert historical['model_witness']==witness
  method_means={}
  for method in METHODS:
   selected=[r for r in obs if r['method']==method];assert sorted(r['position'] for r in selected)==[0,1,2,3]
   row={k:s[k] for k in ('case_id','parent_case_id','dataset','seed','T','n','removed_n','deleted_client')};row['method']=method
   for field in ('algorithm_seconds','request_e2e_seconds','request_preparation_seconds','output_seconds'):
    v=[r[field] for r in selected];row['mean_'+field]=avg(v);row['sd_'+field]=stdev(v);row['min_'+field]=min(v);row['max_'+field]=max(v);row['cv_'+field]=stdev(v)/avg(v)
   for group in ('additive','overlapping_diagnostics','derived_nonadditive'):
    for k in selected[0]['components'][group]:row['mean_'+group+'_'+k+'_seconds']=avg([r['components'][group][k] for r in selected])
   cases.append(row);method_means[method]=row
   work=receipt['unique_work_counters'][method]
   workrows.append({k:s[k] for k in ('case_id','dataset','seed','T')}|{'method':method}|{k:v for k,v in work.items() if k!='rounds'})
   for rnd in work['rounds']:rounds.append({k:s[k] for k in ('case_id','dataset','seed','T')}|{'method':method}|rnd)
  for method in METHODS[1:]:
   paired.append({k:s[k] for k in ('case_id','dataset','seed','T')}|{'method':method,'algorithm_ratio':method_means['fresh']['mean_algorithm_seconds']/method_means[method]['mean_algorithm_seconds'],'request_ratio':method_means['fresh']['mean_request_e2e_seconds']/method_means[method]['mean_request_e2e_seconds']})
   for rep in range(4):
    fresh=next(r for r in obs if r['method']=='fresh' and r['repetition']==rep);replay=next(r for r in obs if r['method']==method and r['repetition']==rep)
    repeat_pairs.append({k:s[k] for k in ('case_id','dataset','seed','T')}|{'method':method,'repetition':rep,'algorithm_ratio':fresh['algorithm_seconds']/replay['algorithm_seconds'],'request_ratio':fresh['request_e2e_seconds']/replay['request_e2e_seconds'],'scope':'timing repetition, not independent trial'})
  setup=json.loads((d/'preparation.json').read_text());row={k:s[k] for k in ('case_id','dataset','seed','T')}
  row.update({k:v for k,v in setup.items() if k.endswith('_seconds') or k=='checkpoint_pickle_bytes'})
  row['output_verification_seconds']=receipt['verification_seconds'];row['max_rss_bytes']=receipt['max_rss_bytes']
  row.update({f'checkpoint_{k}_seconds':v for k,v in setup['checkpoint_components']['additive'].items()});setups.append(row)
  verification.append({'case_id':s['case_id'],'model_files':16,'distinct_replay_comparisons':3,'repeated_replay_comparisons':12,'historical_complete_witness_equal':True,'timer_sums_and_balanced_positions_pass':True,'repeated_counters_equal':True})
 aggregate=[];workagg=[]
 for T in (1,2):
  for dataset in ('all','adult','bank','credit'):
   for method in METHODS[1:]:
    selected=[r for r in paired if r['T']==T and (dataset=='all' or r['dataset']==dataset) and r['method']==method]
    if not selected:continue
    for scope,field in (('algorithm','algorithm_seconds'),('request','request_e2e_seconds')):
     v=[r[scope+'_ratio'] for r in selected]
     fsum=sum(r[field] for r in raw if r['T']==T and r['method']=='fresh' and (dataset=='all' or r['dataset']==dataset));msum=sum(r[field] for r in raw if r['T']==T and r['method']==method and (dataset=='all' or r['dataset']==dataset))
     aggregate.append({'T':T,'dataset':dataset,'method':method,'scope':scope,'distinct_settings':len(v),'observations_per_method':4*len(v),'fresh_total_seconds':fsum,'method_total_seconds':msum,'ratio_of_total_times':fsum/msum,'paired_mean':avg(v),'paired_median':statistics.median(v),'paired_sd':stdev(v),'paired_min':min(v),'paired_max':max(v),'wins':sum(x>1 for x in v),'losses':sum(x<1 for x in v),'ties':sum(x==1 for x in v)})
   for method in METHODS:
    w=[r for r in workrows if r['T']==T and (dataset=='all' or r['dataset']==dataset) and r['method']==method]
    if not w:continue
    sums={k:sum(r[k] for r in w) for k in ('N','A','P','S','J','modeled_point_assignments')}
    workagg.append({'T':T,'dataset':dataset,'method':method,'distinct_settings':len(w),**sums,'pooled_P_over_A':sums['P']/sums['A'] if sums['A'] else None,'pooled_S_over_N':sums['S']/sums['N'],'mean_case_P_over_A':avg([r['pass_fraction'] for r in w if r['pass_fraction'] is not None]) if any(r['pass_fraction'] is not None for r in w) else None,'mean_case_S_over_N':avg([r['useful_fraction'] for r in w]),'threshold_fallback_settings':sum(r['threshold_fallback'] for r in w)})
 quality=[];refs=json.loads((ROOT/'QUALITY_REFERENCE_MANIFEST.json').read_text())
 oldspec={s['case_id']:s for s in json.loads((OLD/'FROZEN_GRID.json').read_text())['cases']}
 for cid,ref in refs['cases'].items():
  assert sha256(Path(ref['path']))==ref['sha256'];s=oldspec[cid]
  for row in json.loads(Path(ref['path']).read_text()):
   exact={k:Fraction(v['numerator'],v['denominator']) for k,v in row['quality']['exact'].items()}
   assert exact['Phi']==max(exact['Phi_A'],exact['Phi_B']) and exact['G']==exact['Phi_A']+exact['Phi_B']
   ng=row['quality']['retained_group_counts'];assert exact['pooled_SSE']==ng[0]*exact['Phi_A']+ng[1]*exact['Phi_B']
   q={'parent_case_id':cid,'dataset':s['dataset'],'seed':s['seed'],'T':row['T'],'n0':ng[0],'n1':ng[1],**{k:float(v) for k,v in exact.items()},'historical_quality_evaluation_seconds':row['quality']['quality_evaluation_seconds'],'new_quality_evaluation_seconds':0.0,'reference_path':ref['path'],'reference_file_sha256':ref['sha256'],'complete_witness_sha256':object_hash(row['model_witness']),'final_centers_sha256':object_hash(row['model_witness']['final_centers']),'matched_new_fresh_witness_verified':row['T']>0 and any(v['case_id']==cid+f"_T{row['T']}" for v in verification),'source_run':'client-c0-20260926-v1'}
   for k,v in exact.items():q[k+'_numerator']=v.numerator;q[k+'_denominator']=v.denominator
   quality.append(q)
 history=[]
 for r in csv.DictReader((OLD/'tables/case_method_timings.csv').open()):history.append({**r,'T':0,'source_run':'client-c0-20260926-v1','historical':True,'method_scope':'compact C0-only candidate' if r['method']=='fast' else 'canonical T0','repetitions':3})
 for name,rows in [('raw_timings.csv',raw),('case_method_timings.csv',cases),('paired_ratios.csv',paired),('repetition_ratios.csv',repeat_pairs),('aggregate_timings.csv',aggregate),('work_counters.csv',workrows),('round_work_counters.csv',rounds),('aggregate_work.csv',workagg),('setup_costs.csv',setups),('quality_exact.csv',quality),('historical_c0_context.csv',history)]:save_csv(out/name,rows)
 write_json(ROOT/'RESULTS_VERIFICATION.json',{'status':'PASS_COMPLETE' if len(verification)==30 else 'PARTIAL','created_utc':datetime.now(timezone.utc).isoformat(),'run_id':run_id,'complete_settings':len(verification),'missing_settings':missing,'distinct_method_outputs':len(verification)*4,'distinct_replay_comparisons':len(verification)*3,'observations':len(raw),'repeated_replay_comparisons':len(repeat_pairs),'historical_quality_rows':len(quality),'quality_rescored':False,'settings':verification,'scope':'Saved exact witnesses, all model file hashes, paired timer sums and counters verified using canonical evidence; no independent numerical oracle or review approval implied.'})
 print(json.dumps({'settings':len(verification),'missing':missing,'observations':len(raw),'distinct_replay_comparisons':len(paired),'all_dataset_aggregates':[r for r in aggregate if r['dataset']=='all']},indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--run-id',default='client-refinement-20260926-v1');a=p.parse_args();main(a.run_id)
