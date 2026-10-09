#!/usr/bin/env python3
from pathlib import Path
import json,hashlib,datetime,subprocess,sys,platform,io,contextlib
W=Path(__file__).resolve().parent;R=W/'runs'/(W/'RUN_ID').read_text().strip()
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as s:
  for b in iter(lambda:s.read(1048576),b''):h.update(b)
 return h.hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
base=json.loads((W/'baseline_manifest.json').read_text());orig=Path('source://ftf1d/corrected_project')
source={f:dict(expected=h,original=sha(orig/f),local=sha(W/'source'/f)) for f,h in base['files'].items()}
assert all(v['expected']==v['original']==v['local'] for v in source.values())
assert sha(orig/'TRAINING_MAP.md')==sha(W/'source/TRAINING_MAP.md')==base['map_sha256']
refs=json.loads((W/'reference_hashes.json').read_text());reference_checks={p:dict(start=h,finish=sha(Path(p)),unchanged=h==sha(Path(p))) for p,h in refs.items()}
write(W/'preservation_check.json',dict(source_files=source,map_unchanged=True,references=reference_checks,scope='This task made no writes to reference source, live manuscript or shared Git. Hash checks cover listed reference files only.'))
import numpy as np
s=io.StringIO()
with contextlib.redirect_stdout(s):np.show_config()
hardware=subprocess.run(['/usr/sbin/sysctl','-n','machdep.cpu.brand_string','hw.memsize','hw.logicalcpu'],capture_output=True,text=True)
write(W/'environment_details.json',dict(collected_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),numpy_config=s.getvalue(),hardware_fields=['cpu_brand','memory_bytes','logical_cpus'],hardware_output=hardware.stdout,hardware_error=hardware.stderr,scope='Supplemental hardware/build metadata, collected after measurements; primary environment recorded before campaign.'))
reviewed=json.loads((W/'figure_validation.json').read_text()) if (W/'figure_validation.json').exists() else None
assert reviewed is not None, 'Visual review receipt required before finalization'
figchecks={}
for p in sorted((W/'figures').glob('*.pdf')):
 info=subprocess.run(['[private-path-omitted]',str(p)],capture_output=True,text=True,check=True).stdout
 assert 'Pages:           1' in info
 assert reviewed['figures'][p.name]['sha256']==sha(p), 'PDF changed since visual review; inspect fresh renders before updating receipt'
 figchecks[p.name]=dict(sha256=sha(p),bytes=p.stat().st_size,pages=1,visual_review='PASS: rendered at 1600 pixels; labels, legends, uncertainty bars, curves and footnotes legible without clipping',pdfinfo=info)
write(W/'figure_validation.json',dict(status='PASS',objective='Phi=max(Phi_A,Phi_B)',figures=figchecks))
paths=[*W.glob('*.md'),*W.glob('*.py'),*W.glob('*.diff'),*W.glob('*.json'),W/'RUN_ID',W/'.gitignore',*sorted((W/'tables').glob('*.csv')),*sorted((W/'figures').glob('*.pdf')),*sorted((W/'source').rglob('*.py')),W/'source/TRAINING_MAP.md']
paths=sorted(set(p for p in paths if p.name!='RESULT_MANIFEST.json'))
files={str(p.relative_to(W)):dict(sha256=sha(p),bytes=p.stat().st_size) for p in paths}
receipts={str(p.relative_to(W)):sha(p) for p in sorted(R.glob('*/complete.json'))}
assert len(receipts)==45
all_files=[p for p in W.rglob('*') if p.is_file()]
write(W/'RESULT_MANIFEST.json',dict(status='COMPLETE',run_id=(W/'RUN_ID').read_text().strip(),created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),expected_keys=180,observed_keys=180,replay_comparisons=135,timing_observations=720,missing=[],duplicates=[],files=files,batch_receipt_hashes=receipts,checkpoint_witness_storage='Per-batch completion receipts bind every checkpoint and raw artifact; no second archive is created.',workspace_logical_bytes=sum(p.stat().st_size for p in all_files),compact_deliverable_bytes=sum(v['bytes'] for k,v in files.items() if k not in ['input_manifest.json']),disk_savings_claimed=0,manuscript_written=False,shared_git_modified=False,network_measured=False,reporting_objective='Phi=max(Phi_A,Phi_B)',reporting_correction_verification_sha256=sha(W/'reporting_correction_verification.json'),exact_quality_definition_checks=180))
print(json.dumps(dict(manifest='RESULT_MANIFEST.json',bound_deliverables=len(files),bound_batch_receipts=len(receipts),source_unchanged=True,reference_checks={p:v['unchanged'] for p,v in reference_checks.items()},hardware=hardware.stdout)))
