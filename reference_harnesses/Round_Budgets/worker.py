#!/usr/bin/env python3
import os
for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):os.environ[k]='1'
import sys,time,json,pickle,gc,argparse,resource
from pathlib import Path
W=Path(__file__).resolve().parent
sys.path[:0]=[str(W/'source/src'),str(W/'source/experiments')]
import numpy as np
from reproducible import exact_witness,write_json,sha256,require_gate
from fixedpoint import FixedPointConfig,represented_clients
from train import train_full
from unlearn import unlearn
from timing import totals
from execution_worker import quality,save_pickle
from p2_core_benchmark import apply_removal
ap=argparse.ArgumentParser();ap.add_argument('--input',required=True);ap.add_argument('--checkpoint',required=True);ap.add_argument('--output',required=True);ap.add_argument('--T',type=int,required=True);ap.add_argument('--method',required=True);ap.add_argument('--quality',action='store_true');ap.add_argument('--launched',type=float,required=True);a=ap.parse_args()
require_gate('source://ftf1d/remediation/evidence/corrected_map_gate.json')
ready=time.time(); start=time.perf_counter()
t=start
with open(a.input,'rb') as f:b=pickle.load(f)
load=time.perf_counter()-t
s=dict(b['settings']);s['T']=a.T
fp=FixedPointConfig(scale_bits=s['scale_bits'],clip=s['clip'])
rm={int(c):np.asarray(v,dtype=np.int64) for c,v in b['removed'].items()}
materialization=cp_load=0.0
if a.method=='checkpoint':cd,go=b['client_data'],b['group_of']
else:
 t=time.perf_counter();cd,go=apply_removal(b['client_data'],b['group_of'],rm);materialization=time.perf_counter()-t
if a.method not in ['fresh','checkpoint']:
 t=time.perf_counter()
 with open(a.checkpoint,'rb') as f:cp=pickle.load(f)
 cp_load=time.perf_counter()-t
 assert cp['T']==a.T
for_gc=time.perf_counter();gc.collect();gc_time=time.perf_counter()-for_gc
t=time.perf_counter()
if a.method in ['fresh','checkpoint']:
 result=train_full(cd,go,s['seed'],s['k'],s['T'],s['L'],gamma=s['gamma'],fp_cfg=fp,anchor_lloyd_iters=0,build_cache=a.method=='checkpoint')
else:result=unlearn(cp,rm,certificate_mode=a.method)
algorithm=time.perf_counter()-t
cp_write=0.0
if a.method=='checkpoint':
 t=time.perf_counter();save_pickle(a.checkpoint,result);cp_write=time.perf_counter()-t
# Identical numerical payload schema for all request methods, at same budget.
t=time.perf_counter();witness=exact_witness(result);witness_build=time.perf_counter()-t
payload=Path(a.output).with_suffix('.witness.json')
t=time.perf_counter();write_json(payload,witness);output=time.perf_counter()-t
request=time.perf_counter()-start
quality_encode=quality_seconds=0.;score=None
if a.quality and a.method!='checkpoint':
 t=time.perf_counter();fixed,_=represented_clients(cd,fp);quality_encode=time.perf_counter()-t
 t=time.perf_counter();score=quality(fixed,go,result['final_centers']);quality_seconds=time.perf_counter()-t
pr=result['timing'];diag=result.get('diagnostics',[])
meta=dict(method=a.method,T=a.T,seed=s['seed'],dataset=s['dataset'],pid=os.getpid(),algorithm_seconds=algorithm,request_seconds=request,input_loading_seconds=load,retained_materialization_seconds=materialization,checkpoint_loading_seconds=cp_load,gc_seconds=gc_time,witness_construction_seconds=witness_build,output_serialization_seconds=output,checkpoint_output_seconds=cp_write,startup_seconds=ready-a.launched,cold_launch_request_seconds=request+ready-a.launched,quality_encoding_seconds=quality_encode,quality_seconds=quality_seconds,quality=score,timing_primitives=pr,timing_totals=totals(pr),diagnostics=diag,cache_valid=result.get('cache_valid'),abandonment_round=result.get('abandonment_round'),witness_path=payload.name,witness_sha256=sha256(payload),output_bytes=payload.stat().st_size,rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,started_unix=ready,finished_unix=time.time())
if a.method=='checkpoint':meta.update(checkpoint_bytes=Path(a.checkpoint).stat().st_size,checkpoint_sha256=sha256(a.checkpoint))
write_json(a.output,meta)
