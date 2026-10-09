#!/usr/bin/env python3
"""Compile an owned source in a pinned external environment; parent holds exclusive lock."""
import argparse,datetime,fcntl,hashlib,json,os,pathlib,subprocess,sys,time
p=argparse.ArgumentParser();p.add_argument('--env',required=True);p.add_argument('--source',default='proof/FiniteLaw.lean');p.add_argument('--tag',default='check');a=p.parse_args()
r=pathlib.Path(__file__).resolve().parent;e=json.loads(pathlib.Path(a.env).read_text());s=r/a.source
(r/'build').mkdir(exist_ok=True);(r/'private').mkdir(exist_ok=True)
cmd=[e['lean'],'-j1','--trust=0','-DwarningAsError=true','-o',str(r/'build'/(s.stem+'.olean')),str(s)]
env={**os.environ,'LEAN_PATH':str(r/'build')+':'+e['lean_path'],'LEAN_NUM_THREADS':'1'}
start=datetime.datetime.now(datetime.timezone.utc).isoformat(); log=r/'private'/(a.tag+'.log')
with open(e['benchmark_lock'],'a') as lock:
 deadline=time.monotonic()+20
 while True:
  try:
   fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);break
  except BlockingIOError:
   if time.monotonic()>=deadline: print('Compilation lock busy; no compilation started.');sys.exit(75)
   time.sleep(0.5)
 with open(log,'w') as f:
  try: ret=subprocess.run(cmd,cwd=r,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=90).returncode
  except subprocess.TimeoutExpired: ret=124;f.write('\nTimed out after 90 seconds.\n')
 fcntl.flock(lock,fcntl.LOCK_UN)
receipt={'source':a.source,'sha256':hashlib.sha256(s.read_bytes()).hexdigest(),'started_utc':start,'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exit_code':ret,'lean_version':e['lean_version'],'mathlib_revision':e['mathlib_revision'],'threads':1,'trust':0,'compiler_output':'private/'+log.name,'command':cmd}
(r/'private'/(a.tag+'.json')).write_text(json.dumps(receipt,indent=2)+'\n')
print(log.read_text());print('exit_code =',ret);sys.exit(ret)
