"""Conservative Basic and runner-up interval certificates, with strict tests."""
import numpy as np
from exact_numeric import ends,up,down


def basic_certificate_vec(d1,d2,j,delta):
    l1,u1=ends(d1);l2,u2=ends(d2);ld,ud=ends(delta)
    j=np.asarray(j,dtype=np.int64);k=len(ud)
    if k==1:return np.ones(j.shape,dtype=bool)
    order=np.argsort(-ud,kind='stable')
    other=np.where(j==order[0],ud[order[1]],ud[order[0]])
    upper=up(u1+ud[j]);lower=np.maximum(0.,down(l2-other))
    return upper<lower


def runner_up_certificate_vec(d1,d2,j,r,delta):
    l1,u1=ends(d1);l2,u2=ends(d2);ld,ud=ends(delta)
    j=np.asarray(j,dtype=np.int64);r=np.asarray(r,dtype=np.int64);k=len(ud)
    if k==1:return np.ones(j.shape,dtype=bool)
    runner_lower=np.maximum(0.,np.maximum(down(l2-ud[r]),down(ld[r]-u2)))
    if k<=2:other_lower=np.full(j.shape,np.inf)
    else:
        max_other=np.full(j.shape,-np.inf)
        for idx in np.argsort(-ud,kind='stable')[:3]:
            eligible=(j!=idx)&(r!=idx)
            max_other=np.where(eligible,np.maximum(max_other,ud[idx]),max_other)
        other_lower=np.maximum(0.,down(l2-max_other))
    return up(u1+ud[j])<np.minimum(runner_lower,other_lower)


def basic_certificate(d1,d2,delta,j):
    return bool(basic_certificate_vec(d1,d2,np.asarray(j),delta))


def runner_up_certificate(d1,d2,delta,j,r):
    return bool(runner_up_certificate_vec(d1,d2,np.asarray(j),np.asarray(r),delta))
