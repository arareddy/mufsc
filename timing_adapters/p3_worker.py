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

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'core/src'), str(ROOT/'core/experiments')]
from reproducible import exact_witness, jsonable, array_witness, write_json, require_gate, sha256
from fixedpoint import FixedPointConfig, represented_clients
from objective import fair_objective
from timing import totals
from train import train_full
from unlearn import unlearn
from p2_core_benchmark import apply_removal
from reproducible import environment_manifest, content_hash


class Observer:
    """Count real production calls, without replacing numerical decisions.

    The small Python observer overhead is inside every method's measured call.
    Distance enclosures and exact ambiguity evaluations are separate counters.
    Local/server initialization distance work is outside these Phase-II counts.
    """
    def __init__(self):
        self.rounds=[]; self.current=self.empty(); self.server=[]; self.active=False
        import train, unlearn, assignment, splitgroup
        original_assign=assignment.assign_all
        original_bounds=assignment.squared_bounds
        original_exact=assignment.squared_exact
        def bounds(X,C):
            if self.active:
                self.current['distance_enclosure_pairs'] += int(np.broadcast_shapes(X.shape[:-1],C.shape[:-1])[0] * C.shape[-2])
            return original_bounds(X,C)
        def exact(x,c):
            if self.active:self.current['exact_distance_fallback_evaluations']+=1
            return original_exact(x,c)
        def assign(X,C):
            self.current['assignment_calls']+=1
            self.current['point_assignments']+=len(X)
            self.current['candidate_center_pairs']+=len(X)*len(C)
            self.active=True
            try:return original_assign(X,C)
            finally:self.active=False
        def update(original):
            def wrapped(*args,**kwargs):
                self.rounds.append(dict(round=len(self.rounds),**self.current));self.current=self.empty()
                return original(*args,**kwargs)
            return wrapped
        train.assign_all=unlearn.assign_all=assign
        assignment.squared_bounds=bounds;assignment.squared_exact=exact
        train.guarded_fair_update=update(train.guarded_fair_update)
        unlearn.guarded_fair_update=update(unlearn.guarded_fair_update)
        original_seed=splitgroup.weighted_kmeanspp
        def server_seed(*args,**kwargs):
            idx=original_seed(*args,**kwargs);self.server.append(idx.tolist());return idx
        splitgroup.weighted_kmeanspp=server_seed

    @staticmethod
    def empty():
        return dict(assignment_calls=0,point_assignments=0,candidate_center_pairs=0,
                    distance_enclosure_pairs=0,exact_distance_fallback_evaluations=0)


def initializer(result, observer, cd, go, removed, is_checkpoint):
    slices=[]
    for (c,g),values in sorted(result['slice_results'].items()):
        original=np.arange(len(cd[c]),dtype=np.int64)
        keep=np.ones(len(original),dtype=bool)
        if not is_checkpoint:keep[removed.get(c,[])]=False
        group_positions=original[keep & (go[c]==g)]
        selected=np.asarray(values['selected_idx'],dtype=np.int64)
        slices.append(dict(client_id=c,group=g,n_e=values['n_e'],k_e=values['k_e'],
                           selected_slice_indices=selected.tolist(),
                           selected_original_client_rows=group_positions[selected].tolist(),
                           anchors=array_witness(values['anchors']),reps=array_witness(values['reps']),
                           multiplicities=values['mult'].tolist()))
    table=result['anchor_table']
    return dict(slices=slices,group_sizes=jsonable(result['group_sizes']),
                anchor_table=dict(anchors=array_witness(table['anchors']),
                                  weights=jsonable(table['weights']),owner=jsonable(table['owner'])),
                server_selected_idx=observer.server[0],
                C0=array_witness(result['trajectory'][0]),
                identity_scope='Original row within the frozen sampled client; dataset membership manifests resolve native source identities.')


def accounting(result,observer,method,n,T):
    raw=result.get('diagnostics',[]);first=result.get('abandonment_round') if method in ('basic','runnerup') else None
    rounds=[]
    if len(observer.rounds)!=T:raise AssertionError('observed update count differs from T')
    for t in range(T):
        r=raw[t] if raw else dict(N=n,A=0,P=0,S=0,J=0)
        values={x:int(r[x]) for x in ('N','A','P','S','J')}
        o=observer.rounds[t]
        if o['point_assignments']!=values['N']-values['S']+values['J']:
            raise AssertionError('observed point-assignment work violates N-S+J')
        rounds.append(dict(round=t,**values,attempted_acceptance=(values['P']/values['A'] if values['A'] else None),
                           effective_saved_coverage=(values['S']/values['N'] if values['N'] else None),
                           abandoned_this_round=first==t,
                           direct_after_abandonment=first is not None and t>first,
                           discarded_certificate_passes=values['P']-values['S'],
                           actual_execution=o))
    totals={x:sum(r[x] for r in rounds) for x in ('N','A','P','S','J')}
    totals.update(attempted_acceptance=totals['P']/totals['A'] if totals['A'] else None,
                  effective_saved_coverage=totals['S']/totals['N'] if totals['N'] else None,
                  discarded_certificate_passes=sum(r['discarded_certificate_passes'] for r in rounds),
                  point_assignments=sum(r['actual_execution']['point_assignments'] for r in rounds),
                  distance_enclosure_pairs=sum(r['actual_execution']['distance_enclosure_pairs'] for r in rounds),
                  exact_distance_fallback_evaluations=sum(r['actual_execution']['exact_distance_fallback_evaluations'] for r in rounds))
    return dict(rounds=rounds,totals=totals,run_abandoned=first is not None,first_fallback_round=first,
                fallback_rounds=[] if first is None else list(range(first,T)),
                scope='Phase-II retained point assignments; N-S+J checked against observed production assignment calls; certificate and other overhead is separately timed.',
                zero_denominator='null means undefined/N/A',observer_overhead='Included in all algorithm elapsed times')


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
    gate=json.loads(Path(args.gate).read_text())
    if gate['execution_environment']!=environment_manifest():raise RuntimeError('P3 execution environment does not match validated gate')
    start=time.perf_counter()
    with Path(args.input).open('rb') as stream:
        bundle=pickle.load(stream)
    input_loading=time.perf_counter()-start
    cd,go=bundle['client_data'],bundle['group_of']
    settings=bundle['settings']
    fp=FixedPointConfig(scale_bits=settings['scale_bits'],clip=settings['clip'])
    removed={int(c):np.asarray(v,dtype=np.int64) for c,v in bundle.get('removed',{}).items()}
    checkpoint_loading=0.0
    observer=Observer()
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
    diagnostics_start=time.perf_counter()
    metadata['initializer']=initializer(result,observer,cd,go,removed,args.method=='checkpoint')
    metadata['accounting']=accounting(result,observer,args.method,
                       sum(len(x) for x in cd.values())-(0 if args.method=='checkpoint' else sum(len(x) for x in removed.values())),settings['T'])
    metadata['diagnostic_materialization_seconds']=time.perf_counter()-diagnostics_start
    metadata['provenance']=bundle['provenance']
    metadata['execution_environment_sha256']=content_hash(environment_manifest())
    metadata['gate_sha256']=sha256(args.gate)
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
