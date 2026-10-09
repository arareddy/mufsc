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
def train(cd,go,spec,T=0,cache=False):
    return train_full(cd,go,spec['seed'],spec['k'],T,spec['L'],gamma=spec['gamma'],fp_cfg=FixedPointConfig(spec['scale_bits'],spec['clip']),anchor_lloyd_iters=spec['anchor_lloyd_iters'],build_cache=cache)

def components(result,method,elapsed):
    t=result['timing']
    if method=='fast':
        named=dict(t)
    else:
        named={'phase1_client_seconds':sum(t['phase1_client'].values()),'server_seconds':t['phase1_server'],'encoding_seconds':t.get('encoding',0.0),'input_materialization_seconds':t.get('input_materialization',0.0),'cache_construction_seconds':t.get('cache_construction',0.0)}
    named['other_algorithm_seconds']=elapsed-sum(named.values())
    return named

def measured_request(method,cd,go,checkpoint,state,spec,destination):
    gc.collect()
    start=time.perf_counter()
    departed=spec['deleted_client']
    if method=='fresh':
        retained={c:x for c,x in cd.items() if c!=departed}
        groups={c:g for c,g in go.items() if c!=departed}
        args=(retained,groups)
    elif method=='direct':args={departed:np.arange(len(cd[departed]),dtype=np.int64)}
    else:args=[departed]
    prepared=time.perf_counter()
    if method=='fresh':result=train(*args,spec)
    elif method=='direct':result=unlearn(checkpoint,args,certificate_mode='none')
    else:result,next_state=delete_clients(state,args)
    finished=time.perf_counter()
    payload=projection(result)
    # Every method has identical bytes once correctness passes. No timing metadata in output.
    encoded=(json.dumps(payload,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
    destination.write_bytes(encoded)
    end=time.perf_counter()
    row={'method':method,'request_preparation_seconds':prepared-start,'algorithm_seconds':finished-prepared,'output_seconds':end-finished,'request_e2e_seconds':end-start,'output_bytes':len(encoded),'output_sha256':hashlib.sha256(encoded).hexdigest(),'components':components(result,method,finished-prepared)}
    return result,row

