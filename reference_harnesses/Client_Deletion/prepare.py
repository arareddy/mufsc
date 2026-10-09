from common import *
from datasets import load_dataset,DATASET_FILES
from datetime import datetime,timezone
import platform
manifest_path=SOURCE/'remediation/manifests/data_p124_unique_v2.json'
manifest=json.loads(manifest_path.read_text())
cases=[];inputs={};identities={}
for name in ('adult','bank','credit'):
    cd,go,meta=load_dataset(name,str(DATA),seed=0)
    accepted=next(x for x in manifest['datasets'] if x['dataset']==name)
    assert meta['source_sha256']==accepted['source_sha256']
    assert sha256(DATA/f'{name}_identities.json')==accepted['identity_sha256']
    counts={c:tuple(int(np.count_nonzero(go[c]==g)) for g in (0,1)) for c in cd}
    totals=tuple(sum(x[g] for x in counts.values()) for g in (0,1))
    sizes=sorted(len(v) for v in cd.values());n=len(sizes)
    median2=sizes[(n-1)//2]+sizes[n//2]
    valid=[c for c in cd if all(totals[g]>counts[c][g] for g in (0,1))]
    chosen=min(valid,key=lambda c:(abs(2*len(cd[c])-median2),c)) if valid else None
    identities[name]={str(c):{'source_client_id':meta['source_client_ids'][c],'row_count':len(cd[c]),'ordered_full_row_ids_sha256':hashlib.sha256(np.asarray(meta['source_record_ids'][c],dtype='<i8').tobytes()).hexdigest()} for c in sorted(cd)}
    inputs[name]={'path':meta['source_file'],'sha256':meta['source_sha256'],'identity_path':str(DATA/f'{name}_identities.json'),'identity_sha256':accepted['identity_sha256'],'C':len(cd),'n':meta['n_total'],'d':meta['d'],'clip':meta['clip'],'group_counts':totals,'selected_client':chosen}
    for trial in range(5):
        spec={'case_id':f'{name}_k10_seed{10000+trial}','case_index':len(cases),'dataset':name,'seed':10000+trial,'trial':trial,'dataset_selection_seed':0,'k':10,'T':0,'L':6,'gamma':0.0,'anchor_lloyd_iters':0,'scale_bits':12,'clip':meta['clip'],'deleted_client':chosen,'excluded':chosen is None}
        if chosen is not None:
            spec.update(n=meta['n_total'],C=len(cd),d=meta['d'],removed_n=len(cd[chosen]),removed_fraction=len(cd[chosen])/meta['n_total'],removed_group_counts=counts[chosen],removed_group_proportions=[x/len(cd[chosen]) for x in counts[chosen]],retained_group_counts=[totals[g]-counts[chosen][g] for g in (0,1)],source_client_id=meta['source_client_ids'][chosen],removed_source_rows=[int(x) for x in meta['source_record_ids'][chosen]])
        cases.append(spec)
grid={'frozen_at_utc':datetime.now(timezone.utc).isoformat(),'before_any_new_training_or_benchmark':True,'selection_rule':'Among clients leaving both groups positive, minimize absolute distance from median size over all original clients; tie by persistent run client ID. Median compared as doubled integer. Same input partition and chosen client across all five seeds.','timing_repetitions':3,'method_order':'For case index i and repetition r, rotate [fresh,direct,fast] left by (i+r)%3. Each method occupies every position once per case.','quality_repetitions':1,'optional_quality_budgets':[1,2],'cases':cases}
for name,value in [('FROZEN_GRID.json',grid),('INPUTS.json',{'files':inputs,'accepted_manifest_path':str(manifest_path),'accepted_manifest_sha256':sha256(manifest_path)}),('IDENTITY_REGISTRY.json',identities)]:
    write_json(ROOT/name,value,immutable=True)
print(json.dumps({'cases':len(cases),'grid_sha256':sha256(ROOT/'FROZEN_GRID.json'),'inputs':inputs},indent=2))
