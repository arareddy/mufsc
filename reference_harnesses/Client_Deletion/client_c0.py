"""Exact whole-client C0 deletion using canonical FTF-1D compact summaries.

State is a trusted internal product of compact_checkpoint(), not an untrusted
serialization format. No raw coordinates, raw group arrays, or row masks enter
delete_clients(). Do not mutate retained summary arrays or state dictionaries.
"""
from dataclasses import dataclass
from time import perf_counter
import numpy as np
from splitgroup import SplitGroupConfig,build_anchor_table,server_step
from validation import integer

@dataclass(frozen=True)
class ClientC0State:
    seed: int
    k: int
    gamma: float
    anchor_lloyd_iters: int
    client_ids: tuple
    client_counts: dict
    group_sizes: dict
    slice_results: dict
    map_version: str = 'FTF-1D-client-C0-v1'


def compact_checkpoint(checkpoint):
    """One-time compact cache production from an already validated T=0 train.

    Counts come from each canonical slice's n_e, recorded by local_slice_step
    during initial training. This touches summaries only: O(C k d) copying plus
    O(C k) integrity checks, no scan of surviving/departing raw records.
    """
    if checkpoint.get('map_version')!='FTF-1' or checkpoint.get('T')!=0:
        raise ValueError('requires a canonical T=0 checkpoint')
    counts={c:[0,0] for c in checkpoint['client_ids']}
    summaries={}
    for (c,g),value in checkpoint['slice_results'].items():
        if c not in counts or g not in (0,1):raise ValueError('invalid slice owner')
        n=int(value['n_e'])
        if n<1 or sum(int(x) for x in value['mult'])!=n:raise ValueError('invalid summary count')
        counts[c][g]=n
        copied={}
        for key,v in value.items():
            if isinstance(v,np.ndarray):
                v=v.copy();v.flags.writeable=False
            copied[key]=v
        summaries[c,g]=copied
    totals={g:sum(v[g] for v in counts.values()) for g in (0,1)}
    if totals!=checkpoint['group_sizes'] or min(totals.values())<=0:
        raise ValueError('summary/global count mismatch')
    return ClientC0State(checkpoint['seed'],checkpoint['k'],checkpoint['gamma'],
                         checkpoint['anchor_lloyd_iters'],tuple(sorted(counts)),
                         {c:tuple(v) for c,v in counts.items()},totals,summaries)


def delete_clients(state, departing):
    """Return (model/state projection, next compact state) for whole clients.

    Persistent survivor IDs and summary slot/selected indices are unchanged.
    A valid sequence uses the returned state; requests may never target a
    previously removed client. Empty requests are defined as canonical reseeds.
    """
    start=perf_counter()
    if not isinstance(state,ClientC0State) or state.map_version!='FTF-1D-client-C0-v1':
        raise ValueError('invalid C0 state')
    if not isinstance(departing,(list,tuple,np.ndarray)):
        raise ValueError('request must be a sequence of client IDs')
    if isinstance(departing,np.ndarray) and departing.ndim!=1:
        raise ValueError('request must have one dimension')
    ids=[]
    for c in departing:
        integer(c,'departing client ID')
        if c not in state.client_counts:raise ValueError('unknown or previously removed client')
        ids.append(int(c))
    if len(ids)!=len(set(ids)):raise ValueError('duplicate client')
    removed=set(ids)
    totals={g:state.group_sizes[g]-sum(state.client_counts[c][g] for c in removed) for g in (0,1)}
    if min(totals.values())<=0:raise ValueError('deletion empties a required global group')
    counts={c:v for c,v in state.client_counts.items() if c not in removed}
    slices={key:v for key,v in state.slice_results.items() if key[0] not in removed}
    next_state=ClientC0State(state.seed,state.k,state.gamma,state.anchor_lloyd_iters,
                            tuple(c for c in state.client_ids if c not in removed),counts,totals,slices)
    metadata_seconds=perf_counter()-start
    start=perf_counter()
    cfg=SplitGroupConfig(state.k,state.gamma)
    table=build_anchor_table(slices,totals,cfg)
    table_seconds=perf_counter()-start
    start=perf_counter()
    centers=server_step(table,state.seed,cfg,state.anchor_lloyd_iters)
    sampler_seconds=perf_counter()-start
    return {'map_version':'FTF-1','cache_valid':False,'trajectory':[centers.copy()],
            'final_centers':centers,'per_round_stats':[],'digests':[],
            'slice_results':slices,'group_sizes':totals,'anchor_table':table,
            'timing':{'metadata_seconds':metadata_seconds,'anchor_table_seconds':table_seconds,
                      'server_sampler_seconds':sampler_seconds}},next_state
