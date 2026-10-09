from pathlib import Path
import json,hashlib,datetime,shutil
W=Path(__file__).resolve().parent
A=Path('study://Round_Budgets');B=Path('study://Client_Deletion');D=Path('source://ftf1d');L=Path('[private-path-omitted]')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(p.read_text())
assert not (W/'INPUT_MANIFEST.json').exists(),'Refuse to replace frozen manifest'
paths=set()
for root,names in [(A,['REPORT.md','CORRECTNESS.md','PROTOCOL.md','REPORTING_CORRECTION.md','verification.json','reporting_correction_verification.json','input_manifest.json','baseline_manifest.json','RUN_ID','tables/quality_summary.csv','tables/quality_definition_checks.csv']),(B,['REPORT.md','PROTOCOL.md','FROZEN_GRID.json','INPUTS.json','IDENTITY_REGISTRY.json','BASELINE_MANIFEST.json','RESULTS_VERIFICATION.json','READY_FOR_REVIEW.json','STATE_INVENTORY.md','REPRODUCE.md','client_c0.py','tables/quality.csv'])]:paths.update(root/n for n in names)
for inp in read(A/'input_manifest.json'):
 paths.update([Path(inp['input']),Path(inp['request'])])
 for t in range(3):
  r=A/'runs'/(A/'RUN_ID').read_text().strip()/f"{inp['dataset']}_s{inp['settings']['seed']}_T{t}"
  paths.update(r/n for n in ['complete.json','correctness.json','checkpoint.witness.json'])
  for m in ['fresh','none','basic','runnerup']:paths.update([r/f'gate_{m}.json',r/f'gate_{m}.witness.json'])
for v in read(B/'INPUTS.json')['files'].values():paths.update([Path(v['path']),Path(v['identity_path'])])
for c in read(B/'FROZEN_GRID.json')['cases']:
 q=B/'runs/client-c0-20260926-v1/quality'/c['case_id'];r=B/'runs/client-c0-20260926-v1/core'/c['case_id']
 paths.update([q/'quality.json',q/'complete.json',r/'rep0_fresh_model.json',r/'extra_state_witness.json',r/'complete.json'])
 for n in read(q/'complete.json')['source_bindings']:paths.add(B/n)
for n in read(A/'baseline_manifest.json')['files']:paths.add(A/'source'/n)
for n,v in read(B/'BASELINE_MANIFEST.json')['files'].items():paths.add(Path(v['source']));paths.add(B/'baseline'/n)
ctx=[L/'AGENTS.md',L/'LIVE_EDITING_RULES.md',L/'LIVE_WORKFLOW.md',L/'main.tex',L/'appendix.tex',L/'stage1_protocol.tex',L/'generated/corrected_p4_full_table.tex',L/'reference_integrity_audit_20260926/evidence/ghadiri2021socially.author_fulltext.txt',D/'corrected_project/experiments/p4_corrected.py',D/'corrected_project/src/centralized.py']
snap=W/'context';snap.mkdir(exist_ok=True)
context=[]
for p in ctx:
 dst=snap/p.name;shutil.copyfile(p,dst);context.append(dict(original_path=str(p),snapshot_path=str(dst),sha256=sha(dst)));paths.add(dst)
records=[]
for p in sorted(paths):
 s=p.stat();records.append(dict(path=str(p),sha256=sha(p),bytes=s.st_size,mtime_ns=s.st_mtime_ns))
x=dict(frozen_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),protocol_sha256=sha(W/'PROTOCOL.md'),files=records,context=context,expected_quality_rows=90,excluded=[])
(W/'INPUT_MANIFEST.json').write_text(json.dumps(x,indent=2)+'\n')
(W/'PROTOCOL_FREEZE.json').write_text(json.dumps(dict(protocol_sha256=x['protocol_sha256'],input_manifest_sha256=sha(W/'INPUT_MANIFEST.json'),frozen_utc=x['frozen_utc']),indent=2)+'\n')
print(json.dumps(dict(frozen_files=len(records),bytes_read=sum(x['bytes'] for x in records),context_snapshots=len(context))))
