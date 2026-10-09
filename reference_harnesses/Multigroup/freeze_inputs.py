from common import *
import shutil
base=json.loads((ROOT/'SOURCE_INPUTS.json').read_text())
accepted=json.loads(Path('source://historical/outputs/dtype_repair_20260919/implementation_manifest.json').read_text())
for f in base['baseline']:
    assert sha(f['path'])==f['sha256']==sha(ROOT/f['copy'])==accepted['files']['src/'+Path(f['path']).name]
original=Path('source://historical')
inputs=[original/'AGENTS.md',original/'STORAGE_LAYOUT.md',original/'corrected_project/dataset_preprocessing/adult_dataset_iid.py',SOURCE/'corrected_project/TRAINING_MAP.md',SOURCE/'corrected_project/experiments/execution_worker.py',SOURCE/'corrected_project/experiments/p3_acs.py',original/'remediation/p3/scripts/prepare_acs2018_v1.py']
for name in ('FINAL_HANDOFF.md','ARTIFACT_INDEX.md','REPRODUCTION.md','implementation_manifest.json','analysis_paths.json'):inputs.append(original/'outputs/dtype_repair_20260919'/name)
for folder,names in [('Fair_to_Forget_Client_Deletion_20260926',['REPORT.md','PROTOCOL.md','FROZEN_GRID.json','INPUTS.json','IDENTITY_REGISTRY.json','STATE_INVENTORY.md','REPRODUCE.md','READY_FOR_REVIEW.json','client_c0.py']),('Fair_to_Forget_Client_Deletion_Review_20260926',['THEORY_REVIEW.md','IMPLEMENTATION_REVIEW.md','CLAIMS_MATRIX.md','REVIEW_READY.json']),('Fair_to_Forget_Round_Budgets_20260926',['REPORT.md','CORRECTNESS.md','PROTOCOL.md','REPORTING_CORRECTION.md','reporting_correction_verification.json'])]:
    inputs.extend(Path('[private-path-omitted]')/folder/n for n in names)
live=Path('[private-path-omitted]');snapshot=ROOT/'source_snapshot';snapshot.mkdir(exist_ok=True)
for n in ('main.tex','appendix.tex','numerical_contract.tex','AGENTS.md','LIVE_EDITING_RULES.md','LIVE_WORKFLOW.md'):
    p=live/n;inputs.append(p);shutil.copyfile(p,snapshot/n)
for n in ('ghadiri2021socially.author_fulltext.txt','pan2023mufc.author_fulltext.txt'):inputs.append(live/'reference_integrity_audit_20260926/evidence'/n)
base.update({'observed_utc':utc(),'accepted_code_sha256':accepted['code_sha256'],'inputs':[{'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in inputs],
             'live_snapshot_note':'Small read-only source snapshot. The live author may change files later; snapshot is the reading context, not a freeze of that task.',
             'excluded_input':'Fair_to_Forget_Client_Refinement_20260926; no unfinished sibling output consumed'})
write_json(ROOT/'SOURCE_INPUTS.json',base)
write_json(ROOT/'CODE_FREEZE.json',{'utc':utc(),'status':'pre_pilot','hashes':{n:sha(ROOT/n) for n in ('multigroup.py','common.py','oracle.py','fixtures.py','test_multigroup.py','benchmark.py','with_lock.py','prepare.py','PROTOCOL.md','FROZEN_GRID.json','CORRECTNESS.json')}},True)
print('baseline and completed input hashes recorded; pilot code frozen')
