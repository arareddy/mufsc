"""Local provenance/serialization helpers. No learning or solver arithmetic."""
from pathlib import Path
import os,sys,json,hashlib
from fractions import Fraction
from datetime import datetime,timezone
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):
    os.environ[key]='1'
os.environ['PYTHONDONTWRITEBYTECODE']='1'
ROOT=Path(__file__).resolve().parent
SOURCE=Path('source://ftf1d')
ACS=SOURCE/'remediation/p3/data/acs2018-ftf1-p3-v1'
POP=ACS/'n100000_C10'
PYTHON=SOURCE/'.venv/bin/python'
sys.path.insert(0,str(ROOT/'baseline/src'))
import numpy as np

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()

def utc():return datetime.now(timezone.utc).isoformat()

def simple(x):
    if isinstance(x,Fraction):return str(x)
    if isinstance(x,np.ndarray):return simple(x.tolist())
    if isinstance(x,np.generic):return x.item()
    if isinstance(x,Path):return str(x)
    if isinstance(x,dict):return {str(k):simple(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)):return [simple(v) for v in x]
    return x

def jsonbytes(x):return (json.dumps(simple(x),sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()

def objhash(x):return hashlib.sha256(jsonbytes(x)).hexdigest()

def write_json(p,x,immutable=False):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    data=jsonbytes(x)
    if immutable and p.exists() and p.read_bytes()!=data:raise RuntimeError('refuse changed frozen file '+str(p))
    p.write_bytes(data)

def array_witness(a):
    a=np.asarray(a,dtype='<f8',order='C')
    return {'shape':list(a.shape),'dtype':'<f8','bytes_hex':a.tobytes().hex(),'float_hex':[float(x).hex() for x in a.flat]}

def projection(out):
    return {'map_version':out['map_version'],'trajectory':[array_witness(c) for c in out['trajectory']],
            'final_centers':array_witness(out['final_centers']),'per_round_stats':out['per_round_stats']}

def extra_witness(out):
    return {'group_sizes':out['group_sizes'],'client_ids':out['client_ids'],
            'summaries':[{**{'owner':key},**{k:array_witness(v) if isinstance(v,np.ndarray) and v.dtype.kind=='f' else simple(v) for k,v in s.items()}} for key,s in sorted(out['slice_results'].items())],
            'owners':out['anchor_table']['owner'],'anchors':array_witness(out['anchor_table']['anchors']),
            'weights':[str(w) for w in out['anchor_table']['weights']]}

def load_population(verify=True):
    frozen=json.loads((ROOT/'INPUTS.json').read_text())
    if verify:
        for f in frozen['files']:
            if sha(f['path'])!=f['sha256']:raise RuntimeError('input hash mismatch '+f['path'])
    x=np.load(POP/'standardized_X.npy',mmap_mode='r');off=np.load(POP/'client_offsets.npy',mmap_mode='r')
    tr=json.loads((ACS/'transform.json').read_text());j=tr['feature_names'].index('RAC1P')
    levels=(np.arange(1,10,dtype=np.float64)-tr['feature_mean'][j])/tr['feature_std'][j]
    group=np.full(len(x),-1,dtype=np.int64)
    for g,level in enumerate(levels):group[x[:,j]==level]=g
    if np.any(group<0):raise RuntimeError('unmatched race category')
    if hashlib.sha256(group.astype('<i8').tobytes()).hexdigest()!=frozen['race_membership_sha256']:raise RuntimeError('label alignment changed')
    return {c:x[int(off[c]):int(off[c+1])] for c in range(len(off)-1)}, {c:group[int(off[c]):int(off[c+1])] for c in range(len(off)-1)}
