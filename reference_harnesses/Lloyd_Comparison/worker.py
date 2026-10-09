from common import *
import numpy as np,pickle,time,datetime,traceback,csv
from fractions import Fraction as F
from train import train_full
from fixedpoint import FixedPointConfig,represented_clients
from datasets import load_dataset
from assignment import assign_labels_only
from objective import fair_objective
from reproducible import exact_witness,jsonable,environment_manifest,require_gate
from lloyd import refine
from scoring import score

def work(key):
 verify_sources();assert load(W/'fixtures/results.json')['status']=='PASS';require_gate()
 case=next(c for c in load(W/'FROZEN_GRID.json')['cases'] if c['case_id']==key);out=W/'runs/matched-start-v1'/key
 assert not out.exists(),'Never overwrite an existing case attempt';out.mkdir(parents=True);started=time.monotonic()
 try:
  pop,ds,seed=case['population'],case['dataset'],case['seed'];retained_ids=[]
  if pop=='record':
   inp=case['record_input'];verify_file(inp['input']);verify_file(inp['request']);req=load(inp['request'])
   with open(inp['input'],'rb') as f:b=pickle.load(f)
   assert {str(c):list(map(int,v)) for c,v in b['removed'].items()}==req['removed']
   cd={};go={};meta=inp['meta']
   for c in sorted(b['client_data']):
    mask=np.ones(len(b['client_data'][c]),dtype=bool);mask[req['removed'].get(str(c),[])]=False
    cd[c]=b['client_data'][c][mask];go[c]=b['group_of'][c][mask]
    retained_ids.extend([c,i,int(v)] for i,v in enumerate(meta['source_record_ids'][str(c)]) if mask[i])
   spec=inp['settings']
  else:
   spec=case['client_spec'];inp=case['client_input'];verify_file(inp['path']);verify_file(inp['identity_path'])
   orig,groups,meta=load_dataset(ds,str(Path(inp['path']).parent),seed=0)
   assert meta['source_sha256']==inp['sha256'];assert jsonable(meta['source_record_ids'])==load(inp['identity_path'])['source_record_ids']
   cdel=spec['deleted_client'];cd={c:x for c,x in orig.items() if c!=cdel};go={c:g for c,g in groups.items() if c!=cdel}
   for c in sorted(cd):retained_ids.extend([c,i,int(v)] for i,v in enumerate(meta['source_record_ids'][c]))
  assert objsha(retained_ids)==case['retained_identity_sha256']
  counts=[sum(int(np.sum(g==h)) for g in go.values()) for h in [0,1]];assert counts==case['counts']
  fp=FixedPointConfig(scale_bits=12,clip=spec['clip']);fixed,ints=represented_clients(cd,fp)
  keys=sorted(fixed);X=np.concatenate([fixed[c] for c in keys]);XI=np.concatenate([ints[c] for c in keys]);G=np.concatenate([go[c] for c in keys])
  assert len(X)==case['retained_n'] and counts==[int(np.sum(G==g)) for g in [0,1]]
  fresh=train_full(cd,go,seed,10,2,6,gamma=0,fp_cfg=fp,anchor_lloyd_iters=0,build_cache=False);fw=exact_witness(fresh)
  saved=[]
  for T in range(3):
   ref=case['references'][str(T)];verify_file(ref['path'])
   if pop=='record':w=load(ref['witness']);verify_file(ref['witness']);q=load(ref['path'])['quality']
   else:rr=next(x for x in load(ref['path']) if x['T']==T);w=rr['model_witness'];q=rr['quality']
   assert w['trajectory']==fw['trajectory'][:T+1] and w['per_round_stats']==fw['per_round_stats'][:T] and w['final_centers']==fw['trajectory'][T],('fair witness',key,T)
   saved.append(q)
  # Fair reproduces first; score its output before constructing Lloyd comparator.
  def checked_score(C,reference=None):
   vals,lab,receipt=score(X,XI,G,C,fp.scale);clab=assign_labels_only(X,C);canonical=fair_objective(X,G,C,return_exact=True)
   assert np.array_equal(lab,clab),'independent label mismatch'
   assert [vals[k] for k in ['Phi_A','Phi_B','G','Phi']]==list(canonical),'independent objective mismatch'
   if reference:
    for k in ['Phi_A','Phi_B','G','Phi']:
     r=reference['exact'][k];assert vals[k]==F(r['numerator'],r['denominator']),('saved objective',k)
    if 'pooled_SSE' in reference['exact']:
     r=reference['exact']['pooled_SSE'];assert vals['pooled_SSE']==F(r['numerator'],r['denominator'])
   return dict(exact={k:str(v) for k,v in vals.items()},values={k:float(v) for k,v in vals.items()},verification=receipt)
  fairq=[checked_score(C,saved[T]) for T,C in enumerate(fresh['trajectory'])]
  ordinary=refine(fixed,ints,go,fresh['trajectory'][0],2,fp.scale);ow=exact_witness(ordinary)
  assert ow['trajectory'][0]==fw['trajectory'][0] and ow['per_round_stats'][0]==fw['per_round_stats'][0]
  lloydq=[fairq[0]]+[checked_score(C) for C in ordinary['trajectory'][1:]]
  outputs=dict(case_id=key,population=pop,dataset=ds,seed=seed,counts=counts,retained_identity_sha256=objsha(retained_ids),represented_integer_sha256=hashlib.sha256(XI.astype('<i8').tobytes()).hexdigest(),represented_group_sha256=hashlib.sha256(G.astype('<i8').tobytes()).hexdigest(),scale=fp.scale,source_bindings=bindings(),methods=dict(fair=dict(witness=fw,quality=fairq),lloyd=dict(witness=ow,quality=lloydq)))
  dump(out/'outputs.json',outputs)
  dump(out/'complete.json',dict(status='PASS',case_id=key,source_bindings=bindings(),output_sha256=sha(out/'outputs.json'),fair_saved_witnesses_reproduced=3,fair_saved_objectives_recomputed=3,independent_canonical_score_crosschecks=5,independent_canonical_label_crosschecks=5,shared_initial_centers=True,shared_round0_stats=True,counts=counts,retained_identity_sha256=objsha(retained_ids),environment=environment_manifest(),elapsed_seconds=time.monotonic()-started,ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
  print(key,'PASS',flush=True)
 except BaseException as e:
  dump(out/'FAILED.json',dict(case_id=key,error=repr(e),traceback=traceback.format_exc(),source_bindings=bindings()));raise
if __name__=='__main__':work(sys.argv[1])
