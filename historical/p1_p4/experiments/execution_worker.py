#!/usr/bin/env python3
"""One isolated method process. Called only by the gated run orchestrator."""
from __future__ import annotations
import os
for thread_variable in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):
    os.environ[thread_variable]='1'
import argparse
import gc
import json
from pathlib import Path
import pickle
import resource
import sys
import time
import numpy as np

sys.path[:0] = [str(Path(__file__).resolve().parents[1]/'src'), str(Path(__file__).resolve().parent)]
from reproducible import exact_witness, jsonable, array_witness, write_json, require_gate, sha256
from fixedpoint import FixedPointConfig, represented_clients
from objective import fair_objective
from timing import totals
from train import train_full
from unlearn import unlearn
from p2_core_benchmark import apply_removal


def quality(cd, go, centers):
    keys=sorted(cd)
    X=np.concatenate([cd[c] for c in keys])
    g=np.concatenate([go[c] for c in keys])
    pa,pb,G,Phi=fair_objective(X,g,centers,return_exact=True)
    return dict(Phi_A=float(pa),Phi_B=float(pb),G=float(G),Phi=float(Phi),
                exact={k: {'numerator':v.numerator,'denominator':v.denominator} for k,v in zip(('Phi_A','Phi_B','G','Phi'),(pa,pb,G,Phi))},
                scope='one fixed represented X; binary group-normalized squared Euclidean cost')


def save_pickle(path, value):
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+f'.{os.getpid()}.tmp')
    with tmp.open('wb') as stream:
        pickle.dump(value,stream,protocol=5)
    os.replace(tmp,path)


def basic_metadata(result, elapsed):
    timings=result.get('timing',{})
    derived=totals(timings) if timings else {}
    return dict(algorithm_elapsed_seconds=elapsed,timing_primitives=jsonable(timings),
                timing_totals=jsonable(derived),
                modeled_client_plus_server_seconds=derived.get('wall_total_parallel'),
                elapsed_scope='serial measured method call; no network traffic',
                diagnostics=jsonable(result.get('diagnostics',{})),
                cert_log=jsonable(result.get('cert_log',[])),
                abandonment_round=result.get('abandonment_round'),
                cache_valid=result.get('cache_valid',False))


def deletion_worker(args):
    require_gate(args.gate)
    start=time.perf_counter()
    with Path(args.input).open('rb') as stream:
        bundle=pickle.load(stream)
    input_loading=time.perf_counter()-start
    cd,go=bundle['client_data'],bundle['group_of']
    settings=bundle['settings']
    fp=FixedPointConfig(scale_bits=settings['scale_bits'],clip=settings['clip'])
    removed={int(c):np.asarray(v,dtype=np.int64) for c,v in bundle.get('removed',{}).items()}
    checkpoint_loading=0.0
    if args.method=='checkpoint':
        gc.collect(); start=time.perf_counter()
        result=train_full(cd,go,settings['seed'],settings['k'],settings['T'],settings['L'],
                          gamma=settings.get('gamma',0.0),fp_cfg=fp,anchor_lloyd_iters=0,build_cache=True)
        elapsed=time.perf_counter()-start
        start=time.perf_counter(); save_pickle(args.checkpoint,result); output=time.perf_counter()-start
        metadata=dict(method='checkpoint',process_id=os.getpid(),**basic_metadata(result,elapsed),
                      input_loading_seconds=input_loading,checkpoint_output_seconds=output,
                      checkpoint_bytes=Path(args.checkpoint).stat().st_size,
                      checkpoint_sha256=sha256(args.checkpoint),witness=exact_witness(result),
                      slice_results=jsonable(result.get('slice_results',{})),
                      anchor_table=jsonable(result.get('anchor_table',{})))
    else:
        start=time.perf_counter(); retained,groups=apply_removal(cd,go,removed); materialization=time.perf_counter()-start
        if args.method=='fresh':
            gc.collect(); start=time.perf_counter()
            result=train_full(retained,groups,settings['seed'],settings['k'],settings['T'],settings['L'],
                              gamma=settings.get('gamma',0.0),fp_cfg=fp,anchor_lloyd_iters=0,build_cache=False)
            elapsed=time.perf_counter()-start
        else:
            start=time.perf_counter()
            with Path(args.checkpoint).open('rb') as stream:
                checkpoint=pickle.load(stream)
            checkpoint_loading=time.perf_counter()-start
            gc.collect(); start=time.perf_counter()
            result=unlearn(checkpoint,removed,certificate_mode=args.method)
            elapsed=time.perf_counter()-start
        # The caller's deletion masking acts on the same pre-encoded dataset;
        # explicitly represent quality inputs using the frozen clip/scale too.
        start=time.perf_counter(); fixed,_=represented_clients(retained,fp); quality_encoding=time.perf_counter()-start
        start=time.perf_counter(); scored=quality(fixed,groups,result['final_centers']); quality_time=time.perf_counter()-start
        metadata=dict(method=args.method,process_id=os.getpid(),**basic_metadata(result,elapsed),
                      input_loading_seconds=input_loading,checkpoint_loading_seconds=checkpoint_loading,
                      retained_input_materialization_seconds=materialization,
                      quality_encoding_seconds=quality_encoding,quality_evaluation_seconds=quality_time,
                      witness=exact_witness(result),quality=scored)
    metadata['max_rss_native']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    metadata['max_rss_unit']='bytes' if sys.platform=='darwin' else 'KiB'
    # Every measured method persists the same witness schema. Archive/output
    # time is outside algorithm time and charged identically in E2E views.
    start=time.perf_counter(); write_json(args.output,metadata); output_time=time.perf_counter()-start
    receipt=dict(artifact=Path(args.output).name,sha256=sha256(args.output),
                 output_bytes=Path(args.output).stat().st_size,output_serialization_seconds=output_time,
                 comparable_end_to_end_seconds=elapsed+input_loading+checkpoint_loading+output_time+
                    metadata.get('retained_input_materialization_seconds',0.0))
    write_json(Path(args.output).with_suffix('.receipt.json'),receipt)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--input',required=True);ap.add_argument('--checkpoint',required=True)
    ap.add_argument('--output',required=True);ap.add_argument('--method',choices=['checkpoint','fresh','none','basic','runnerup'],required=True)
    ap.add_argument('--gate')
    deletion_worker(ap.parse_args())

if __name__=='__main__':
    main()
