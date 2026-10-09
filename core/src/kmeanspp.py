"""Ordinary rational categorical D² seeding, with canonical completion."""
import numpy as np
from math import gcd
from exact_numeric import dyadic_matrix,integer_weights,finite_matrix
from rng import random_below


def _weighted_choice(mass,rng):
    nums=integer_weights(mass)
    return _integer_choice(nums,rng)


def _integer_choice(mass,rng):
    divisor=0
    for x in mass: divisor=gcd(divisor,int(x))
    mass=[int(x)//divisor for x in mass] if divisor else list(mass)
    total=sum(int(x) for x in mass)
    if total<=0:raise ValueError('positive categorical mass required')
    draw=random_below(total,rng)
    cumulative=0
    for i,v in enumerate(mass):
        cumulative+=int(v)
        if draw<cumulative:return i
    raise AssertionError('categorical range invariant')


def _canonical_complete(chosen,n,k):
    chosen=list(chosen)
    if not n and k:raise ValueError('cannot select from empty data')
    seen=set(chosen)
    for i in range(n):
        if len(chosen)>=k:break
        if i not in seen:chosen.append(i);seen.add(i)
    i=0
    while len(chosen)<k:chosen.append(i%n);i+=1
    return chosen


def weighted_kmeanspp(X,weights,k,rng):
    X=finite_matrix(X,'seeding X');n=len(X)
    if isinstance(k,(bool,np.bool_)) or not isinstance(k,(int,np.integer)) or k<0:raise ValueError('invalid k')
    if len(weights)!=n:raise ValueError('weights shape mismatch')
    w=integer_weights(weights)
    if not k:return np.array([],dtype=np.int64)
    if not n:raise ValueError('cannot seed empty input')
    if k>=n:return np.array(_canonical_complete(list(range(n)),n,k),dtype=np.int64)
    if sum(w)==0:return np.array(_canonical_complete([],n,k),dtype=np.int64)
    points=dyadic_matrix(X)
    chosen=[_integer_choice(w,rng)]
    def distances(idx):return np.sum((points-points[idx])**2,axis=1)
    nearest=distances(chosen[0])
    while len(chosen)<k:
        mass=[int(a)*b for a,b in zip(nearest,w)]
        if sum(mass)==0:break
        idx=_integer_choice(mass,rng);chosen.append(idx)
        nearest=np.minimum(nearest,distances(idx))
    return np.array(_canonical_complete(chosen,n,k),dtype=np.int64)


def ordinary_kmeanspp(X,k,rng):return weighted_kmeanspp(X,[1]*len(X),k,rng)
