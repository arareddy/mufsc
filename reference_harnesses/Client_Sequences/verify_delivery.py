"""Read-only standard-library final manifest checks; no training or pickle loads."""
from pathlib import Path
import json,hashlib,math
ROOT=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=read(ROOT/'DELIVERABLE_MANIFEST.json')
for name,item in manifest['files'].items():
 p=ROOT/name;assert p.is_file() and p.stat().st_size==item['bytes'] and sha(p)==item['sha256'],name
verification=read(ROOT/'VERIFICATION.json');summary=read(ROOT/'SUMMARY.json');report=(ROOT/'REPORT.md').read_text()
assert verification['status']=='PASS' and verification['observations']==270 and verification['full_indexed_model_comparisons']==135
for key in ('pooled_matched_ratio','pooled_operational_ratio','pooled_algorithm_ratio'):assert f'{summary[key]:.2f}x' in report
for name,h in verification['checked_artifacts'].items():assert sha(ROOT/name)==h,name
for name,h in verification['table_hashes'].items():assert sha(ROOT/'tables'/name)==h,name
run=ROOT/'runs/sequences-20260926-v1';inputs=read(ROOT/'INPUT_MANIFEST.json')
for name,record in inputs['read_only_inputs'].items():
 # Live manuscript is deliberately editable in another task, hence only a point-in-time input binding.
 if '/Fair_to_Forget_Live/' not in name:assert sha(Path(name))==record['sha256'],name
for name,r in read(ROOT/'BASELINE_MANIFEST.json')['files'].items():assert sha(ROOT/'baseline'/name)==r['sha256']==sha(Path(r['source'])),name
assert sha(ROOT/'client_c0.py')==inputs['reviewed_candidate_sha256']
assert read(ROOT/'FINAL_STATE_VERIFICATION.json')['status']=='PASS'
assert read(ROOT/'PDF_QA.json')['status']=='PASS'
assert len(list(run.glob('*_k10_seed*/complete.json')))==15
print(json.dumps({'status':'PASS','manifest_files_verified':len(manifest['files']),'manifested_bytes':sum(x['bytes'] for x in manifest['files'].values()),'source_and_historical_inputs_unchanged':True,'live_source':'Snapshot only; concurrent edits allowed','scientific_grid':'15 sequences / 45 cases / 135 comparisons / 270 observations','manifest_sha256':sha(ROOT/'DELIVERABLE_MANIFEST.json')},indent=2))
