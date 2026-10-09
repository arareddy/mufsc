#!/usr/bin/env python3
import argparse, datetime, fcntl, hashlib, json, os, pathlib, subprocess, sys
p=argparse.ArgumentParser();p.add_argument('--env',required=True);p.add_argument('source');p.add_argument('--name',default='check');a=p.parse_args()
r=pathlib.Path(__file__).resolve().parent;e=json.loads(pathlib.Path(a.env).read_text());s=r/a.source
(r/'build').mkdir(exist_ok=True);(r/'private').mkdir(exist_ok=True);(r/'logs').mkdir(exist_ok=True)
cmd=[e['lean'],'-j1','--trust=0','-o',str(r/'build'/(s.stem+'.olean')),str(s)]
env={**os.environ,'LEAN_PATH':str(r/'build')+':'+e['lean_path'],'LEAN_NUM_THREADS':'1'}
start=datetime.datetime.now(datetime.timezone.utc).isoformat()
with open(e['benchmark_lock'],'a') as lk:
 fcntl.flock(lk,fcntl.LOCK_EX)
 try:
  result=subprocess.run(cmd,cwd=r,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=90)
 finally: fcntl.flock(lk,fcntl.LOCK_UN)
log=result.stdout
(r/'private'/(a.name+'.log')).write_text(log)
portable=log.replace(str(r),'BUNDLE').replace(str(pathlib.Path(e['lean']).parent.parent),'LEAN').replace(e['mathlib'],'MATHLIB')
(r/'logs'/(a.name+'.log')).write_text(portable)
receipt=dict(source=a.source,sha256=hashlib.sha256(s.read_bytes()).hexdigest(),started_utc=start,finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),exit_code=result.returncode,lean_version=e['lean_version'],mathlib_revision=e['mathlib_revision'],trust=0,threads=1,compiler_output='logs/'+a.name+'.log')
(r/'logs'/(a.name+'.json')).write_text(json.dumps(receipt,indent=2)+'\n')
print(portable);print(json.dumps(receipt,indent=2));sys.exit(result.returncode)
