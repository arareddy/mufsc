from pathlib import Path
import json,hashlib
from datetime import datetime,timezone
R=Path(__file__).resolve().parent
py='source://ftf1d/.venv/bin/python'
(R/'REPRODUCE.md').write_text(f'''# Reproduce and inspect

Completed run: `runs/diversity-v1`. Inspect REPORT.md, PROTOCOL.md, SELECTION.json, tables/ and VERIFICATION.json before considering new measurements. All 30 unique cases and 270 timed requests completed. No resume work remains.

Use the existing read-only Python/NumPy environment at `{py}`. The read-only dataset files and SHA256s are in INPUTS.json. The read-only completed inputs and reviewed source are bound in COMPLETED_INPUT_BINDINGS.json and SOURCE_VERIFICATION.json. Local baseline files are exact small copies of the 21 frozen map/source/driver files; client_c0.py matches reviewed v1. No data/environment copy, download or full-checkpoint restoration is needed.

## Saved-evidence verification (no training)

From `{R}`:

```sh
{py} -B with_lock.py analysis_verify_lock.jsonl {py} -B analyze.py
{py} -B verify_tables.py
```

The first command rechecks outputs and regenerates tables and VERIFICATION.json from saved observations; the second independently recomputes 3,342 numeric fields from raw JSON and regenerates TABLE_VERIFICATION.json. Tables use request-time ratios unless the column explicitly says algorithm. G is the sum of group means; Phi is the maximum. Raw timings and witnesses remain untouched. Generated analysis/report artifacts have their own final manifest; regeneration of logs changes that manifest and should be performed in a small separate copy if final-package hashes must remain fixed.

To regenerate the report and PNG only:

```sh
{py} -B with_lock.py report_regeneration_lock.jsonl {py} -B make_report.py
```

The existing environment includes Matplotlib. The local font cache remains excluded from delivery. No PDF/page-render batch is produced.

## Fresh bounded repeat (prepared command, not executed a second time)

Preserve the completed run. Use a new run ID; the command below holds the shared lock across one worker per dataset/seed and releases it between all 15 batches:

```sh
{py} -B worker.py run --run diversity-independent-repeat
```

The frozen selection is already present. Do not rerun prepare.py over immutable metadata: its timestamped FROZEN_GRID.json intentionally refuses a differing overwrite. For a new separate workspace, copy only root source scripts plus baseline/, INPUTS.json, IDENTITY_REGISTRY.json, BASELINE_MANIFEST.json and the frozen protocol/selection/grid/source receipts; keep original absolute read-only dependencies. Never copy datasets, environments, historical Git pointers or bulky evidence. No manuscript edit is part of this workflow.

The runner resumes only complete batches whose source/protocol/grid bindings match. It refuses any existing incomplete batch instead of silently appending a retry. Preserve failure evidence, diagnose, and use a new run ID. One dataset/seed worker builds the original checkpoint and compact state once, then independently tests both selected departing clients. Each case gates exact output/state equality before its three balanced timing repetitions. The 600-second worker timeout and 5,400-second scheduling bound are part of PROTOCOL.md. No timing outcome changes selection or triggers retries.

The reporting scripts deliberately read `runs/diversity-v1`; a future run needs a separately documented reporting-path change before analysis, never an overwrite of v1. These are execution commands, not evidence of a second campaign.

## Storage

New workspace is local, outside iCloud. Only small source, compact JSON models/receipts, tables and the final PNG are retained. Full checkpoints and initial pickle serializations existed in memory only. No external share, archive, cloud export or upload was made. Local-only files need a separately chosen backup.
''')
(R/'FIGURE_VERIFICATION.json').write_text(json.dumps({'status':'PASS','figure':'figures/client_latency.png','inspection':'Rendered PNG visually inspected: readable axes/legend, all six clients labeled, five-seed means shown, log-ms axis explicit, 10x line is reference only; no clipping.','plot_inputs':'tables/cases.csv, analysis_summary.json'},indent=2)+'\n')
(R/'READY_FOR_REVIEW.json').write_text(json.dumps({'status':'COMPLETE_READY_FOR_REVIEW','run':'diversity-v1','completed_cases':30,'unique_dataset_clients':6,'timed_observations':270,'scientific_scope':'Unchanged reviewed T0; same-seed indexed model and declared compact-state equality; resident request output boundary','no_new_manuscript_integration':True,'no_positive_refinement_inputs':True,'no_failed_or_discarded_cases':True,'verification_files':['VERIFICATION.json','TABLE_VERIFICATION.json','SOURCE_VERIFICATION.json','FIGURE_VERIFICATION.json'],'candidate_sha256':'6d7b8d993ed9e9fcda896192ee6e6299a434ab7cdc25ab9907fc6b4bc1cf3dde'},indent=2)+'\n')
# Inventory after completion; omit mutable font caches and this manifest's own bytes.
def files():
 return [p for p in sorted(R.rglob('*')) if p.is_file() and not any(x in p.parts for x in ('.mplconfig','__pycache__')) and p.name not in ('MANIFEST.json','DELIVERY_VERIFICATION.json')]
manifest={str(p.relative_to(R)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files()}
(R/'MANIFEST.json').write_text(json.dumps({'created_utc':datetime.now(timezone.utc).isoformat(),'workspace':str(R),'files':manifest},indent=2,sort_keys=True)+'\n')
for name,v in manifest.items():assert hashlib.sha256((R/name).read_bytes()).hexdigest()==v['sha256'] and (R/name).stat().st_size==v['bytes']
(R/'DELIVERY_VERIFICATION.json').write_text(json.dumps({'status':'PASS','manifest_files_verified':len(manifest),'manifested_bytes':sum(v['bytes'] for v in manifest.values()),'manifest_sha256':hashlib.sha256((R/'MANIFEST.json').read_bytes()).hexdigest(),'excluded_local_cache_directories':['.mplconfig','__pycache__'],'measurement_run_status':json.loads((R/'runs/diversity-v1/status.json').read_text())['status'],'source_and_table_audits':'PASS'},indent=2)+'\n')
print(json.dumps(json.loads((R/'DELIVERY_VERIFICATION.json').read_text()),indent=2))
