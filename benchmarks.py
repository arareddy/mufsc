#!/usr/bin/env python3
"""Serial fresh timing measurements with the archived request-function boundaries."""
from reproduce import *
import pickle,importlib,types

def selected(study,case,limit,full):
 cases=read(ROOT/'configs'/(study+'.json'))
 if case:cases=[c for c in cases if c['id']==case]
 if limit:cases=cases[:limit]
 if not (case or limit or full):raise ValueError('select --case, --limit, or --full')
 assert cases
 return cases

def request_data(spec):
 import numpy as np
 kind='acs' if spec['stage']=='P3' else 'tabular';name=f"n{spec['n']}_C{spec['C']}" if kind=='acs' else spec['dataset'];cd,go,meta,a=load(name,kind)
 if 'removed' in spec:removed=spec['removed']
 elif spec['stage']=='P3':removed=read(ROOT/'data/acs_requests'/f"design{spec['design_index']}_seed{spec['seed']}.json")['removed']
 elif spec['stage']=='P2':removed=read(ROOT/'data/tabular_requests'/f"{name}_k{spec['k']}_t{spec['trial']}_seed{spec['seed']}.json")['removed']
 else:removed={spec['deleted_client']:list(range(len(cd[spec['deleted_client']]))) }
 return cd,go,meta,{int(c):np.asarray(v,dtype=np.int64) for c,v in removed.items()}

def isolated(spec,out,repeats,portable_gate=None):
 cd,go,meta,removed=request_data(spec);settings={**spec,'clip':spec.get('clip',meta.get('clip',8.))}
 bundle={'client_data':cd,'group_of':go,'settings':settings,'removed':removed,'provenance':{'release_data':'safe NPZ, verified before private local serialization','case_id':spec['id']}}
 (out/'input.pkl').write_bytes(pickle.dumps(bundle,protocol=5));gate=ROOT/'evidence/original_p2_p3/accepted_validation/remediation/evidence/corrected_map_gate.json'
 # Original accepted gate is checked against the byte-identical current numerical source; not reissued.
 from reproducible import require_gate
 require_gate(gate)
 if spec['stage']=='P3':
  assert portable_gate,'P3 requires a freshly validated portable execution gate'
  gate=Path(portable_gate);require_gate(gate)
 methods=['fresh','none','basic','runnerup'];rows=[];reference=None
 for rep in range(-1,repeats):
  order=['checkpoint'] if rep==-1 else methods[(rep%4):]+methods[:(rep%4)]
  for method in order:
   name=f'r{rep}_{method}';cmd=[sys.executable,'-B',str(ROOT/'benchmarks.py'),'_worker','--study',spec['stage'],'--input',str(out/'input.pkl'),'--checkpoint',str(out/'checkpoint.pkl'),'--output',str(out/(name+'.json')),'--method',method,'--gate',str(gate)]
   started=time.perf_counter();subprocess.run(cmd,check=True,cwd=out);wall=time.perf_counter()-started
   if method=='checkpoint':continue
   result=read(out/(name+'.json'));receipt=read(out/(name+'.receipt.json'))
   if reference is None:reference=result['witness']
   assert result['witness']==reference
   rows.append({'repeat':rep,'method':method,'algorithm_seconds':result['algorithm_elapsed_seconds'],'request_seconds':receipt['comparable_end_to_end_seconds'],'cold_launch_seconds':wall,'exact_witness_equal':True})
 (out/'input.pkl').unlink();(out/'checkpoint.pkl').unlink()
 return rows

def resident(spec,out,repeats):
 import numpy as np
 from train import train_full
 from fixedpoint import FixedPointConfig
 from client_c0 import compact_checkpoint
 sys.path.insert(0,str(ROOT/'timing_adapters'))
 study=spec['stage'];rows=[]
 if study=='Multigroup':
  import Multigroup as m
  mg=m.mg;cd,_,_,a=load('n100000_C50','acs');tr=read(ROOT/'data/acs_transform.json');j=tr['feature_names'].index('RAC1P');levels=(np.arange(1,10)-tr['feature_mean'][j])/tr['feature_std'][j];g=np.full(len(a['X']),-1,dtype=np.int64)
  for i,v in enumerate(levels):g[a['X'][:,j]==v]=i
  assert np.all(g>=0);go={int(c):g[int(a['offsets'][i]):int(a['offsets'][i+1])] for i,c in enumerate(a['client_ids'])}
  original=mg.train(cd,go,spec['seed'],mg.Config(9,k=spec['k'],T=spec['T']),True);cp=original['state'];state=mg.compact(cp) if spec['T']==0 else None;methods=['fresh','direct','compact'] if state else ['fresh','direct']
  def call(method,path):return m.output_call(method,cd,go,cp,state,spec,path)
  project=m.projection
 else:
  cd,go,meta,arrays=load(spec['dataset']);spec={**spec,'anchor_lloyd_iters':spec.get('anchor_lloyd_iters',0)}
  cp=train_full(cd,go,spec['seed'],spec['k'],spec['T'],spec['L'],gamma=spec['gamma'],fp_cfg=FixedPointConfig(spec['scale_bits'],spec['clip']),anchor_lloyd_iters=spec['anchor_lloyd_iters'],build_cache=True)
  if study=='Client_Refinement':
   import Client_Refinement as m
   methods=['fresh','direct','basic','runnerup']
   def call(method,path):
    result,payload,row=m.measured_request(method,cd,go,cp,spec,path);return result,row
  else:
   import Client_Deletion as m
   state=compact_checkpoint(cp);methods=['fresh','direct','fast']
   def call(method,path):return m.measured_request(method,cd,go,cp,state,spec,path)
  project=m.projection
 reference=None
 for rep in range(repeats):
  offset=(spec.get('setting_index',spec.get('case_index',0))+rep)%len(methods);order=methods[offset:]+methods[:offset]
  for method in order:
   result,row=call(method,out/f'r{rep}_{method}_model.json');payload=project(result)
   if reference is None:reference=payload
   assert payload==reference
   rows.append({'repeat':rep,'method':method,**row,'exact_witness_equal':True})
 return rows

def sequences(spec,out,repeats):
 import numpy as np
 from client_c0 import compact_checkpoint
 sys.path.insert(0,str(ROOT/'timing_adapters'));import Client_Sequences as m
 cd,go,_,_=load(spec['dataset']);cp=m.train(cd,go,spec,True);original=compact_checkpoint(cp);rows=[]
 for rep in range(repeats):
  states={'fresh':tuple(sorted(cd)),'compact':original}
  for step in spec['steps']:
   results={}
   methods=['fresh','compact'];offset=(spec['case_index']+rep+step['step']-1)%2;order=methods[offset:]+methods[:offset]
   for method in order:
    result,nxt,loaded,row=m.measured(method,cd,go,states[method],spec,step,out/f'r{rep}_s{step["step"]}_{method}.json');states[method]=loaded;results[method]=result;rows.append({'repeat':rep,'step':step['step'],'method':method,**row})
   assert m.projection(results['fresh'])==m.projection(results['compact'])
 for p in out.glob('*_current.*'):p.unlink()
 return rows

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['run','_case','_worker']);p.add_argument('--study',required=True);p.add_argument('--case');p.add_argument('--limit',type=int);p.add_argument('--full',action='store_true');p.add_argument('--repeats',type=int);p.add_argument('--output',type=Path,required=True)
 for name in ['input','checkpoint','method','gate']:p.add_argument('--'+name)
 a=p.parse_args();setup()
 if a.action=='_worker':
  sys.path.insert(0,str(ROOT/'timing_adapters'));m=importlib.import_module('p3_worker' if a.study=='P3' else 'execution_worker');m.deletion_worker(a);return
 assert a.study in ['P2','P3','Round_Budgets','Client_Deletion','Client_Refinement','Client_Diversity','Client_Sequences','Multigroup']
 out=a.output.resolve();out.mkdir(parents=True,exist_ok=False);cases=selected(a.study,a.case,a.limit,a.full)
 repeats=a.repeats or (4 if a.study in ['Round_Budgets','Client_Refinement'] else 3)
 assert repeats>0
 if a.action=='run':
  gate_args=[]
  if a.study=='P3':
   subprocess.run([sys.executable,'-B',str(ROOT/'reproduce.py'),'fixtures','--output',str(out/'portable_validation')],check=True,cwd=out)
   from reproducible import source_manifest,environment_manifest
   gate=out/'portable_execution_gate.json'
   write(gate,{'status':'PASS',**source_manifest(),'execution_environment':environment_manifest(),'scope':'new portable core/independent/scalar/multigroup fixture gate; not the historical P3 validation gate','fixture_receipt_sha256':sha(out/'portable_validation/receipt.json')})
   gate_args=['--gate',str(gate)]
  for spec in cases:subprocess.run([sys.executable,'-B',str(ROOT/'benchmarks.py'),'_case','--study',a.study,'--case',spec['id'],'--repeats',str(repeats),'--output',str(out/spec['id']),*gate_args],check=True,cwd=out)
  write(out/'receipt.json',{'status':'PASS','study':a.study,'cases':len(cases),'repeats':repeats});return
 assert len(cases)==1;spec=cases[0]
 rows=isolated(spec,out,repeats,a.gate) if a.study in ['P2','P3','Round_Budgets'] else sequences(spec,out,repeats) if a.study=='Client_Sequences' else resident(spec,out,repeats)
 write(out/'observations.json',rows);write(out/'receipt.json',{'status':'PASS','study':a.study,'case':a.case,'timing_observations':len(rows),'repeats':repeats,'exact_output_gate':'all repeated outputs agree','portability_notes':'Client_Diversity uses the original Client_Deletion request function; setup is per case. Round_Budgets uses the original P2 isolated worker. See TIMING_SCOPE.md.'});print(a.study,a.case,'PASS',flush=True)
if __name__=='__main__':main()
