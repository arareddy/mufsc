"""Local paths and witness helpers; no learning arithmetic."""
from pathlib import Path
import os,sys,json,hashlib
for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):
    os.environ[name]='1'
ROOT=Path(__file__).resolve().parent
SOURCE=Path('source://ftf1d')
DATA=SOURCE/'remediation/data/p124-unique-source-v2'
PYTHON=SOURCE/'.venv/bin/python'
sys.path[:0]=[str(ROOT/'baseline/src'),str(ROOT/'baseline/experiments')]
import numpy as np
from reproducible import exact_witness,jsonable,write_json,sha256,environment_manifest

def object_hash(x):
    return hashlib.sha256(json.dumps(jsonable(x),sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def projection(result):
    return {'map_version':result['map_version'],**exact_witness(result)}

def same_array(a,b):
    a=np.asarray(a);b=np.asarray(b)
    return a.dtype==b.dtype and a.shape==b.shape and (np.array_equal(a,b) if a.dtype==object else a.tobytes()==b.tobytes())

def check_extra(a,b):
    assert a['group_sizes']==b['group_sizes']
    assert set(a['slice_results'])==set(b['slice_results'])
    for key in a['slice_results']:
        x,y=a['slice_results'][key],b['slice_results'][key]
        assert set(x)==set(y)
        for field in x:
            if isinstance(x[field],np.ndarray):assert same_array(x[field],y[field]),(key,field)
            else:assert x[field]==y[field],(key,field)
    assert a['anchor_table']['owner']==b['anchor_table']['owner']
    assert same_array(a['anchor_table']['anchors'],b['anchor_table']['anchors'])
    assert same_array(a['anchor_table']['weights'],b['anchor_table']['weights'])
