from reproduce import *
setup()
import numpy as np
import time,gc,pickle,hashlib
from train import train_full
from unlearn import unlearn
from fixedpoint import FixedPointConfig
from reproducible import jsonable,exact_witness
from client_c0 import compact_checkpoint,delete_clients
def projection(x):return {'map_version':x['map_version'],**exact_witness(x)}
from dataclasses import fields
from client_c0 import ClientC0State
from reproducible import content_hash as object_hash
def same_array(a,b):return a.shape==b.shape and a.dtype==b.dtype and a.tobytes()==b.tobytes()
def check_state(a,b):
    assert isinstance(a,ClientC0State) and isinstance(b,ClientC0State)
    for field in fields(a):
        key=field.name
        if key=='slice_results':continue
        assert getattr(a,key)==getattr(b,key),key
    assert set(a.slice_results)==set(b.slice_results)
    for key in a.slice_results:
        x,y=a.slice_results[key],b.slice_results[key]
        assert set(x)==set(y)
        for name,value in x.items():
            if isinstance(value,np.ndarray):assert same_array(value,y[name]),(key,name)
            else:assert value==y[name],(key,name)
    assert a.client_ids==tuple(sorted(a.client_counts))
    assert set(a.group_sizes)=={0,1} and min(a.group_sizes.values())>0
    counts={c:[0,0] for c in a.client_ids}
    for (c,g),summary in a.slice_results.items():
        assert c in counts and g in (0,1)
        assert sum(int(x) for x in summary['mult'])==summary['n_e']>0
        counts[c][g]=int(summary['n_e'])
        for value in summary.values():
            if isinstance(value,np.ndarray):assert not value.flags.writeable
    assert {c:tuple(v) for c,v in counts.items()}==a.client_counts
    assert {g:sum(v[g] for v in counts.values()) for g in (0,1)}==a.group_sizes

def state_hash(state):
    return object_hash({field.name:getattr(state,field.name) for field in fields(state)})

def persist(method,state,path):
    start=time.perf_counter()
    if method=='compact':blob=pickle.dumps(state,protocol=5)
    else:blob=(json.dumps({'active_client_ids':list(state)},sort_keys=True,separators=(',',':'))+'\n').encode()
    serialized=time.perf_counter()
    path.write_bytes(blob)
    written=time.perf_counter()
    loaded_blob=path.read_bytes()
    read=time.perf_counter()
    if method=='compact':loaded=pickle.loads(loaded_blob)
    else:loaded=tuple(json.loads(loaded_blob)['active_client_ids'])
    decoded=time.perf_counter()
    expected=hashlib.sha256(blob).hexdigest();actual=hashlib.sha256(loaded_blob).hexdigest()
    assert actual==expected
    if method=='compact':check_state(loaded,state)
    else:assert loaded==state and loaded==tuple(sorted(set(loaded)))
    finished=time.perf_counter()
    return loaded,{'serialization_seconds':serialized-start,'write_seconds':written-serialized,
      'read_seconds':read-written,'deserialize_seconds':decoded-read,'reload_validation_seconds':finished-decoded,
      'persistence_seconds':finished-start,'state_bytes':len(blob),'state_sha256':expected,'reload_validated':True,
      'storage_contract':'ordinary buffered local write/close/read; no fsync; trusted bytes'}

def train(cd,go,spec,cache=False):
 return train_full(cd,go,spec['seed'],spec['k'],0,spec['L'],gamma=spec['gamma'],fp_cfg=FixedPointConfig(spec['scale_bits'],spec['clip']),anchor_lloyd_iters=spec['anchor_lloyd_iters'],build_cache=cache)

def measured(method,cd,go,current,spec,step,path):
 gc.collect();start=time.perf_counter();c=step['client_id']
 if method=='fresh':
  active=tuple(x for x in current if x!=c)
  assert c in current
  retained={x:cd[x] for x in active};groups={x:go[x] for x in active}
 else:depart=[c]
 prepared=time.perf_counter()
 if method=='fresh':result=train(retained,groups,spec);next_state=active
 else:result,next_state=delete_clients(current,depart)
 finished=time.perf_counter()
 blob=(json.dumps(projection(result),sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
 path.write_bytes(blob);end=time.perf_counter()
 row={'request_preparation_seconds':prepared-start,'algorithm_seconds':finished-prepared,'model_output_seconds':end-finished,'request_seconds':end-start,'model_output_bytes':len(blob),'model_output_sha256':hashlib.sha256(blob).hexdigest()}
 loaded,storage=persist(method,next_state,path.parent/(f'{method}_current.'+('pkl' if method=='compact' else 'json')))
 row.update(storage);row['operational_seconds']=row['request_seconds']+row['persistence_seconds']
 return result,next_state,loaded,row

