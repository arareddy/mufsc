"""Quality on the ONE represented dataset; exact values available on request."""
from fractions import Fraction
import numpy as np
from assignment import assign_labels_only
from exact_numeric import squared_exact,dyadic_matrix,rational


def fair_objective(X,group,centers,return_exact=False):
    labels=assign_labels_only(X,centers)
    group=np.asarray(group)
    if group.shape!=(len(X),) or not np.all((group==0)|(group==1)):
        raise ValueError('invalid quality groups')
    # Build exact integer moments at a common dyadic scale. This is linear
    # in points and avoids per-point Fraction arithmetic for real datasets.
    data=np.asarray(X,dtype=float)
    den=max((float(x).as_integer_ratio()[1] for x in data.flat),default=1)
    if den<=2**30:
        ints=np.ldexp(data,den.bit_length()-1).astype(np.int64)
        from fixedpoint import accumulate_stats
        from fair_update import exact_group_cost
        try:
            N,S,SS=accumulate_stats(ints,group.astype(np.int64),labels,2,len(centers))
            vals=[exact_group_cost(centers,N[g],S[g],SS[g],int(np.sum(group==g)),den) for g in (0,1)]
        except ValueError:
            vals=None
    else:vals=None
    if vals is None:
        vals=[]
        for g in (0,1):
            ids=np.flatnonzero(group==g)
            if not len(ids):raise ValueError('both groups required for quality')
            vals.append(sum(squared_exact(data[i],centers[labels[i]]) for i in ids)/len(ids))
    result=(vals[0],vals[1],sum(vals),max(vals))
    return result if return_exact else tuple(float(v) for v in result)
