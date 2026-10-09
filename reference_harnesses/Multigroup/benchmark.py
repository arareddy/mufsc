"""Matched real-data gates/timings and prespecified administrative growth probe."""
from common import *
import multigroup as mg
from with_lock import run_locked
from dataclasses import replace
import argparse,time,gc,pickle,resource,traceback
RUN='multigroup-20260926-v1'
FROZEN=('multigroup.py','common.py','oracle.py','fixtures.py','test_multigroup.py','benchmark.py','with_lock.py','prepare.py','PROTOCOL.md','FROZEN_GRID.json','INPUTS.json','IDENTITY_REGISTRY.json','CORRECTNESS.json','SOURCE_INPUTS.json')

def bindings():
    out={n:sha(ROOT/n) for n in FROZEN}
    out.update({str(p.relative_to(ROOT)):sha(p) for p in sorted((ROOT/'baseline/src').glob('*.py'))})
    return out

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

def worker(spec):
    directory=ROOT/'runs'/RUN/spec['case_id'];directory.mkdir(parents=True,exist_ok=False)
    start=time.perf_counter();data,groups=load_population();loading=time.perf_counter()-start
    cfg=mg.Config(m=9,k=10,T=spec['T']);gone=spec['deleted_client'];seed=spec['seed']
    retained={c:x for c,x in data.items() if c!=gone};retained_groups={c:g for c,g in groups.items() if c!=gone}
    begin=time.perf_counter();original=mg.train(data,groups,seed,cfg,True);setup_seconds=time.perf_counter()-begin;checkpoint=original['state']
    begin=time.perf_counter();fullsize=len(pickle.dumps(original,protocol=5));state_size=len(pickle.dumps(checkpoint,protocol=5));state_serialization=time.perf_counter()-begin
    compact=None;compact_seconds=None;compact_size=None
    if spec['T']==0:
        begin=time.perf_counter();compact=mg.compact(checkpoint);compact_seconds=time.perf_counter()-begin;compact_size=len(pickle.dumps(compact,protocol=5))
    prep={'load_verify_seconds':loading,'original_training_seconds':setup_seconds,'original_training_components':original['timing'],'original_full_output_pickle_bytes':fullsize,
        'DIRECT_state_pickle_bytes':state_size,'state_serialization_seconds':state_serialization,'compaction_seconds':compact_seconds,'compact_pickle_bytes':compact_size,
        'original_summary_slots':sum(s['k_e'] for s in checkpoint['slices'].values()),'original_nonempty_slices':len(checkpoint['slices']),
        'original_rows':sum(map(len,data.values())),'survivor_rows':sum(map(len,retained.values()))}
    write_json(directory/'preparation.json',prep)
    write_json(directory/'original_model.json',projection(original))
    methods=['fresh','direct','compact'] if spec['T']==0 else ['fresh','direct']
    outputs={};gate={}
    for method in methods:
        if method=='fresh':out=mg.train(retained,retained_groups,seed,cfg)
        elif method=='direct':out=mg.direct(checkpoint,[gone])
        else:out,_=mg.delete_c0(compact,[gone])
        outputs[method]=projection(out);gate[method]=objhash(outputs[method])
        write_json(directory/f'gate_{method}_model.json',outputs[method])
        if method=='fresh':reference=out
        else:
            assert outputs[method]==outputs['fresh']
            assert jsonbytes(extra_witness(out))==jsonbytes(extra_witness(reference))
            assert jsonbytes(out['updates'])==jsonbytes(reference['updates'])
    write_json(directory/'gate_extra_state.json',extra_witness(reference))
    write_json(directory/'gate_updates.json',reference['updates'])
    # Quality is outside every timed request, once per saved distinct trajectory.
    begin=time.perf_counter();rd,re=mg.represented_clients(retained,cfg.fp);qs=[]
    for t,centers in enumerate(reference['trajectory']):
        q=mg.quality(rd,re,retained_groups,centers,reference['group_sizes'],cfg)
        assert q['Phi']==max(q['group_costs']) and q['G']==sum(q['group_costs'])
        if t:assert q['Phi']<=qs[-1]['Phi']
        qs.append(q)
    qtime=time.perf_counter()-begin;write_json(directory/'quality.json',{'seconds':qtime,'group_counts':reference['group_sizes'],'trajectory_quality':qs})
    write_json(directory/'correctness_gate.json',{'status':'PASS','models':gate,'exact_extra_state_equal':True,'exact_solver_trace_equal':True,'trajectory_arrays':spec['T']+1,'moment_triples':spec['T']})
    count=0;seed_index=seed-10000
    for rep in range(3):
        if spec['T']==0:
            offset=(seed_index+rep)%3;order=methods[offset:]+methods[:offset]
        else:order=methods if (seed_index+spec['T']+rep)%2==0 else methods[::-1]
        for position,method in enumerate(order):
            out,row=output_call(method,data,groups,checkpoint,compact,spec,directory/f'rep{rep}_{method}_model.json')
            assert projection(out)==outputs['fresh'];assert jsonbytes(out['updates'])==jsonbytes(reference['updates'])
            assert jsonbytes(extra_witness(out))==jsonbytes(extra_witness(reference))
            row.update(case_id=spec['case_id'],seed=seed,T=spec['T'],m=9,method=method,repetition=rep,position=position,order=order,utc=utc())
            with (directory/'observations.jsonl').open('a') as f:f.write(json.dumps(row,sort_keys=True)+'\n')
            count+=1
    artifacts={p.name:sha(p) for p in sorted(directory.iterdir()) if p.is_file()}
    write_json(directory/'complete.json',{'status':'PASS','case':spec,'bindings':bindings(),'artifacts':artifacts,'timed_outputs':count,
        'max_rss_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'completed_utc':utc()},True)
    print(json.dumps({'case':spec['case_id'],'status':'PASS','timed_outputs':count,'Phi':float(qs[-1]['Phi']),
                      'max_fixed_partition_gap':max([float(u['gap']) for u in reference['updates']],default=None)}),flush=True)

def growth():
    directory=ROOT/'runs'/RUN/'growth';directory.mkdir(parents=True,exist_ok=False)
    data={c:np.array([[((i*11+q*3+c)%31-15)/4 for q in range(4)] for i in range(180)],float) for c in (0,3,8,21,33,47)}
    observations=[];ms=[2,3,5,9]
    for rep in range(3):
        order=ms[rep:]+ms[:rep]
        for position,m in enumerate(order):
            groups={c:np.arange(180,dtype=np.int64)%m for c in data};cfg=mg.Config(m,k=10)
            gc.collect();begin=time.perf_counter();trained=mg.train(data,groups,7,cfg,True);train_seconds=time.perf_counter()-begin
            begin=time.perf_counter();compact=mg.compact(trained['state']);compaction=time.perf_counter()-begin
            observations.append({'m':m,'repetition':rep,'position':position,'train_seconds':train_seconds,'compaction_seconds':compaction,
                'state_pickle_bytes':len(pickle.dumps(trained['state'],protocol=5)),'compact_pickle_bytes':len(pickle.dumps(compact,protocol=5)),
                'nonempty_slices':len(compact.slices),'anchor_slots':sum(s['k_e'] for s in compact.slices.values()),'client_group_count_cells':len(compact.client_ids)*m})
    write_json(directory/'observations.json',observations)
    write_json(directory/'complete.json',{'status':'PASS','bindings':bindings(),'artifacts':{'observations.json':sha(directory/'observations.json')},'completed_utc':utc()})
    print('growth PASS',flush=True)

def run():
    base=ROOT/'runs'/RUN;base.mkdir(parents=True,exist_ok=True)
    gate=json.loads((ROOT/'CORRECTNESS.json').read_text());assert gate['status']=='PASS'
    for n,h in gate['code_hashes'].items():assert sha(ROOT/n)==h
    write_json(base/'run_manifest.json',{'run_id':RUN,'bindings':bindings(),'contract':'resident matched budget model output; self-validation'},True)
    specs=json.loads((ROOT/'FROZEN_GRID.json').read_text())['cases'];done=[]
    for spec in [*specs,{'case_id':'growth'}]:
        directory=base/spec['case_id'];complete=directory/'complete.json'
        if complete.exists():
            receipt=json.loads(complete.read_text());assert receipt['status']=='PASS' and receipt['bindings']==bindings()
            for n,h in receipt['artifacts'].items():assert sha(directory/n)==h
            done.append(spec['case_id']);continue
        if directory.exists():raise RuntimeError('Preserved incomplete case; diagnose before any explicit replacement: '+str(directory))
        command=[str(PYTHON),'-B',str(ROOT/'benchmark.py'),'worker','--case',spec['case_id']]
        rc=run_locked(command,base/'lock.jsonl',timeout=600)
        if rc:
            write_json(base/'failure.json',{'utc':utc(),'case':spec,'returncode':rc,'completed':done});raise SystemExit(rc)
        done.append(spec['case_id']);write_json(base/'progress.json',{'completed':done,'total':16,'utc':utc()})
    write_json(base/'status.json',{'status':'COMPLETE','completed':done,'utc':utc()})
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['run','worker']);parser.add_argument('--case');args=parser.parse_args()
    if args.mode=='run':run()
    elif args.case=='growth':growth()
    else:
        spec=next(s for s in json.loads((ROOT/'FROZEN_GRID.json').read_text())['cases'] if s['case_id']==args.case)
        try:worker(spec)
        except Exception:
            write_json(ROOT/'runs'/RUN/spec['case_id']/'failure.json',{'utc':utc(),'traceback':traceback.format_exc()});raise
