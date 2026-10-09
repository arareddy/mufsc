#!/usr/bin/env python3
"""Freeze and prepare a new public ACS population; never match historical results."""
from pathlib import Path
import os
for _key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):
    os.environ[_key]='1'
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import inspect
import io
import json
import math
import pickle
import sys
import numpy as np
import pandas as pd
import folktables
from folktables import ACSEmployment

P3=Path(__file__).resolve().parents[1]
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'core/experiments'),str(ROOT/'core/src')]
from p3_acs import (STATE_FIPS,FEATURE_NAMES,FrozenACSPool,prepare_federation,
                    fractional_design,sample_deletion,federation_diagnostic_rows,deletion_count)
from fixedpoint import FixedPointConfig,represented_clients
from reproducible import sha256,content_hash,jsonable,source_manifest

VERSION='acs2018-ftf1-p3-v1'
DATA=P3/'data'/VERSION
PROTOCOL=P3/'specification/PROTOCOL_v1.json'


def write_bytes(path, value, verify=False):
    path=Path(path)
    if path.exists():
        if path.read_bytes()!=value:raise RuntimeError(f'Frozen output differs: {path}')
        return
    if verify:raise RuntimeError(f'Regeneration cannot create missing output: {path}')
    path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_name(path.name+'.part')
    temporary.write_bytes(value)
    os.replace(temporary,path)


def save_json(path, value, verify=False):
    write_bytes(path,(json.dumps(jsonable(value),indent=2,sort_keys=True,allow_nan=False)+'\n').encode(),verify)


def save_array(path,array,verify=False):
    stream=io.BytesIO();np.save(stream,np.asarray(array),allow_pickle=False)
    write_bytes(path,stream.getvalue(),verify)


def save_csv(path,rows,verify=False):
    stream=io.StringIO(newline='')
    writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    write_bytes(path,stream.getvalue().encode(),verify)


def point_dict(point):
    return dict(design_index=point.design_index,n=point.n,C=point.C,k=point.k,T=point.T,
                deletion_fraction=format(point.deletion_fraction,'f'),r=deletion_count(point.n,point.deletion_fraction),
                seeds=list(range(5)),selection_reason=point.selection_reason)


def freeze_protocol():
    check_environment()
    if PROTOCOL.exists():
        value=json.loads(PROTOCOL.read_text())
        if value['preparer_sha256']!=sha256(Path(__file__)):raise RuntimeError('Preparer changed after protocol freeze')
        return value
    points=[point_dict(point) for point in fractional_design()]
    protocol=dict(schema_version=1,dataset_version=VERSION,created_utc=datetime.now(timezone.utc).isoformat(),
      scientific_scope='New authorized public ACS population; no historical count/hash matching, original recovery, or old seed1 causal diagnosis',
      preparer_sha256=sha256(Path(__file__)),reference_helper_sha256=sha256(ROOT/'corrected_project/experiments/p3_acs.py'),
      code_and_map=source_manifest(),environment_manifest_sha256=sha256(P3/'manifests/environment_v1.json'),
      requirements_lock_sha256=sha256(P3/'manifests/requirements_lock_v1.txt'),
      source_manifest_sha256=sha256(P3/'manifests/source_manifest_v1.json'),
      state_concatenation_order=[dict(state=s,fips=f) for s,f in STATE_FIPS.items()],excluded=['DC','PR'],
      survey=dict(year=2018,horizon='1-Year',type='person'),feature_columns=list(FEATURE_NAMES),
      folktables_scope='Pinned ACSEmployment sixteen-feature schema and identity prefilter only; do not call df_to_numpy or its postprocessor. Our group is SEX, not default RAC1P.',
      csv_parsing='pandas2.3.3 C parser, low_memory=False, float64 numeric selected columns, SERIALNO pandas string; preserve file row order and zero-based source row index',
      eligibility='Require ST equal file FIPS; retain finite SEX in{1,2} and finite positive PUMA; require eligible PUMA integral; identity prefilter; no age/employment/income threshold',
      missing_values='After eligibility, replace feature NaN with numeric-1; reject remaining feature infinity. Require nonmissing SERIALNO and integral positive SPORDER; do not silently filter invalid native IDs.',
      feature_encoding='Keep all categorical integer codes as numeric coordinates, including SEX; no one-hot expansion, weighting, learned ordering or target column',
      group_definition='A=SEX1 maps0; B=SEX2 maps1',
      native_identity='(2018,stateFIPS,SERIALNO,SPORDER); additionally bind source CSV SHA256 and zero-based CSV row. Geography/PUMA is lineage, not a replacement native identity.',
      standardization='Convert each eligible raw feature array to C-contiguous float64; concatenate states in state_concatenation_order and within-state original file row order into one C-contiguous array. NumPy2.3.5 mean(axis=0,dtype=float64) and std(axis=0,ddof=0,dtype=float64); replace zero std by1. Apply (X-mean)/std before client selection; never refit after sampling or deletion.',
      clipping='Fix clip=ceil(max absolute standardized coordinate over entire eligible50-state pool)+1; b=12; one canonical ties-to-even encoding. Archive raw standardized float64 and exact encoded int64 arrays; all initialization/refinement/quality use the represented map.',
      encoded_hash_contract='Sorted client IDs; for each client concatenate little-endian int64[client,n,d], C-order encoded X int64 bytes, group int64 bytes, source-row int64 bytes. Geography and native-ID files have separate hashes.',
      client_selection='Sort all state names lexicographically or all state:PUMA:five-digit-PUMA keys lexicographically. Use PCG64 default_rng(SeedSequence([0,role])),role0 state or1 PUMA; permute once, take first C. States C10/25/50; PUMA C100/250.',
      quota='Exact integer largest-remainder allocation proportional to eligible client size; ties by selected prefix position. Require n<=capacity and all quotas positive; no population tuning.',
      derived_seed='SHA256 of ASCII str(base) then NUL+UTF8(role), then NUL+UTF8(str(value)) for each value; first8digest bytes interpreted unsigned little-endian',
      record_sampling='For geography: derived_seed(1,record-subsample,n,C,client_type,geography); PCG64 default_rng(seed).choice(size,quota,replace=False), sort indices; if quota==size use all rows without a draw.',
      deletion_sampling='r=max(1,ROUND_HALF_UP(n*fraction)); derive seed(2,uniform-deletion,master_seed,n,C,k,T,format(fraction,f)); for attempt0 derive seed(deletion_seed,validity-attempt,0), sorted uniform size-r choice from pooled client-order rows without replacement. Requests independent and noncumulative.',
      deletion_validity='Reference helper permits up to100 fresh attempts if a global group disappears; require r<min(n_A,n_B) for every new request, proving all candidates valid and attempt0 always accepted. Otherwise stop before outcomes; never silently condition a claimed unconditional law.',
      matrix=points,populations=[dict(n=n,C=C) for n,C in sorted({(p['n'],p['C']) for p in points})],
      execution=dict(methods=['fresh','none','basic','runnerup'],gamma=0.0,b=12,L=6,anchor_lloyd_iters=0,
                     indexed_centers=True,abandon_threshold=0.5,pilot_order='design15 seeds0..4 (r1), then design16 seeds0..4 (r10), before remaining matrix'))
    save_json(PROTOCOL,protocol)
    return protocol


def check_environment():
    frozen=json.loads((P3/'manifests/environment_v1.json').read_text())
    actual={d.metadata['Name']:d.version for d in importlib.metadata.distributions()}
    if sys.version!=frozen['python'] or actual!=frozen['packages']:
        raise RuntimeError('Preparation runtime differs from frozen Python/package versions')
    if sha256(Path(inspect.getfile(ACSEmployment._preprocess)))!=frozen['folktables_acs_source_sha256']:
        raise RuntimeError('Pinned Folktables source changed')


def build_pool(protocol,verify=False):
    source=json.loads((P3/'manifests/source_manifest_v1.json').read_text())
    if source['source_states']!=50 or set(source['states'])!=set(STATE_FIPS):raise RuntimeError('Source manifest state coverage mismatch')
    if tuple(ACSEmployment.features)!=tuple(FEATURE_NAMES):raise RuntimeError('Folktables feature schema changed')
    raw={};groups={};pumas={};rows={};native={};diagnostics=[]
    numeric=list(dict.fromkeys([*FEATURE_NAMES,'ST','PUMA','SPORDER']))
    for state,fips in STATE_FIPS.items():
        record=source['states'][state];path=P3/record['csv_file']
        if sha256(path)!=record['csv_sha256']:raise RuntimeError(f'Source bytes changed:{state}')
        frame=pd.read_csv(path,usecols=[*numeric,'SERIALNO'],dtype={**{k:'float64' for k in numeric},'SERIALNO':'string'},low_memory=False,engine='c')
        if ACSEmployment._preprocess(frame) is not frame:raise RuntimeError('Expected identity prefilter')
        if not np.all(frame['ST'].to_numpy()==fips):raise RuntimeError(f'State code mismatch:{state}')
        sex=frame['SEX'].to_numpy();puma=frame['PUMA'].to_numpy()
        valid=np.isfinite(sex)&np.isin(sex,[1,2])&np.isfinite(puma)&(puma>0)
        eligible=frame.loc[valid]
        sex=sex[valid];puma=puma[valid]
        if not np.all(puma==np.floor(puma)):raise RuntimeError('Nonintegral eligible PUMA')
        feature=np.ascontiguousarray(eligible.loc[:,list(FEATURE_NAMES)].to_numpy(dtype=np.float64),dtype='<f8')
        nan_count=np.isnan(feature).sum(axis=0).astype(np.int64);feature[np.isnan(feature)]=-1.0
        if not np.isfinite(feature).all() or not np.all(feature==np.floor(feature)):raise RuntimeError('Nonfinite or noninteger raw feature code')
        if eligible['SERIALNO'].isna().any():raise RuntimeError('Missing eligible native SERIALNO')
        serial=np.asarray(eligible['SERIALNO'].astype(str).tolist(),dtype=str)
        order=eligible['SPORDER'].to_numpy()
        if not np.all(np.isfinite(order)&(order>0)&(order==np.floor(order))):raise RuntimeError('Invalid SPORDER')
        order=order.astype('<i8');row=np.asarray(eligible.index,dtype='<i8')
        identities=set(zip(serial.tolist(),order.tolist()))
        if len(identities)!=len(row):raise RuntimeError(f'Duplicate native identities:{state}')
        raw[state]=feature;groups[state]=np.where(sex==1,0,1).astype('<i8');pumas[state]=puma.astype('<i8');rows[state]=row
        native[state]=dict(serialno=serial,sporder=order,source_row=row)
        location=DATA/'source_id_catalog'/state
        for name,array in dict(source_row=row,SERIALNO=serial,SPORDER=order,PUMA=pumas[state],group=groups[state]).items():
            save_array(location/f'{name}.npy',array,verify)
        diagnostics.append(dict(state=state,fips=fips,source_rows=len(frame),eligible_rows=len(row),excluded_rows=int((~valid).sum()),
                                group_A=int((sex==1).sum()),group_B=int((sex==2).sum()),natural_pumas=len(np.unique(puma)),
                                feature_nan_replacements=nan_count.tolist(),source_csv_sha256=record['csv_sha256']))
        print(json.dumps(dict(step='read_state',state=state,eligible_rows=len(row))),flush=True)
    pooled=np.ascontiguousarray(np.concatenate([raw[s] for s in STATE_FIPS],axis=0),dtype='<f8')
    if not pooled.flags.c_contiguous:raise RuntimeError('Unexpected reduction layout')
    mean=pooled.mean(axis=0,dtype=np.float64);std=pooled.std(axis=0,ddof=0,dtype=np.float64);std=np.where(std==0,1.0,std)
    integer=pooled.astype('<i8')
    maximum=int(np.max(np.abs(integer)))
    if len(integer)*maximum*maximum>=2**63:raise RuntimeError('Raw moment range unsafe')
    exact_sum=integer.sum(axis=0,dtype=np.int64);exact_ss=(integer*integer).sum(axis=0,dtype=np.int64)
    del pooled,integer
    state_data={};puma_data={};puma_groups={};puma_rows={};max_abs=0.0
    for state in STATE_FIPS:
        value=np.ascontiguousarray((raw.pop(state)-mean)/std,dtype='<f8');state_data[state]=value
        max_abs=max(max_abs,float(np.max(np.abs(value))))
        for puma in np.unique(pumas[state]):
            mask=pumas[state]==puma;key=f'{state}:PUMA:{int(puma):05d}'
            puma_data[key]=np.ascontiguousarray(value[mask]);puma_groups[key]=np.ascontiguousarray(groups[state][mask]);puma_rows[key]=np.ascontiguousarray(rows[state][mask])
    clip=float(math.ceil(max_abs)+1)
    transform=dict(protocol_sha256=sha256(PROTOCOL),source_manifest_sha256=sha256(P3/'manifests/source_manifest_v1.json'),
                   pool_rows=sum(len(v) for v in state_data.values()),d=16,feature_names=list(FEATURE_NAMES),
                   feature_mean=mean,feature_std=std,mean_hex=[x.hex() for x in mean],std_hex=[x.hex() for x in std],
                   raw_feature_integer_sums=exact_sum,raw_feature_integer_squared_sums=exact_ss,
                   max_abs_standardized=max_abs,clip=clip,b=12,reduction_layout='C-contiguous float64; FIPS-order states and source row order',
                   state_diagnostics=diagnostics,native_identity='2018,stateFIPS,SERIALNO,SPORDER',
                   historical_identity='not asserted; new public population')
    save_json(DATA/'transform.json',transform,verify)
    return FrozenACSPool(state_data,groups,rows,puma_data,puma_groups,puma_rows,mean,std,clip,
                         tuple(source['states'][s]['csv_file'] for s in STATE_FIPS),folktables.__version__),native,source


def prepare(verify=False):
    check_environment()
    protocol=json.loads(PROTOCOL.read_text())
    if protocol['preparer_sha256']!=sha256(Path(__file__)):raise RuntimeError('Preparer differs from frozen protocol')
    if protocol['code_and_map']!=source_manifest():raise RuntimeError('Canonical source/map differs from protocol')
    for key,path in [('source_manifest_sha256',P3/'manifests/source_manifest_v1.json'),('environment_manifest_sha256',P3/'manifests/environment_v1.json'),('requirements_lock_sha256',P3/'manifests/requirements_lock_v1.txt')]:
        if protocol[key]!=sha256(path):raise RuntimeError(f'Frozen dependency differs:{key}')
    pool,native,source=build_pool(protocol,verify)
    points=fractional_design();population_rows=[];request_rows=[]
    for n,C in sorted({(p.n,p.C) for p in points}):
        federation,reason=prepare_federation(pool,n,C)
        if reason:raise RuntimeError(reason)
        keys=sorted(federation.client_data);base=DATA/f'n{n}_C{C}'
        cfg=FixedPointConfig(scale_bits=12,clip=pool.fixed_point_clip)
        represented,encoded=represented_clients(federation.client_data,cfg)
        encoded_digest=hashlib.sha256();native_digest=hashlib.sha256();native_rows=[]
        offsets=[0]
        for c in keys:
            geography=federation.geography_of[c];state=geography.split(':')[0];fips=STATE_FIPS[state]
            group=federation.group_of[c];source_ids=federation.source_record_ids[c]
            encoded_digest.update(np.asarray([c,len(group),16],dtype='<i8').tobytes())
            for a in (encoded[c],group,source_ids):encoded_digest.update(np.asarray(a,dtype='<i8').tobytes())
            positions=np.searchsorted(native[state]['source_row'],source_ids)
            if not np.array_equal(native[state]['source_row'][positions],source_ids):raise RuntimeError('Source-row join mismatch')
            for local,(row,pos) in enumerate(zip(source_ids,positions)):
                serial=str(native[state]['serialno'][pos]);order=int(native[state]['sporder'][pos]);identifier=f'2018:{fips:02d}:{serial}:{order}'
                native_digest.update(identifier.encode()+b'\0')
                native_rows.append(dict(client_id=c,local_row=local,geography=geography,source_row=int(row),state_fips=fips,SERIALNO=serial,SPORDER=order,native_id=identifier,source_csv_sha256=source['states'][state]['csv_sha256']))
            offsets.append(offsets[-1]+len(group))
        flat=dict(standardized_X=np.concatenate([federation.client_data[c] for c in keys]),
                  represented_X_int=np.concatenate([encoded[c] for c in keys]),groups=np.concatenate([federation.group_of[c] for c in keys]),
                  source_row_ids=np.concatenate([federation.source_record_ids[c] for c in keys]),
                  client_offsets=np.asarray(offsets,dtype='<i8'))
        for name,array in flat.items():save_array(base/f'{name}.npy',array,verify)
        save_csv(base/'native_ids.csv',native_rows,verify)
        save_json(base/'geography.json',federation.geography_of,verify)
        n_A=int((flat['groups']==0).sum());n_B=n-n_A
        meta=dict(version=VERSION,data_origin='new public Census acquisition; no historical equivalence claim',n=n,C=C,d=16,
                  clip=pool.fixed_point_clip,b=12,protocol_sha256=sha256(PROTOCOL),transform_sha256=sha256(DATA/'transform.json'),
                  source_manifest_sha256=sha256(P3/'manifests/source_manifest_v1.json'),
                  geography_of=federation.geography_of,source_record_ids=federation.source_record_ids,
                  selected_clients=federation.selected_clients,eligible_sizes=federation.eligible_sizes,quotas=federation.quotas,
                  client_type=federation.client_type,capacity=federation.capacity,permutation_sha256=federation.permutation_hash,
                  membership_source_row_sha256=federation.sample_hash,native_membership_sha256=native_digest.hexdigest(),
                  encoded_X_sha256=encoded_digest.hexdigest(),native_ids_file=f'n{n}_C{C}/native_ids.csv',native_ids_sha256=sha256(base/'native_ids.csv'),
                  group_counts=[n_A,n_B],historical_feature_identity_verified=False,historical_transform_identity_verified=False,
                  historical_causal_diagnostic_permitted=False)
        save_json(base/'population.json',meta,verify)
        write_bytes(DATA/f'n{n}_C{C}.pkl',pickle.dumps(dict(client_data=federation.client_data,group_of=federation.group_of,meta=meta),protocol=5),verify)
        population_rows.append(dict(n=n,C=C,group_A=n_A,group_B=n_B,clip=pool.fixed_point_clip,capacity=federation.capacity,
                                    membership_source_row_sha256=federation.sample_hash,native_membership_sha256=native_digest.hexdigest(),encoded_X_sha256=encoded_digest.hexdigest()))
        save_csv(base/'client_diagnostics.csv',federation_diagnostic_rows(federation,n,C),verify)
        for point in points:
            if (point.n,point.C)!=(n,C):continue
            r=deletion_count(n,point.deletion_fraction)
            if r>=min(n_A,n_B):raise RuntimeError('Request may remove an entire group; stop rather than condition declared sampling')
            for seed in range(5):
                removed,digest,deletion_seed,records=sample_deletion(federation,point,seed)
                for record in records:
                    selected=native_rows[offsets[record['client_id']]+record['local_sample_index']]
                    record.update({k:selected[k] for k in ('state_fips','SERIALNO','SPORDER','native_id','source_csv_sha256')})
                request=dict(data_version=VERSION,protocol_sha256=sha256(PROTOCOL),design_index=point.design_index,master_seed=seed,
                             removed=removed,source_records=records,removal_source_hash=digest,deletion_seed=deletion_seed,
                             accepted_validity_attempt=0,unconditional_validity_proof=dict(r=r,group_A=n_A,group_B=n_B,r_less_than_both_groups=True))
                request_path=DATA/'requests'/f'design{point.design_index}_seed{seed}.json';save_json(request_path,request,verify)
                request_rows.append(dict(design_index=point.design_index,master_seed=seed,n=n,C=C,k=point.k,T=point.T,r=r,deletion_seed=deletion_seed,source_identity_hash=digest,request_sha256=sha256(request_path)))
        print(json.dumps(dict(step='population',n=n,C=C,encoded_X_sha256=encoded_digest.hexdigest())),flush=True)
        del federation,represented,encoded,flat,native_rows
    save_csv(DATA/'populations.csv',population_rows,verify);save_csv(DATA/'requests.csv',sorted(request_rows,key=lambda v:(v['design_index'],v['master_seed'])),verify)
    files={str(path.relative_to(DATA)):sha256(path) for path in sorted(DATA.rglob('*')) if path.is_file() and path.name!='manifest.json'}
    manifest=dict(schema_version=1,version=VERSION,files=files,source_manifest_sha256=sha256(P3/'manifests/source_manifest_v1.json'),
                  protocol_sha256=sha256(PROTOCOL),environment_manifest_sha256=sha256(P3/'manifests/environment_v1.json'),
                  code_sha256=source_manifest()['code_sha256'],map_sha256=source_manifest()['map_sha256'],
                  population_count=len(population_rows),design_count=len(points),request_count=len(request_rows),
                  populations=population_rows,new_public_dataset=True,historical_causal_diagnostic_permitted=False)
    save_json(DATA/'manifest.json',manifest,verify)
    print(json.dumps(dict(status='DETERMINISTIC_REGENERATION_PASS' if verify else 'DATA_PREPARED',population_count=len(population_rows),request_count=len(request_rows),manifest_sha256=sha256(DATA/'manifest.json'))),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    action=parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--freeze-protocol',action='store_true');action.add_argument('--prepare',action='store_true');action.add_argument('--verify-regeneration',action='store_true')
    args=parser.parse_args()
    if args.freeze_protocol:freeze_protocol();print(PROTOCOL)
    else:prepare(args.verify_regeneration)
