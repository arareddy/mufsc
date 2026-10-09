"""One P4 setting using the canonical represented-data seeding and update kernels."""
from __future__ import annotations
from fractions import Fraction
from pathlib import Path
import pickle
import time
import numpy as np
from assignment import assign_all
from centralized import run_centralized
from datasets import load_dataset
from exact_numeric import squared_exact
from fair_update import guarded_fair_update, exact_group_cost
from fixedpoint import FixedPointConfig,represented_clients,accumulate_stats,add_stats,new_zero_stats
from merged_baseline import merged_slice_step,build_merged_anchor_table,merged_server_step
from objective import fair_objective
from splitgroup import SplitGroupConfig,local_slice_step,build_anchor_table,server_step
from reproducible import jsonable,write_json,exact_witness,array_witness


def exact_scores(cd,go,centers):
    keys=sorted(cd)
    values=fair_objective(np.concatenate([cd[c] for c in keys]),np.concatenate([go[c] for c in keys]),centers,return_exact=True)
    return {name:{'value':float(v),'numerator':v.numerator,'denominator':v.denominator}
            for name,v in zip(('Phi_A','Phi_B','G','Phi'),values)}


def run_setting(spec,directory,data_dir):
    cd,go,meta=load_dataset(spec['dataset'],data_dir,seed=0)
    fp=FixedPointConfig(scale_bits=spec['scale_bits'],clip=meta['clip'])
    t=time.perf_counter();cd,xi=represented_clients(cd,fp);encoding=time.perf_counter()-t
    ng={g:sum(int(np.sum(y==g)) for y in go.values()) for g in (0,1)}
    slices={};payloads=[];table=None;d=meta['d'];k=spec['k'];gamma=spec['gamma']
    start=time.perf_counter();local_time=0.0
    if spec['method']=='centralized':
        centers=run_centralized(cd,go,spec['seed'],k)
        server_time=time.perf_counter()-start
        # Explicit serialized local input transfer representation, never claimed
        # to be measured network transport, and distinct from model-output size.
        payloads=[pickle.dumps({'client_id':c,'X':cd[c],'group':go[c]},protocol=5) for c in sorted(cd)]
    elif spec['method']=='splitgroup_2k':
        cfg=SplitGroupConfig(k=k,gamma=gamma,num_groups=2)
        for c in sorted(cd):
            for g in (0,1):
                mask=go[c]==g
                if not np.any(mask):continue
                slices[(c,g)]=local_slice_step(cd[c][mask],spec['seed'],c,g,cfg)
                r=slices[(c,g)]
                payloads.append(pickle.dumps({'client':c,'group':g,'anchors':r['anchors'],'mult':r['mult']},protocol=5))
        local_time=time.perf_counter()-start
        t=time.perf_counter();table=build_anchor_table(slices,ng,cfg);centers=server_step(table,spec['seed'],cfg,0)
        server_time=time.perf_counter()-t
    else:
        budget=k if spec['method']=='merged_1k' else 2*k
        for c in sorted(cd):
            slices[c]=merged_slice_step(cd[c],go[c],spec['seed'],c,budget,gamma)
            r=slices[c]
            payloads.append(pickle.dumps({'client':c,'anchors':r['anchors'],'h_A':r['h_A'],'h_B':r['h_B']},protocol=5))
        local_time=time.perf_counter()-start
        t=time.perf_counter();table=build_merged_anchor_table(slices,ng[0],ng[1]);centers=merged_server_step(table,spec['seed'],k)
        server_time=time.perf_counter()-t
    phase1_seconds=time.perf_counter()-start
    warm=centers.copy();warm_scores=exact_scores(cd,go,warm)
    Q=Fraction(0);Dloc=Fraction(0);Dq=Fraction(0);residuals=[]
    anchors=[];reps=[];weights=[]
    for key,res in slices.items():
        if isinstance(key,tuple):
            c,g=key;mask=go[c]==g;localX=cd[c][mask];localI=xi[c][mask];localG=go[c][mask]
            localweights=[Fraction(int(h),ng[g]) for h in res['mult']]
        else:
            c=key;localX=cd[c];localI=xi[c];localG=go[c]
            localweights=[Fraction(int(a),ng[0])+Fraction(int(b),ng[1]) for a,b in zip(res['h_A'],res['h_B'])]
        labels=assign_all(localX,res['reps'])[0]
        N,S,SS=accumulate_stats(localI,localG,labels,2,res['k_e'])
        for g in (0,1):
            Dloc+=exact_group_cost(res['reps'],N[g],S[g],SS[g],ng[g],fp.scale)
            Dq+=exact_group_cost(res['anchors'],N[g],S[g],SS[g],ng[g],fp.scale)
        for z,q,w in zip(res['reps'],res['anchors'],localweights):
            residual=squared_exact(z,q);residuals.append(residual);Q+=w*residual
            reps.append(z);anchors.append(q);weights.append(w)
    stats=[];trajectory=[warm];updates=[]
    t=time.perf_counter()
    for round_index in range(spec['T']):
        N,S,SS=new_zero_stats(2,k,d)
        for c in sorted(cd):
            labels=assign_all(cd[c],centers)[0]
            Nc,Sc,SSc=accumulate_stats(xi[c],go[c],labels,2,k)
            N,S,SS=add_stats((N,S,SS),(Nc,Sc,SSc))
        stats.append((N,S,SS))
        centers,info=guarded_fair_update(centers,N,S,SS,ng[0],ng[1],k,spec['L'],fp.scale)
        updates.append(jsonable(info));trajectory.append(centers.copy())
    phase2=time.perf_counter()-t
    final_scores=exact_scores(cd,go,centers)
    def rational_value(v):return dict(value=float(v),numerator=v.numerator,denominator=v.denominator)
    quant=None
    if residuals:
        an=np.asarray(anchors);rp=np.asarray(reps)
        unique,counts=np.unique(an,axis=0,return_counts=True)
        nr_unique=len(np.unique(rp,axis=0));na_unique=len(unique)
        collided={tuple(row) for row,count in zip(unique,counts) if count>1}
        collision_mass=sum(w for row,w in zip(an,weights) if tuple(row) in collided)
        H=sum(w*squared_exact(q,warm[j]) for q,w,j in zip(table['anchors'],table['weights'],assign_all(table['anchors'],warm)[0]))
        # Binary64 grid construction can add representation rounding beyond
        # the ideal d*gamma^2/2 envelope. Report actual residual/bound, no forced pass.
        envelope=Fraction(d,2)*Fraction.from_float(float(gamma))**2
        quant=dict(mean_squared_residual=rational_value(sum(residuals)/len(residuals)),
                   max_squared_residual=rational_value(max(residuals)),weighted_Q=rational_value(Q),
                   ideal_grid_Q_envelope=rational_value(envelope),actual_Q_within_ideal_grid_envelope=Q<=envelope,
                   D_loc=rational_value(Dloc),D_q=rational_value(Dq),anchor_H=rational_value(H),
                   n_anchor_ids=len(anchors),n_unique_anchor_locations=na_unique,
                   duplicate_ids=len(anchors)-na_unique,baseline_duplicate_ids=len(reps)-nr_unique,
                   additional_quantization_duplicate_ids=nr_unique-na_unique,
                   weight_on_collided_locations=rational_value(collision_mass),
                   definition='exact squared Euclidean residual of represented q-z; mean unweighted over representative IDs; Q uses normalized server weights')
    result=dict(spec=spec,data_provenance=meta,encoding_seconds=encoding,
                warm=warm_scores,final=final_scores,quantization=quant,
                phase1_seconds=phase1_seconds,local_seeding_seconds=local_time,server_seeding_seconds=server_time,phase2_seconds=phase2,
                communication=dict(serialized_payload_bytes=sum(map(len,payloads)),serialization='pickle protocol 5, explicit client dictionaries',
                                   coordinate_count=(sum(len(r['anchors'])*d for r in slices.values()) if slices else sum(x.size for x in cd.values())),
                                   coordinate_array_bytes=(sum(r['anchors'].nbytes for r in slices.values()) if slices else sum(x.nbytes for x in cd.values())),
                                   scope='serialized logical Phase I input payload only; no actual network measurement; centralized uploads represented records+groups'),
                model_output_bytes=centers.nbytes,slice_results=jsonable(slices),anchor_table=jsonable(table),
                update_branches=updates,witness=exact_witness(dict(trajectory=trajectory,per_round_stats=stats,final_centers=centers)))
    write_json(Path(directory)/'setting.json',result)
    return dict(method_rows=1,warm_and_final_quality=True,serialized_payload_bytes=result['communication']['serialized_payload_bytes'])
