"""Certified exact indexed nearest/runner-up assignments for FTF-1."""
import numpy as np
from exact_numeric import finite_matrix,squared_bounds,squared_exact,Bounds,down,up


def assign_all(X, centers):
    X=finite_matrix(X,'X');centers=finite_matrix(centers,'centers')
    n,d=X.shape;k=centers.shape[0]
    if k<1 or centers.shape[1]!=d:raise ValueError('incompatible or empty centers')
    labels=np.empty(n,dtype=np.int64);runner=np.full(n,-1,dtype=np.int64)
    low1=np.empty(n);high1=np.empty(n);low2=np.full(n,np.inf);high2=np.full(n,np.inf)
    for start in range(0,n,2048):
        end=min(n,start+2048);pts=X[start:end]
        lo,hi=squared_bounds(pts[:,None,:],centers[None,:,:])
        order=np.argsort(lo,axis=1,kind='stable')
        for row in range(len(pts)):
            first=int(order[row,0]);second=int(order[row,1]) if k>1 else -1
            uncertain=k>1 and hi[row,first]>=lo[row,second]
            if k>2:uncertain=uncertain or hi[row,second]>=lo[row,order[row,2]]
            if uncertain:
                # Only intersecting intervals can precede the tentative top2.
                ceiling=max(hi[row,first], hi[row,second])
                candidates=[j for j in range(k) if lo[row,j]<=ceiling]
                exact=sorted((squared_exact(pts[row],centers[j]),j) for j in candidates)
                first=exact[0][1];second=exact[1][1]
            labels[start+row]=first;runner[start+row]=second
            low1[start+row]=lo[row,first];high1[start+row]=hi[row,first]
            if k>1:low2[start+row]=lo[row,second];high2[start+row]=hi[row,second]
    def norms(lo,hi):
        return Bounds(np.where(lo==0,0.,np.maximum(0.,down(np.sqrt(lo)))),np.where(hi==0,0.,up(np.sqrt(hi))))
    return labels,norms(low1,high1),norms(low2,high2),runner


def assign_labels_only(X,centers):
    return assign_all(X,centers)[0]
