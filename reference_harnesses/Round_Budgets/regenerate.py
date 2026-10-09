#!/usr/bin/env python3
from pathlib import Path
import subprocess,sys,fcntl,os
W=Path(__file__).resolve().parent
for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):os.environ[k]='1'
print('Waiting for the shared benchmark lock before verification and plotting',flush=True)
with open('/private/tmp/ftf_benchmark_20260926.lock','a+') as lock:
 fcntl.flock(lock.fileno(),fcntl.LOCK_EX)
 for script in ['analyze.py','make_report.py','plot.py','finalize.py']:
  subprocess.run([sys.executable,'-B',str(W/script)],cwd=W,check=True)
 fcntl.flock(lock.fileno(),fcntl.LOCK_UN)
