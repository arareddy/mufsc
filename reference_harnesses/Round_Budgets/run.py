#!/usr/bin/env python3
"""One advisory-locked batch at a time; safe resume of completed immutable batches."""
import os
for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):os.environ[k]='1'
import sys,json,hashlib,time,subprocess,fcntl,traceback,argparse
from pathlib import Path
W=Path(__file__).resolve().parent
sys.path[:0]=[str(W/'source/src'),str(W/'source/experiments')]
from reproducible import sha256,write_json
ap=argparse.ArgumentParser();ap.add_argument('--limit',type=int);a=ap.parse_args()
run=(W/'RUN_ID').read_text().strip();R=W/'runs'/run;R.mkdir(parents=True,exist_ok=True)
inputs=json.loads((W/'input_manifest.json').read_text());methods=['fresh','none','basic','runnerup']
manifest={str(p.relative_to(W)):sha256(p) for p in [W/'worker.py',W/'run.py',W/'PROTOCOL.md',W/'input_manifest.json',W/'environment.json',*sorted((W/'source').rglob('*.py')),W/'source/TRAINING_MAP.md']}
if (R/'execution_manifest.json').exists():assert json.loads((R/'execution_manifest.json').read_text())==manifest,'Code/protocol changed: new run required'
else:write_json(R/'execution_manifest.json',manifest)
for inp in inputs:assert sha256(inp['input'])==inp['input_sha256'] and sha256(inp['request'])==inp['request_sha256']
def load(p):return json.loads(p.read_text())
def prefix(old,T):return dict(trajectory=old['trajectory'][:T+1],final_centers=old['trajectory'][T],per_round_stats=old['per_round_stats'][:T])
def load_snapshot():
 try:ps=subprocess.run(['ps','-Ao','pid,pcpu,comm','-r'],capture_output=True,text=True).stdout.splitlines()[:16]
 except Exception as e:ps=[str(e)]
 return dict(unix=time.time(),loadavg=os.getloadavg(),processes=ps)
def worker(d,inp,T,m,name,quality=False):
 out=d/(name+'.json');cmd=[sys.executable,'-B',str(W/'worker.py'),'--input',inp['input'],'--checkpoint',str(d/'checkpoint.pkl'),'--T',str(T),'--method',m,'--output',str(out),'--launched',str(time.time())]
 if quality:cmd+=['--quality']
 with (d/(name+'.log')).open('w') as log:result=subprocess.run(cmd,cwd=W,stdout=log,stderr=subprocess.STDOUT)
 if result.returncode:raise RuntimeError(f'{name} exit {result.returncode}; see log')
 return load(out),load(out.with_suffix('.witness.json'))
completed=0
for inp in inputs:
 for T in range(3):
  key=f"{inp['dataset']}_s{inp['settings']['seed']}_T{T}";d=R/key;d.mkdir(exist_ok=True)
  if (d/'complete.json').exists():
   for name,h in load(d/'complete.json')['files'].items():assert sha256(d/name)==h
   print('RESUME VERIFIED',key,flush=True);continue
  if any(d.glob('*.json')):raise RuntimeError(f'Partial batch {d}; preserve it and use a fresh run ID or explicitly audit before resuming')
  print('QUEUED',key,flush=True);queued=time.time()
  with open('/private/tmp/ftf_benchmark_20260926.lock','a+') as lock:
   fcntl.flock(lock.fileno(),fcntl.LOCK_EX)
   before=load_snapshot();wait=time.time()-queued
   print('LOCK ACQUIRED',key,'wait_seconds',round(wait,2),flush=True)
   write_json(d/'batch_start.json',dict(input=inp['input'],input_sha256=inp['input_sha256'],request_sha256=inp['request_sha256'],T=T,queue_seconds=wait,load_before=before))
   try:
    cp,cw=worker(d,inp,T,'checkpoint','checkpoint')
    olddir=Path(inp['input']).parent
    assert cw==prefix(load(olddir/'checkpoint.json')['witness'],T),'Checkpoint prefix mismatch'
    offset=(['adult','bank','credit'].index(inp['dataset'])+inp['trial']+T)%4
    gates={};order=methods[offset:]+methods[:offset]
    for m in order:gates[m]=worker(d,inp,T,m,'gate_'+m,True)
    fresh=gates['fresh'][1];fq=gates['fresh'][0]['quality']['exact'];checks=[]
    for m in methods:
     meta,wi=gates[m]
     checks.append(dict(method=m,full_witness_equal=wi==fresh,exact_quality_equal=meta['quality']['exact']==fq,accepted_T15_prefix_equal=wi==prefix(load(olddir/(m+'.json'))['witness'],T),trajectory_length=len(wi['trajectory']),statistics_length=len(wi['per_round_stats'])))
    assert all(c['full_witness_equal'] and c['exact_quality_equal'] and c['accepted_T15_prefix_equal'] and c['trajectory_length']==T+1 and c['statistics_length']==T for c in checks)
    write_json(d/'correctness.json',dict(status='PASS',checks=checks,checkpoint_prefix_equal=True,quality=gates['fresh'][0]['quality']))
    for rep in range(4):
     shift=(offset+rep)%4;order=methods[shift:]+methods[:shift]
     write_json(d/f'order_r{rep}.json',order)
     for position,m in enumerate(order):
      meta,wi=worker(d,inp,T,m,f'r{rep}_{m}')
      equal=wi==fresh
      write_json(d/f'r{rep}_{m}.verification.json',dict(status='PASS' if equal else 'FAIL',full_witness_equal=equal,repetition=rep,position=position,gate_witness_sha256=gates[m][0]['witness_sha256'],measured_witness_sha256=meta['witness_sha256']))
      assert equal,'Measured output differs from gate'
    write_json(d/'batch_end.json',dict(load_after=load_snapshot(),seconds=time.time()-before['unix']))
    files={p.name:sha256(p) for p in d.iterdir() if p.is_file()}
    write_json(d/'complete.json',dict(status='PASS',setting=key,unique_method_keys=4,timing_observations=16,replay_comparisons=3,files=files))
    completed+=1;print('COMPLETE',key,'batch_seconds',round(time.time()-before['unix'],2),flush=True)
   except Exception:
    write_json(d/'failure.json',dict(status='FAIL',traceback=traceback.format_exc(),load=load_snapshot()));raise
   finally:fcntl.flock(lock.fileno(),fcntl.LOCK_UN)
  if a.limit and completed>=a.limit:sys.exit(0)
  time.sleep(1)
print('CAMPAIGN COMPLETE',run,flush=True)
