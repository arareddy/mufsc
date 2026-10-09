from common import *
from datasets import load_dataset
from datetime import datetime,timezone
BASE=Path('study://Client_Deletion')
REVIEW=Path('study://Client_Deletion_Review')
review=json.loads((REVIEW/'REVIEW_READY.json').read_text())
assert sha256(ROOT/'client_c0.py')==review['candidate_sha256']==sha256(BASE/'review_snapshots/v1/client_c0.py')
baseline=json.loads((ROOT/'BASELINE_MANIFEST.json').read_text())
for name,record in baseline['files'].items():
 assert sha256(ROOT/'baseline'/name)==record['sha256'],name
inputs=json.loads((ROOT/'INPUTS.json').read_text());registry=json.loads((ROOT/'IDENTITY_REGISTRY.json').read_text())
cases=[];sequences={}
for name in ('adult','bank','credit'):
 cd,go,meta=load_dataset(name,str(DATA),seed=0)
 inp=inputs['files'][name]
 assert meta['source_sha256']==inp['sha256'] and sha256(inp['identity_path'])==inp['identity_sha256']
 counts={c:[int(np.count_nonzero(go[c]==g)) for g in (0,1)] for c in cd}
 for c in cd:
  assert registry[name][str(c)]['source_client_id']==meta['source_client_ids'][c]
  assert registry[name][str(c)]['ordered_full_row_ids_sha256']==hashlib.sha256(np.asarray(meta['source_record_ids'][c],dtype='<i8').tobytes()).hexdigest()
 totals=[sum(v[g] for v in counts.values()) for g in (0,1)];active=sorted(cd);steps=[];skips=[]
 for c in sorted(cd):
  remaining=[totals[g]-counts[c][g] for g in (0,1)]
  if min(remaining)<=0:
   skips.append({'client_id':c,'reason':'empties required global group','proposed_group_counts':remaining});continue
  active.remove(c);totals=remaining
  removed=[int(x) for x in meta['source_record_ids'][c]]
  survivor_rows=np.concatenate([meta['source_record_ids'][a] for a in active]).astype('<i8')
  steps.append({'step':len(steps)+1,'client_id':c,'source_client_id':meta['source_client_ids'][c],
    'removed_n':len(cd[c]),'removed_group_counts':counts[c],'removed_source_rows':removed,
    'removed_ordered_rows_sha256':registry[name][str(c)]['ordered_full_row_ids_sha256'],
    'retained_n':sum(totals),'retained_group_counts':list(totals),'active_client_ids':list(active),
    'retained_ordered_rows_sha256':hashlib.sha256(survivor_rows.tobytes()).hexdigest(),
    'retained_group_universe':[0,1]})
  if len(steps)==3:break
 assert len(steps)==3
 sequences[name]={'steps':steps,'skipped_candidates':skips,'original_group_counts':inp['group_counts'],'original_n':inp['n'],'original_C':inp['C'],'d':inp['d']}
 for seed in range(10000,10005):
  cases.append({'case_id':f'{name}_k10_seed{seed}','case_index':len(cases),'dataset':name,'seed':seed,'k':10,'T':0,'L':6,'gamma':0.0,'scale_bits':12,'clip':meta['clip'],'anchor_lloyd_iters':0,'steps':steps})
write_json(ROOT/'FROZEN_GRID.json',{'utc':datetime.now(timezone.utc).isoformat(),'cases':cases,'sequences':sequences,'expected_cases':45,'repeats':3,'expected_observations':270},immutable=True)
paths=[BASE/x for x in ('REPORT.md','PROTOCOL.md','FROZEN_GRID.json','INPUTS.json','IDENTITY_REGISTRY.json','STATE_INVENTORY.md','REPRODUCE.md','READY_FOR_REVIEW.json','client_c0.py')]
paths += [REVIEW/x for x in ('THEORY_REVIEW.md','IMPLEMENTATION_REVIEW.md','CLAIMS_MATRIX.md','REVIEW_READY.json')]
rounds=Path('study://Round_Budgets')
paths += [rounds/x for x in ('REPORT.md','CORRECTNESS.md','PROTOCOL.md','REPORTING_CORRECTION.md')]
old=Path('source://historical/outputs/dtype_repair_20260919')
paths += [old/x for x in ('FINAL_HANDOFF.md','ARTIFACT_INDEX.md','REPRODUCTION.md','implementation_manifest.json','analysis_paths.json')]
paths += [SOURCE/'corrected_project/TRAINING_MAP.md',SOURCE/'corrected_project/experiments/execution_worker.py']
live=Path('[private-path-omitted]')
paths += [live/x for x in ('AGENTS.md','LIVE_EDITING_RULES.md','main.tex','appendix.tex')]
paths += [live/'reference_integrity_audit_20260926/evidence'/x for x in ('ghadiri2021socially.author_fulltext.txt','pan2023mufc.author_fulltext.txt')]
write_json(ROOT/'INPUT_MANIFEST.json',{'utc':datetime.now(timezone.utc).isoformat(),'read_only_inputs':{str(p):{'sha256':sha256(p),'bytes':p.stat().st_size} for p in paths},'copied_baseline_files':len(baseline['files']),'reviewed_candidate_sha256':review['candidate_sha256'],'live_source_note':'Read-only source hash snapshot; live source may subsequently change in another task.'},immutable=True)
print(json.dumps({name:{'withdrawals':[x['client_id'] for x in v['steps']],'retained_n':[x['retained_n'] for x in v['steps']],'skips':v['skipped_candidates']} for name,v in sequences.items()}))
