"""Separately implemented scalar rational oracle; no production-kernel imports.

Only NumPy's PCG64/SeedSequence primitive and binary64 conversions are shared.
The small optimizer searches the primal center box, not simplex weights.
"""
from fractions import Fraction as F
from math import gcd,lcm
import heapq
import numpy as np


def rat(x):return x if isinstance(x,F) else F(int(x)) if isinstance(x,(int,np.integer)) else F.from_float(float(x))
def dist(x,y):return sum((rat(a)-rat(b))**2 for a,b in zip(x,y))
def label(x,c):return min(range(len(c)),key=lambda j:(dist(x,c[j]),j))
def complete(chosen,n,k):
    out=list(chosen)
    for i in range(n):
        if i not in out:out.append(i)
    while len(out)<k:out.append((len(out)-n)%n)
    return out[:k]
def draw(weights,tape):
    weights=list(map(rat,weights));den=lcm(*(w.denominator for w in weights))
    mass=[w.numerator*(den//w.denominator) for w in weights];common=gcd(*mass)
    mass=[v//common for v in mass];total=sum(mass);bits=(total-1).bit_length()
    if bits:
        while True:
            u=sum(int(tape.random_raw())<<(64*q) for q in range((bits+63)//64)) & ((1<<bits)-1)
            if u<total:break
    else:u=0
    for i,v in enumerate(mass):
        if u<v:return i
        u-=v
    raise AssertionError('bad mass')
def seed(points,weights,k,key):
    n=len(points)
    if k>=n or sum(weights)==0:return complete([],n,k)
    tape=np.random.PCG64(np.random.SeedSequence(key));chosen=[draw(weights,tape)]
    while len(chosen)<k:
        masses=[w*min(dist(x,points[j]) for j in chosen) for x,w in zip(points,weights)]
        if sum(masses)==0:break
        chosen.append(draw(masses,tape))
    return complete(chosen,n,k)
def encode(data,bits,clip):
    s=2**bits
    return {c:[[round(min(clip,max(-clip,float(v)))*s)/s for v in row] for row in a] for c,a in sorted(data.items())}
def local(points,training_seed,c,g,k,gamma):
    ke=min(len(points),k);ids=seed(points,[F(1)]*len(points),ke,[training_seed,1,c,g])
    reps=[points[i] for i in ids];mult=[0]*ke
    for x in points:mult[label(x,reps)]+=1
    anchors=[[float(round(rat(v)/rat(gamma))*rat(gamma)) for v in row] for row in reps] if gamma else reps
    return {'anchors':np.array(anchors,dtype=float),'reps':np.array(reps,dtype=float),'mult':np.array(mult,dtype=np.int64),
            'selected_idx':np.array(ids,dtype=np.int64),'k_e':ke,'n_e':len(points)}
def fresh0(data,groups,training_seed,cfg):
    represented=encode(data,cfg.scale_bits,cfg.clip);counts=[sum(int(g==a) for gs in groups.values() for g in gs) for a in range(cfg.m)]
    if min(counts)<=0:raise ValueError('empty global group')
    summaries={}
    for c,rows in represented.items():
        for g in range(cfg.m):
            subset=[x for x,a in zip(rows,groups[c]) if a==g]
            if subset:summaries[c,g]=local(subset,training_seed,c,g,cfg.k,cfg.gamma)
    anchors=[];weights=[];owners=[]
    for (c,g),s in sorted(summaries.items()):
        for j,a in enumerate(s['anchors']):anchors.append(a);weights.append(F(int(s['mult'][j]),counts[g]));owners.append((c,g,j))
    selected=seed(anchors,weights,cfg.k,[training_seed,2]);centers=np.array([anchors[i] for i in selected],dtype=float)
    def obj(cs):return sum(w*dist(x,cs[label(x,cs)]) for x,w in zip(anchors,weights))
    for _ in range(cfg.anchor_lloyd_iters):
        labels=[label(x,centers) for x in anchors];candidate=centers.copy()
        for j in range(cfg.k):
            ids=[i for i,a in enumerate(labels) if a==j];total=sum(weights[i] for i in ids)
            if total:candidate[j]=[float(sum(weights[i]*rat(anchors[i][q]) for i in ids)/total) for q in range(centers.shape[1])]
        if obj(candidate)<=obj(centers):centers=candidate
        else:break
    return {'group_sizes':tuple(counts),'client_ids':tuple(sorted(data)),'slice_results':summaries,'anchor_table':{'anchors':np.array(anchors,dtype=float),'weights':weights,'owner':owners},'final_centers':centers}
def scalar_stats(data,groups,centers,m,scale):
    k=len(centers);d=len(centers[0]);N=[[0]*k for _ in range(m)];S=[[[0]*d for _ in range(k)] for _ in range(m)];SS=[[0]*k for _ in range(m)]
    for c,x in sorted(data.items()):
        for point,g in zip(x,groups[c]):
            j=label(point,centers);v=[int(rat(q)*scale) for q in point];g=int(g)
            N[g][j]+=1;SS[g][j]+=sum(a*a for a in v)
            for q,a in enumerate(v):S[g][j][q]+=a
    return N,S,SS
def scalar_costs(data,groups,centers,m):
    sums=[F(0)]*m;ns=[0]*m
    for c,x in sorted(data.items()):
        for point,g in zip(x,groups[c]):
            g=int(g);sums[g]+=dist(point,centers[label(point,centers)]);ns[g]+=1
    return tuple(a/n for a,n in zip(sums,ns))

def primal_reference(cells,old,limit=20000,tolerance=F(1,100000)):
    """Rigorous 1D-per-center epigraph optimum bracket over group-mean hull.

    Each node's lower bound is max_g min_box f_g. The objective is evaluated
    point by point; exact interval splitting gives valid bounds even at limit.
    The optimum can be chosen inside each coordinate's group-mean hull.
    """
    m=len(cells);k=len(old);ns=[sum(map(len,row)) for row in cells]
    cells=[[[rat(x) for x in points] for points in row] for row in cells]
    means=[[sum(p)/len(p) if p else None for p in row] for row in cells]
    initial=[]
    for j in range(k):
        values=[means[g][j] for g in range(m) if means[g][j] is not None]
        initial.append((min(values),max(values)) if values else (rat(old[j]),rat(old[j])))
    def costs(c):return tuple(sum((x-c[j])**2 for j,p in enumerate(row) for x in p)/ns[g] for g,row in enumerate(cells))
    def bounds(box):
        low=[]
        for g,row in enumerate(cells):
            total=F(0)
            for j,points in enumerate(row):
                if points:
                    v=max(box[j][0],min(box[j][1],means[g][j]));total+=sum((x-v)**2 for x in points)
            low.append(total/ns[g])
        mid=tuple((a+b)/2 for a,b in box);return max(low),max(costs(mid)),mid
    lb,ub,point=bounds(initial);queue=[(lb,0,tuple(initial))];counter=0;visited=0
    while queue and ub-queue[0][0]>tolerance and visited<limit:
        low,_,box=heapq.heappop(queue);visited+=1
        if low>=ub:continue
        j=min(range(k),key=lambda j:(-(box[j][1]-box[j][0]),j))
        a,b=box[j];mid=(a+b)/2
        if a==b:continue
        for interval in ((a,mid),(mid,b)):
            child=list(box);child[j]=interval;lower,upper,p=bounds(child)
            if upper<ub:ub=upper;point=p
            if lower<ub:
                counter+=1;heapq.heappush(queue,(lower,counter,tuple(child)))
    lb=min(ub,queue[0][0]) if queue else ub
    return {'lower':lb,'upper':ub,'point':point,'boxes':visited,'tolerance_met':ub-lb<=tolerance,'width':ub-lb}
