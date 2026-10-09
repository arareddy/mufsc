"""Resume only completed hash-matching cases; never overwrite incomplete attempts."""
from common import *
import subprocess,datetime
verify_sources();grid=load(W/'FROZEN_GRID.json');done=[]
for c in grid['cases']:
 out=W/'runs/matched-start-v1'/c['case_id'];complete=out/'complete.json'
 if complete.exists():
  rr=load(complete);assert rr['status']=='PASS' and rr['output_sha256']==sha(out/'outputs.json') and rr['source_bindings']==bindings();done.append(c['case_id']);continue
 assert not out.exists(),'Incomplete attempt retained; diagnose before any new attempt'
 cmd=[str(PY),'-B',str(W/'with_lock.py'),str(PY),'-B',str(W/'worker.py'),c['case_id']]
 rc=subprocess.run(cmd).returncode
 if rc:dump(W/'PROGRESS.json',dict(status='FAILED',failed_case=c['case_id'],completed=done));sys.exit(rc)
 done.append(c['case_id']);dump(W/'PROGRESS.json',dict(status='COMPLETE' if len(done)==30 else 'RUNNING',completed=done,expected=30,utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
print('COMPLETE: 30 cases',flush=True)
