"""Freeze a local manifest/ready pointer only; no publication or manuscript edit."""
from common import *
import ast,subprocess

def main():
    assert not (ROOT/'READY_FOR_REVIEW.json').exists()
    for p in ROOT.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
    verify=json.loads((ROOT/'VERIFICATION.json').read_text());assert verify['status']=='PASS'
    tests=json.loads((ROOT/'CORRECTNESS.json').read_text());assert tests['status']=='PASS'
    code=json.loads((ROOT/'CODE_FREEZE.json').read_text())
    for n,h in code['hashes'].items():assert sha(ROOT/n)==h
    table_rows={n:sha(ROOT/'tables'/n) for n in verify['tables']};assert table_rows==verify['tables']
    excluded={'MANIFEST.json','READY_FOR_REVIEW.json','HANDOFF_VERIFICATION.json'}
    files=[{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(ROOT.rglob('*')) if p.is_file() and p.name not in excluded and '__pycache__' not in p.parts]
    write_json(ROOT/'MANIFEST.json',{'version':'multigroup-review-v1','created_utc':utc(),'scope':'All local source, reports, protocol, compact tables and full new evidence; external datasets/env not copied.',
        'excluded_circular_metadata':sorted(excluded),'files':files},True)
    result=subprocess.run([str(PYTHON),'-B',str(ROOT/'verify_handoff.py')],check=True,text=True,capture_output=True)
    receipt=json.loads(result.stdout);assert receipt['status']=='PASS';receipt['created_utc']=utc()
    write_json(ROOT/'HANDOFF_VERIFICATION.json',receipt,True)
    names=('multigroup.py','PROTOCOL.md','FROZEN_GRID.json','INPUTS.json','IDENTITY_REGISTRY.json','oracle.py','fixtures.py','test_multigroup.py','CORRECTNESS.json','benchmark.py','verify_results.py','VERIFICATION.json','CODE_FREEZE.json','REPORT.md','INTEGRATION_NOTES.md','APPENDIX_PROPOSAL.tex','THEORY.md')
    ready={'status':'READY_FOR_REVIEW_SELF_VALIDATED_NOT_INDEPENDENT_SIGNOFF','version':'multigroup-review-v1','created_utc':utc(),'workspace':str(ROOT),'numerical_map':'FTF-MG-FW12-B6-v1',
        'frozen_hashes':{n:sha(ROOT/n) for n in names},'manifest':str(ROOT/'MANIFEST.json'),'manifest_sha256':sha(ROOT/'MANIFEST.json'),
        'handoff_verification':str(ROOT/'HANDOFF_VERIFICATION.json'),'handoff_verification_sha256':sha(ROOT/'HANDOFF_VERIFICATION.json'),
        'report':str(ROOT/'REPORT.md'),'integration_notes':str(ROOT/'INTEGRATION_NOTES.md'),'appendix_proposal':str(ROOT/'APPENDIX_PROPOSAL.tex'),
        'completed':{'synthetic_m':[3,5],'scalar_T0_cases':len(tests['t0_comparisons']),'positive_replay_cases':len(tests['T1_T2_comparisons']),
            'compact_sequence_steps':len(tests['sequence_steps']),'invalid_checks':tests['invalid_requests_rejected'],'primal_reference_cases':len(tests['optimizer_cases']),
            'real_population':'acs2018-ftf1-p3-v1/n100000_C10','real_m':9,'seeds':[10000,10001,10002,10003,10004],'T':[0,1,2],
            'real_gate_models':verify['gate_models'],'real_timed_models':verify['timed_models'],'gate_replay_comparisons':verify['gate_replay_comparisons'],
            'saved_candidate_certificates_rederived':verify['dual_candidate_certificates_rederived'],'manifest_files':len(files)},
        'claims':{'proved_conditional':['Same-seed whole-client model equality for fixed deterministic map and trusted state','Compact T0 sequence invariant','Exact weak-duality fixed-partition gap','Represented-center guard nonincrease'],
            'tested':['Independent scalar small m=3,5 fixtures','Six bounded primal reference fixtures','One nine-category real population/request/five-seed pilot at matched T0/T1/T2','Saved exact trajectories/statistics/guard/gap/reporting checks'],
            'unresolved_or_not_claimed':['Independent review','Global clustering optimum','General utility adequacy','Full cache equality or personal-data erasure','Model-adaptive fresh-independent law','Record-level/certificate extension','Hostile-state validation','General/cold/durable service speed factor','Positive-round binary bit identity']},
        'blockers':[],'exclusions':[],'scientific_reruns':0,'review_instruction':'Inspect this exact manifest identity. Self-validation only; no earlier binary independent review applies. Do not integrate into the live manuscript without separate authorization.',
        'external_publication':False,'canonical_or_manuscript_changes':False,'unfinished_sibling_inputs_consumed':False}
    write_json(ROOT/'READY_FOR_REVIEW.json',ready,True)
    print(json.dumps({'status':ready['status'],'manifest_sha256':ready['manifest_sha256'],'files':len(files),'bytes':sum(f['bytes'] for f in files)}))
if __name__=='__main__':main()
