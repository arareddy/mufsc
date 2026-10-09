from common import *
from service import check_state,state_hash
from splitgroup import SplitGroupConfig,build_anchor_table,server_step
import pickle
run=ROOT/'runs/sequences-20260926-v1'
old=Path('study://Client_Deletion/runs/client-c0-20260926-v1/core')
records=[]
for spec in json.loads((ROOT/'FROZEN_GRID.json').read_text())['cases']:
 dr=run/spec['case_id'];receipt=json.loads((dr/'complete.json').read_text())
 assert sha256(dr/'compact_current.pkl')==receipt['artifact_hashes']['compact_current.pkl']
 state=pickle.loads((dr/'compact_current.pkl').read_bytes());check_state(state,state)
 audits=[json.loads(x) for x in (dr/'comparisons.jsonl').read_text().splitlines()]
 last=audits[-1];assert state_hash(state)==last['next_state_hash']
 cfg=SplitGroupConfig(state.k,state.gamma);table=build_anchor_table(state.slice_results,state.group_sizes,cfg)
 centers=server_step(table,state.seed,cfg,state.anchor_lloyd_iters)
 rebuilt=projection({'map_version':'FTF-1','trajectory':[centers],'final_centers':centers,'per_round_stats':[]})
 assert rebuilt==json.loads((dr/'r2_s3_compact_model.json').read_text())
 historical=old/spec['case_id']/'rep0_fresh_model.json'
 assert historical.read_bytes()==(dr/'r0_s1_fresh_model.json').read_bytes()
 records.append({'case_id':spec['case_id'],'final_state_reload_and_model':'PASS','final_state_sha256':sha256(dr/'compact_current.pkl'),'historical_first_step_model_path':str(historical),'historical_first_step_model_sha256':sha256(historical),'first_step_full_bytes_equal':True})
write_json(ROOT/'FINAL_STATE_VERIFICATION.json',{'status':'PASS','cases':records,'fresh_process_final_states_checked':len(records),'historical_first_step_model_comparisons':len(records),'training_calls':0,'timing_claim':'No benchmark inference; only reconstruction/check of retained final states.','source_hashes':{x:sha256(ROOT/x) for x in ('client_c0.py','service.py','final_state_check.py')}})
print('15 final-state reload/model checks and 15 historical first-step full-byte checks PASS')
