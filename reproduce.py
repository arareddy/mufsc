#!/usr/bin/env python3
"""Portable review harness. Scientific kernels remain in their frozen source trees."""
from pathlib import Path
import argparse, os, sys, json, hashlib, subprocess, time, csv, statistics
ROOT=Path(__file__).resolve().parent
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):os.environ[key]='1'
os.environ['PYTHONDONTWRITEBYTECODE']='1';sys.dont_write_bytecode=True
os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1'
def offline(event,args):
    if event in ('socket.connect','socket.getaddrinfo'):raise RuntimeError('network disabled in reproduction commands')
sys.addaudithook(offline)
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def read(p):return json.loads(Path(p).read_text())
def plain(x):
    import numpy as np
    from fractions import Fraction
    if isinstance(x,np.ndarray):return plain(x.tolist())
    if isinstance(x,np.generic):return x.item()
    if isinstance(x,Fraction):return str(x)
    if isinstance(x,Path):return str(x)
    if isinstance(x,dict):return {str(k):plain(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)):return [plain(v) for v in x]
    return x
def write(p,x):Path(p).write_text(json.dumps(plain(x),sort_keys=True,indent=2,allow_nan=False)+'\n')
def setup(historical=False):
    base=ROOT/'historical/p1_p4' if historical else ROOT/'core'
    sys.path[:0]=[str(base/'src'),str(base/'experiments'),str(ROOT/'variants/binary')]
def load(name,kind='tabular'):
    import numpy as np
    m=read(ROOT/'data'/kind/(name+'.json'));p=ROOT/m['release_file']
    assert sha(p)==m['release_sha256'],'dataset container hash mismatch'
    with np.load(p,allow_pickle=False) as z:a={k:z[k] for k in z.files}
    for k,d in m['arrays'].items():
        assert str(a[k].dtype)==d['dtype'] and list(a[k].shape)==d['shape']
        assert hashlib.sha256(a[k].tobytes(order='C')).hexdigest()==d['raw_C_order_sha256'],k
    cd={int(c):a['X'][int(a['offsets'][i]):int(a['offsets'][i+1])] for i,c in enumerate(a['client_ids'])}
    go={int(c):a['groups'][int(a['offsets'][i]):int(a['offsets'][i+1])] for i,c in enumerate(a['client_ids'])}
    return cd,go,m['scientific_metadata'],a

def witness(out):
    from reproducible import exact_witness
    return exact_witness(out)
def equal(a,b):
    assert witness(a)==witness(b),'exact trajectory/aggregate/final-center witness mismatch'
def retained(cd,go,removed):
    import numpy as np
    d={};g={}
    for c,x in cd.items():
        mask=np.ones(len(x),dtype=bool);mask[removed.get(c,[])]=False
        if mask.any():d[c]=x[mask];g[c]=go[c][mask]
    return d,g

def score_all(cd,go,out,fp):
    import numpy as np
    from fixedpoint import represented_clients
    from scoring import score
    represented,encoded=represented_clients(cd,fp);keys=sorted(cd)
    X=np.concatenate([represented[c] for c in keys]);xi=np.concatenate([encoded[c] for c in keys]);groups=np.concatenate([go[c] for c in keys])
    result=[]
    for C in out['trajectory']:
        values,labels,receipt=score(X,xi,groups,C,fp.scale)
        result.append({'exact':{k:str(v) for k,v in values.items()},'values':{k:float(v) for k,v in values.items()},'verification':receipt})
    return result

def binary(spec,outdir):
    import numpy as np
    from fixedpoint import FixedPointConfig,represented_clients
    from train import train_full
    from unlearn import unlearn
    from client_c0 import compact_checkpoint,delete_clients
    study=spec['stage'];kind='acs' if study=='P3' else 'tabular'
    name=f"n{spec['n']}_C{spec['C']}" if kind=='acs' else spec['dataset']
    cd,go,meta,arrays=load(name,kind)
    fp=FixedPointConfig(spec.get('scale_bits',12),spec.get('clip',meta.get('clip',8.)))
    kw=dict(seed=spec['seed'],k=spec['k'],T=spec['T'],L=spec.get('L',6),gamma=spec.get('gamma',0),fp_cfg=fp,anchor_lloyd_iters=spec.get('anchor_lloyd_iters',0))
    def train(d,g,cache=False):return train_full(d,g,build_cache=cache,**kw)
    result={'case':spec,'timing_scope':'single process resident scientific computation; original paper timing tables are frozen separately','data_container_sha256':sha(ROOT/'data'/kind/(name+'.npz'))}
    if study=='Client_Sequences':
        import pickle
        original=train(cd,go,True);state=compact_checkpoint(original);steps=[]
        for s in spec['steps']:
            c=s['client_id'];start=time.perf_counter();fast,state=delete_clients(state,[c]);duration=time.perf_counter()-start
            cd={i:x for i,x in cd.items() if i!=c};go={i:x for i,x in go.items() if i!=c}
            start=time.perf_counter();fresh=train(cd,go);fresh_duration=time.perf_counter()-start;equal(fast,fresh)
            expected_state=compact_checkpoint(train(cd,go,True))
            assert plain(state.client_counts)==plain(expected_state.client_counts)
            assert tuple(state.client_ids)==tuple(s['active_client_ids'])
            # Only this run's trusted in-memory object is serialized and immediately read.
            p=outdir/('state-step-'+str(s['step'])+'.pickle');p.write_bytes(pickle.dumps(state,protocol=5));state=pickle.loads(p.read_bytes());p.unlink()
            steps.append({'step':s['step'],'exact_equal':True,'next_state_ids':state.client_ids,'direct_seconds':duration,'fresh_seconds':fresh_duration,'witness':witness(fresh)})
        result.update(steps=steps,status='PASS');return result
    if 'removed' in spec:removed={int(c):v for c,v in spec['removed'].items()}
    elif 'deleted_client' in spec:removed={spec['deleted_client']:list(range(len(cd[spec['deleted_client']]))) }
    elif study=='P2':
        req=read(ROOT/'data/tabular_requests'/f"{name}_k{spec['k']}_t{spec['trial']}_seed{spec['seed']}.json");removed={int(c):v for c,v in req['removed'].items()}
    elif study=='P3':
        req=read(ROOT/'data/acs_requests'/f"design{spec['design_index']}_seed{spec['seed']}.json");removed={int(c):v for c,v in req['removed'].items()}
    else:raise ValueError('missing removal request')
    rd,rg=retained(cd,go,removed)
    start=time.perf_counter();fresh=train(rd,rg);fresh_s=time.perf_counter()-start
    result.update(fresh_seconds=fresh_s,witness=witness(fresh),quality=score_all(rd,rg,fresh,fp))
    if study=='Lloyd_Comparison':
        from lloyd import refine
        represented,encoded=represented_clients(rd,fp)
        start=time.perf_counter();ll=refine(represented,encoded,rg,fresh['trajectory'][0],spec['T'],fp.scale);ll_s=time.perf_counter()-start
        quality=score_all(rd,rg,ll,fp)
        expected=read(ROOT/'expected/lloyd'/(spec['id']+'.json'))
        for method,obj,q in [('fair',fresh,result['quality']),('lloyd',ll,quality)]:
            assert witness(obj)==expected['methods'][method]['witness'],method+' saved witness mismatch'
            assert [v['exact'] for v in q]==[v['exact'] for v in expected['methods'][method]['quality']],method+' saved exact quality mismatch'
        result.update(lloyd_witness=witness(ll),lloyd_quality=quality,lloyd_seconds=ll_s,saved_exact_match=True)
    else:
        original=train(cd,go,True);runs=[]
        if spec['T']==0 and 'deleted_client' in spec:
            state=compact_checkpoint(original);start=time.perf_counter();fast,next_state=delete_clients(state,[spec['deleted_client']]);duration=time.perf_counter()-start;equal(fast,fresh)
            runs.append({'method':'compact_client_c0','seconds':duration,'exact_equal':True,'surviving_client_ids':next_state.client_ids})
        modes=['none','basic','runnerup'] if study in ('P2','P3','Round_Budgets') else ['none']
        for mode in modes:
            start=time.perf_counter();got=unlearn(original,removed,certificate_mode=mode,abandon_threshold=spec.get('abandon_threshold',.5));duration=time.perf_counter()-start;equal(got,fresh)
            runs.append({'method':mode,'seconds':duration,'exact_equal':True,'diagnostics':got.get('diagnostics'),'abandonment_round':got.get('abandonment_round')})
        result['methods']=runs
        ep=ROOT/'expected/client'/f"{name}_k{spec['k']}_seed{spec['seed']}.json"
        if spec.get('deleted_client')==0 and ep.exists() and spec['T']<=2:
            expected=read(ep)[spec['T']]['model_witness'];got={'map_version':fresh['map_version'],**witness(fresh)}
            assert got==expected,'saved whole-client witness mismatch';result['saved_exact_match']=True
    result['status']='PASS';return result

def multi(spec,outdir):
    import numpy as np
    sys.path.insert(0,str(ROOT/'variants/multigroup'))
    import multigroup as mg
    from common import projection,extra_witness
    cd,_,meta,a=load('n100000_C50','acs');tr=read(ROOT/'data/acs_transform.json');j=tr['feature_names'].index('RAC1P')
    levels=(np.arange(1,10,dtype=np.float64)-tr['feature_mean'][j])/tr['feature_std'][j]
    groups=np.full(len(a['X']),-1,dtype=np.int64)
    for g,level in enumerate(levels):groups[a['X'][:,j]==level]=g
    assert np.all(groups>=0)
    go={int(c):groups[int(a['offsets'][i]):int(a['offsets'][i+1])] for i,c in enumerate(a['client_ids'])}
    cfg=mg.Config(m=9,k=spec['k'],T=spec['T']);c=spec['deleted_client']
    original=mg.train(cd,go,spec['seed'],cfg,True)
    rd={i:x for i,x in cd.items() if i!=c};rg={i:g for i,g in go.items() if i!=c}
    start=time.perf_counter();fresh=mg.train(rd,rg,spec['seed'],cfg);fresh_s=time.perf_counter()-start
    start=time.perf_counter();direct=mg.direct(original['state'],[c]);direct_s=time.perf_counter()-start
    assert projection(direct)==projection(fresh) and plain(extra_witness(direct))==plain(extra_witness(fresh))
    if spec['T']==0:
        fast,nxt=mg.delete_c0(mg.compact(original['state']),[c]);assert projection(fast)==projection(fresh)
    return {'status':'PASS','case':spec,'exact_equal':True,'witness':projection(fresh),'quality':fresh.get('quality'),'fresh_seconds':fresh_s,'direct_seconds':direct_s,'timing_scope':'single-process scientific replay, not historical timing protocol'}

def historical(spec,outdir):
    if spec['stage']=='P1':
        from p1_compressed import compressed_seed
        rows=[]
        for seed in range(spec['seed_start'],spec['seed_stop']):
            for method in ['centralized','splitgroup_2k','merged_1k','merged_2k']:
                centers,trace=compressed_seed(spec['kappa'],seed,method,spec['unit'],spec['distance']);z=float(centers[0,0]);k=spec['kappa'];n=k+1
                A=z*z;B=((10-z)**2+k*z*z)/n
                rows.append({'kappa':k,'seed':seed,'method':method,'centers':centers,'G':A+B,'Phi':max(A,B),'trace':trace})
        return {'status':'PASS','spec':spec,'rows':rows,'scope':'exact historical compressed P1 training source; objective values reported as binary64 summaries'}
    import p4_corrected
    p4_corrected.load_dataset=lambda name,data_dir,seed=0:load(name)[:3]
    receipt=p4_corrected.run_setting(spec,outdir,ROOT/'data/tabular')
    return {'status':'PASS','spec':spec,'receipt':receipt,'scope':'historical P4 source with lossless packaged data loader'}

def fixtures(outdir):
    # Core tests exercise exact ties, negative requests, complete witnesses and dtype regressions.
    env=dict(os.environ);env['PYTHONPATH']=os.pathsep.join([str(ROOT/'core/src'),str(ROOT/'core/experiments'),os.environ.get('PYTHONPATH','')]);env['PYTEST_ADDOPTS']='';env['FTF_ORACLE_PROCESS_EVIDENCE']=str(outdir/'independent-processes')
    p=subprocess.run([sys.executable,'-B','-m','pytest','-q','-p','no:cacheprovider',str(ROOT/'core/tests'),str(ROOT/'validation/oracle')],env=env,cwd=outdir,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    (outdir/'core-tests.txt').write_text(p.stdout);print(p.stdout,flush=True);assert p.returncode==0
    for name in ['p1_check.py','lloyd_check.py']:
        extra_env=dict(env);extra_env['PYTHONPATH']=os.pathsep.join([str(ROOT),env['PYTHONPATH']])
        run=subprocess.run([sys.executable,'-B',str(ROOT/'validation'/name)],cwd=outdir,env=extra_env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        (outdir/(name+'.log')).write_text(run.stdout);print(run.stdout,flush=True);assert run.returncode==0
    sys.path.insert(0,str(ROOT/'validation/client'))
    import run_fixtures as cf
    for name,fn in [('whole_client_grid_scalar_vs_frozen',cf.run_grid),('invalid_requests',cf.invalid_requests),('degeneracies',cf.degeneracy),('counterexamples',cf.counterexamples),('ideal_law_enumeration',cf.law_enumeration)]:cf.check(name,fn)
    assert all(x['status']=='PASS' for x in cf.checks),cf.checks
    write(outdir/'client-scalar-fixtures.json',dict(checks=cf.checks,details=cf.details))
    import review_candidate as cr
    for name,fn in [('scalar_grid_and_sequences',cr.grid),('request_validation',cr.validation),('no_raw_access',cr.no_raw_access),('trusted_alias_scope',cr.alias_scope)]:cr.check(name,fn)
    assert all(x['status']=='PASS' for x in cr.checks),cr.checks
    write(outdir/'client-candidate-fixtures.json',dict(checks=cr.checks,details=cr.details))
    sys.path.insert(0,str(ROOT/'variants/multigroup'));import test_multigroup as mt
    actual_sha=mt.sha
    mt.ROOT=outdir
    def fixture_sha(p):
        n=Path(p).name;q=ROOT/'variants/multigroup'/n
        if not q.exists():q=ROOT/'evidence/Multigroup'/n
        return actual_sha(q)
    mt.sha=fixture_sha;mt.main()
    return {'status':'PASS','core_pytest_returncode':p.returncode,'multigroup':'full fixture/oracle/negative suite'}

def verify(outdir):
    files=0
    if (ROOT/'MANIFEST.sha256').exists():
        for line in (ROOT/'MANIFEST.sha256').read_text().splitlines():
            expected,name=line.split('  ',1);p=ROOT/name
            assert p.is_file() and sha(p)==expected,'file mismatch '+name;files+=1
    for item in read(ROOT/'SCIENTIFIC_SOURCE_HASHES.json'):assert sha(ROOT/item['path'])==item['sha256'],item['path']
    datasets=[]
    for kind in ['tabular','acs']:
        for p in sorted((ROOT/'data'/kind).glob('*.json')):load(p.stem,kind);datasets.append(kind+'/'+p.stem)
    return {'status':'PASS','manifest_files':files,'safe_datasets_checked':datasets,'scientific_source_hashes':'PASS','network':'disabled'}

def aggregate(outdir):
    rows=[];ratios=[]
    for p in sorted((ROOT/'evidence').rglob('*.csv')):
        with p.open(newline='') as f:items=list(csv.DictReader(f))
        rows.append({'file':str(p.relative_to(ROOT)),'rows':len(items),'sha256':sha(p)})
        if p.name=='paired_ratios.csv':
            for row in items:
                for k,v in row.items():
                    if 'ratio' in k.lower() or 'speedup' in k.lower() or '_over_' in k.lower():
                        try:value=float(v)
                        except (ValueError,TypeError):continue
                        ratios.append({'study':p.relative_to(ROOT).parts[1],'metric':k,'value':value})
    groups={}
    for r in ratios:groups.setdefault((r['study'],r['metric']),[]).append(r['value'])
    summary=[{'study':s,'metric':m,'n':len(v),'min':min(v),'median':statistics.median(v),'max':max(v)} for (s,m),v in sorted(groups.items())]
    write(outdir/'table-inventory.json',rows);write(outdir/'paired-ratio-summary.json',summary)
    if summary:
        with (outdir/'paired-ratio-summary.csv').open('w',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(summary[0]));writer.writeheader();writer.writerows(summary)
    from verify_tables import run as verify_quality
    quality_checks=verify_quality(ROOT,outdir)
    return {'status':'PASS','quality_checks':quality_checks,'tables_read':len(rows),'paired_ratio_groups':len(summary),'scope':'reaggregates saved paired ratios; frozen timing observations are not new measurements'}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['verify','fixtures','aggregate','run','list','_case']);p.add_argument('--study');p.add_argument('--case');p.add_argument('--limit',type=int);p.add_argument('--full',action='store_true');p.add_argument('--output',type=Path);a=p.parse_args()
    if a.action=='list':
        for f in sorted((ROOT/'configs').glob('*.json')):print(f.stem,len(read(f)))
        return
    if a.output is None:p.error('--output is required and must be a new directory')
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    if a.action in ('run','_case'):
        if not a.study:p.error('--study is required')
        cases=read(ROOT/'configs'/(a.study+'.json'))
        if a.case:cases=[x for x in cases if x['id']==a.case]
        if a.limit:cases=cases[:a.limit]
        if not cases:p.error('no cases; Group_Quality is a derived view: use aggregate')
        if not a.case and not a.limit and not a.full:p.error('choose --case, --limit, or --full explicitly')
        if a.action=='run':
            records=[]
            for spec in cases:
                command=[sys.executable,'-B',str(ROOT/'reproduce.py'),'_case','--study',a.study,'--case',spec['id'],'--output',str(out/spec['id'])]
                start=time.perf_counter();r=subprocess.run(command,cwd=out);records.append({'id':spec['id'],'returncode':r.returncode,'wall_seconds':time.perf_counter()-start});write(out/'run-index.json',records)
                if r.returncode:raise RuntimeError('case failed '+spec['id'])
            print(json.dumps({'status':'PASS','study':a.study,'cases':len(records)}));return
        assert len(cases)==1;spec=cases[0];setup(a.study in ('P1','P4'))
        result=historical(spec,out) if a.study in ('P1','P4') else multi(spec,out) if a.study=='Multigroup' else binary(spec,out)
    else:
        setup();result={'verify':verify,'fixtures':fixtures,'aggregate':aggregate}[a.action](out)
    result['runtime']={'python':sys.version.split()[0],'numpy':__import__('numpy').__version__,'threads':1,'network':'disabled'}
    write(out/'receipt.json',result);print(json.dumps({'status':result['status'],'action':a.action,'study':a.study,'case':a.case}),flush=True)
if __name__=='__main__':main()
