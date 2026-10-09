import os,sys,fcntl,json,time,subprocess,datetime,pathlib
W=pathlib.Path(__file__).resolve().parent
for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):os.environ[k]='1'
os.environ['PYTHONDONTWRITEBYTECODE']='1';os.environ['MPLCONFIGDIR']=str(W/'.mplconfig')
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def emit(x):
 with (W/'LOCK_RECEIPTS.jsonl').open('a') as f:f.write(json.dumps(x)+'\n')
def load():
 return {'loadavg':os.getloadavg(),'top_cpu':subprocess.run(['ps','-A','-o','pid,pcpu,comm','-r'],capture_output=True,text=True).stdout.splitlines()[:9]}
start=time.monotonic();batch=utc();emit(dict(event='queued',batch=batch,command=sys.argv[1:],utc=utc(),pid=os.getpid()))
print('Waiting for shared lock',flush=True)
with open('/private/tmp/ftf_benchmark_20260926.lock','a+') as f:
 fcntl.flock(f,fcntl.LOCK_EX);held=time.monotonic();emit(dict(event='acquired',batch=batch,utc=utc(),wait_seconds=held-start,**load()));print('Shared lock acquired',flush=True)
 try:r=subprocess.run(sys.argv[1:]);code=r.returncode
 except BaseException as e:code=1;emit(dict(event='exception',batch=batch,error=repr(e)));raise
 finally:
  emit(dict(event='released',batch=batch,utc=utc(),held_seconds=time.monotonic()-held,exit_code=locals().get('code',1),**load()));fcntl.flock(f,fcntl.LOCK_UN)
sys.exit(code)
