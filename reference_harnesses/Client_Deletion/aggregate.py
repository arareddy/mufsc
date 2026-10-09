"""Verify saved receipts and compute transparent, repetition-balanced summaries."""
from common import *
import argparse,csv,statistics,math

def save_csv(path,rows):
    keys=list(dict.fromkeys(k for row in rows for k in row))
    with Path(path).open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=keys);writer.writeheader();writer.writerows(rows)

def mean(values):return statistics.mean(values)
def sd(values):return statistics.stdev(values) if len(values)>1 else 0.0

def aggregate(run_id):
    run=ROOT/'runs'/run_id;out=ROOT/'tables';out.mkdir(exist_ok=True)
    grid=json.loads((ROOT/'FROZEN_GRID.json').read_text())['cases'];manifest=json.loads((run/'run_manifest.json').read_text())
    raw=[];case_rows=[];ratios=[];prep=[];quality=[];completed=[];missing=[];verification=[]
    for spec in grid:
        d=run/'core'/spec['case_id'];receipt_path=d/'complete.json'
        if not receipt_path.exists():missing.append(spec['case_id']);continue
        receipt=json.loads(receipt_path.read_text());assert receipt['status']=='PASS'
        assert receipt['source_bindings']==manifest['source_bindings']
        assert sha256(d/'observations.jsonl')==receipt['observations_sha256']
        assert sha256(d/'extra_state_witness.json')==receipt['extra_state_witness_sha256']
        rows=[json.loads(line) for line in (d/'observations.jsonl').read_text().splitlines()]
        assert len(rows)==9 and len({(r['repetition'],r['method']) for r in rows})==9
        witnesses=[]
        for r in rows:
            p=d/f"rep{r['repetition']}_{r['method']}_model.json"
            assert sha256(p)==r['output_sha256'] and p.stat().st_size==r['output_bytes']
            witnesses.append(json.loads(p.read_text()))
            assert math.isclose(r['request_e2e_seconds'],r['request_preparation_seconds']+r['algorithm_seconds']+r['output_seconds'],rel_tol=1e-12,abs_tol=1e-12)
            assert math.isclose(sum(r['components'].values()),r['algorithm_seconds'],rel_tol=1e-12,abs_tol=1e-12)
            raw.append({k:v for k,v in r.items() if k not in ('components','order')}|{f'component_{k}':v for k,v in r['components'].items()}|{'order':'/'.join(r['order'])})
        assert all(x==receipt['full_model_witness'] for x in witnesses)
        for method in ('fresh','direct','fast'):
            selected=[r for r in rows if r['method']==method]
            assert sorted(r['position'] for r in selected)==[0,1,2]
            entry={k:spec[k] for k in ('case_id','dataset','seed','deleted_client','n','removed_n','removed_fraction')}
            entry['method']=method
            for field in ('algorithm_seconds','request_e2e_seconds','request_preparation_seconds','output_seconds'):
                values=[r[field] for r in selected]
                entry[f'mean_{field}']=mean(values);entry[f'sd_{field}']=sd(values);entry[f'min_{field}']=min(values);entry[f'max_{field}']=max(values)
            for field in selected[0]['components']:entry[f'mean_component_{field}']=mean([r['components'][field] for r in selected])
            case_rows.append(entry)
        methods={r['method']:r for r in case_rows if r['case_id']==spec['case_id']}
        ratio={k:spec[k] for k in ('case_id','dataset','seed','removed_n','removed_fraction')}
        for scope,field in (('algorithm','mean_algorithm_seconds'),('request','mean_request_e2e_seconds')):
            ratio[f'fresh_over_fast_{scope}']=methods['fresh'][field]/methods['fast'][field]
            ratio[f'fresh_over_direct_{scope}']=methods['fresh'][field]/methods['direct'][field]
            ratio[f'direct_over_fast_{scope}']=methods['direct'][field]/methods['fast'][field]
        setup=json.loads((d/'preparation.json').read_text())
        entry={k:spec[k] for k in ('case_id','dataset','seed','n','d','C')}|{'canonical_initial_training_seconds':setup['canonical_initial_training_seconds'],'incremental_compaction_seconds':setup['incremental_compaction_seconds'],'canonical_checkpoint_pickle_bytes':setup['canonical_checkpoint_storage']['pickle_bytes'],'compact_state_pickle_bytes':setup['compact_state_storage']['pickle_bytes'],'checkpoint_serialization_seconds':setup['canonical_checkpoint_storage']['serialization_seconds'],'compact_state_serialization_seconds':setup['compact_state_storage']['serialization_seconds'],'data_load_verify_seconds':setup['full_data_load_verify_seconds'],'compact_summary_slots':setup['compact_summary_slots']}
        for name in ('fresh','direct'):
            saving=methods[name]['mean_request_e2e_seconds']-methods['fast']['mean_request_e2e_seconds']
            entry[f'incremental_break_even_requests_vs_{name}']=math.ceil(setup['incremental_compaction_seconds']/saving) if saving>0 else None
            if name=='fresh':entry['full_setup_break_even_requests_vs_fresh']=math.ceil((setup['canonical_initial_training_seconds']+setup['incremental_compaction_seconds'])/saving) if saving>0 else None
        prep.append(entry);ratios.append(ratio);completed.append(spec['case_id'])
        qdir=run/'quality'/spec['case_id']
        if (qdir/'complete.json').exists():
            qreceipt=json.loads((qdir/'complete.json').read_text());assert qreceipt['status']=='PASS' and qreceipt['source_bindings']==manifest['source_bindings']
            assert sha256(qdir/'quality.json')==qreceipt['quality_sha256']
            for q in json.loads((qdir/'quality.json').read_text()):
                assert q['model_witness']['trajectory'][0]==receipt['full_model_witness']['trajectory'][0]
                assert len(q['model_witness']['trajectory'])==q['T']+1 and len(q['model_witness']['per_round_stats'])==q['T']
                assert q['quality']['retained_group_counts']==spec['retained_group_counts']
                quality.append({'case_id':spec['case_id'],'dataset':spec['dataset'],'seed':spec['seed'],'T':q['T'],'learning_seconds':q['learning_seconds'],**q['quality']['values'],'quality_evaluation_seconds':q['quality']['quality_evaluation_seconds']})
        verification.append({'case_id':spec['case_id'],'saved_model_witnesses_verified':9,'all_model_witnesses_equal':True,'extra_state_receipt_and_hash_verified':True,'component_times_sum_to_algorithm':True,'request_components_sum_to_e2e':True,'balanced_order_verified':True})
    summary=[]
    for dataset in ('all','adult','bank','credit'):
        selected=[r for r in ratios if dataset=='all' or r['dataset']==dataset]
        if not selected:continue
        for scope,field in (('algorithm','algorithm_seconds'),('request','request_e2e_seconds')):
            for method in ('direct','fast'):
                x=[r[f'fresh_over_{method}_{scope}'] for r in selected]
                numerator=sum(r[field] for r in raw if r['method']=='fresh' and (dataset=='all' or r['dataset']==dataset))
                denominator=sum(r[field] for r in raw if r['method']==method and (dataset=='all' or r['dataset']==dataset))
                summary.append({'dataset':dataset,'method':method,'scope':scope,'cases':len(x),'observations_per_method':3*len(x),'fresh_total_seconds':numerator,'method_total_seconds':denominator,'ratio_of_total_times':numerator/denominator,'paired_case_ratio_mean':mean(x),'paired_case_ratio_median':statistics.median(x),'paired_case_ratio_sd':sd(x),'paired_case_ratio_min':min(x),'paired_case_ratio_max':max(x),'case_wins':sum(v>1 for v in x),'cases_at_least_10x':sum(v>=10 for v in x)})
    for name,rows in [('raw_timings.csv',raw),('case_method_timings.csv',case_rows),('paired_ratios.csv',ratios),('aggregate_timings.csv',summary),('preparation_storage.csv',prep),('quality.csv',quality)]:save_csv(out/name,rows)
    status={'run_id':run_id,'completed_core_cases':completed,'missing_core_cases':missing,'raw_observations':len(raw),'quality_rows':len(quality),'core_verification':verification,'scope':'Saved output bytes/receipts/time identities/order rechecked. Extra state values were compared in worker; their saved reference hash is rechecked here. No independent arithmetic or Task C approval.'}
    write_json(ROOT/'RESULTS_VERIFICATION.json',status)
    print(json.dumps({'completed_core_cases':len(completed),'missing':missing,'observations':len(raw),'quality_rows':len(quality),'summary':summary},indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run-id',default='client-c0-20260926-v1');a=p.parse_args();aggregate(a.run_id)
