"""Final exact-table/preservation/PDF checks; manifest only after parent lock release."""
from pathlib import Path
from fractions import Fraction as F
import json,csv,hashlib,sys,math,subprocess,datetime
W=Path(__file__).resolve().parent
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def load(n):return json.loads((W/n).read_text())
def read(n):return list(csv.DictReader((W/'tables'/n).open()))
def write(n,v):(W/n).write_text(json.dumps(v,indent=2)+'\n')
if '--manifest' in sys.argv:
 assert load('FINAL_VERIFICATION.json')['status']=='PASS'
 last=json.loads((W/'LOCK_RECEIPTS.jsonl').read_text().splitlines()[-1]);assert last['event']=='released' and last['exit_code']==0
 files=[]
 for p in sorted(W.rglob('*')):
  if not p.is_file() or p.name=='MANIFEST.json' or any(x in p.parts for x in ['tmp','.mplconfig','__pycache__']):continue
  files.append(dict(path=str(p.relative_to(W)),bytes=p.stat().st_size,sha256=sha(p)))
 write('MANIFEST.json',dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='All durable local deliverables except self; excludes regenerable PNG/font caches',files=files,total_bytes=sum(x['bytes'] for x in files),local_only=True))
 print(json.dumps(dict(manifest_files=len(files),durable_bytes=sum(x['bytes'] for x in files))))
 sys.exit(0)
fm=load('INPUT_MANIFEST.json')
for r in fm['files']:
 p=Path(r['path']);st=p.stat();assert (sha(p),st.st_size,st.st_mtime_ns)==(r['sha256'],r['bytes'],r['mtime_ns']),str(p)
rows=read('case_quality.csv');pairs=read('paired_changes.csv');summary=read('summary.csv');assert len(rows)==90 and len(pairs)==720 and len(summary)==144
bykey={(r['population'],r['dataset'],r['seed'],r['T']):r for r in rows};assert len(bykey)==90
metrics=['Phi_A','Phi_B','Phi','G','pooled_SSE','population_average','absolute_group_gap','max_min_group_ratio']
for r in rows:
 a,b=F(r['Phi_A_exact']),F(r['Phi_B_exact']);n0,n1=int(r['n_group0']),int(r['n_group1']);assert F(r['Phi_exact'])==max(a,b) and F(r['G_exact'])==a+b
 assert F(r['pooled_SSE_exact'])==n0*a+n1*b and F(r['population_average_exact'])==(n0*a+n1*b)/(n0+n1)
 for k in metrics:assert float(r[k])==float(F(r[k+'_exact']))
for r in summary:
 xs=[F(x[r['metric']+'_exact']) for x in rows if (x['population'],x['dataset'],x['T'])==(r['population'],r['dataset'],r['T'])];assert len(xs)==5
 mean=sum(xs,F(0))/5;var=sum(((x-mean)**2 for x in xs),F(0))/4
 assert F(r['mean_exact'])==mean and F(r['sample_variance_exact'])==var and float(r['sample_sd'])==math.sqrt(float(var))
for r in pairs:
 a=bykey[r['population'],r['dataset'],r['seed'],r['T_from']];b=bykey[r['population'],r['dataset'],r['seed'],r['T_to']];k=r['metric'];av=F(a[k+'_exact']);bv=F(b[k+'_exact'])
 assert F(r['change_exact'])==bv-av and F(r['relative_decrease_exact'])==(av-bv)/av
endpoints=[p for p in pairs if p['T_from']=='0' and p['T_to']=='2' and p['metric'] in ['Phi_A','Phi_B','Phi','population_average']]
assert len(endpoints)==120 and all(F(p['change_exact'])<0 for p in endpoints)
adverse=[]
for t in read('transition_checks.csv'):
 if t['any_group_increase_while_Phi_decreases']!='True':continue
 relevant={r['metric']:r for r in pairs if all(r[k]==t[k] for k in ['population','dataset','seed','T_from','T_to'])}
 out={k:t[k] for k in ['population','dataset','seed','T_from','T_to']}
 for k in ['Phi_A','Phi_B','Phi','population_average']:
  for f in ['before_exact','after_exact','change_exact','change']:out[k+'_'+f]=relevant[k][f]
 adverse.append(out)
assert len(adverse)==5
with (W/'tables/adverse_changes.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(adverse[0]));w.writeheader();w.writerows(adverse)
pop_increases=[p for p in pairs if p['metric']=='population_average' and F(p['change_exact'])>0];assert len(pop_increases)==2
qa=load('VISUAL_QA.json');assert qa['status']=='PASS';pdfchecks=[]
binroot=Path('[private-path-omitted]')
for r in load('FIGURE_RECEIPTS.json')['figures']:
 p=Path(r['path']);assert sha(p)==r['sha256']==qa['pdf_hashes'][p.name]
 info=subprocess.check_output([str(binroot/'pdfinfo'),str(p)],text=True);assert 'Pages:           1' in info
 txt=subprocess.check_output(['[private-path-omitted]',str(p),'-'],text=True)
 for word in ['Adult','Bank','Credit','refinement rounds','Population-average','Group 0','Group 1']:assert word in txt,word
 pdfchecks.append(dict(path=str(p),sha256=sha(p),one_page=True,required_labels_present=True,visually_inspected=True))
write('FINAL_VERIFICATION.json',dict(status='PASS',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),frozen_input_files_unchanged=len(fm['files']),case_rows_exactly_rechecked=90,summary_means_variances_rechecked=144,paired_metric_changes_rechecked=720,all_120_endpoint_group_Phi_population_changes_negative=True,adverse_group_events=5,population_average_increases=2,pdf_checks=pdfchecks,no_new_training=True,no_original_file_writes_by_scripts=True,live_source_scope='reading-time snapshots only; another task may independently edit live source',failures_file_exists=(W/'FAILURES.jsonl').exists(),finalize_sha256=sha(Path(__file__))))
print('PASS: final preservation, exact-table and PDF checks.')
