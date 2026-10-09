"""Frozen 15-case resident-data core and matched quality references."""
from common import *
from train import train_full
from unlearn import unlearn
from fixedpoint import FixedPointConfig,represented_clients
from datasets import load_dataset
from objective import fair_objective
from client_c0 import compact_checkpoint,delete_clients
from with_lock import run_locked
from datetime import datetime,timezone
import argparse,time,gc,pickle,subprocess,resource,traceback,itertools

CORE_FILES=('benchmark.py','client_c0.py','common.py','with_lock.py','PROTOCOL.md','FROZEN_GRID.json','BASELINE_MANIFEST.json','INPUTS.json','IDENTITY_REGISTRY.json','CORRECTNESS.json')

def bindings():
    out={name:sha256(ROOT/name) for name in CORE_FILES}
    for p in sorted((ROOT/'baseline/src').glob('*.py')):out[str(p.relative_to(ROOT))]=sha256(p)
    return out

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

def state_witness(result):
    # Object arrays contain exact Fractions; canonical JSON stores numerator/denominator.
    return jsonable({key:result[key] for key in ('group_sizes','slice_results','anchor_table')})

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

def quality(cd,go,centers,spec):
    begin=time.perf_counter();fixed,_=represented_clients(cd,FixedPointConfig(spec['scale_bits'],spec['clip']))
    X=np.concatenate([fixed[c] for c in sorted(fixed)]);groups=np.concatenate([go[c] for c in sorted(go)])
    materialized=time.perf_counter();values=fair_objective(X,groups,centers,return_exact=True)
    exact={key:{'numerator':v.numerator,'denominator':v.denominator} for key,v in zip(('Phi_A','Phi_B','G','Phi'),values)}
    # G is the unweighted sum of group means. Pooled SSE requires group sizes.
    ng=[int(np.count_nonzero(groups==g)) for g in (0,1)]
    sse=sum(ng[g]*values[g] for g in (0,1))
    exact['pooled_SSE']={'numerator':sse.numerator,'denominator':sse.denominator}
    return {'values':{**{k:float(v) for k,v in zip(('Phi_A','Phi_B','G','Phi'),values)},'pooled_SSE':float(sse)},'exact':exact,'quality_input_materialization_seconds':materialized-begin,'quality_evaluation_seconds':time.perf_counter()-materialized,'retained_group_counts':ng}

def worker(run_dir,spec,stage):
    directory=run_dir/stage/spec['case_id'];directory.mkdir(parents=True,exist_ok=True)
    started=datetime.now(timezone.utc).isoformat()
    start=time.perf_counter();cd,go,meta=load_dataset(spec['dataset'],str(DATA),seed=spec['dataset_selection_seed']);load=time.perf_counter()-start
    assert meta['source_sha256']==json.loads((ROOT/'INPUTS.json').read_text())['files'][spec['dataset']]['sha256']
    assert meta['clip']==spec['clip']
    departed=spec['deleted_client'];retained={c:x for c,x in cd.items() if c!=departed};groups={c:g for c,g in go.items() if c!=departed}
    assert sum(len(v) for v in retained.values())==spec['n']-spec['removed_n']
    observations=[]
    if stage=='core':
        gc.collect();start=time.perf_counter();checkpoint=train(cd,go,spec,cache=True);training_seconds=time.perf_counter()-start
        start=time.perf_counter();state=compact_checkpoint(checkpoint);compact_seconds=time.perf_counter()-start
        start=time.perf_counter();checkpoint_blob=pickle.dumps(checkpoint,protocol=5);checkpoint_storage={'pickle_bytes':len(checkpoint_blob),'serialization_seconds':time.perf_counter()-start};del checkpoint_blob
        start=time.perf_counter();state_blob=pickle.dumps(state,protocol=5);state_storage={'pickle_bytes':len(state_blob),'serialization_seconds':time.perf_counter()-start};del state_blob
        setup={'canonical_initial_training_seconds':training_seconds,'incremental_compaction_seconds':compact_seconds,'canonical_checkpoint_storage':checkpoint_storage,'compact_state_storage':state_storage,'compact_client_count':len(state.client_ids),'compact_slice_count':len(state.slice_results),'compact_summary_slots':sum(s['k_e'] for s in state.slice_results.values()),'source_rows':spec['n'],'initial_training_timing':jsonable(checkpoint['timing']),'full_data_load_verify_seconds':load,'environment':environment_manifest()}
        write_json(directory/'preparation.json',setup)
        canonical=('fresh','direct','fast');reference=None
        for rep in range(3):
            offset=(spec['case_index']+rep)%3;order=canonical[offset:]+canonical[:offset]
            results={}
            for position,method in enumerate(order):
                result,row=measured_request(method,cd,go,checkpoint,state,spec,directory/f'rep{rep}_{method}_model.json')
                results[method]=result
                row.update(case_id=spec['case_id'],dataset=spec['dataset'],seed=spec['seed'],repetition=rep,position=position,order=list(order),observed_utc=datetime.now(timezone.utc).isoformat())
                observations.append(row)
                with (directory/'observations.jsonl').open('a') as stream:stream.write(json.dumps(row,sort_keys=True)+'\n')
            fresh=results['fresh']
            for method in ('direct','fast'):
                assert projection(results[method])==projection(fresh),(spec['case_id'],rep,method,'model')
                check_extra(results[method],fresh)
            if reference is None:
                reference=projection(fresh)
                write_json(directory/'extra_state_witness.json',state_witness(fresh))
            assert projection(fresh)==reference
            for method in results:assert state_witness(results[method])==state_witness(fresh)
            del results
        receipt={'status':'PASS','case_id':spec['case_id'],'model_comparisons':6,'extra_state_comparisons':6,'across_repetition_fresh_equal':True,'full_model_witness':reference,'extra_state_witness_sha256':sha256(directory/'extra_state_witness.json'),'observations_sha256':sha256(directory/'observations.jsonl'),'started_utc':started,'ended_utc':datetime.now(timezone.utc).isoformat(),'max_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'source_bindings':bindings()}
    else:
        core=run_dir/'core'/spec['case_id']
        canonical=json.loads((core/'complete.json').read_text())['full_model_witness']
        center=canonical['final_centers'];centers=np.frombuffer(bytes.fromhex(center['bytes_hex']),dtype='<f8').reshape(center['shape'])
        q0=quality(retained,groups,centers,spec)
        quality_rows=[{'T':0,'quality':q0,'model_witness':canonical,'learning_seconds':None}]
        for T in (1,2):
            gc.collect();start=time.perf_counter();fresh=train(retained,groups,spec,T);elapsed=time.perf_counter()-start
            quality_rows.append({'T':T,'quality':quality(retained,groups,fresh['final_centers'],spec),'model_witness':projection(fresh),'learning_seconds':elapsed})
        write_json(directory/'quality.json',quality_rows)
        receipt={'status':'PASS','case_id':spec['case_id'],'same_population_as_core':True,'full_data_load_verify_seconds':load,'started_utc':started,'ended_utc':datetime.now(timezone.utc).isoformat(),'quality_sha256':sha256(directory/'quality.json'),'source_bindings':bindings()}
    write_json(directory/'complete.json',receipt)
    print(stage,spec['case_id'],'PASS',flush=True)

def campaign(run_id,stage,budget):
    if not run_id or Path(run_id).name!=run_id:raise ValueError('simple fresh run ID required')
    run_dir=ROOT/'runs'/run_id;run_dir.mkdir(parents=True,exist_ok=True)
    gate=json.loads((ROOT/'CORRECTNESS.json').read_text());assert gate['status']=='PASS'
    assert gate['source_hashes']['client_c0.py']==sha256(ROOT/'client_c0.py')
    manifest={'run_id':run_id,'source_bindings':bindings(),'environment':environment_manifest(),'contract':'Resident data/checkpoints; equal model-only output; no network/cold-start claim'}
    write_json(run_dir/'run_manifest.json',manifest,immutable=True)
    specs=json.loads((ROOT/'FROZEN_GRID.json').read_text())['cases']
    start=time.perf_counter();done=[];skipped=[]
    for spec in specs:
        directory=run_dir/stage/spec['case_id']
        if spec['excluded']:skipped.append(spec['case_id']);continue
        complete=directory/'complete.json'
        if complete.exists():
            old=json.loads(complete.read_text());assert old['status']=='PASS' and old['source_bindings']==bindings();done.append(spec['case_id']);continue
        if directory.exists():raise RuntimeError(f'Incomplete case retained at {directory}; use fresh run ID after diagnosis, never append a rerun.')
        if stage=='quality' and not (run_dir/'core'/spec['case_id']/'complete.json').exists():skipped.append(spec['case_id']);continue
        if time.perf_counter()-start>=budget:break
        command=[str(PYTHON),'-B',str(ROOT/'benchmark.py'),'worker','--run-id',run_id,'--case',spec['case_id'],'--stage',stage]
        rc=run_locked(command,run_dir/'lock.jsonl',timeout=600)
        if rc!=0:
            write_json(run_dir/f'{stage}_failure.json',{'case':spec['case_id'],'returncode':rc,'completed':done});raise SystemExit(rc)
        done.append(spec['case_id'])
        write_json(run_dir/f'{stage}_progress.json',{'completed':done,'excluded_or_unavailable':skipped,'elapsed_seconds':time.perf_counter()-start})
    write_json(run_dir/f'{stage}_status.json',{'status':'COMPLETE' if len(done)+len(skipped)==len(specs) else 'PARTIAL','completed':done,'excluded_or_unavailable':skipped,'elapsed_seconds':time.perf_counter()-start})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['run','worker']);p.add_argument('--run-id',required=True);p.add_argument('--case');p.add_argument('--stage',choices=['core','quality'],default='core');p.add_argument('--budget-seconds',type=int,default=5400);a=p.parse_args()
    if a.mode=='run':campaign(a.run_id,a.stage,a.budget_seconds)
    else:
        spec=next(x for x in json.loads((ROOT/'FROZEN_GRID.json').read_text())['cases'] if x['case_id']==a.case)
        worker(ROOT/'runs'/a.run_id,spec,a.stage)
