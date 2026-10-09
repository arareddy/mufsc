from common import *
from fractions import Fraction
from datasets import load_dataset
from datetime import datetime,timezone
O=Path('study://Client_Deletion')
V=Path('study://Client_Deletion_Review')
review=json.loads((V/'REVIEW_READY.json').read_text())
assert sha256(ROOT/'client_c0.py')==review['candidate_sha256']==sha256(O/'review_snapshots/v1/client_c0.py')
baseline=json.loads((ROOT/'BASELINE_MANIFEST.json').read_text())
for f,v in baseline['files'].items():assert sha256(ROOT/'baseline'/f)==v['sha256']==sha256(v['source'])
old=json.loads((O/'FROZEN_GRID.json').read_text())['cases'];inputs=json.loads((ROOT/'INPUTS.json').read_text());ident=json.loads((ROOT/'IDENTITY_REGISTRY.json').read_text())
selections={};cases=[]
for ds in ('adult','bank','credit'):
 cd,go,meta=load_dataset(ds,str(DATA),seed=0); inp=inputs['files'][ds]
 assert meta['source_sha256']==inp['sha256'] and sha256(inp['identity_path'])==inp['identity_sha256']
 counts={c:[int(np.count_nonzero(go[c]==g)) for g in (0,1)] for c in sorted(cd)};tot=[sum(v[g] for v in counts.values()) for g in (0,1)]
 valid=[c for c,v in counts.items() if min(tot[g]-v[g] for g in (0,1))>0];sizes=sorted(sum(counts[c]) for c in valid)
 median2=sizes[(len(sizes)-1)//2]+sizes[len(sizes)//2]
 fraction=lambda c:Fraction(counts[c][0],sum(counts[c]))
 roles={'smallest':min(valid,key=lambda c:(sum(counts[c]),c)), 'median_size':min(valid,key=lambda c:(abs(2*sum(counts[c])-median2),c)), 'largest':min(valid,key=lambda c:(-sum(counts[c]),c)), 'min_group0_fraction':min(valid,key=lambda c:(fraction(c),c)), 'max_group0_fraction':min(valid,key=lambda c:(-fraction(c),c)), 'min_surviving_smaller_group':min(valid,key=lambda c:(min(tot[g]-counts[c][g] for g in (0,1)),c))}
 clients=[]
 for c,v in counts.items():
  ids=np.asarray(meta['source_record_ids'][c],dtype='<i8'); h=hashlib.sha256(ids.tobytes()).hexdigest()
  assert h==ident[ds][str(c)]['ordered_full_row_ids_sha256'] and meta['source_client_ids'][c]==ident[ds][str(c)]['source_client_id']
  clients.append({'client':c,'source_client_id':meta['source_client_ids'][c],'size':sum(v),'group_counts':v,'group0_fraction':jsonable(fraction(c)),'remaining_group_counts':[tot[g]-v[g] for g in (0,1)],'valid':c in valid,'roles':[r for r,j in roles.items() if j==c],'ordered_row_ids_sha256':h})
 selections[ds]={'roles':roles,'clients':clients,'valid_count':len(valid),'excluded_clients':[c for c in counts if c not in valid],'unique_selected_clients':sorted(set(roles.values())),'size_range':[min(sizes),max(sizes)],'group_counts':tot,'median_size_times_two':median2}
 for seed in range(10000,10005):
  template=next(x for x in old if x['dataset']==ds and x['seed']==seed)
  for c in sorted(set(roles.values())):
   cl=next(x for x in clients if x['client']==c)
   spec={k:template[k] for k in ('dataset','seed','dataset_selection_seed','k','T','L','gamma','anchor_lloyd_iters','scale_bits','clip','n','C','d')}
   spec.update(case_id=f'{ds}_c{c}_k10_seed{seed}',case_index=len(cases),deleted_client=c,roles=cl['roles'],removed_n=cl['size'],removed_group_counts=cl['group_counts'],retained_group_counts=cl['remaining_group_counts'],source_client_id=cl['source_client_id'],ordered_removed_row_ids_sha256=cl['ordered_row_ids_sha256'])
   cases.append(spec)
write_json(ROOT/'SELECTION.json',selections,immutable=True)
write_json(ROOT/'FROZEN_GRID.json',{'frozen_utc':datetime.now(timezone.utc).isoformat(),'before_new_training_or_timings':True,'cases':cases,'unique_cases':len(cases),'timed_observations':len(cases)*9,'gate_method_calls':len(cases)*3,'setup_batches':15,'timing_repetitions':3},immutable=True)
# Bind small completed evidence; no unfinished refinement workspace is accessed.
refs={}
for base,names in [(O,['REPORT.md','PROTOCOL.md','FROZEN_GRID.json','INPUTS.json','IDENTITY_REGISTRY.json','STATE_INVENTORY.md','REPRODUCE.md','READY_FOR_REVIEW.json','client_c0.py']), (V,['THEORY_REVIEW.md','IMPLEMENTATION_REVIEW.md','CLAIMS_MATRIX.md','REVIEW_READY.json']), (Path('study://Round_Budgets'),['REPORT.md','CORRECTNESS.md','PROTOCOL.md','REPORTING_CORRECTION.md','verification.json','reporting_correction_verification.json']), (Path('source://historical/outputs/dtype_repair_20260919'),['FINAL_HANDOFF.md','ARTIFACT_INDEX.md','REPRODUCTION.md','implementation_manifest.json','analysis_paths.json'])]:
 for n in names:refs[str(base/n)]=sha256(base/n)
write_json(ROOT/'COMPLETED_INPUT_BINDINGS.json',refs,immutable=True)
write_json(ROOT/'SOURCE_VERIFICATION.json',{'status':'PASS','candidate_sha256':review['candidate_sha256'],'baseline_files':len(baseline['files']),'environment':environment_manifest()},immutable=True)
print(json.dumps({d:{'roles':s['roles'],'unique':s['unique_selected_clients'],'size_range':s['size_range']} for d,s in selections.items()},indent=2));print('Unique cases:',len(cases))
