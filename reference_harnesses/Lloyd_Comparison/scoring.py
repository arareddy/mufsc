"""Independent exact represented nearest-center quality; no canonical imports.

Binary64 directed coordinate intervals plus conservative nonnegative-sum
bound certify unique nearest centers; ambiguous rows use scalar Fractions.
Integer moments use a separately guarded vector reduction, not production
accumulators. Scalar fixtures compare pointwise fractions independently.
"""
from fractions import Fraction as F
import numpy as np,hashlib

def scalar_dist(x,c):return sum((F(float(a))-F(float(b)))**2 for a,b in zip(x,c))
def independent_labels(X,C):
 n,d=X.shape;k=len(C);labels=np.empty(n,dtype=np.int64);ambiguous=0
 eps=np.finfo(np.float64).eps;gam=d*eps/(1-d*eps)
 assert d*eps<.01 and np.isfinite(X).all() and np.isfinite(C).all()
 for start in range(0,n,512):
  z=X[start:start+512,None,:]-C[None,:,:]
  zl=np.nextafter(z,-np.inf);zh=np.nextafter(z,np.inf)
  lowmag=np.where((zl<=0)&(zh>=0),0.,np.minimum(np.abs(zl),np.abs(zh)))
  highmag=np.maximum(np.abs(zl),np.abs(zh))
  sl=np.maximum(0.,np.nextafter(lowmag*lowmag,-np.inf));sh=np.nextafter(highmag*highmag,np.inf)
  lo=np.maximum(0.,np.nextafter(np.sum(sl,axis=2)*(1-gam),-np.inf));hi=np.nextafter(np.sum(sh,axis=2)/(1-gam),np.inf)
  assert np.isfinite(lo).all() and np.isfinite(hi).all()
  tentative=np.argmin(hi,axis=1)
  for i,j in enumerate(tentative):
   candidates=np.flatnonzero(lo[i]<=hi[i,j])
   if len(candidates)==1:labels[start+i]=j
   else:
    ambiguous+=1;labels[start+i]=min((scalar_dist(X[start+i],C[h]),int(h)) for h in candidates)[1]
 return labels,ambiguous

def score(X,xi,groups,C,scale):
 assert np.array_equal(X,xi.astype(float)/scale)
 n,d=X.shape;k=len(C);M=max(abs(int(np.min(xi))),abs(int(np.max(xi))))
 assert n*d*M*M < 2**63 and n*M<2**63,'independent moment reduction overflow guard'
 labels,ambiguous=independent_labels(X,C);counts=[int(np.sum(groups==g)) for g in [0,1]];assert min(counts)>0
 costs=[]
 for g in [0,1]:
  total=F(0)
  for j in range(k):
   a=xi[(groups==g)&(labels==j)];count=len(a)
   if not count:continue
   sums=np.sum(a,axis=0,dtype=np.int64);squares=int(np.sum(a*a,dtype=np.int64))
   c=[F(float(v)) for v in C[j]]
   total+=F(squares,scale*scale)+count*sum(v*v for v in c)-2*sum(F(int(v),scale)*q for v,q in zip(sums,c))
  costs.append(total/counts[g])
 sse=sum(n*v for n,v in zip(counts,costs))
 vals=dict(Phi_A=costs[0],Phi_B=costs[1],Phi=max(costs),G=sum(costs),population_average=sse/n,pooled_SSE=sse)
 assert min(vals.values())>=0
 return vals,labels,dict(counts=counts,ambiguous_rows=ambiguous,labels_sha256=hashlib.sha256(labels.astype('<i8').tobytes()).hexdigest(),scorer='independent outward-interval assignments with scalar exact ambiguous fallback; separate exact moment cost')
