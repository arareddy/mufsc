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
sys.path.insert(0,str(ROOT/'variants/multigroup'))
import multigroup as mg
from common import projection,jsonbytes
def output_call(method,data,groups,checkpoint,compact,spec,path):
    gc.collect();begin=time.perf_counter();gone=spec['deleted_client']
    if method=='fresh':args=({c:x for c,x in data.items() if c!=gone},{c:g for c,g in groups.items() if c!=gone})
    else:args=[gone]
    ready=time.perf_counter()
    if method=='fresh':out=mg.train(*args,spec['seed'],checkpoint['cfg'])
    elif method=='direct':out=mg.direct(checkpoint,args)
    else:out,_=mg.delete_c0(compact,args)
    finish=time.perf_counter();blob=jsonbytes(projection(out));path.write_bytes(blob);end=time.perf_counter()
    return out,{'preparation_seconds':ready-begin,'algorithm_seconds':finish-ready,'output_seconds':end-finish,'request_seconds':end-begin,
        'output_bytes':len(blob),'output_sha256':hashlib.sha256(blob).hexdigest(),'components':out['timing']}

