#!/usr/bin/env python3
"""Parent-owned POSIX advisory lock; serial CPU child, never unlink lock file."""
import argparse,fcntl,subprocess,os,tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--lock',type=Path,default=Path(tempfile.gettempdir())/'ftf-review-benchmark.lock');p.add_argument('command',nargs=argparse.REMAINDER);a=p.parse_args();cmd=a.command
if cmd and cmd[0]=='--':cmd=cmd[1:]
if not cmd:p.error('provide a command after --')
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):env[key]='1'
with a.lock.open('a') as f:
 fcntl.flock(f,fcntl.LOCK_EX)
 try:status=subprocess.run(cmd,env=env).returncode
 finally:fcntl.flock(f,fcntl.LOCK_UN)
raise SystemExit(status)
