#!/usr/bin/env python3
"""Snapshot-specific independent review; all outputs in this review workspace."""
import os
for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):os.environ[name]='1'
os.environ['PYTHONDONTWRITEBYTECODE']='1'
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import argparse,datetime,hashlib,importlib.util,itertools,json,time,traceback
from unittest.mock import patch
import numpy as np
import scalar_oracle as o
import run_fixtures as f
W=Path(__file__).resolve().parent
import client_c0 as c
checks=[];details={}

def state_repr(state):
    return json.dumps(f.plain(vars(state)),sort_keys=True)


def check(name,fn):
    start=time.perf_counter()
    try:
        answer=fn();checks.append({'name':name,'status':'PASS','elapsed_seconds':time.perf_counter()-start})
        if answer is not None:details[name]=f.plain(answer)
    except Exception as e:
        checks.append({'name':name,'status':'FAIL','error':repr(e),'traceback':traceback.format_exc(),'elapsed_seconds':time.perf_counter()-start})


def grid():
    cases=0;rejects=0;sequences=0;arrays=0
    for name,data,groups,k,gamma,ta,seeds in f.fixture_cases():
        cd,go=f.prod_data(data,groups)
        for seed in seeds:
            checkpoint=f.train_full(cd,go,seed,k,0,0,gamma=gamma,fp_cfg=f.FP,anchor_lloyd_iters=ta)
            state=c.compact_checkpoint(checkpoint)
            before=state_repr(state)
            for key,s in state.slice_results.items():
                for field,v in s.items():
                    if isinstance(v,np.ndarray):
                        assert not v.flags.writeable
                        assert not np.shares_memory(v,checkpoint['slice_results'][key][field]);arrays+=1
            for flags in itertools.product((False,True),repeat=len(data)):
                dropped=[cid for cid,z in zip(data,flags) if z]
                retained={cid:x for cid,x in data.items() if cid not in dropped}
                if not any(retained.values()):
                    f.rejects(lambda:c.delete_clients(state,dropped));rejects+=1;continue
                oracle=o.train(retained,{cid:groups[cid] for cid in retained},seed,k,gamma,anchor_iters=ta)
                result,new=c.delete_clients(state,dropped)
                f.same_result(result,oracle)
                f.same_float(result['trajectory'][0],oracle['final_centers'])
                assert len(result['trajectory'])==1 and result['per_round_stats']==[] and result['digests']==[]
                assert not result['cache_valid'] and result['map_version']=='FTF-1'
                assert new.client_ids==tuple(sorted(retained))
                assert new.group_sizes==oracle['group_sizes']
                assert new.client_counts=={cid:tuple(sum(int(x)==g for x in groups[cid]) for g in (0,1)) for cid in retained}
                for key,s in new.slice_results.items():assert s is state.slice_results[key]
                assert state_repr(state)==before
                cases+=1
            for order in ((1001,42,2),(2,1001,42)):
                current=state;removed=set()
                for departing in order:
                    result,current=c.delete_clients(current,[departing]);removed.add(departing)
                    retained={cid:x for cid,x in data.items() if cid not in removed}
                    oracle=o.train(retained,{cid:groups[cid] for cid in retained},seed,k,gamma,anchor_iters=ta)
                    f.same_result(result,oracle)
                    assert current.client_ids==tuple(sorted(retained))
                    f.rejects(lambda:c.delete_clients(current,[departing]))
                    sequences+=1
                assert state_repr(state)==before
    return dict(valid_independent_cases=cases,invalid_empty_subsets=rejects,sequential_steps=sequences,read_only_independent_array_copies_checked=arrays)


def validation():
    data={2:np.array([[0.],[2.]]),42:np.array([[1.],[3.]]),105:np.array([[4.]]),1001:np.empty((0,1))}
    groups={2:np.array([0,0]),42:np.array([1,1]),105:np.array([0]),1001:np.array([],dtype=int)}
    cp=f.train_full(data,groups,0,1,0,0,fp_cfg=f.FP);state=c.compact_checkpoint(cp);before=state_repr(state)
    bad=[[-1],[True],[np.bool_(True)],[2.0],np.array([2.0]),[999],[2,2],{2:[0]},'2',None,[[2]],np.array([[2]]),np.array(2),[2,105],[42],[2,42,105]]
    for request in bad:
        f.rejects(lambda:c.delete_clients(state,request));assert state_repr(state)==before
    for request in ([],(),np.array([],dtype=int),[1001],[2],[105],[np.int64(2)],np.array([2],dtype=np.int64)):
        c.delete_clients(state,request)
    f.rejects(lambda:c.compact_checkpoint(dict(cp,T=1)))
    f.rejects(lambda:c.compact_checkpoint(dict(cp,map_version='wrong')))
    f.rejects(lambda:c.compact_checkpoint(dict(cp,group_sizes={0:9,1:2})))
    f.rejects(lambda:c.delete_clients({},[]))
    # Sole one-per-group boundary; both active group deletions must fail.
    thin=f.train_full({2:np.array([[0.]]),42:np.array([[1.]])},{2:np.array([0]),42:np.array([1])},0,5,0,0,fp_cfg=f.FP)
    thin=c.compact_checkpoint(thin)
    for request in ([2],[42],[2,42]):f.rejects(lambda:c.delete_clients(thin,request))
    return dict(invalid_requests=len(bad),valid_request_forms=8,bad_initial_state_or_checkpoint=4,one_each_group_rejections=3)


def no_raw_access():
    name,data,groups,k,gamma,ta,seeds=f.fixture_cases()[0]
    cd,go=f.prod_data(data,groups)
    cp=f.train_full(cd,go,0,k,0,0,fp_cfg=f.FP)
    expected=o.train({i:x for i,x in data.items() if i!=42},{i:g for i,g in groups.items() if i!=42},0,k)
    forbidden={'client_data','encoded_data','group_of','client_cache','per_round_stats','trajectory','final_centers','anchor_table'}
    class Checked(dict):
        def __init__(self,source):super().__init__(source);self.access=[]
        def __getitem__(self,key):
            self.access.append(key)
            if key in forbidden:raise AssertionError(f'forbidden checkpoint access {key}')
            return super().__getitem__(key)
        def get(self,key,default=None):return self[key] if key in self else default
    checked=Checked(cp)
    def stop(*args,**kwargs):raise AssertionError('local training or encoding invoked')
    with patch('splitgroup.local_slice_step',stop),patch('train.train_full',stop),patch('fixedpoint.quantize',stop),patch('fixedpoint.represented_clients',stop):
        state=c.compact_checkpoint(checked)
        del cp,checked['client_data'],checked['encoded_data'],checked['group_of']
        result,new=c.delete_clients(state,[42])
    f.same_result(result,expected)
    return dict(compaction_keys=sorted(set(checked.access)),raw_and_cache_keys_not_read=True,no_local_training_or_encoding=True,state_fields=sorted(vars(state)))


def wrapper_boundary():
    # Import only snapshot source; its main/campaign functions never execute.
    sys.path.insert(0,str(SNAP))
    b=load_module('reviewed_benchmark',SNAP/'benchmark.py')
    _,data,groups,k,gamma,ta,_=f.fixture_cases()[0]
    cd,go=f.prod_data(data,groups)
    spec=dict(seed=0,k=k,T=0,L=0,gamma=0.,anchor_lloyd_iters=0,scale_bits=2,clip=8.,deleted_client=42)
    checkpoint=f.train_full(cd,go,0,k,0,0,fp_cfg=f.FP)
    state=c.compact_checkpoint(checkpoint)
    class Trap:
        def __getitem__(self,*a):raise AssertionError('fast wrapper touched raw input')
        def __iter__(self):raise AssertionError('fast wrapper scanned raw input')
        def items(self):raise AssertionError('fast wrapper requested raw items')
        def __len__(self):raise AssertionError('fast wrapper measured raw length')
    out=W/'results/wrapper_fixture';out.mkdir(exist_ok=True)
    rows={};models={}
    for method in ('fresh','direct','fast'):
        args=(Trap(),Trap(),Trap()) if method=='fast' else (cd,go,checkpoint)
        models[method],rows[method]=b.measured_request(method,*args,state,spec,out/f'{method}.json')
    raw=[(out/f'{method}.json').read_bytes() for method in ('fresh','direct','fast')]
    assert raw[0]==raw[1]==raw[2]
    for method,row in rows.items():
        assert row['request_e2e_seconds']>=row['algorithm_seconds']
        assert row['output_bytes']==len(raw[0])
    expected=o.train({cid:x for cid,x in data.items() if cid!=42},{cid:g for cid,g in groups.items() if cid!=42},0,k)
    for model in models.values():f.same_result(model,expected)
    return dict(equal_output_bytes=True,output_bytes=len(raw[0]),model_sha256=hashlib.sha256(raw[0]).hexdigest(),fast_arguments_were_raw_access_traps=True,
                timing_rows=rows,timing_scope='tiny correctness call only; these values do not estimate speedup',wrapper_sha256=sha(SNAP/'benchmark.py'))


def alias_scope():
    # Confirm the documented trusted-state boundary, without mutating the candidate or a published state.
    _,data,groups,k,gamma,ta,_=f.fixture_cases()[0]
    cd,go=f.prod_data(data,groups);cp=f.train_full(cd,go,0,k,0,0,fp_cfg=f.FP)
    state=c.compact_checkpoint(cp);result,next_state=c.delete_clients(state,[42])
    shared={'group_sizes_alias':result['group_sizes'] is next_state.group_sizes,'slice_dict_alias':result['slice_results'] is next_state.slice_results,'surviving_summary_alias':all(v is state.slice_results[key] for key,v in next_state.slice_results.items())}
    assert all(shared.values())
    # No mutation is performed: aliases are a contract limitation, not a failure under the contract.
    return dict(**shared,conclusion='Do not mutate returned summary/group dictionaries; frozen dataclass is shallow. Within explicit trusted-state scope this is nonblocking.')


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='results/candidate_review_initial.json');args=ap.parse_args()
    start=time.perf_counter();load=os.getloadavg()
    check('candidate_vs_independent_scalar_grid_and_sequences',grid)
    check('candidate_request_validation',validation)
    check('compaction_and_replay_raw_access_traps',no_raw_access)
    check('actual_request_wrapper_boundary',wrapper_boundary)
    check('trusted_state_alias_contract',alias_scope)
    verify()
    result=dict(status='PASS' if all(x['status']=='PASS' for x in checks) else 'FAIL',snapshot=str(SNAP),snapshot_manifest_sha256=MANIFEST_SHA,
                candidate_sha256=sha(SNAP/'client_c0.py'),snapshot_files_verified=35,checks=checks,details=details,
                utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),elapsed_seconds=time.perf_counter()-start,
                load_before=load,load_after=os.getloadavg(),source_hashes={p.name:sha(p) for p in (Path(__file__),W/'scalar_oracle.py',W/'run_fixtures.py')},
                shared_dependencies='Candidate uses canonical build_anchor_table/server_step and validated frozen arithmetic; independent oracle shares only NumPy PCG64/SeedSequence and runtime binary64 conversion.',
                lock='tiny correctness exception; no dataset, training campaign or benchmark run',imported_kernel_paths={name:getattr(sys.modules[name],'__file__',None) for name in ('train','splitgroup','kmeanspp','fixedpoint','rng')})
    target=W/args.output;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(json.dumps(f.plain(result),indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':result['status'],'elapsed_seconds':result['elapsed_seconds'],'checks':checks,'grid':details.get('candidate_vs_independent_scalar_grid_and_sequences')},indent=2))
    return 0 if result['status']=='PASS' else 1
if __name__=='__main__':raise SystemExit(main())
