"""Separate population-unweighted Lloyd update. No objective acceptance guard."""
from fractions import Fraction
import numpy as np
from assignment import assign_labels_only
from fixedpoint import accumulate_stats,add_stats,new_zero_stats

def update(centers,N,S,scale):
 out=np.array(centers,dtype=np.float64,copy=True)
 for j in range(len(out)):
  n=sum(int(N[g][j]) for g in range(len(N)))
  if n:
   for d in range(out.shape[1]):out[j,d]=float(Fraction(sum(int(S[g][j][d]) for g in range(len(N))),n*scale))
 return out

def refine(cd,xi,go,initial,T,scale):
 centers=initial.copy();trajectory=[centers.copy()];stats=[];k,d=centers.shape
 for t in range(T):
  N,S,SS=new_zero_stats(2,k,d)
  for c in sorted(cd):
   lab=assign_labels_only(cd[c],centers);part=accumulate_stats(xi[c],go[c],lab,2,k)
   N,S,SS=add_stats((N,S,SS),part)
  stats.append((N,S,SS));centers=update(centers,N,S,scale);trajectory.append(centers.copy())
 return dict(trajectory=trajectory,per_round_stats=stats,final_centers=centers)
