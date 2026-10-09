"""Audited serial timer decomposition and point-work accounting (no arithmetic changes)."""

def components(timing,elapsed):
    t=timing
    additive={k:float(t[k]) for k in ('encoding','input_materialization','cache_construction','shift_bounds','phase1_server','phase2_server')}
    additive['phase1_client']=sum(t['phase1_client'].values())
    additive['phase2_client_certify']=sum(sum(v) for v in t['phase2_client_certify'].values())
    additive['phase2_client_recompute']=sum(sum(v) for v in t['phase2_client_recompute'].values())
    additive['unattributed']=elapsed-sum(additive.values())
    if additive['unattributed'] < -1e-8:raise AssertionError('overlapping additive timers')
    overlapping={k:float(t[k]) for k in ('certificate_scan','failed_assignment','fallback_sunk','fallback_rebuild')}
    derived={'phase1':additive['phase1_client']+additive['phase1_server'],
             'refinement_instrumented':sum(additive[k] for k in ('shift_bounds','phase2_client_certify','phase2_client_recompute','phase2_server'))}
    return {'additive':additive,'overlapping_diagnostics':overlapping,'derived_nonadditive':derived}

def counters(result,method,survivors,T):
    if method=='fresh':
        rounds=[{'round':t,'N':survivors,'A':0,'P':0,'S':0,'J':0} for t in range(T)]
    else:rounds=result['diagnostics']
    assert len(rounds)==T
    sums={k:sum(int(r[k]) for r in rounds) for k in ('N','A','P','S','J')}
    assert sums['N']==survivors*T
    assert 0<=sums['S']<=sums['P']<=sums['A']<=sums['N']
    assert sums['J']<=sums['A']-sums['P']
    fallback=method in ('basic','runnerup') and result['abandonment_round'] is not None
    return {**sums,'pass_fraction':sums['P']/sums['A'] if sums['A'] else None,
            'useful_fraction':sums['S']/sums['N'],'modeled_point_assignments':sums['N']-sums['S']+sums['J'],
            'threshold_fallback':fallback,'abandonment_round':result.get('abandonment_round') if fallback else None,'rounds':rounds}
