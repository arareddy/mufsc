"""Inspect authoritative schemas and freeze cases before training/measurements."""
from common import *
import csv,platform,importlib.metadata,shutil
from fixedpoint import FixedPointConfig,quantize

def main():
    manifest=json.loads((ACS/'manifest.json').read_text());tr=json.loads((ACS/'transform.json').read_text())
    meta=json.loads((POP/'population.json').read_text())
    assert sha(ACS/'transform.json')==meta['transform_sha256']
    files=[]
    for rel in ['transform.json','n100000_C10/standardized_X.npy','n100000_C10/represented_X_int.npy','n100000_C10/groups.npy','n100000_C10/client_offsets.npy','n100000_C10/source_row_ids.npy','n100000_C10/geography.json','n100000_C10/population.json','n100000_C10/native_ids.csv']:
        p=ACS/rel; h=sha(p);assert manifest['files'][rel]==h
        files.append({'path':str(p),'sha256':h,'bytes':p.stat().st_size})
    files.append({'path':str(ACS/'manifest.json'),'sha256':sha(ACS/'manifest.json'),'bytes':(ACS/'manifest.json').stat().st_size})
    x=np.load(POP/'standardized_X.npy',mmap_mode='r');enc=np.load(POP/'represented_X_int.npy',mmap_mode='r')
    off=np.load(POP/'client_offsets.npy');rows=np.load(POP/'source_row_ids.npy',mmap_mode='r');old=np.load(POP/'groups.npy',mmap_mode='r')
    assert tr['feature_names'][-1]=='RAC1P' and x.shape==(100000,16)
    assert np.array_equal(quantize(x,FixedPointConfig(12,8.0)),enc)
    j=tr['feature_names'].index('RAC1P');levels=(np.arange(1,10,dtype=np.float64)-tr['feature_mean'][j])/tr['feature_std'][j]
    group=np.full(len(x),-1,dtype=np.int64)
    for g,lev in enumerate(levels):group[x[:,j]==lev]=g
    assert np.all(group>=0) and len(set(levels))==9
    sex=tr['feature_names'].index('SEX');sexlevels=(np.arange(1,3,dtype=np.float64)-tr['feature_mean'][sex])/tr['feature_std'][sex]
    assert np.array_equal(x[:,sex],sexlevels[old])
    seen=set(); count=0
    with (POP/'native_ids.csv').open() as f:
        for record in csv.DictReader(f):
            c=int(record['client_id']);local=int(record['local_row']);idx=int(off[c])+local
            assert idx==count and int(record['source_row'])==int(rows[idx])
            assert record['geography']==meta['geography_of'][str(c)]
            assert int(meta['source_record_ids'][str(c)][local])==int(rows[idx])
            assert record['native_id'] not in seen;seen.add(record['native_id']);count+=1
    assert count==len(x)
    counts=[np.bincount(group[int(off[c]):int(off[c+1])],minlength=9).tolist() for c in range(10)]
    totals=np.bincount(group,minlength=9).tolist();sizes=np.diff(off).tolist();ss=sorted(sizes);median2=ss[4]+ss[5]
    eligible=[c for c in range(10) if all(totals[g]>counts[c][g] for g in range(9))]
    chosen=min(eligible,key=lambda c:(abs(2*sizes[c]-median2),c))
    registry={str(c):{'geography':meta['geography_of'][str(c)],'n':sizes[c],'group_counts':counts[c],
        'ordered_source_rows_sha256':hashlib.sha256(rows[off[c]:off[c+1]].astype('<i8').tobytes()).hexdigest(),
        'ordered_race_membership_sha256':hashlib.sha256(group[off[c]:off[c+1]].astype('<i8').tobytes()).hexdigest()} for c in range(10)}
    membership=hashlib.sha256(group.astype('<i8').tobytes()).hexdigest()
    write_json(ROOT/'INPUTS.json',{'files':files,'race_attribute':'RAC1P','group_id_rule':'g=original RAC1P code minus 1, codes 1..9; disjoint and exhaustive',
        'race_membership_sha256':membership,'schema_column_zero_based':j,'standardized_levels_hex':[v.hex() for v in levels],
        'verification':{'mapped_rows':count,'unmatched_rows':0,'full_encoding_equal':True,'native_row_alignment_equal':True,'legacy_sex_alignment_equal':True},
        'feature_processing':'All original 16 standardized features, clip=8, b=12; no refitting. RAC1P remains a feature. No survey weighting.',
        'code_dictionary_url':'https://api.census.gov/data/2018/acs/acs1/pums/variables/RAC1P.json'},True)
    write_json(ROOT/'IDENTITY_REGISTRY.json',registry,True)
    cases=[{'case_index':3*i+T,'case_id':f'acs_race9_seed{seed}_T{T}','seed':seed,'T':T,'m':9,'k':10,'deleted_client':chosen} for i,seed in enumerate(range(10000,10005)) for T in (0,1,2)]
    write_json(ROOT/'FROZEN_GRID.json',{'frozen_at_utc':utc(),'pre_outcome':True,'population':'acs2018-ftf1-p3-v1/n100000_C10','n':100000,'C':10,'d':16,'group_counts':totals,
        'selected_client':chosen,'removed_n':sizes[chosen],'removed_counts':counts[chosen],'retained_counts':[totals[g]-counts[chosen][g] for g in range(9)],
        'selection_rule':'Smallest existing ACS n, then C; valid whole client closest to median original size, tie persistent ID; independently of seed/outcomes.',
        'seeds_note':'10000..10004 reuse completed whole-client task training seeds; this is a new ACS race objective, not the earlier ACS binary panel.',
        'solver_iterations':12,'line_bisections':6,'gamma':0.0,'scale_bits':12,'clip':8.0,'anchor_lloyd_iters':0,'repetitions':3,
        'cases':cases,'expected_timed_observations':105,'expected_gate_models':35,'expected_replay_gate_comparisons':20},True)
    write_json(ROOT/'ENVIRONMENT.json',{'created_utc':utc(),'python':sys.version,'executable':sys.executable,'platform':platform.platform(),'numpy':np.__version__,
        'thread_environment':{k:os.environ[k] for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS')},
        'native_threadpool_inspection':'threadpoolctl not installed; environment limits only','packages':{d.metadata['Name']:d.version for d in importlib.metadata.distributions()}},True)
    print(json.dumps({'n':len(x),'m':9,'counts':totals,'chosen':chosen,'removed':sizes[chosen],'removed_counts':counts[chosen],'grid_sha256':sha(ROOT/'FROZEN_GRID.json')}))
if __name__=='__main__':main()
