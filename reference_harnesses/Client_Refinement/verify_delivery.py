from common import *
from fractions import Fraction
from datetime import datetime,timezone
import ast,csv,math

def main():
 old=json.loads((ROOT/'C0_PRESERVATION.json').read_text());oldroot=Path(old['root'])
 for rel,h in old['files'].items():assert sha256(oldroot/rel)==h,('C0 changed',rel)
 b=json.loads((ROOT/'BASELINE_MANIFEST.json').read_text())
 for rel,r in b['files'].items():assert sha256(ROOT/'baseline'/rel)==r['sha256']==sha256(Path(r['source']))
 for p in ROOT.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
 assert 'client_c0' not in (ROOT/'benchmark.py').read_text()
 parent=json.loads((oldroot/'FROZEN_GRID.json').read_text());new=json.loads((ROOT/'FROZEN_GRID.json').read_text())
 assert sha256(oldroot/'FROZEN_GRID.json')==new['parent_grid_sha256']
 assert len(new['cases'])==30
 for s in new['cases']:
  c=next(c for c in parent['cases'] if c['case_id']==s['parent_case_id'])
  for key,v in c.items():
   if key not in ('case_id','T'):assert s[key]==v,(key,s['case_id'])
  assert s['T'] in (1,2)
 run=ROOT/'runs/client-refinement-20260926-v1';manifest=json.loads((run/'run_manifest.json').read_text())
 for rel,h in manifest['source_bindings'].items():assert sha256(ROOT/rel)==h
 status=json.loads((run/'status.json').read_text());assert status['status']=='COMPLETE' and len(status['completed'])==30
 v=json.loads((ROOT/'RESULTS_VERIFICATION.json').read_text());assert v['status']=='PASS_COMPLETE' and v['observations']==480 and v['distinct_replay_comparisons']==90 and v['distinct_method_outputs']==120
 logs=[json.loads(line) for line in (run/'lock.jsonl').read_text().splitlines()]
 acquired=[x for x in logs if x['event']=='acquired'];released=[x for x in logs if x['event']=='released'];finished=[x for x in logs if x['event']=='worker_finished']
 assert len(acquired)==len(released)==len(finished)==30 and all(x['returncode']==0 for x in finished)
 assert [x['event'] for x in logs]==['waiting','acquired','worker_finished','released']*30
 # Verify exact quality table semantics and hashes independently of rounded figures.
 qs=list(csv.DictReader((ROOT/'tables/quality_exact.csv').open()));assert len(qs)==45
 for q in qs:
  e={k:Fraction(int(q[k+'_numerator']),int(q[k+'_denominator'])) for k in ('Phi_A','Phi_B','Phi','G','pooled_SSE')}
  assert e['Phi']==max(e['Phi_A'],e['Phi_B']);assert e['G']==e['Phi_A']+e['Phi_B'];assert e['pooled_SSE']==int(q['n0'])*e['Phi_A']+int(q['n1'])*e['Phi_B']
  for k,x in e.items():assert float(x)==float(q[k])
  assert float(q['new_quality_evaluation_seconds'])==0
  if q['T']!='0':assert q['matched_new_fresh_witness_verified']=='True'
 # Recompute headline ratio-of-total-times directly from flat raw table.
 raw=list(csv.DictReader((ROOT/'tables/raw_timings.csv').open()));a=list(csv.DictReader((ROOT/'tables/aggregate_timings.csv').open()))
 for row in a:
  subset=[x for x in raw if x['T']==row['T'] and (row['dataset']=='all' or x['dataset']==row['dataset'])]
  field='algorithm_seconds' if row['scope']=='algorithm' else 'request_e2e_seconds'
  fresh=sum(float(x[field]) for x in subset if x['method']=='fresh');replay=sum(float(x[field]) for x in subset if x['method']==row['method'])
  assert math.isclose(fresh/replay,float(row['ratio_of_total_times']),rel_tol=1e-14)
 for r in raw:
  if r['method']=='fresh':assert float(r['additive_cache_construction_seconds'])==0
 wc=list(csv.DictReader((ROOT/'tables/work_counters.csv').open()));assert len(wc)==120
 for r in wc:
  if r['method'] in ('basic','runnerup'):
   assert r['threshold_fallback']=='True' and r['abandonment_round']=='0' and r['P']=='0' and r['S']=='0'
  else:assert r['threshold_fallback']=='False' and r['A']=='0'
 pdf=json.loads((ROOT/'PDF_VERIFICATION.json').read_text());assert pdf['status']=='PASS' and pdf['pages']==1 and sha256(Path(pdf['path']))==pdf['sha256']
 required=['REPORT.md','PROTOCOL.md','CORRECTNESS.md','INTEGRATION_NOTES.md','REPRODUCE.md','SETUP_COST_INVENTORY.md','tables/raw_timings.csv','tables/aggregate_timings.csv','tables/quality_exact.csv']
 assert all((ROOT/x).exists() for x in required)
 gate=json.loads((ROOT/'HARNESS_GATE.json').read_text());assert gate['status']=='PASS' and gate['distinct_fixture_comparisons']==12
 receipt={'status':'PASS','created_utc':datetime.now(timezone.utc).isoformat(),'baseline_files_verified':len(b['files']),'old_C0_artifacts_unchanged':len(old['files']),'fixed_grid_settings':30,'distinct_method_outputs':120,'distinct_replay_comparisons':90,'timing_observations':480,'repeated_comparisons':360,'positive_T_historical_witness_matches':30,'exact_quality_rows_reused':45,'new_quality_evaluations':0,'timer_sums_and_aggregate_ratios_verified':True,'fresh_cache_construction_zero_all_observations':True,'lock_batches':30,'lock_wait_seconds':sum(x['wait_seconds'] for x in acquired),'lock_held_seconds':sum(x['held_seconds'] for x in released),'load_average_1m_range':[min(x['load_average'][0] for x in acquired),max(x['load_average'][0] for x in acquired)],'pdf_pages_verified':1,'failures':0,'retries':0,'no_source_algorithm_changes':True,'scope':'Local saved-evidence/source/accounting verification, not an independent numerical oracle or manuscript approval.'}
 write_json(ROOT/'DELIVERY_VERIFICATION.json',receipt);print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
