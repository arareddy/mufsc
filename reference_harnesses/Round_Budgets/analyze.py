#!/usr/bin/env python3
"""Read-only verification of observations and descriptive reporting. No training imports."""
import os
for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):os.environ[k]='1'
import csv,json,hashlib,struct,statistics as st,sys,collections,math
from pathlib import Path
from fractions import Fraction
W=Path(__file__).resolve().parent;R=W/'runs'/(W/'RUN_ID').read_text().strip();OUT=W/'tables'
methods=['fresh','none','basic','runnerup'];names=dict(fresh='Fresh',none='Direct',basic='Basic',runnerup='Runner-up')
def load(p):return json.loads(p.read_text())
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def csvout(name,rows):
 if not rows:return
 with (OUT/name).open('w',newline='') as f:
  c=csv.DictWriter(f,fieldnames=list(rows[0]));c.writeheader();c.writerows(rows)
def exact_quality(q):
 v={name:Fraction(q['exact'][name]['numerator'],q['exact'][name]['denominator']) for name in ['Phi_A','Phi_B','Phi','G']}
 assert v['Phi']==max(v['Phi_A'],v['Phi_B']), 'Phi is not the exact max-group cost'
 assert v['G']==v['Phi_A']+v['Phi_B'], 'G is not the exact sum of group-normalized costs'
 assert all(q[name]==float(value) for name,value in v.items()), 'Saved quality float disagrees with exact fraction'
 return v

def validate_array(a):
 b=bytes.fromhex(a['bytes_hex']);n=math.prod(a['shape']);assert a['dtype']=='<f8' and len(b)==8*n and len(a['values_hex'])==n
 assert b==struct.pack('<'+'d'*n,*map(float.fromhex,a['values_hex']))
 assert all(math.isfinite(v) for v in struct.unpack('<'+'d'*n,b))
def valid_witness(w,T,k,d,n):
 assert len(w['trajectory'])==T+1 and len(w['per_round_stats'])==T
 assert w['final_centers']==w['trajectory'][-1]
 for a in w['trajectory']+[w['final_centers']]:validate_array(a);assert a['shape']==[k,d]
 def ints(v):return all(ints(x) for x in v) if isinstance(v,list) else type(v) is int
 for s in w['per_round_stats']:
  assert ints(s) if isinstance(s,list) else all(ints(s[x]) for x in ['N','S','SS'])
  assert len(s['N'])==len(s['S'])==len(s['SS'])==2
  assert all(len(s[x][g])==k for x in ['N','S','SS'] for g in range(2))
  assert all(len(s['S'][g][j])==d for g in range(2) for j in range(k))
  assert sum(sum(x) for x in s['N'])==n
  assert all(x>=0 for z in s['N'] for x in z) and all(x>=0 for z in s['SS'] for x in z)
inputs=load(W/'input_manifest.json');raw=[];keys=[];setups=[];correct=[];missing=[];seen=[];identity=[];quality_checks=[]
for inp in inputs:
 req=load(Path(inp['request']));assert sha(Path(inp['input']))==inp['input_sha256'];assert sha(Path(inp['request']))==inp['request_sha256']
 meta=inp['meta'];ids=meta['source_record_ids'];clientids=meta['source_client_ids'];records=[]
 all_ids=[i for arr in ids.values() for i in arr];assert len(all_ids)==len(set(all_ids))==inp['n']
 for c in sorted(req['removed'],key=int):
  for i in req['removed'][c]:
   v=ids[c][i];records.append(dict(client_id=int(c),local_row=i,processed_full_row=v,source_client_id=clientids[c],stable_record_id=f"{meta['source_sha256']}:full-row:{v}"))
 assert records==req['removed_source_records']
 h=hashlib.sha256(json.dumps(records,sort_keys=True,separators=(',',':')).encode()).hexdigest();assert h==req['removal_source_identity_hash']
 identity.append(dict(dataset=inp['dataset'],seed=inp['settings']['seed'],records=inp['n'],removed=inp['removed'],stable_identity_hash=h,unique_source_rows=True))
 for T in range(3):
  d=R/f"{inp['dataset']}_s{inp['settings']['seed']}_T{T}"
  if not (d/'complete.json').exists():missing.extend([(inp['dataset'],inp['settings']['seed'],T,m) for m in methods]);continue
  receipt=load(d/'complete.json');assert receipt['status']=='PASS'
  for file,h in receipt['files'].items():assert sha(d/file)==h,f'hash mismatch {d/file}'
  cg=load(d/'correctness.json');assert cg['status']=='PASS'
  cw=load(d/'checkpoint.witness.json');oldcp=load(Path(inp['input']).parent/'checkpoint.json')['witness'];assert cw['trajectory']==oldcp['trajectory'][:T+1] and cw['per_round_stats']==oldcp['per_round_stats'][:T] and cw['final_centers']==oldcp['trajectory'][T]
  cp=load(d/'checkpoint.json');setups.append(dict(dataset=inp['dataset'],seed=inp['settings']['seed'],T=T,checkpoint_algorithm_seconds=cp['algorithm_seconds'],setup_seconds=cp['request_seconds'],input_loading_seconds=cp['input_loading_seconds'],checkpoint_output_seconds=cp['checkpoint_output_seconds'],checkpoint_bytes=cp['checkpoint_bytes'],startup_seconds=cp['startup_seconds'],cache_construction_seconds=cp['timing_primitives']['cache_construction']))
  fresh=load(d/'gate_fresh.witness.json');n=inp['n']-inp['removed'];valid_witness(fresh,T,10,inp['d'],n)
  for m in methods:
   gm=load(d/f'gate_{m}.json');gw=load(d/f'gate_{m}.witness.json');assert gw==fresh and gm['quality']['exact']==cg['quality']['exact']
   quality_exact=exact_quality(gm['quality'])
   quality_checks.append(dict(dataset=inp['dataset'],seed=inp['settings']['seed'],T=T,method=m,Phi_numerator=quality_exact['Phi'].numerator,Phi_denominator=quality_exact['Phi'].denominator,Phi_A_numerator=quality_exact['Phi_A'].numerator,Phi_A_denominator=quality_exact['Phi_A'].denominator,Phi_B_numerator=quality_exact['Phi_B'].numerator,Phi_B_denominator=quality_exact['Phi_B'].denominator,sum_group_normalized_costs_numerator=quality_exact['G'].numerator,sum_group_normalized_costs_denominator=quality_exact['G'].denominator,Phi_is_exact_max=True,G_is_exact_sum=True))
   valid_witness(gw,T,10,inp['d'],n)
   old=load(Path(inp['input']).parent/(m+'.json'))['witness'];assert gw['trajectory']==old['trajectory'][:T+1] and gw['per_round_stats']==old['per_round_stats'][:T]
   correct.append(dict(dataset=inp['dataset'],seed=inp['settings']['seed'],T=T,method=m,full_witness_equal=True,quality_equal=True,accepted_prefix_equal=True,trajectory_centers=T+1,statistic_rounds=T))
   obs=[]
   for rep in range(4):
    x=load(d/f'r{rep}_{m}.json');v=load(d/f'r{rep}_{m}.verification.json');wi=load(d/f'r{rep}_{m}.witness.json');assert v['status']=='PASS' and wi==gw
    assert x['witness_sha256']==sha(d/f'r{rep}_{m}.witness.json')
    assert x['cache_valid']==False
    p=x['timing_primitives'];t=x['timing_totals'];di=x['diagnostics']
    N=n*T;A=sum(z['A'] for z in di);P=sum(z['P'] for z in di);S=sum(z['S'] for z in di);J=sum(z['J'] for z in di)
    if m!='fresh':assert sum(z['N'] for z in di)==N
    assert 0<=S<=P<=A<=N and 0<=J<=A-P
    for z in di:
     assert z['A']-z['P']==z['failing'];assert z['S']==(0 if z['abandoned_this_round'] else z['P'])
     if z['J']:assert z['J']==z['failing'] and 2*z['failing']>z['N']
    if T==0:assert N==A==P==S==J==0
    components=sum(x[k] for k in ['input_loading_seconds','retained_materialization_seconds','checkpoint_loading_seconds','gc_seconds','algorithm_seconds','witness_construction_seconds','output_serialization_seconds'])
    assert x['request_seconds']>=components-1e-8
    row=dict(dataset=inp['dataset'],seed=inp['settings']['seed'],T=T,method=m,repetition=rep,position=v['position'],algorithm_seconds=x['algorithm_seconds'],e2e_seconds=x['request_seconds'],startup_seconds=x['startup_seconds'],cold_launch_e2e_seconds=x['cold_launch_request_seconds'],input_loading_seconds=x['input_loading_seconds'],retained_materialization_seconds=x['retained_materialization_seconds'],checkpoint_loading_seconds=x['checkpoint_loading_seconds'],gc_seconds=x['gc_seconds'],witness_construction_seconds=x['witness_construction_seconds'],output_serialization_seconds=x['output_serialization_seconds'],request_other_seconds=x['request_seconds']-components,encoding_seconds=p['encoding'],internal_materialization_seconds=p['input_materialization'],phase1_client_seconds=t['phase1_client_total'],phase1_server_seconds=p['phase1_server'],phase2_certify_seconds=t['certify_total'],phase2_recompute_seconds=t['recompute_total'],phase2_server_seconds=p['phase2_server'],shift_bounds_seconds=p['shift_bounds'],algorithm_other_seconds=x['algorithm_seconds']-t['wall_total_compute']-p['encoding']-p['input_materialization']-p['cache_construction']-p['shift_bounds'],failed_assignment_seconds=p['failed_assignment'],fallback_sunk_seconds=p['fallback_sunk'],fallback_rebuild_seconds=p['fallback_rebuild'],ideal_parallel_compute_seconds=t['wall_total_parallel'],N=N,A=A,P=P,S=S,J=J,assignment_point_units=N-S+J,abandonment_round=x['abandonment_round'],Phi=float(quality_exact['Phi']),sum_group_normalized_costs=float(quality_exact['G']),Phi_A=float(quality_exact['Phi_A']),Phi_B=float(quality_exact['Phi_B']),output_bytes=x['output_bytes'],rss_bytes=x['rss_bytes'],started_unix=x['started_unix'],metadata_path=str((d/f'r{rep}_{m}.json').relative_to(W)),correctness='PASS')
    raw.append(row);obs.append(row)
   assert sorted(z['position'] for z in obs)==list(range(4))
   seen.append((inp['dataset'],inp['settings']['seed'],T,m))
   kr={k:obs[0][k] for k in ['dataset','seed','T','method','Phi','sum_group_normalized_costs','Phi_A','Phi_B','N','A','P','S','J','assignment_point_units','abandonment_round']}
   for metric in ['algorithm_seconds','e2e_seconds','cold_launch_e2e_seconds','ideal_parallel_compute_seconds']:
    a=[z[metric] for z in obs];kr[metric]=st.median(a);kr[metric+'_min']=min(a);kr[metric+'_max']=max(a);kr[metric+'_cv']=st.stdev(a)/st.mean(a)
   kr.update(repetitions=4,pass_rate=P/A if A else '',useful_coverage=S/N if N else '')
   keys.append(kr)
duplicates=[k for k,c in collections.Counter(seen).items() if c>1]
status='PASS' if len(keys)==180 and len(raw)==720 and len(correct)==180 and not missing and not duplicates else 'INCOMPLETE'
summary=dict(status=status,expected_unique_keys=180,observed_unique_keys=len(keys),expected_replay_comparisons=135,observed_replay_comparisons=sum(x['method']!='fresh' for x in correct),expected_timing_observations=720,observed_timing_observations=len(raw),gate_method_outputs=len(correct),measured_witness_comparisons=len(raw),missing=missing,duplicates=duplicates,independent_seeds_per_dataset=5,repetitions_per_key=4,identity_checks=identity,objective_definition='Phi=max(Phi_A,Phi_B); G=Phi_A+Phi_B (sum of group-normalized costs)',exact_quality_definition_checks=len(quality_checks))
write(W/'verification.json',summary)
csvout('quality_definition_checks.csv',quality_checks)
csvout('raw_observations.csv',raw);csvout('key_medians.csv',keys);csvout('checkpoint_setup.csv',setups);csvout('correctness.csv',correct)
paired=[]
for x in keys:
 if x['method']=='fresh':continue
 f=next(z for z in keys if (z['dataset'],z['seed'],z['T'],z['method'])==(x['dataset'],x['seed'],x['T'],'fresh'))
 pair={k:x[k] for k in ['dataset','seed','T','method']}
 for metric in ['algorithm_seconds','e2e_seconds','cold_launch_e2e_seconds','ideal_parallel_compute_seconds']:
  pair[metric+'_ratio']=f[metric]/x[metric];pair['fresh_'+metric]=f[metric];pair['method_'+metric]=x[metric]
 paired.append(pair)
csvout('paired_seed_ratios.csv',paired)
agg=[]
for ds in ['adult','bank','credit']:
 for T in range(3):
  for m in methods[1:]:
   pp=[x for x in paired if (x['dataset'],x['T'],x['method'])==(ds,T,m)]
   if not pp:continue
   row=dict(dataset=ds,T=T,method=m,seeds=len(pp),repetitions_per_seed=4)
   for metric in ['algorithm_seconds','e2e_seconds','cold_launch_e2e_seconds','ideal_parallel_compute_seconds']:
    ratios=[x[metric+'_ratio'] for x in pp]
    rr=[x for x in raw if x['dataset']==ds and x['T']==T]
    row.update({metric+'_mean_paired_ratio':st.mean(ratios),metric+'_ratio_total_seed_medians':sum(x['fresh_'+metric] for x in pp)/sum(x['method_'+metric] for x in pp),metric+'_ratio_total_observed':sum(x[metric] for x in rr if x['method']=='fresh')/sum(x[metric] for x in rr if x['method']==m),metric+'_seed_min':min(ratios),metric+'_seed_max':max(ratios),metric+'_wins':sum(x>1 for x in ratios),metric+'_losses':sum(x<1 for x in ratios),metric+'_ties':sum(x==1 for x in ratios)})
   agg.append(row)
csvout('aggregate_ratios.csv',agg)
quality=[]
for ds in ['adult','bank','credit']:
 for T in range(3):
  rr=[x for x in keys if x['dataset']==ds and x['T']==T and x['method']=='fresh']
  if rr:quality.append(dict(dataset=ds,T=T,seeds=len(rr),Phi_mean=st.mean(x['Phi'] for x in rr),Phi_sd=st.stdev(x['Phi'] for x in rr),Phi_min=min(x['Phi'] for x in rr),Phi_max=max(x['Phi'] for x in rr)))
csvout('quality_summary.csv',quality)
print(json.dumps({k:v for k,v in summary.items() if k!='identity_checks'},indent=2))
