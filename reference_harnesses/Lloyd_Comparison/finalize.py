from common import *
from fractions import Fraction as F
import csv,math,datetime,struct,subprocess

def read(n):return list(csv.DictReader((W/'tables'/n).open()))
if '--manifest' in sys.argv:
 assert load(W/'FINAL_VERIFICATION.json')['status']=='PASS'
 last=json.loads((W/'LOCK_RECEIPTS.jsonl').read_text().splitlines()[-1]);assert last['event']=='released' and last['exit_code']==0
 rr=[]
 for p in sorted(W.rglob('*')):
  if not p.is_file() or p.name=='MANIFEST.json' or any(k in p.parts for k in ['tmp','.mplconfig','__pycache__']):continue
  rr.append(dict(path=str(p.relative_to(W)),bytes=p.stat().st_size,sha256=sha(p)))
 dump(W/'MANIFEST.json',dict(status='COMPLETE',created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),files=rr,total_bytes=sum(x['bytes'] for x in rr),scope='All durable outputs excluding self and regenerable page/font caches; originals remain external read-only dependencies'))
 print('Manifest:',len(rr),'files,',sum(x['bytes'] for x in rr),'bytes');sys.exit(0)
verify_sources();assert load(W/'PROTOCOL_FREEZE.json')['bindings']==bindings()
for r in load(W/'INPUT_MANIFEST.json')['files']:
 p=Path(r['path']);assert (sha(p),p.stat().st_size,p.stat().st_mtime_ns)==(r['sha256'],r['bytes'],r['mtime_ns'])
# Prove the previous completed workspace's manifest-bound outputs remain untouched.
prior=load(Q/'MANIFEST.json')
for r in prior['files']:assert sha(Q/r['path'])==r['sha256'] and (Q/r['path']).stat().st_size==r['bytes']
rows=read('quality.csv');assert len(rows)==180
lookup={(r['population'],r['dataset'],r['seed'],r['method'],r['T']):r for r in rows};assert len(lookup)==180
for r in rows:
 a,b=F(r['Phi_A_exact']),F(r['Phi_B_exact']);n0,n1=int(r['n0']),int(r['n1']);assert F(r['Phi_exact'])==max(a,b) and F(r['G_exact'])==a+b
 assert F(r['pooled_SSE_exact'])==n0*a+n1*b and F(r['population_average_exact'])==(n0*a+n1*b)/(n0+n1)
for r in read('summary.csv'):
 xs=[F(x[r['metric']+'_exact']) for x in rows if all(x[k]==r[k] for k in ['population','dataset','method','T'])];assert len(xs)==5;mean=sum(xs)/5;var=sum((x-mean)**2 for x in xs)/4
 assert F(r['mean_exact'])==mean and F(r['sample_variance_exact'])==var and float(r['sample_sd'])==math.sqrt(float(var))
for r in read('paired_methods.csv'):
 a=lookup[r['population'],r['dataset'],r['seed'],'fair',r['T']];b=lookup[r['population'],r['dataset'],r['seed'],'lloyd',r['T']];k=r['metric'];av,bv=F(a[k+'_exact']),F(b[k+'_exact'])
 assert F(r['fair_minus_lloyd_exact'])==av-bv and F(r['relative_difference_exact'])==(av-bv)/bv
for c in load(W/'FROZEN_GRID.json')['cases']:
 p=W/'runs/matched-start-v1'/c['case_id'];receipt=load(p/'complete.json');assert receipt['status']=='PASS' and receipt['output_sha256']==sha(p/'outputs.json') and receipt['source_bindings']==bindings()
 for m,res in load(p/'outputs.json')['methods'].items():
  for ar in res['witness']['trajectory']:
   vals=struct.unpack('<'+'d'*math.prod(ar['shape']),bytes.fromhex(ar['bytes_hex']));assert all(math.isfinite(x) for x in vals) and list(map(float.hex,vals))==ar['values_hex']
  for stats in res['witness']['per_round_stats']:assert [sum(x) for x in stats['N']]==c['counts']
logs=[json.loads(x) for x in (W/'LOCK_RECEIPTS.jsonl').read_text().splitlines()];batches={x['batch'] for x in logs if x['event']=='queued' and any(s.endswith('/worker.py') for s in x['command'])};assert len(batches)==30
for batch in batches:
 events=[x['event'] for x in logs if x['batch']==batch];assert events==['queued','acquired','released']
 assert next(x for x in logs if x['batch']==batch and x['event']=='released')['exit_code']==0
p=W/'figures/matched_start_quality.pdf';qa=load(W/'VISUAL_QA.json');assert qa['status']=='PASS' and qa['pdf_sha256']==sha(p)==load(W/'FIGURE_RECEIPT.json')['sha256']
info=subprocess.check_output(['[private-path-omitted]',str(p)],text=True);assert 'Pages:           1' in info
text=subprocess.check_output(['[private-path-omitted]',str(p),'-'],text=True)
for label in ['Lloyd','Group 0','Group 1','Worst-group','Population-average','refinement rounds','Record deletion','Whole-client deletion']:assert label in text,label
# Record both fixtures that require fallback and the actual runtime settings.
f=load(W/'fixtures/results.json');assert f['status']=='PASS' and len(f['fixtures'])==7
ambiguous_fixture_evaluations=sum(q['ambiguous_rows'] for x in f['fixtures'] for q in x.get('quality',[]));assert ambiguous_fixture_evaluations>0
assert not list((W/'runs').rglob('FAILED.json'))
report=load(W/'VERIFICATION.json');assert report['status']=='PASS' and report['fresh_fair_witnesses_reproduced']==90 and report['independent_objective_checks']==150
receipt=dict(status='PASS',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),frozen_inputs_unchanged=len(load(W/'INPUT_MANIFEST.json')['files']),frozen_source_files_unchanged=len(load(W/'SOURCE_MANIFEST.json')['files']),previous_group_quality_files_unchanged=len(prior['files']),case_output_hashes_verified=30,finite_indexed_center_encodings_verified=True,statistic_group_counts_verified=True,exact_quality_rows_rechecked=180,exact_summary_means_variances_rechecked=216,paired_metric_differences_rechecked=540,case_parent_lock_batches_verified=30,case_queue_seconds=sum(x['wait_seconds'] for x in logs if x['batch'] in batches and x['event']=='acquired'),case_held_seconds=sum(x['held_seconds'] for x in logs if x['batch'] in batches and x['event']=='released'),ambiguous_fixture_point_evaluations=ambiguous_fixture_evaluations,pdf_pages=1,pdf_sha256=sha(p),visual_qa='PASS',failed_cases=[],unresolved_correctness=[],finalizer_sha256=sha(Path(__file__)))
dump(W/'FINAL_VERIFICATION.json',receipt);print(json.dumps(receipt,indent=2))
