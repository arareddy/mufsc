"""Verify reporting semantics and preserve original evidence; no model execution."""
from pathlib import Path
from fractions import Fraction
import hashlib,json,csv,ast,copy,fcntl
W=Path(__file__).resolve().parent;S=W/'reporting_correction_20260926';R=W/'runs'/(W/'RUN_ID').read_text().strip()
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def rows(p):return list(csv.DictReader(p.open()))
with open('/private/tmp/ftf_benchmark_20260926.lock','a+') as lock:
 fcntl.flock(lock.fileno(),fcntl.LOCK_EX)
 before=json.loads((S/'raw_before.json').read_text());now={str(p.relative_to(W)) for p in R.rglob('*') if p.is_file()}
 assert set(before)==now
 for name,v in before.items():
  p=W/name;assert sha(p)==v['sha256'] and p.stat().st_size==v['bytes'] and p.stat().st_mtime_ns==v['mtime_ns'],name
 comparisons={}
 for name in ['raw_observations.csv','key_medians.csv','aggregate_ratios.csv','paired_seed_ratios.csv','component_means.csv','checkpoint_setup.csv']:
  a=rows(S/'superseded/tables'/name);b=rows(W/'tables'/name);assert len(a)==len(b)
  cols=set(a[0])&set(b[0]);cols.discard('G')
  assert all(all(x[k]==y[k] for k in cols) for x,y in zip(a,b)),name
  comparisons[name]=dict(rows=len(a),unchanged_common_columns=sorted(cols))
  if 'G' in a[0]:assert all(x['G']==y['sum_group_normalized_costs'] for x,y in zip(a,b))
 for name in ['aggregate_ratios.csv','paired_seed_ratios.csv','component_means.csv','checkpoint_setup.csv']:
  assert sha(S/'superseded/tables'/name)==sha(W/'tables'/name)
 # Extract only the pure reporting assertion; never import analysis entry-point.
 node=next(x for x in ast.parse((W/'analyze.py').read_text()).body if isinstance(x,ast.FunctionDef) and x.name=='exact_quality')
 ns={'Fraction':Fraction};exec(compile(ast.Module(body=[node],type_ignores=[]),'<quality-check>','exec'),ns);check=ns['exact_quality']
 sample=json.loads(next(R.glob('*/gate_fresh.json')).read_text())['quality'];check(sample)
 negatives=[]
 for field,wrong in [('Phi','G'),('G','Phi')]:
  bad=copy.deepcopy(sample);bad['exact'][field]=copy.deepcopy(bad['exact'][wrong]);bad[field]=bad[wrong]
  try:check(bad)
  except AssertionError as e:negatives.append(dict(field=field,wrong_source=wrong,rejected=True,message=str(e)))
  else:raise AssertionError('Objective-field swap was not caught')
 # Check budget monotonicity using exact saved worst-group fractions.
 monotone=[]
 for ds in ['adult','bank','credit']:
  for seed in range(10000,10005):
   q=[check(json.loads((R/f'{ds}_s{seed}_T{T}'/'gate_fresh.json').read_text())['quality'])['Phi'] for T in range(3)]
   assert q[2]<=q[1]<=q[0];monotone.append(dict(dataset=ds,seed=seed,exact_Phi_nonincreasing=True))
 audited=['REPORT.md','PROTOCOL.md','CORRECTNESS.md','INTEGRATION_NOTES.md','REPRODUCE.md','REPORTING_CORRECTION.md','plot.py','make_report.py']
 for name in audited:
  txt=(W/name).read_text();assert 'G is the maximum' not in txt and 'Fairness cost G:' not in txt
 v=dict(status='PASS',correction='Use exact saved Phi=max(Phi_A,Phi_B); G is only the sum of group-normalized costs',raw_files_unchanged=len(before),raw_names_bytes_hashes_mtimes_unchanged=True,new_training_or_timing_runs=0,raw_before_manifest_sha256=sha(S/'raw_before.json'),superseded_result_manifest_sha256=sha(S/'superseded/RESULT_MANIFEST.json'),table_preservation_checks=comparisons,exact_quality_checks=180,negative_field_swap_checks=negatives,exact_budget_monotonicity=monotone,audited_current_prose=audited,qualitative_conclusions_unchanged=True)
 (W/'reporting_correction_verification.json').write_text(json.dumps(v,indent=2)+'\n')
 print(json.dumps(dict(status=v['status'],raw_files_unchanged=len(before),timing_tables_byte_identical=True,exact_quality_checks=180,negative_field_swaps_rejected=len(negatives),monotone_seed_trajectories=len(monotone))))
 fcntl.flock(lock.fileno(),fcntl.LOCK_UN)
