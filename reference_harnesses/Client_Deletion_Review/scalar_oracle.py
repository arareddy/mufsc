"""Independent tiny FTF-1 T=0 oracle: scalar Fraction geometry and enumeration.

No production imports. NumPy PCG64/SeedSequence is the sole shared numerical
primitive in fixed-seed checks. Ideal-law enumeration does not import NumPy.
"""
from collections import defaultdict
from fractions import Fraction as Q
from math import gcd
from numbers import Integral


def frac(x):
    return x if isinstance(x, Q) else Q(x) if isinstance(x, int) else Q.from_float(float(x))


def d2(a, b):
    return sum((frac(x)-frac(y))**2 for x, y in zip(a, b))


def nearest(x, centers):
    return min(range(len(centers)), key=lambda j: (d2(x, centers[j]), j))


def encode(data, bits=2, clip=8.0):
    scale=2**bits
    return {int(c): tuple(tuple(round(min(clip,max(-clip,float(x)))*scale)/scale for x in row)
                          for row in rows) for c,rows in sorted(data.items())}


class Tape:
    def __init__(self, seed, role, *ids):
        import numpy as np
        self.raw=np.random.PCG64(np.random.SeedSequence([seed,role,*ids]))
        self.words=0
    def word(self):
        self.words+=1
        return int(self.raw.random_raw())


def integer_mass(weights):
    qs=[frac(x) for x in weights]
    if any(x<0 for x in qs):
        raise ValueError('negative mass')
    denominator=1
    for x in qs:
        denominator=denominator*x.denominator//gcd(denominator,x.denominator)
    ns=[x.numerator*(denominator//x.denominator) for x in qs]
    common=0
    for x in ns:
        common=gcd(common,x)
    return [x//common for x in ns] if common else ns


def categorical(weights,tape):
    mass=integer_mass(weights)
    total=sum(mass)
    if total<=0: raise ValueError('nonpositive mass')
    bits=(total-1).bit_length()
    if not bits:
        u=0
    else:
        while True:
            u=sum(tape.word()<<(64*j) for j in range((bits+63)//64))&((1<<bits)-1)
            if u<total: break
    for i,m in enumerate(mass):
        if u<m: return i
        u-=m
    raise AssertionError('unreachable')


def complete(prefix,n,k):
    out=list(prefix)
    out.extend(i for i in range(n) if i not in out)
    if not n and k: raise ValueError('empty input')
    j=0
    while len(out)<k:
        out.append(j%n); j+=1
    return tuple(out[:k])


def kpp(points,weights,k,tape):
    n=len(points)
    if not k: return ()
    if not n: raise ValueError('empty input')
    weights=[frac(x) for x in weights]
    if any(x<0 for x in weights): raise ValueError('negative mass')
    if k>=n or sum(weights)==0: return complete((),n,k)
    chosen=[categorical(weights,tape)]
    while len(chosen)<k:
        mass=[w*min(d2(x,points[i]) for i in chosen) for x,w in zip(points,weights)]
        if sum(mass)==0: break
        chosen.append(categorical(mass,tape))
    return complete(chosen,n,k)


def local(points,seed,c,g,k,gamma):
    slots=min(k,len(points))
    if not slots: raise ValueError('omit empty slice')
    chosen=kpp(points,[Q(1)]*len(points),slots,Tape(seed,1,c,g))
    reps=tuple(points[i] for i in chosen)
    mult=[0]*slots
    for x in points: mult[nearest(x,reps)]+=1
    step=frac(gamma)
    anchors=tuple(tuple(float(round(frac(x)/step)*step) for x in row) for row in reps) if gamma else reps
    return dict(anchors=anchors,reps=reps,mult=tuple(mult),selected_idx=chosen,k_e=slots,n_e=len(points))


def table(summaries,counts):
    anchors=[];weights=[];owners=[]
    for c,g in sorted(summaries):
        s=summaries[c,g]
        for j in range(s['k_e']):
            anchors.append(s['anchors'][j]);weights.append(Q(s['mult'][j],counts[g]));owners.append((c,g,j))
    return dict(anchors=tuple(anchors),weights=tuple(weights),owner=tuple(owners))


def weighted_objective(points,weights,centers):
    return sum(w*d2(x,centers[nearest(x,centers)]) for x,w in zip(points,weights))


def server(tab,seed,k,anchor_iters=0):
    pts,weights=tab['anchors'],tab['weights']
    chosen=kpp(pts,weights,k,Tape(seed,2))
    centers=tuple(pts[j] for j in chosen)
    for _ in range(anchor_iters):
        labels=[nearest(x,centers) for x in pts]
        candidate=[]
        for j,old in enumerate(centers):
            indices=[i for i in range(len(pts)) if labels[i]==j]
            mass=sum(weights[i] for i in indices)
            candidate.append(tuple(float(sum(weights[i]*frac(pts[i][q]) for i in indices)/mass)
                                   for q in range(len(old))) if mass else old)
        candidate=tuple(candidate)
        if weighted_objective(pts,weights,candidate)<=weighted_objective(pts,weights,centers):
            centers=candidate
        else: break
    return centers


def train(data,groups,seed,k,gamma=0.0,bits=2,clip=8.0,anchor_iters=0):
    data=encode(data,bits,clip)
    summaries={};counts={0:0,1:0};client_counts={}
    for c,rows in sorted(data.items()):
        client_counts[c]={g:sum(int(z)==g for z in groups[c]) for g in (0,1)}
        for g in (0,1):
            pts=tuple(x for x,z in zip(rows,groups[c]) if int(z)==g)
            counts[g]+=len(pts)
            if pts:summaries[c,g]=local(pts,seed,c,g,k,gamma)
    if min(counts.values())<=0:raise ValueError('empty global group')
    tab=table(summaries,counts)
    return dict(client_counts=client_counts,group_sizes=counts,slice_results=summaries,anchor_table=tab,
                final_centers=server(tab,seed,k,anchor_iters),seed=seed,k=k,anchor_iters=anchor_iters)


def reuse(cp,deleted):
    if not isinstance(deleted,(list,tuple)):raise ValueError('whole-client IDs required')
    for c in deleted:
        if isinstance(c,bool) or not isinstance(c,Integral) or c<0 or c not in cp['client_counts']:
            raise ValueError('invalid client ID')
    if len(set(deleted))!=len(deleted):raise ValueError('duplicate client ID')
    drop=set(deleted)
    counts={g:cp['group_sizes'][g]-sum(cp['client_counts'][c][g] for c in drop) for g in (0,1)}
    if min(counts.values())<=0:raise ValueError('empty global group')
    summaries={key:v for key,v in cp['slice_results'].items() if key[0] not in drop}
    tab=table(summaries,counts)
    return dict(group_sizes=counts,slice_results=summaries,anchor_table=tab,
                final_centers=server(tab,cp['seed'],cp['k'],cp['anchor_iters']))


def ideal_paths(points,k,prefix=()):
    """Exact ideal ordinary k++ law on record IDs, positive-potential regime.

    points is {persistent row id: coordinate tuple}. Prefix repair enumeration
    uses the same routine with surviving IDs. The declared k>=n boundary is
    reproduced for empty-prefix fresh calls. No PCG64/production code used.
    """
    ids=tuple(points)
    if not prefix and k>=len(ids):
        if not ids and k:raise ValueError('empty')
        out=list(ids)
        while len(out)<k:out.append(ids[(len(out)-len(ids))%len(ids)])
        return {tuple(out):Q(1)}
    if len(prefix)==k:return {tuple(prefix):Q(1)}
    weights={i:Q(1) if not prefix else min(d2(points[i],points[j]) for j in prefix) for i in ids}
    total=sum(weights.values())
    if not total:
        out=list(prefix)+[i for i in ids if i not in prefix]
        while len(out)<k:out.append(ids[(len(out)-len(ids))%len(ids)])
        return {tuple(out[:k]):Q(1)}
    result=defaultdict(Q)
    for i,w in weights.items():
        if w:
            for path,p in ideal_paths(points,k,(*prefix,i)).items():result[path]+=w/total*p
    return dict(result)


def ideal_repair_law(points,k,removed,whole_restart=False):
    remain={i:x for i,x in points.items() if i not in removed}
    result=defaultdict(Q)
    for path,p in ideal_paths(points,k).items():
        hit=next((j for j,i in enumerate(path) if i in removed),None)
        if hit is None:result[path]+=p
        else:
            prefix=() if whole_restart else path[:hit]
            for fixed,q in ideal_paths(remain,k,prefix).items():result[fixed]+=p*q
    return dict(result)
