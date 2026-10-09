"""Measured local persistence wrapper; reviewed deletion method is unchanged."""
from common import *
from client_c0 import ClientC0State
from dataclasses import fields
import pickle,time

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
