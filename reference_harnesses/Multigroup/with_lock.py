"""Hold the common OS advisory lock across a single worker subprocess."""
import os,sys,time,fcntl,json,subprocess
from pathlib import Path
from datetime import datetime,timezone
LOCK='/private/tmp/ftf_benchmark_20260926.lock'

def run_locked(command,log_path,timeout=600):
    log_path=Path(log_path);log_path.parent.mkdir(parents=True,exist_ok=True)
    def record(event,**extra):
        with log_path.open('a') as f:f.write(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),'event':event,'pid':os.getpid(),**extra})+'\n')
    requested=time.perf_counter();record('waiting',lock=LOCK,command=command)
    with open(LOCK,'a+') as lock:
        fcntl.flock(lock.fileno(),fcntl.LOCK_EX)
        acquired=time.perf_counter()
        load=subprocess.run(['ps','-A','-o','pid,pcpu,comm','-r'],capture_output=True,text=True).stdout.splitlines()[:16]
        record('acquired',wait_seconds=acquired-requested,load_average=os.getloadavg(),top_cpu_processes=load)
        print('Lock acquired; running',Path(command[-1]).name,flush=True)
        try:
            completed=subprocess.run(command,timeout=timeout,env={**os.environ,**{k:'1' for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS')},'PYTHONDONTWRITEBYTECODE':'1'})
            record('worker_finished',returncode=completed.returncode)
            return completed.returncode
        finally:
            record('released',held_seconds=time.perf_counter()-acquired,load_average=os.getloadavg())
            fcntl.flock(lock.fileno(),fcntl.LOCK_UN)

if __name__=='__main__':
    if len(sys.argv)<3:raise SystemExit('with_lock.py LOG COMMAND [ARGS...]')
    raise SystemExit(run_locked(sys.argv[2:],sys.argv[1]))
