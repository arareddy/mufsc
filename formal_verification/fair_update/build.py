#!/usr/bin/env python3
"""Offline direct Lean build. Never installs, downloads, or writes shared dependencies."""
import argparse
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

parser = argparse.ArgumentParser()
parser.add_argument('--lean', type=Path, required=True)
parser.add_argument('--mathlib', type=Path, required=True)
parser.add_argument('--lock', type=Path, required=True)
parser.add_argument('--label', default='build')
parser.add_argument('--kernel', action='store_true', help='Recheck imported modules at trust level zero')
args = parser.parse_args()
root = Path(__file__).resolve().parent
os.chdir(root)
(root / 'build').mkdir(exist_ok=True)
(root / 'logs').mkdir(exist_ok=True)
(root / 'private').mkdir(exist_ok=True)
source = root / 'proof' / 'Geometry.lean'
modules = ['FairUpdate', 'Moments', 'Geometry']
names = [ns + '.' + n for mod, ns in [('FairUpdate','FairUpdate'),('Moments','FairUpdate.Moments'),('Geometry','FairUpdate.Geometry')] for n in re.findall(r'^(?:lemma|theorem)\s+(\w+)', (root/'proof'/(mod+'.lean')).read_text(), re.M)]
audit = 'import Geometry\n\n' + '\n\n'.join('#check @' + n + '\n#print axioms ' + n for n in names) + '\n'
(root / 'proof' / 'AxiomAudit.lean').write_text(audit)
paths = [root / 'build', args.mathlib / '.lake/build/lib/lean']
paths += sorted((args.mathlib / '.lake/packages').glob('*/.lake/build/lib/lean'))
env = dict(os.environ)
env['LEAN_PATH'] = ':'.join(str(p.resolve()) for p in paths)
for k in ['LEAN_NUM_THREADS','OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS']:
    env[k] = '1'
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
receipt = dict(label=args.label, started_utc=started, source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
               single_worker=True, lock_unlinked=False, theorem_count=len(names), commands=[], results=[])
commands = [[str(args.lean), '-j1', '--root=proof', '-o', 'build/'+m+'.olean', 'proof/'+m+'.lean'] for m in modules]
commands += [[str(args.lean), '-j1', '--root=proof', 'proof/AxiomAudit.lean']]
receipt['source_hashes'] = {m: hashlib.sha256((root/'proof'/(m+'.lean')).read_bytes()).hexdigest() for m in modules}
if args.kernel:
    commands = [cmd[:1] + ['--trust=0'] + cmd[1:] for cmd in commands]
receipt['trust_level'] = 0 if args.kernel else 'Lean default'
rc = 0
for idx, cmd in enumerate(commands):
    log_path = root / 'logs' / (args.label + ('_'+modules[idx]+'_compiler.log' if idx < len(modules) else '_axioms.log'))
    with args.lock.open('a') as lock:
        deadline = time.monotonic() + 30
        while True:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    print('Shared lock busy after 30 seconds; no compilation started for this command.')
                    sys.exit(75)
                time.sleep(0.5)
        acquired = datetime.datetime.now(datetime.timezone.utc).isoformat()
        begin = time.monotonic()
        with log_path.open('w') as log:
            try:
                proc = subprocess.run(cmd, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=300)
                rc = proc.returncode
            except subprocess.TimeoutExpired:
                log.write('\nBUILD TIMEOUT after 300 seconds\n')
                rc = 124
        duration = time.monotonic() - begin
        fcntl.flock(lock, fcntl.LOCK_UN)
    receipt['commands'].append(['<LEAN>'] + cmd[1:])
    receipt['results'].append(dict(exit_code=rc, lock_acquired_utc=acquired, held_seconds=duration, log=str(log_path.relative_to(root))))
    print(log_path.read_text())
    print(f'{log_path.name}: exit {rc}; held lock {duration:.3f}s', flush=True)
    if rc:
        break
receipt['finished_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
receipt['exit_code'] = rc
(root / 'logs' / (args.label + '_receipt.json')).write_text(json.dumps(receipt, indent=2) + '\n')
private = dict(lean=str(args.lean), mathlib=str(args.mathlib), lock=str(args.lock), LEAN_PATH=env['LEAN_PATH'], commands=commands)
(root / 'private' / (args.label + '_invocation.json')).write_text(json.dumps(private, indent=2) + '\n')
sys.exit(rc)
