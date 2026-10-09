#!/usr/bin/env python3
"""Check this proof with the separately installed pinned shared environment."""
import argparse, datetime, fcntl, hashlib, json, os, pathlib, subprocess
ap=argparse.ArgumentParser()
ap.add_argument('--env',required=True,help='Path to the shared ENV_READY.json')
ap.add_argument('--source',default='MatchedBudget.lean')
ap.add_argument('--log',default='build/lean.stdout.log')
a=ap.parse_args()
r=pathlib.Path(__file__).resolve().parent
e=json.loads(pathlib.Path(a.env).read_text())
source=r/a.source
out=r/'build'; out.mkdir(exist_ok=True)
log=r/a.log; log.parent.mkdir(parents=True,exist_ok=True)
cmd=[e['lean'],'-j1','-DwarningAsError=true','-o',str(out/(source.stem+'.olean')),str(source)]
env={**os.environ,'LEAN_PATH':str(out)+':'+e['lean_path'],'LEAN_NUM_THREADS':'1'}
started=datetime.datetime.now(datetime.timezone.utc).isoformat()
with open(e['benchmark_lock'],'a') as lock, open(log,'w') as f:
 fcntl.flock(lock,fcntl.LOCK_EX)
 p=subprocess.run(cmd,cwd=r,env=env,stdout=f,stderr=subprocess.STDOUT)
 fcntl.flock(lock,fcntl.LOCK_UN)
receipt={'source':str(source.relative_to(r)),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'started_utc':started,'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exit_code':p.returncode,'lean_version':e['lean_version'],'threads':1,'compiler_output':str(log.relative_to(r))}
(out/(source.stem+'.receipt.json')).write_text(json.dumps(receipt,indent=2)+'\n')
print(log.read_text()); print(json.dumps(receipt,indent=2))
raise SystemExit(p.returncode)
