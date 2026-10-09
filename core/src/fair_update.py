"""Exact represented-candidate comparisons for finite binary fair updates."""
from fractions import Fraction as F
import numpy as np
from exact_numeric import rational,finite_matrix
from fixedpoint import exact_squared_norm
GROUP_A,GROUP_B=0,1


def group_means(N,S,k,scale):
    return [[[F(int(v),int(N[g][j])*scale) for v in S[g][j]] if N[g][j] else None for j in range(k)] for g in (0,1)]


def group_delta(N_g,S_g,SS_g,n_g,k,scale):
    if n_g<=0:raise ValueError('global group must be nonempty')
    return sum((F(int(SS_g[j]))-F(exact_squared_norm(S_g[j]),int(N_g[j]))) for j in range(k) if N_g[j])/ (n_g*scale*scale)


def group_objective(centers,mu_g,weight_g,delta_g,k):
    return rational(delta_g)+sum(rational(weight_g[j])*sum((rational(c)-rational(m))**2 for c,m in zip(centers[j],mu_g[j])) for j in range(k) if mu_g[j] is not None)


def exact_group_cost(centers,N,S,SS,n_g,scale):
    if n_g<=0:raise ValueError('global group must be nonempty')
    total=F(sum(int(v) for v in SS),scale*scale)
    for j,c in enumerate(centers):
        for q,s in zip(c,S[j]):
            q=rational(q)
            total+=int(N[j])*q*q-F(2*int(s),scale)*q
    return total/n_g


def _lambda_center(mu_a_j,mu_b_j,alpha_j,beta_j,lam,old_center_j):
    lam=rational(lam);a=rational(alpha_j);b=rational(beta_j)
    if mu_a_j is not None and mu_b_j is not None:
        wa=lam*a;wb=(1-lam)*b;den=wa+wb
        if not den:return old_center_j.copy()
        return np.array([float((wa*rational(x)+wb*rational(y))/den) for x,y in zip(mu_a_j,mu_b_j)])
    mu=mu_a_j if mu_a_j is not None else mu_b_j
    return np.array([float(rational(x)) for x in mu]) if mu is not None else old_center_j.copy()


def guarded_fair_update(centers,N,S,SS,n_A,n_B,k,L,scale):
    centers=finite_matrix(centers,'centers')
    if centers.shape[0]!=k or not isinstance(L,(int,np.integer)) or isinstance(L,(bool,np.bool_)) or not 0<=L<=256:
        raise ValueError('invalid shape or bisection length')
    if n_A<=0 or n_B<=0 or not isinstance(scale,int) or scale<=0:raise ValueError('invalid groups or scale')
    if sum(N[0])!=n_A or sum(N[1])!=n_B:raise ValueError('group counts disagree')
    mu=group_means(N,S,k,scale)
    a=[F(int(v),n_A) for v in N[0]];b=[F(int(v),n_B) for v in N[1]]
    def build(lam):return np.array([_lambda_center(mu[0][j],mu[1][j],a[j],b[j],lam,centers[j]) for j in range(k)])
    def costs(c):return tuple(exact_group_cost(c,N[g],S[g],SS[g],n,scale) for g,n in enumerate((n_A,n_B)))
    candidates={}
    def add(lam):
        c=build(lam);vals=costs(c);candidates[lam]=(c,vals);return vals
    add(F(0));add(F(1));lo=F(0);hi=F(1)
    branches=[]
    for _ in range(L):
        lam=(lo+hi)/2;fa,fb=add(lam)
        branches.append({"lambda":str(lam),"f_A":str(fa),"f_B":str(fb),"lower":bool(fa>fb)})
        if fa>fb:lo=lam
        else:hi=lam
    best=min(candidates,key=lambda lam:(max(candidates[lam][1]),lam))
    candidate,values=candidates[best];current=costs(centers)
    accepted=max(values)<=max(current)
    winner=candidate if accepted else centers.copy();vals=values if accepted else current
    return winner,{'lambda':float(best) if accepted else None,'lambda_exact':str(best) if accepted else None,
        'branches':branches,'f_A':float(vals[0]),'f_B':float(vals[1]),'f_A_exact':str(vals[0]),'f_B_exact':str(vals[1]),'accepted':accepted}
