#!/usr/bin/env python3
"""Tiny independent review fixtures; no production source writes or bulk inputs."""
import os
for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):
    os.environ[name]='1'
os.environ['PYTHONDONTWRITEBYTECODE']='1'
import sys
sys.dont_write_bytecode=True
import argparse,datetime,hashlib,itertools,json,time,traceback
from pathlib import Path
from fractions import Fraction as Q
import numpy as np
import scalar_oracle as o
BASE=Path(__file__).resolve().parents[2]/'core'
sys.path.insert(0,str(BASE/'src'))
from train import train_full
from fixedpoint import FixedPointConfig
from unlearn import unlearn
from splitgroup import build_anchor_table,server_step,SplitGroupConfig
from assignment import assign_labels_only
from kmeanspp import weighted_kmeanspp
from rng import canonical_tape

SEEDS=(0,1,2,3,4,7,11,19)
FP=FixedPointConfig(2,8.0)
checks=[];details={}

def plain(x):
    if isinstance(x,Q):return f'{x.numerator}/{x.denominator}'
    if isinstance(x,np.ndarray):return plain(x.tolist())
    if isinstance(x,dict):return {str(k):plain(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)):return [plain(v) for v in x]
    if isinstance(x,np.generic):return x.item()
    return x

def same_float(a,b):
    a=np.array(a,dtype=np.float64);b=np.array(b,dtype=np.float64)
    assert a.shape==b.shape,(a.shape,b.shape)
    assert a.tobytes()==b.tobytes(),(a.tolist(),b.tolist())

def same_summary(a,b):
    for field in ('anchors','reps'):same_float(a[field],b[field])
    for field in ('mult','selected_idx'):assert tuple(a[field])==tuple(b[field]),field
    for field in ('k_e','n_e'):assert int(a[field])==int(b[field]),field

def same_result(a,b):
    same_float(a['final_centers'],b['final_centers'])
    assert a['group_sizes']==b['group_sizes']
    assert set(a['slice_results'])==set(b['slice_results'])
    for key in a['slice_results']:same_summary(a['slice_results'][key],b['slice_results'][key])
    ta,tb=a['anchor_table'],b['anchor_table']
    assert tuple(ta['owner'])==tuple(tb['owner'])
    assert tuple(ta['weights'])==tuple(tb['weights'])
    same_float(ta['anchors'],tb['anchors'])

def check(name,fn):
    t=time.perf_counter()
    try:
        value=fn()
        checks.append(dict(name=name,status='PASS',elapsed_seconds=time.perf_counter()-t))
        if value is not None:details[name]=plain(value)
    except Exception as e:
        checks.append(dict(name=name,status='FAIL',error=repr(e),traceback=traceback.format_exc(),elapsed_seconds=time.perf_counter()-t))

def rejects(fn):
    try:fn()
    except (ValueError,TypeError):return
    raise AssertionError('accepted invalid request')

def fixture_cases():
    groups={2:[0,0,0,0,1,1,1,1],42:[0,0,1,1],105:[0,0,1,1],1001:[]}
    base={2:[[-3,0],[-1,0],[1,0],[3,0],[-2,2],[0,2],[2,2],[4,2]],42:[[-2,-1],[2,-1],[0,3],[2,3]],105:[[-1,1],[1,1],[-1,-2],[1,-2]],1001:[]}
    repeat={c:([[0,0],[0,0],[2,0],[2,0],[0,0],[0,0],[2,0],[2,0]] if c==2 else [[1,0],[1,0],[1,0],[1,0]]) if c!=1001 else [] for c in base}
    zero={c:[[0,0] for _ in xs] for c,xs in base.items()}
    rounding={c:[[float(x)+0.125,float(y)+0.375] for x,y in xs] for c,xs in base.items()}
    rounding[2][0]=[-20,20]
    return [('gaps',base,groups,2,0.0,0,SEEDS),('ties_saturation',repeat,groups,5,0.0,0,(0,7)),
            ('zero_potential',zero,groups,3,0.5,0,(0,7)),('rounding_lloyd',rounding,groups,2,0.5,2,(0,7))]


def prod_data(data,groups):
    return ({c:np.array(rows,dtype=float).reshape(-1,2) for c,rows in data.items()},
            {c:np.array(groups[c],dtype=np.int64) for c in data})


def run_grid():
    counts={'configurations':0,'valid_subsets':0,'invalid_subsets':0,'baseline_replay_cases':0}
    for name,data,groups,k,gamma,ta,seeds in fixture_cases():
        ids=tuple(data)
        cd,go=prod_data(data,groups)
        for seed in seeds:
            counts['configurations']+=1
            cp=o.train(data,groups,seed,k,gamma,anchor_iters=ta)
            frozen=train_full(cd,go,seed,k,0,0,gamma=gamma,fp_cfg=FP,anchor_lloyd_iters=ta)
            same_result(cp,frozen)
            for flags in itertools.product((False,True),repeat=len(ids)):
                drop=[c for c,z in zip(ids,flags) if z]
                kept={c:x for c,x in data.items() if c not in drop}
                retained_groups={c:groups[c] for c in kept}
                if not any(kept.values()):
                    rejects(lambda:o.reuse(cp,drop));counts['invalid_subsets']+=1;continue
                fresh=o.train(kept,retained_groups,seed,k,gamma,anchor_iters=ta)
                fast=o.reuse(cp,drop)
                same_result(fast,fresh)
                pcd,pgo=prod_data(kept,retained_groups)
                freshprod=train_full(pcd,pgo,seed,k,0,0,gamma=gamma,fp_cfg=FP,anchor_lloyd_iters=ta,build_cache=False)
                same_result(fast,freshprod)
                assert len(freshprod['trajectory'])==1 and freshprod['per_round_stats']==[]
                for key,s in fast['slice_results'].items():
                    assert s is cp['slice_results'][key]
                    assert sum(s['mult'])==s['n_e']
                assert sum(fast['anchor_table']['weights'])==2
                for g in (0,1):assert sum(w for w,owner in zip(fast['anchor_table']['weights'],fast['anchor_table']['owner']) if owner[1]==g)==1
                counts['valid_subsets']+=1
            # Focused comparison against the existing full-record replay API.
            removed={42:np.arange(len(cd[42]),dtype=np.int64)}
            rp=unlearn(frozen,removed,certificate_mode='none')
            same_float(rp['final_centers'],o.reuse(cp,[42])['final_centers'])
            assert rp['per_round_stats']==[] and len(rp['trajectory'])==1
            counts['baseline_replay_cases']+=1
    return counts


def invalid_requests():
    data={2:[[0.0],[2.0]],42:[[1.0],[3.0]],105:[[4.0]],1001:[]}
    groups={2:[0,0],42:[1,1],105:[0],1001:[]}
    cp=o.train(data,groups,0,1)
    invalid=[[-1],[True],[2.0],[999],[2,2],{2:[0]},[2,105],[42],[2,42,105]]
    for x in invalid:rejects(lambda:o.reuse(cp,x))
    for x in ([],[1001],[2],[105]):o.reuse(cp,x)
    # Frozen record-deletion API's domain checks (oracle validation alone is not a candidate test).
    cd={c:np.array(x,dtype=float).reshape(-1,1) for c,x in data.items()};go={c:np.array(x,dtype=np.int64) for c,x in groups.items()}
    p=train_full(cd,go,0,1,0,0,fp_cfg=FP)
    requests=[{999:[0]},{2:[0,0]},{2:[-1]},{2:[2]},{2:[0.0]},{True:[0]},{42:[0,1]},{2:[0,1],105:[0]}]
    for x in requests:rejects(lambda:unlearn(p,x,certificate_mode='none'))
    return dict(oracle_invalid=len(invalid),oracle_valid=4,frozen_record_api_invalid=len(requests))


def degeneracy():
    class Never:
        def word(self):raise AssertionError('unexpected random draw')
    assert o.categorical([0,Q(3,7),0],Never())==1
    assert o.kpp(((0.,),(1.,)),[0,1],5,Never())==(0,1,0,1,0)
    assert o.kpp(((0.,),(1.,),(2.,)),[0,0,0],2,Never())==(0,1)
    assert o.nearest((0.,),((-1.,),(1.,)))==0
    assert o.nearest((1.,),((1.,),(1.,)))==0
    assert assign_labels_only(np.array([[0.],[1.]]),np.array([[-1.],[1.]])).tolist()==[0,1]
    for k in (1,2,3,5):
        pts=((0.,),(0.,),(2.,))
        for weights in ([0,0,0],[0,Q(1,3),Q(2,3)],[1,1,1]):
            for seed in (0,7):
                a=o.kpp(pts,weights,k,o.Tape(seed,2))
                b=weighted_kmeanspp(np.array(pts),weights,k,canonical_tape(seed,'server'))
                assert a==tuple(b)
    # Full fair server has fewer input anchors than k and must cycle deterministically.
    data={2:[[1.0]],42:[[1.0]]};groups={2:[0],42:[1]}
    cp=o.train(data,groups,0,5)
    pd={c:np.array(x) for c,x in data.items()};pg={c:np.array(x) for c,x in groups.items()}
    same_result(cp,train_full(pd,pg,0,5,0,0,fp_cfg=FP))
    return dict(categorical_sampler_comparisons=24,cyclic_C0=cp['final_centers'])


def counterexamples():
    result={}
    # IDs determine streams; renumbering a retained client changes the local map.
    points=tuple((float(i),) for i in range(6))
    id_changes=[]
    for seed in SEEDS:
        old=o.local(points,seed,42,0,2,0.0)
        new=o.local(points,seed,0,0,2,0.0)
        if old['selected_idx']!=new['selected_idx']:
            id_changes.append(dict(seed=seed,persistent_42=old['selected_idx'],renumbered_0=new['selected_idx']))
    assert id_changes;result['renumbering']=id_changes
    # Fixed preprocessing is essential: a fitted mean would change surviving coordinates.
    result['refitted_preprocessing']={'original_mean':'10/3','retained_mean':'0/1','retained_raw_point':0,'encoded_before':o.encode({42:[[float(-Q(10,3))]]})[42],'encoded_refit':o.encode({42:[[0.0]]})[42]}
    assert result['refitted_preprocessing']['encoded_before']!=result['refitted_preprocessing']['encoded_refit']
    # Local pooled global group weights change the first-draw law even on an untouched client.
    result['global_weights_in_mixed_local_sampler']={'untouched_rows':[0,1],'row_groups':[0,1],'before_nA_nB':[2,1],'after_nA_nB':[1,1],'before_P_row0':'1/3','after_P_row0':'1/2'}
    # Stale denominators after removing a pure A client alter the retained table law.
    data={2:[[2.]],42:[[0.]],105:[[3.]]};groups={2:[0],42:[0],105:[1]}
    cp=o.train(data,groups,0,1)
    fast=o.reuse(cp,[2]);stale=o.table(fast['slice_results'],cp['group_sizes'])
    result['stale_denominators']={'owners':fast['anchor_table']['owner'],'correct_weights':fast['anchor_table']['weights'],'stale_weights':stale['weights'],'correct_P_A':'1/2','stale_P_A':'1/3'}
    # Removing a nonselected record still changes its local multiplicity.
    pts=((0.,),(1.,),(2.,),(3.,))
    s=o.local(pts,0,42,0,1,0.0)
    removed=next(i for i in range(4) if i not in s['selected_idx'])
    result['record_miss_changes_count']={'selected':s['selected_idx'],'removed_unselected':removed,'old_mult':s['mult'],'required_new_total':3}
    assert sum(s['mult'])!=3
    # Reordering rows can change the fixed-seed chosen record even with one stable key.
    a=o.local(points,0,42,0,1,0.0);b=o.local(tuple(reversed(points)),0,42,0,1,0.0)
    assert a['reps']!=b['reps'];result['row_order']={'original':a['reps'],'reversed':b['reps']}
    return result


def law_enumeration():
    points={i:(Q(i),) for i in range(4)};removed={3};survive={i:x for i,x in points.items() if i not in removed}
    fresh=o.ideal_paths(survive,2)
    prefix=o.ideal_repair_law(points,2,removed)
    restart=o.ideal_repair_law(points,2,removed,whole_restart=True)
    assert fresh==prefix and fresh!=restart
    def unordered(law,chosen):return sum(p for ids,p in law.items() if set(ids)==chosen)
    assert unordered(fresh,{0,1})==Q(7,30)
    assert unordered(restart,{0,1})==Q(257,1260)
    # Saturation demonstrates why an unmodified prefix construction cannot simply
    # replace FTF's indexed k>=n map, even in the ideal-bit model.
    small={0:(Q(0),),1:(Q(1),),2:(Q(2),)}
    fs=o.ideal_paths({0:small[0],1:small[1]},2)
    pr=o.ideal_repair_law(small,2,{2})
    assert fs!=pr
    return dict(fresh=fresh,prefix=prefix,restart=restart,fresh_unordered_01=Q(7,30),restart_unordered_01=Q(257,1260),
                saturation_fresh=fs,saturation_prefix=pr,scope='Exact enumeration on stated tiny populations, not a global law proof.')


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='results/fixtures.json');args=ap.parse_args()
    start=time.perf_counter();load_before=os.getloadavg()
    check('whole_client_grid_scalar_vs_frozen',run_grid)
    check('valid_and_invalid_requests',invalid_requests)
    check('ties_zero_mass_saturation',degeneracy)
    check('assumption_counterexamples',counterexamples)
    check('ideal_prefix_vs_restart_enumeration',law_enumeration)
    result=dict(status='PASS' if all(x['status']=='PASS' for x in checks) else 'FAIL',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                elapsed_seconds=time.perf_counter()-start,checks=checks,details=details,python=sys.version,numpy=np.__version__,seeds=SEEDS,
                load_before=load_before,load_after=os.getloadavg(),lock='not acquired: only tiny fixtures under explicit protocol exception; no timing claims',
                shared_primitives=['NumPy PCG64','NumPy SeedSequence','binary64 runtime conversions'],
                independent_kernels=['Fraction squared distances','indexed nearest/ties','integer categorical sampler','canonical completion','scalar snapping','local multiplicities','table weights/order','server anchor Lloyd','exact ideal law enumerator'],
                source_hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),Path(o.__file__)]})
    out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(plain(result),indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':result['status'],'elapsed_seconds':result['elapsed_seconds'],'checks':checks,'grid':details.get('whole_client_grid_scalar_vs_frozen')},indent=2))
    return 0 if result['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
