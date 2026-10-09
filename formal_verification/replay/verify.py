#!/usr/bin/env python3
"""Offline, one-worker, trust-zero verification against an existing pinned environment."""
import argparse, datetime, fcntl, hashlib, json, os, pathlib, re, shutil, subprocess, tempfile, time
MODULES = ['ExactPatch','Initialization','Nearest','Certificates','IntegerStats','Trajectory',
           'CertifiedReplay','Pipeline','IntervalCertificate','CertificateStrength',
           'CertificateTightness','LocalStability','ReplayBundle','AxiomAudit','Statements']
MATHLIB = 'c44e0c8ee63ca166450922a373c7409c5d26b00b'
LEAN_COMMIT = '6caaee842e94'
ALLOWED_AXIOMS = {'propext','Classical.choice','Quot.sound'}
def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('--env',help='Existing environment descriptor; never installs dependencies')
 ap.add_argument('--lean',help='Pinned Lean compiler, if --env is omitted')
 ap.add_argument('--lean-path',help='Existing mathlib and dependency olean directories')
 ap.add_argument('--mathlib',help='Existing mathlib source checkout for revision validation')
 ap.add_argument('--lock',help='Shared benchmark lock; never removed')
 a=ap.parse_args()
 root=pathlib.Path(__file__).resolve().parent
 envdata=json.loads(pathlib.Path(a.env).read_text()) if a.env else {}
 lean=a.lean or envdata.get('lean') or shutil.which('lean'); lp=a.lean_path or envdata.get('lean_path') or os.environ.get('LEAN_PATH')
 mathlib=a.mathlib or envdata.get('mathlib')
 if not lean or not lp or not mathlib: ap.error('Supply --env, or --lean, --lean-path and --mathlib')
 version=subprocess.check_output([lean,'--version'],text=True).strip()
 commit=subprocess.check_output([lean,'--githash'],text=True).strip()
 rev=subprocess.check_output(['git','-C',mathlib,'rev-parse','HEAD'],text=True).strip()
 if 'version 4.19.0' not in version or not commit.startswith(LEAN_COMMIT):
  raise SystemExit('Lean version/commit mismatch')
 if rev != MATHLIB: raise SystemExit('mathlib revision mismatch')
 lockpath=a.lock or envdata.get('benchmark_lock') or str(pathlib.Path(tempfile.gettempdir())/'replay-lean-verification.lock')
 out=root/'build'; out.mkdir(exist_ok=True)
 receipts=[]
 for name in MODULES:
  src=root/'proof'/(name+'.lean'); log=out/(name+'.log'); obj=out/(name+'.olean')
  source=src.read_text()
  if re.search(r'\b(sorry|admit|native_decide|unsafe)\b|^\s*axiom\s',source,re.M):
   raise SystemExit('Forbidden proof escape in '+src.name)
  command=[lean,'-j1','-t0','-DwarningAsError=true','-o',str(obj),str(src)]
  start=datetime.datetime.now(datetime.timezone.utc).isoformat()
  env={**os.environ,'LEAN_PATH':str(out)+os.pathsep+lp,'LEAN_NUM_THREADS':'1'}
  with open(lockpath,'a') as lock:
   fcntl.flock(lock,fcntl.LOCK_EX)
   with log.open('w') as f:
    process=subprocess.run(command,cwd=root,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=120)
   fcntl.flock(lock,fcntl.LOCK_UN)
  receipt={'source':'proof/'+src.name,'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),
   'started_utc':start,'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
   'exit_code':process.returncode,'lean_version':version,'lean_commit':commit,'mathlib_revision':rev,
   'threads':1,'trust_level':0,'warning_as_error':True,'command':['lean','-j1','-t0','-DwarningAsError=true',
    '-o','build/'+obj.name,'proof/'+src.name],'log_sha256':hashlib.sha256(log.read_bytes()).hexdigest()}
  receipts.append(receipt)
  (out/(name+'.receipt.json')).write_text(json.dumps(receipt,indent=2)+'\n')
  print(name+': exit '+str(process.returncode),flush=True)
  if process.returncode:
   dest=root/'private'/str(time.time_ns());dest.mkdir(parents=True)
   (dest/src.name).write_bytes(src.read_bytes());(dest/log.name).write_bytes(log.read_bytes())
   raise SystemExit(log.read_text())
 audit={}
 for line in (out/'AxiomAudit.log').read_text().splitlines():
  m=re.fullmatch(r"'([^']+)' depends on axioms: \[(.*)\]",line)
  if m:
   axs=[x.strip() for x in m.group(2).split(',') if x.strip()]
   if set(axs)-ALLOWED_AXIOMS: raise SystemExit('Disallowed axioms: '+line)
   audit[m.group(1)]=axs
  else:
   m=re.fullmatch(r"'([^']+)' does not depend on any axioms",line)
   if m: audit[m.group(1)]=[]
 expected=sum(1 for line in (root/'proof/AxiomAudit.lean').read_text().splitlines() if line.startswith('#print axioms '))
 if len(audit)!=expected: raise SystemExit('Incomplete axiom audit')
 result={'status':'passed','theorem_count':len(audit),'allowed_axioms':sorted(ALLOWED_AXIOMS),'theorems':audit}
 (out/'AXIOM_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n')
 (out/'COMPILER_RECEIPTS.json').write_text(json.dumps(receipts,indent=2)+'\n')
 print('Verified '+str(len(audit))+' theorem declarations; only standard axioms.',flush=True)
if __name__=='__main__':main()
