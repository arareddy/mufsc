from common import *
from fractions import Fraction
from datetime import datetime,timezone
import subprocess
OLD=Path('study://Client_Deletion')
oldrun=OLD/'runs/client-c0-20260926-v1'
oldmanifest=json.loads((oldrun/'run_manifest.json').read_text())
base=json.loads((ROOT/'BASELINE_MANIFEST.json').read_text())
for rel,r in base['files'].items():assert sha256(ROOT/'baseline'/rel)==r['sha256']==sha256(Path(r['source']))
for rel,r in base['files'].items():
 if rel.startswith('src/'):assert oldmanifest['source_bindings']['baseline/'+rel]==r['sha256']
inputs=json.loads((ROOT/'INPUTS.json').read_text())
for name,r in inputs['files'].items():
 assert sha256(Path(r['path']))==r['sha256'];assert sha256(Path(r['identity_path']))==r['identity_sha256']
for f in ('INPUTS.json','IDENTITY_REGISTRY.json'):assert sha256(ROOT/f)==oldmanifest['source_bindings'][f]
refs={}
for c in json.loads((OLD/'FROZEN_GRID.json').read_text())['cases']:
 d=oldrun/'quality'/c['case_id'];p=d/'quality.json';receipt=d/'complete.json';r=json.loads(receipt.read_text())
 assert r['status']=='PASS' and sha256(p)==r['quality_sha256'] and r['source_bindings']==oldmanifest['source_bindings']
 rows=json.loads(p.read_text());witnesses={}
 for row in rows:
  e={k:Fraction(v['numerator'],v['denominator']) for k,v in row['quality']['exact'].items()}
  assert e['Phi']==max(e['Phi_A'],e['Phi_B']);assert e['G']==e['Phi_A']+e['Phi_B']
  n=row['quality']['retained_group_counts'];assert n==c['retained_group_counts']
  assert e['pooled_SSE']==n[0]*e['Phi_A']+n[1]*e['Phi_B']
  witnesses[row['T']]={'full_witness_sha256':object_hash(row['model_witness']),'final_centers_sha256':object_hash(row['model_witness']['final_centers']),'exact_quality_sha256':object_hash(row['quality']['exact'])}
 refs[c['case_id']]={'path':str(p),'sha256':sha256(p),'receipt_path':str(receipt),'receipt_sha256':sha256(receipt),'budgets':witnesses}
write_json(ROOT/'QUALITY_REFERENCE_MANIFEST.json',{'status':'PASS','created_utc':datetime.now(timezone.utc).isoformat(),'parent_run':str(oldrun),'parent_run_manifest_sha256':sha256(oldrun/'run_manifest.json'),'source_and_input_bindings_match':True,'cases':refs},immutable=True)
write_json(ROOT/'ENVIRONMENT.json',{'created_utc':datetime.now(timezone.utc).isoformat(),'environment':environment_manifest(),'hardware':subprocess.run(['/usr/sbin/sysctl','-n','machdep.cpu.brand_string','hw.memsize'],capture_output=True,text=True).stdout,'native_pool_introspection':'threadpoolctl absent in reused environment; five controls set to 1; single measurement worker','read_only_environment':True},immutable=True)
print('Preflight PASS: 19 source/map/helper files; 3 dataset+identity files; 15 prior quality files and 45 exact quality identities. No training.')
