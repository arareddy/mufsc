"""Independent reporting/certificate check; imports no learner/assignment/solver.

Consumes saved integer moments, exact rational traces and binary64 byte witnesses.
Does not independently reassign the full real population; tiny raw-row oracle does.
"""
from common import ROOT,sha,jsonbytes,write_json,utc
from fractions import Fraction as Q
import json,csv,struct,math,statistics as st,collections
RUN=ROOT/'runs/multigroup-20260926-v1'

def decode(w):
    assert w['dtype']=='<f8';k,d=w['shape'];b=bytes.fromhex(w['bytes_hex']);assert len(b)==8*k*d
    vals=list(struct.unpack('<'+'d'*(k*d),b));assert all(math.isfinite(x) for x in vals)
    assert [x.hex() for x in vals]==w['float_hex']
    return [[Q.from_float(x) for x in vals[j*d:(j+1)*d]] for j in range(k)]

def validate_stats(stats,ns,k,d):
    N,S,SS=stats;m=len(ns);assert len(N)==len(S)==len(SS)==m
    for g in range(m):
        assert len(N[g])==len(S[g])==len(SS[g])==k and sum(N[g])==ns[g]
        for j in range(k):
            assert type(N[g][j]) is int and N[g][j]>=0 and type(SS[g][j]) is int and SS[g][j]>=0
            assert len(S[g][j])==d and all(type(v) is int for v in S[g][j])
            if N[g][j]==0:assert SS[g][j]==0 and not any(S[g][j])
            else:assert sum(x*x for x in S[g][j])<=N[g][j]*SS[g][j]

def costs(c,stats,ns,scale=4096):
    N,S,SS=stats;out=[]
    for g,n in enumerate(ns):
        total=Q(0)
        for j,row in enumerate(c):
            total+=Q(SS[g][j],scale*scale)
            total+=sum(N[g][j]*v*v-2*Q(S[g][j][a],scale)*v for a,v in enumerate(row))
        out.append(total/n)
    return tuple(out)

def dual_and_center(lam,stats,ns,old,scale=4096):
    N,S,SS=stats;m=len(ns);k=len(old);d=len(old[0]);weight=[v/n for v,n in zip(lam,ns)]
    assert len(lam)==m and all(x>=0 for x in lam) and sum(lam)==1
    constant=sum(weight[g]*sum(SS[g]) for g in range(m))/(scale*scale);centers=[]
    for j in range(k):
        mass=sum(weight[g]*N[g][j] for g in range(m));moment=[sum(weight[g]*S[g][j][q] for g in range(m)) for q in range(d)]
        if mass:
            centers.append([s/(scale*mass) for s in moment]);constant-=sum(s*s for s in moment)/(scale*scale*mass)
        else:
            assert not any(moment);occupied=[g for g in range(m) if N[g][j]]
            centers.append([Q(s,scale*N[occupied[0]][j]) for s in S[occupied[0]][j]] if len(occupied)==1 else old[j])
    return constant,centers

def verify_update(info,stats,ns,old,new):
    values={};exact_grad={};rounded={}
    for row in info['evaluations']:
        lam=tuple(map(Q,row['lambda']));D,c=dual_and_center(lam,stats,ns,old)
        assert D==Q(row['D']);g=costs(c,stats,ns);assert sum(l*v for l,v in zip(lam,g))==D
        r=[[Q.from_float(float(v)) for v in x] for x in c];p=costs(r,stats,ns)
        assert p==tuple(map(Q,row['represented_group_costs'])) and max(p)==Q(row['Phi'])
        assert D<=max(p);values[lam]=(D,max(p));exact_grad[lam]=g;rounded[lam]=r
    best=min(values,key=lambda l:(values[l][1],l));lower=min(values,key=lambda l:(-values[l][0],l))
    assert best==tuple(map(Q,info['candidate_lambda'])) and lower==tuple(map(Q,info['dual_lambda']))
    before=costs(old,stats,ns);after=costs(new,stats,ns)
    accepted=values[best][1]<=max(before);assert info['accepted']==accepted
    assert new==(rounded[best] if accepted else old)
    assert before==tuple(map(Q,info['incumbent_costs'])) and after==tuple(map(Q,info['returned_costs']))
    assert max(after)==Q(info['Phi']) and sum(after)==Q(info['G'])
    assert Q(info['D'])==values[lower][0] and Q(info['gap'])==max(after)-values[lower][0]>=0
    assert max(after)<=max(before)
    m=len(ns);current=tuple(Q(1,m) for _ in ns)
    assert len(info['steps'])<=12 and info['unique_evaluations']==len(values)
    for t,step in enumerate(info['steps']):
        assert step['iteration']==t and tuple(map(Q,step['start_lambda']))==current
        grad=exact_grad[current];target=min(range(m),key=lambda g:(-grad[g],g));assert target==step['target_group']
        assert Q(step['FW_gap'])==grad[target]-values[current][0]>0
        vertex=tuple(Q(int(g==target)) for g in range(m));direction=tuple(a-b for a,b in zip(vertex,current));candidates=[current,vertex]
        lo=Q(0);hi=Q(1);assert len(step['branches'])==6
        for branch in step['branches']:
            alpha=(lo+hi)/2;assert Q(branch['alpha'])==alpha
            lam=tuple(a+alpha*b for a,b in zip(current,direction));derivative=sum(a*b for a,b in zip(direction,exact_grad[lam]))
            assert derivative==Q(branch['derivative']) and (derivative>0)==branch['lower']
            if derivative>0:lo=alpha
            else:hi=alpha
            candidates.append(lam)
        chosen=min(candidates,key=lambda l:(-values[l][0],l));assert chosen==tuple(map(Q,step['chosen_lambda']))
        assert step['stalled']==(chosen==current);current=chosen
    if info['termination']=='exact_zero_FW_gap':assert max(exact_grad[current])-values[current][0]==0
    else:assert info['termination']=='iteration_bound' and len(info['steps'])==12
    return len(values)

def csvwrite(name,rows):
    out=ROOT/'tables'/name;out.parent.mkdir(exist_ok=True)
    with out.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)

def main():
    assert json.loads((RUN/'status.json').read_text())['status']=='COMPLETE'
    grid=json.loads((ROOT/'FROZEN_GRID.json').read_text());ns=grid['retained_counts'];manifest=json.loads((RUN/'run_manifest.json').read_text())
    for path,h in manifest['bindings'].items():assert sha(ROOT/path)==h
    raw=[];quality=[];group_quality=[];optimization=[];preparation=[];gates=0;replays=0;arrays=0;moment_triples=0;certificate_evaluations=0;models={}
    for spec in grid['cases']:
        directory=RUN/spec['case_id'];receipt=json.loads((directory/'complete.json').read_text());assert receipt['status']=='PASS' and receipt['bindings']==manifest['bindings']
        for n,h in receipt['artifacts'].items():assert sha(directory/n)==h
        T=spec['T'];methods=['fresh','direct','compact'] if T==0 else ['fresh','direct'];fresh=json.loads((directory/'gate_fresh_model.json').read_text())
        for p in sorted(directory.glob('*_model.json')):
            model=json.loads(p.read_text());assert model['map_version']=='FTF-MG-FW12-B6-v1'
            centers=[decode(w) for w in model['trajectory']];assert len(centers)==T+1 and decode(model['final_centers'])==centers[-1]
            assert len(model['per_round_stats'])==T
            counts=grid['group_counts'] if p.name=='original_model.json' else ns
            for stats in model['per_round_stats']:validate_stats(stats,counts,10,16);moment_triples+=1
            if p.name!='original_model.json':assert model==fresh
            arrays+=len(centers)
        models[spec['seed'],T]=fresh
        for method in methods:
            assert json.loads((directory/f'gate_{method}_model.json').read_text())==fresh;gates+=1;replays+=method!='fresh'
        extra=json.loads((directory/'gate_extra_state.json').read_text());assert extra['group_sizes']==ns
        assert extra['client_ids']==[i for i in range(10) if i!=grid['selected_client']]
        by_group=[Q(0)]*9
        assert extra['owners']==sorted(extra['owners'])
        for owner,w in zip(extra['owners'],extra['weights']):assert owner[0]!=grid['selected_client'];by_group[owner[1]]+=Q(w)
        assert by_group==[1]*9
        trace=json.loads((directory/'gate_updates.json').read_text());assert len(trace)==T
        for t,info in enumerate(trace):
            certificate_evaluations+=verify_update(info,fresh['per_round_stats'][t],ns,decode(fresh['trajectory'][t]),decode(fresh['trajectory'][t+1]))
            optimization.append({'seed':spec['seed'],'T':T,'round':t,'Phi_fixed_partition':float(Q(info['Phi'])),'D':float(Q(info['D'])),'gap':float(Q(info['gap'])),
                'relative_gap_to_primal':float(Q(info['gap'])/Q(info['Phi'])) if Q(info['Phi']) else 0.,'gap_exact':info['gap'],'D_exact':info['D'],
                'guard_accepted':info['accepted'],'evaluations':info['unique_evaluations'],'iterations':info['iterations_completed'],'termination':info['termination']})
        qs=json.loads((directory/'quality.json').read_text());assert qs['group_counts']==ns and len(qs['trajectory_quality'])==T+1
        last=None
        for t,q in enumerate(qs['trajectory_quality']):
            validate_stats(q['stats'],ns,10,16);v=costs(decode(fresh['trajectory'][t]),q['stats'],ns)
            assert v==tuple(map(Q,q['group_costs'])) and max(v)==Q(q['Phi']) and sum(v)==Q(q['G'])
            assert sum(n*c for n,c in zip(ns,v))==Q(q['pooled_SSE'])
            if last is not None:assert max(v)<=last
            last=max(v)
        q=qs['trajectory_quality'][-1]
        quality.append({'seed':spec['seed'],'T':T,'Phi':float(Q(q['Phi'])),'Phi_exact':q['Phi'],'G_sum':float(Q(q['G'])),'G_exact':q['G'],
                        'pooled_SSE':float(Q(q['pooled_SSE'])),'quality_seconds':qs['seconds']})
        for g,v in enumerate(q['group_costs']):group_quality.append({'seed':spec['seed'],'T':T,'group_id':g,'RAC1P':g+1,'n_g':ns[g],'cost':float(Q(v)),'exact_cost':v})
        obs=[json.loads(l) for l in (directory/'observations.jsonl').read_text().splitlines()];assert len(obs)==3*len(methods)
        for row in obs:
            assert row['seed']==spec['seed'] and row['T']==T and row['m']==9
            assert row['order'][row['position']]==row['method']
            rep=row['repetition'];i=spec['seed']-10000
            expected=methods[(i+rep)%3:]+methods[:(i+rep)%3] if T==0 else (methods if (i+T+rep)%2==0 else methods[::-1])
            assert row['order']==expected
            path=directory/f"rep{rep}_{row['method']}_model.json";assert sha(path)==row['output_sha256'] and path.stat().st_size==row['output_bytes']
            assert abs(row['request_seconds']-sum(row[k] for k in ('preparation_seconds','algorithm_seconds','output_seconds')))<1e-12
            named=sum(row['components'].values());assert row['algorithm_seconds']-named>=-1e-9
            raw.append({**{k:v for k,v in row.items() if k not in ('components','order')},'order':','.join(row['order']),
                **{f'component_{k}':row['components'].get(k,0) for k in ('validation','encoding','local_summaries','metadata','table','server_seed','assignment_stats','solver')},'component_other':row['algorithm_seconds']-named})
        prep=json.loads((directory/'preparation.json').read_text());preparation.append({'seed':spec['seed'],'T':T,**{k:v for k,v in prep.items() if k!='original_training_components'}})
    for seed in range(10000,10005):
        for T in (0,1):
            assert models[seed,T]['trajectory']==models[seed,2]['trajectory'][:T+1]
            assert models[seed,T]['per_round_stats']==models[seed,2]['per_round_stats'][:T]
    assert len(raw)==105 and gates==35 and replays==20 and len(quality)==15 and len(optimization)==15
    case_rows=[]
    groups=collections.defaultdict(list)
    for row in raw:groups[row['seed'],row['T'],row['method']].append(row)
    for (seed,T,method),rows in sorted(groups.items()):
        assert len(rows)==3 and sorted(r['repetition'] for r in rows)==[0,1,2]
        row={'seed':seed,'T':T,'method':method,'repeats':3}
        for key in ('algorithm_seconds','request_seconds','preparation_seconds','output_seconds'):
            values=[r[key] for r in rows];mean=st.mean(values);sd=st.stdev(values)
            row.update({key+'_mean':mean,key+'_sd':sd,key+'_min':min(values),key+'_max':max(values),key+'_CV':sd/mean if mean else 0})
        case_rows.append(row)
    pairs=[];lookup={(r['seed'],r['T'],r['method']):r for r in case_rows}
    for seed in range(10000,10005):
        for T in (0,1,2):
            for method in (['direct','compact'] if T==0 else ['direct']):
                a=lookup[seed,T,'fresh'];b=lookup[seed,T,method]
                pairs.append({'seed':seed,'T':T,'method':method,'algorithm_ratio':a['algorithm_seconds_mean']/b['algorithm_seconds_mean'],
                              'request_ratio':a['request_seconds_mean']/b['request_seconds_mean'],'fresh_algorithm_seconds':a['algorithm_seconds_mean'],
                              'method_algorithm_seconds':b['algorithm_seconds_mean'],'fresh_request_seconds':a['request_seconds_mean'],'method_request_seconds':b['request_seconds_mean']})
    aggregates=[]
    for T,method in ((0,'direct'),(0,'compact'),(1,'direct'),(2,'direct')):
        p=[r for r in pairs if r['T']==T and r['method']==method];out={'T':T,'method':method,'seeds':5}
        for boundary in ('algorithm','request'):
            ratios=[r[boundary+'_ratio'] for r in p];fresh=sum(r['fresh_'+boundary+'_seconds'] for r in p);other=sum(r['method_'+boundary+'_seconds'] for r in p)
            out.update({boundary+'_total_ratio':fresh/other,boundary+'_mean_paired':st.mean(ratios),boundary+'_seed_sd':st.stdev(ratios),boundary+'_min':min(ratios),boundary+'_max':max(ratios),boundary+'_wins':sum(r>1 for r in ratios),boundary+'_losses':sum(r<1 for r in ratios),boundary+'_ties':sum(r==1 for r in ratios)})
        aggregates.append(out)
    quality_summary=[]
    for T in (0,1,2):
        rs=[r for r in quality if r['T']==T];values=[r['Phi'] for r in rs]
        quality_summary.append({'T':T,'Phi_mean':st.mean(values),'Phi_sd':st.stdev(values),'Phi_min':min(values),'Phi_max':max(values)})
    growth=json.loads((RUN/'growth/observations.json').read_text());receipt=json.loads((RUN/'growth/complete.json').read_text())
    assert receipt['bindings']==manifest['bindings'] and sha(RUN/'growth/observations.json')==receipt['artifacts']['observations.json'] and len(growth)==12
    for r in growth:assert r['nonempty_slices']==6*r['m'] and r['anchor_slots']==60*r['m'] and r['client_group_count_cells']==6*r['m']
    growth_summary=[]
    for m in (2,3,5,9):
        rs=[r for r in growth if r['m']==m]
        growth_summary.append({'m':m,'slices':6*m,'anchors':60*m,'count_cells':6*m,'train_seconds_mean':st.mean(r['train_seconds'] for r in rs),
            'compaction_seconds_mean':st.mean(r['compaction_seconds'] for r in rs),'compact_pickle_bytes':rs[0]['compact_pickle_bytes'],'DIRECT_state_pickle_bytes':rs[0]['state_pickle_bytes']})
    for name,rows in [('raw_timings.csv',raw),('case_method_timings.csv',case_rows),('paired_ratios.csv',pairs),('aggregate_timings.csv',aggregates),('quality.csv',quality),('group_quality.csv',group_quality),('quality_summary.csv',quality_summary),('optimization.csv',optimization),('preparation.csv',preparation),('growth_raw.csv',growth),('growth_summary.csv',growth_summary)]:csvwrite(name,rows)
    locks=[json.loads(l) for l in (RUN/'lock.jsonl').read_text().splitlines()]
    assert len(locks)==64
    for i in range(0,len(locks),4):
        events=locks[i:i+4];assert [r['event'] for r in events]==['waiting','acquired','worker_finished','released'] and events[2]['returncode']==0
    loads=[r['load_average'][0] for r in locks if 'load_average' in r]
    lock_receipt={'batches':16,'wait_seconds':sum(r['wait_seconds'] for r in locks if r['event']=='acquired'),'held_seconds':sum(r['held_seconds'] for r in locks if r['event']=='released'),'one_minute_load_min':min(loads),'one_minute_load_max':max(loads),'unrelated_load_controlled':False}
    verification={'status':'PASS','created_utc':utc(),'timed_models':len(raw),'gate_models':gates,'gate_replay_comparisons':replays,'indexed_center_arrays_including_original':arrays,
        'moment_triples_including_original':moment_triples,'all_saved_centers_finite_and_hex_equal':True,'all_timed_and_gate_model_fields_equal':True,
        'budget_prefix_equal':True,'fixed_partition_updates_verified':len(optimization),'distinct_seed_round_partitions':10,'dual_candidate_certificates_rederived':certificate_evaluations,
        'exact_Phi_max_G_sum_checked':True,'model_comparison_scope':'No tolerance or permutation; full raw integer moments. Model equality is not full-state equality.',
        'independence_scope':'Separate saved-moment rational formulas and binary witness parser; real assignments not independently recomputed from every raw record. Separate tiny scalar oracle covers raw assignments.',
        'lock_summary':lock_receipt,'baseline_files_preserved':all(sha(f['path'])==f['sha256']==sha(ROOT/f['copy']) for f in json.loads((ROOT/'SOURCE_INPUTS.json').read_text())['baseline']),
        'tables':{p.name:sha(p) for p in sorted((ROOT/'tables').glob('*.csv'))}}
    write_json(ROOT/'VERIFICATION.json',verification)
    print(json.dumps({'status':'PASS','models':len(raw)+gates,'exact_dual_candidates':certificate_evaluations,'ratios':aggregates,'quality':quality_summary,'lock':lock_receipt}))
if __name__=='__main__':main()
