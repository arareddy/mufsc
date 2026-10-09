"""Read-only source/snapshot/evidence checks, then write a compact receipt."""
from common import *
from fractions import Fraction
from datetime import datetime,timezone
import ast,csv,difflib

def main():
    baseline=json.loads((ROOT/'BASELINE_MANIFEST.json').read_text())
    for rel,record in baseline['files'].items():
        assert sha256(ROOT/'baseline'/rel)==record['sha256']
        assert sha256(Path(record['source']))==record['sha256']
    snap=ROOT/'review_snapshots/v1';sm=json.loads((snap/'SNAPSHOT_MANIFEST.json').read_text())
    for rel,r in sm.items():
        p=snap/rel;assert sha256(p)==r['sha256'] and p.stat().st_size==r['bytes']
    for rel in ('client_c0.py','common.py','test_client_c0.py','benchmark.py','with_lock.py','prepare.py','PROTOCOL.md','FROZEN_GRID.json','BASELINE_MANIFEST.json','INPUTS.json','IDENTITY_REGISTRY.json','ENVIRONMENT.json','CORRECTNESS.json'):
        assert (ROOT/rel).read_bytes()==(snap/rel).read_bytes(),rel
    expected_diff=''.join(difflib.unified_diff([], (ROOT/'client_c0.py').read_text().splitlines(keepends=True),fromfile='/dev/null',tofile='variant/client_c0.py'))
    assert (ROOT/'implementation.diff').read_text()==expected_diff
    for p in ROOT.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
    grid=json.loads((ROOT/'FROZEN_GRID.json').read_text())['cases'];run=ROOT/'runs/client-c0-20260926-v1'
    manifest=json.loads((run/'run_manifest.json').read_text())
    for rel,h in manifest['source_bindings'].items():assert sha256(ROOT/rel)==h
    for stage in ('core','quality'):
        status=json.loads((run/f'{stage}_status.json').read_text())
        assert status['status']=='COMPLETE' and len(status['completed'])==15 and not status['excluded_or_unavailable']
    exact_quality_checks=0
    for spec in grid:
        qs=json.loads((run/'quality'/spec['case_id']/'quality.json').read_text())
        values=[]
        for q in qs:
            e={k:Fraction(v['numerator'],v['denominator']) for k,v in q['quality']['exact'].items()}
            assert e['Phi']==max(e['Phi_A'],e['Phi_B']) and e['G']==e['Phi_A']+e['Phi_B']
            ng=q['quality']['retained_group_counts'];assert e['pooled_SSE']==ng[0]*e['Phi_A']+ng[1]*e['Phi_B']
            assert all(float(e[k])==v for k,v in q['quality']['values'].items())
            values.append(e['Phi']);exact_quality_checks+=1
        assert values[0]>=values[1]>=values[2]
    prep=list(csv.DictReader((ROOT/'tables/preparation_storage.csv').open()))
    assert all(r['incremental_break_even_requests_vs_fresh']=='1' and r['incremental_break_even_requests_vs_direct']=='1' and r['full_setup_break_even_requests_vs_fresh']=='2' for r in prep)
    results=json.loads((ROOT/'RESULTS_VERIFICATION.json').read_text())
    assert results['raw_observations']==135 and results['quality_rows']==45 and not results['missing_core_cases']
    review=json.loads((ROOT/'INDEPENDENT_REVIEW_STATUS.json').read_text())
    assert review['status']=='REVIEW_COMPLETE_SCOPED_PASS'
    assert sha256(snap/'SNAPSHOT_MANIFEST.json')==review['snapshot_manifest_sha256']
    assert sha256(ROOT/'client_c0.py')==review['candidate_sha256']
    assert sha256(Path(review['review_pointer_path']))==review['review_pointer_sha256']
    assert sha256(Path(review['implementation_review_path']))==review['implementation_review_sha256']
    files=[p for p in ROOT.rglob('*') if p.is_file()]
    receipt={'status':'PASS','created_utc':datetime.now(timezone.utc).isoformat(),'frozen_baseline_files_verified':len(baseline['files']),'immutable_snapshot_files_verified':len(sm),'root_core_matches_review_snapshot':True,'core_cases':15,'timing_observations':135,'matched_quality_rows':exact_quality_checks,'exact_group_cost_identities_and_monotonicity_pass':True,'source_bound_review_status':review['status'],'scope':'No new training. Checks source/snapshot identity, reporting completion, saved exact quality identities, setup break-even and review binding; raw model/receipt checks are in RESULTS_VERIFICATION.json.','local_file_logical_bytes_at_check':sum(p.stat().st_size for p in files),'local_files_at_check':len(files),'actual_disk_savings_claimed':0,'bulk_export_to_icloud':False}
    write_json(ROOT/'DELIVERY_VERIFICATION.json',receipt)
    print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
