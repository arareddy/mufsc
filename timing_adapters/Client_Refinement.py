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
from accounting import components,counters
MODES={'direct':'none','basic':'basic','runnerup':'runnerup'}
def train(cd,go,spec,cache=False):
 return train_full(cd,go,spec['seed'],spec['k'],spec['T'],spec['L'],gamma=spec['gamma'],fp_cfg=FixedPointConfig(spec['scale_bits'],spec['clip']),anchor_lloyd_iters=spec['anchor_lloyd_iters'],build_cache=cache)

def measured_request(method,cd,go,checkpoint,spec,path):
 gc.collect();start=time.perf_counter();departed=spec['deleted_client']
 if method=='fresh':args=({c:x for c,x in cd.items() if c!=departed},{c:g for c,g in go.items() if c!=departed})
 else:args={departed:np.arange(len(cd[departed]),dtype=np.int64)}
 prepared=time.perf_counter()
 result=train(*args,spec) if method=='fresh' else unlearn(checkpoint,args,certificate_mode=MODES[method])
 finished=time.perf_counter()
 payload=projection(result)
 encoded=(json.dumps(payload,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
 path.write_bytes(encoded);end=time.perf_counter()
 obs={'method':method,'algorithm_seconds':finished-prepared,'request_preparation_seconds':prepared-start,'output_seconds':end-finished,'request_e2e_seconds':end-start,'output_sha256':hashlib.sha256(encoded).hexdigest(),'output_bytes':len(encoded),'timing_primitives':jsonable(result['timing']),'components':components(result['timing'],finished-prepared),'work':counters(result,method,spec['n']-spec['removed_n'],spec['T'])}
 return result,payload,obs

