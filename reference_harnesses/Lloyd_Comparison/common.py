import os,sys,json,hashlib
from pathlib import Path
for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):os.environ[k]='1'
W=Path(__file__).resolve().parent
D=Path('source://ftf1d');SRC=D/'corrected_project';A=Path('study://Round_Budgets');B=Path('study://Client_Deletion');Q=Path('study://Group_Quality');PY=D/'.venv/bin/python'
sys.path[:0]=[str(SRC/'src'),str(SRC/'experiments')]
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def load(p):return json.loads(Path(p).read_text())
def dump(p,x):Path(p).write_text(json.dumps(x,sort_keys=True,indent=2)+'\n')
def objsha(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def bindings():
 return {str(p):sha(p) for p in [W/'PROTOCOL.md',W/'FROZEN_GRID.json',W/'INPUT_MANIFEST.json',W/'SOURCE_MANIFEST.json']}
def verify_sources():
 for r in load(W/'SOURCE_MANIFEST.json')['files']:assert sha(r['path'])==r['sha256'],r['path']
def verify_file(p):
 r=next(r for r in load(W/'INPUT_MANIFEST.json')['files'] if r['path']==str(p));assert sha(p)==r['sha256'];return r['sha256']
