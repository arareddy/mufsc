"""FTF-MG-FW12-B6-v1: isolated categorical multi-group whole-client prototype.

Canonical numerical primitives are imported from byte-verified baseline/src.
Positive-round outputs define a distinct map. State is trusted in-process data.
"""
from common import np
from fractions import Fraction as F
from dataclasses import dataclass
from time import perf_counter
from exact_numeric import finite_matrix, rational
from fixedpoint import FixedPointConfig, represented_clients, new_zero_stats, accumulate_stats, add_stats
from assignment import assign_labels_only
from splitgroup import SplitGroupConfig, snap_gamma, build_anchor_table, server_step
from kmeanspp import ordinary_kmeanspp
from rng import canonical_tape
from validation import integer

MAP='FTF-MG-FW12-B6-v1'

@dataclass(frozen=True)
class Config:
    m:int
    k:int=10
    T:int=0
    iterations:int=12
    line_bits:int=6
    scale_bits:int=12
    clip:float=8.0
    gamma:float=0.0
    anchor_lloyd_iters:int=0
    def __post_init__(self):
        for name,low,high in [('m',2,None),('k',1,None),('T',0,None),('iterations',0,256),('line_bits',0,32),('anchor_lloyd_iters',0,None)]:
            integer(getattr(self,name),name,low,high)
        if not np.isfinite(self.gamma) or self.gamma<0:raise ValueError('invalid gamma')
        FixedPointConfig(self.scale_bits,self.clip)
    @property
    def fp(self):return FixedPointConfig(self.scale_bits,self.clip)
    @property
    def sg(self):return SplitGroupConfig(self.k,self.gamma,self.m)


def validate_inputs(data,groups,seed,cfg):
    integer(seed,'seed')
    if not isinstance(data,dict) or not data or not isinstance(groups,dict) or set(data)!=set(groups):raise ValueError('client/group keys mismatch')
    d=None;counts=[0]*cfg.m
    for c in sorted(data):
        integer(c,'client ID');x=finite_matrix(data[c],'features');cfg.fp.validate_dimension(x.shape[1])
        if d is not None and x.shape[1]!=d:raise ValueError('dimension mismatch')
        d=x.shape[1];g=np.asarray(groups[c])
        if g.shape!=(len(x),) or g.dtype.kind not in 'iu' or np.any(g<0) or np.any(g>=cfg.m):raise ValueError('invalid categorical groups')
        for a in range(cfg.m):counts[a]+=int(np.count_nonzero(g==a))
    if min(counts)<=0:raise ValueError('every declared global group must be nonempty')
    return tuple(counts)


def local_summary(x,seed,client,group,cfg):
    x=finite_matrix(x,'slice')
    if not len(x):raise ValueError('empty slice must be omitted')
    ke=min(cfg.k,len(x))
    selected=ordinary_kmeanspp(x,ke,canonical_tape(seed,'local',client,group))
    reps=x[selected];labels=assign_labels_only(x,reps)
    return {'anchors':snap_gamma(reps,cfg.gamma),'reps':reps,'mult':np.bincount(labels,minlength=ke).astype(np.int64),
            'selected_idx':selected,'k_e':ke,'n_e':len(x)}


class Partition:
    """Exact fixed-partition quadratics f_g = Q_g + sum(a||c||^2-2 b.c)."""
    def __init__(self,N,S,SS,counts,scale,old):
        self.m=len(counts);self.k=len(old);self.d=old.shape[1]
        if scale<=0 or len(N)!=self.m or len(S)!=self.m or len(SS)!=self.m:raise ValueError('invalid moments')
        for g,n in enumerate(counts):
            if n<=0 or len(N[g])!=self.k or len(S[g])!=self.k or len(SS[g])!=self.k or sum(N[g])!=n:raise ValueError('invalid group moments')
            for j in range(self.k):
                if N[g][j]<0 or SS[g][j]<0 or len(S[g][j])!=self.d:raise ValueError('invalid cell')
                if not N[g][j] and (SS[g][j] or any(S[g][j])):raise ValueError('empty cell has nonzero moments')
        self.a=[[F(int(v),int(counts[g])) for v in N[g]] for g in range(self.m)]
        self.b=[[[F(int(v),int(counts[g])*scale) for v in row] for row in S[g]] for g in range(self.m)]
        self.q=[F(sum(map(int,SS[g])),int(counts[g])*scale*scale) for g in range(self.m)]
        self.means=[[[F(int(v),int(N[g][j])*scale) for v in S[g][j]] if N[g][j] else None for j in range(self.k)] for g in range(self.m)]
        self.old=[[rational(v) for v in row] for row in old]
    def costs(self,c):
        c=[[rational(v) for v in row] for row in c]
        norms=[sum(v*v for v in row) for row in c]
        return tuple(self.q[g]+sum(self.a[g][j]*norms[j]-2*sum(v*b for v,b in zip(c[j],self.b[g][j])) for j in range(self.k) if self.a[g][j]) for g in range(self.m))
    def minimum(self,lam):
        if len(lam)!=self.m or any(v<0 for v in lam) or sum(lam)!=1:raise ValueError('lambda outside simplex')
        centers=[];dual=sum(lam[g]*self.q[g] for g in range(self.m));zero=[]
        for j in range(self.k):
            a=sum(lam[g]*self.a[g][j] for g in range(self.m))
            b=[sum(lam[g]*self.b[g][j][q] for g in range(self.m)) for q in range(self.d)]
            if a:
                center=[v/a for v in b];dual-=sum(v*v for v in b)/a
            else:
                assert all(v==0 for v in b)
                occupied=[g for g in range(self.m) if self.means[g][j] is not None]
                center=self.means[occupied[0]][j] if len(occupied)==1 else self.old[j]
                zero.append({'cluster':j,'occupied_groups':occupied,'rule':'sole_mean' if len(occupied)==1 else 'incumbent'})
            centers.append(list(center))
        return centers,dual,zero


def guarded_update(centers,N,S,SS,counts,cfg):
    centers=finite_matrix(centers,'centers')
    if centers.shape[0]!=cfg.k:raise ValueError('center count mismatch')
    problem=Partition(N,S,SS,counts,cfg.fp.scale,centers)
    evaluated={};trace=[]
    def evaluate(lam,origin):
        lam=tuple(F(v) for v in lam)
        if lam not in evaluated:
            exact,dual,zero=problem.minimum(lam)
            unrounded=problem.costs(exact)
            assert sum(l*v for l,v in zip(lam,unrounded))==dual
            returned=np.array([[float(v) for v in row] for row in exact],dtype=np.float64)
            actual=problem.costs(returned)
            assert dual<=max(actual)
            evaluated[lam]=(returned,actual,dual,unrounded)
            trace.append({'lambda':lam,'D':dual,'represented_group_costs':actual,'Phi':max(actual),'origin':origin,'zero_denominators':zero})
        return evaluated[lam]
    current=tuple(F(1,cfg.m) for _ in range(cfg.m));evaluate(current,'uniform')
    for g in range(cfg.m):evaluate(tuple(F(int(a==g)) for a in range(cfg.m)),f'vertex_{g}')
    steps=[];termination='iteration_bound'
    for t in range(cfg.iterations):
        _,_,dual,gradient=evaluate(current,'current')
        target=min(range(cfg.m),key=lambda g:(-gradient[g],g))
        gap=gradient[target]-dual
        if gap==0:
            termination='exact_zero_FW_gap';break
        direction=tuple(F(int(g==target))-current[g] for g in range(cfg.m))
        choices=[current,tuple(F(int(g==target)) for g in range(cfg.m))]
        lo=F(0);hi=F(1);branches=[]
        for bit in range(cfg.line_bits):
            alpha=(lo+hi)/2
            lam=tuple(current[g]+alpha*direction[g] for g in range(cfg.m))
            _,_,_,grad=evaluate(lam,f'iteration_{t}_bisect_{bit}')
            derivative=sum(direction[g]*grad[g] for g in range(cfg.m))
            branches.append({'alpha':alpha,'derivative':derivative,'lower':derivative>0})
            if derivative>0:lo=alpha
            else:hi=alpha
            choices.append(lam)
        chosen=min(choices,key=lambda lam:(-evaluate(lam,'line_endpoint')[2],lam))
        assert evaluate(chosen,'chosen')[2]>=dual
        steps.append({'iteration':t,'start_lambda':current,'target_group':target,'FW_gap':gap,'branches':branches,'chosen_lambda':chosen,'stalled':chosen==current})
        current=chosen
    best=min(evaluated,key=lambda lam:(max(evaluated[lam][1]),lam))
    lower=min(evaluated,key=lambda lam:(-evaluated[lam][2],lam))
    candidate,vals,_,_=evaluated[best];old=problem.costs(centers)
    accepted=max(vals)<=max(old)
    out=candidate if accepted else centers.copy();costs=vals if accepted else old
    lower_bound=evaluated[lower][2];gap=max(costs)-lower_bound
    assert gap>=0 and max(costs)<=max(old)
    return out,{'map':MAP,'candidate_lambda':best,'dual_lambda':lower,'incumbent_costs':old,'candidate_costs':vals,'returned_costs':costs,
                'Phi':max(costs),'G':sum(costs),'D':lower_bound,'gap':gap,'accepted':accepted,'termination':termination,
                'iterations_completed':len(steps),'unique_evaluations':len(evaluated),'evaluations':trace,'steps':steps}


def aggregate(data,encoded,groups,centers,cfg):
    d=centers.shape[1];stats=new_zero_stats(cfg.m,cfg.k,d)
    for c in sorted(data):
        labels=assign_labels_only(data[c],centers)
        stats=add_stats(stats,accumulate_stats(encoded[c],groups[c],labels,cfg.m,cfg.k))
    return stats


def quality(data,encoded,groups,centers,counts,cfg):
    stats=aggregate(data,encoded,groups,centers,cfg)
    vals=Partition(*stats,counts,cfg.fp.scale,centers).costs(centers)
    return {'group_costs':vals,'Phi':max(vals),'G':sum(vals),'pooled_SSE':sum(n*v for n,v in zip(counts,vals)),'stats':stats}


def finish(data,encoded,groups,seed,cfg,slices,counts,client_ids):
    timing={};start=perf_counter()
    table=build_anchor_table(slices,dict(enumerate(counts)),cfg.sg)
    timing['table']=perf_counter()-start;start=perf_counter()
    centers=server_step(table,seed,cfg.sg,cfg.anchor_lloyd_iters)
    timing['server_seed']=perf_counter()-start
    trajectory=[centers.copy()];allstats=[];updates=[];timing['assignment_stats']=0.;timing['solver']=0.
    for _ in range(cfg.T):
        start=perf_counter();stats=aggregate(data,encoded,groups,centers,cfg);timing['assignment_stats']+=perf_counter()-start
        allstats.append(stats);start=perf_counter()
        centers,info=guarded_update(centers,*stats,counts,cfg);timing['solver']+=perf_counter()-start
        updates.append(info);trajectory.append(centers.copy())
    return {'map_version':MAP,'cfg':cfg,'seed':seed,'client_ids':tuple(client_ids),'group_sizes':tuple(counts),'slice_results':slices,
            'anchor_table':table,'trajectory':trajectory,'per_round_stats':allstats,'final_centers':centers,'updates':updates,'timing':timing}


def train(data,groups,seed,cfg,keep_state=False):
    start=perf_counter();counts=validate_inputs(data,groups,seed,cfg);validation=perf_counter()-start
    start=perf_counter();represented,encoded=represented_clients(data,cfg.fp)
    groups={c:np.asarray(groups[c],dtype=np.int64).copy() for c in sorted(data)}
    encoding=perf_counter()-start;start=perf_counter();slices={}
    for c,x in represented.items():
        for g in range(cfg.m):
            mask=groups[c]==g
            if np.any(mask):slices[c,g]=local_summary(x[mask],seed,c,g,cfg)
    local=perf_counter()-start
    out=finish(represented,encoded,groups,seed,cfg,slices,counts,sorted(data))
    out['timing'].update(validation=validation,encoding=encoding,local_summaries=local)
    if keep_state:
        for mapping in (represented,encoded,groups):
            for v in mapping.values():v.flags.writeable=False
        out['state']={'map_version':MAP,'cfg':cfg,'seed':seed,'data':represented,'encoded':encoded,'groups':groups,
                      'client_ids':tuple(sorted(data)),'counts':counts,'slices':slices,
                      'client_counts':{c:tuple(slices[c,g]['n_e'] if (c,g) in slices else 0 for g in range(cfg.m)) for c in sorted(data)}}
    return out


def retained_metadata(client_ids,client_counts,counts,removed):
    if not isinstance(removed,(list,tuple,set,np.ndarray,range)):raise ValueError('client request must be a collection of IDs')
    ids=list(removed)
    for c in ids:
        integer(c,'request client ID')
        if c not in client_counts:raise ValueError('unknown or already deleted client')
    if len(ids)!=len(set(ids)):raise ValueError('duplicate client ID')
    gone=set(map(int,ids));new=tuple(counts[g]-sum(client_counts[c][g] for c in gone) for g in range(len(counts)))
    if min(new)<=0:raise ValueError('deletion empties a declared global group')
    return tuple(c for c in client_ids if c not in gone),new,gone


def direct(state,removed):
    start=perf_counter()
    if state.get('map_version')!=MAP:raise ValueError('wrong numerical map')
    ids,counts,gone=retained_metadata(state['client_ids'],state['client_counts'],state['counts'],removed)
    slices={key:s for key,s in state['slices'].items() if key[0] not in gone}
    # Whole-client removal changes no surviving row; read-only views suffice.
    data={c:state['data'][c] for c in ids};encoded={c:state['encoded'][c] for c in ids};groups={c:state['groups'][c] for c in ids}
    metadata=perf_counter()-start
    out=finish(data,encoded,groups,state['seed'],state['cfg'],slices,counts,ids)
    out['timing']['metadata']=metadata
    return out


@dataclass(frozen=True)
class Compact:
    map_version:str
    cfg:Config
    seed:int
    client_ids:tuple
    client_counts:dict
    counts:tuple
    slices:dict


def compact(state):
    if state.get('map_version')!=MAP or state['cfg'].T!=0:raise ValueError('compact state requires this T0 map')
    slices={};counts={c:[0]*state['cfg'].m for c in state['client_ids']}
    for key,s in sorted(state['slices'].items()):
        c,g=key;assert sum(map(int,s['mult']))==s['n_e'];counts[c][g]=s['n_e'];copy={}
        for field,value in s.items():
            if isinstance(value,np.ndarray):
                value=value.copy();value.flags.writeable=False
            copy[field]=value
        slices[key]=copy
    counts={c:tuple(v) for c,v in counts.items()}
    assert tuple(sum(v[g] for v in counts.values()) for g in range(state['cfg'].m))==state['counts']
    return Compact(MAP,state['cfg'],state['seed'],state['client_ids'],counts,state['counts'],slices)


def delete_c0(state,removed):
    start=perf_counter()
    if not isinstance(state,Compact) or state.map_version!=MAP or state.cfg.T!=0:raise ValueError('requires trusted compact T0 state')
    ids,counts,gone=retained_metadata(state.client_ids,state.client_counts,state.counts,removed)
    slices={key:s for key,s in state.slices.items() if key[0] not in gone}
    nxt=Compact(MAP,state.cfg,state.seed,ids,{c:state.client_counts[c] for c in ids},counts,slices)
    metadata=perf_counter()-start
    out=finish(None,None,None,state.seed,state.cfg,slices,counts,ids)
    out['timing']['metadata']=metadata
    return out,nxt
