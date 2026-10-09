from common import *
import numpy as np
from fractions import Fraction as F
from lloyd import refine,update
from scoring import score,independent_labels
from fair_update import guarded_fair_update
from assignment import assign_labels_only
from fixedpoint import accumulate_stats
from reproducible import exact_witness,jsonable

def scalar_labels(X,C):
 return [min((sum((F(float(a))-F(float(b)))**2 for a,b in zip(x,c)),j) for j,c in enumerate(C))[1] for x in X]
def scalar_score(X,g,C):
 labs=scalar_labels(X,C);cost=[]
 for h in [0,1]:
  terms=[sum((F(float(a))-F(float(b)))**2 for a,b in zip(x,C[j])) for x,q,j in zip(X,g,labs) if q==h];cost.append(sum(terms)/len(terms))
 return cost
fixtures=[('unequal_groups_genuine_difference',[[0.],[0.],[0.],[10.]],[0,0,0,1],[[0.]],1),('indexed_ties_empty', [[-1.],[0.],[1.]],[0,1,1],[[-1.],[1.],[99.]],1),('duplicate_centers',[[-2.],[0.],[2.],[4.]],[0,0,1,1],[[0.],[0.],[4.]],1),('rounding_thirds',[[0.],[0.],[1.]],[0,1,1],[[0.]],1),('two_dimensional',[[0.,0.],[1.,0.],[0.,1.],[2.,2.],[3.,1.]],[0,0,1,1,1],[[0.,0.],[2.,2.],[9.,9.]],4)]
verify_sources();out=[]
for name,x,g,c,scale in fixtures:
 X=np.array(x);go=np.array(g,dtype=np.int64);C=np.array(c);xi=(X*scale).astype(np.int64);scalar=C.copy();expected=[scalar.copy()]
 for t in range(2):
  labs=scalar_labels(X,scalar);new=scalar.copy()
  for j in range(len(C)):
   chosen=[x for x,h in zip(X,labs) if h==j]
   if chosen:
    for d in range(X.shape[1]):new[j,d]=float(sum(F(float(x[d])) for x in chosen)/len(chosen))
  scalar=new;expected.append(scalar.copy())
 result=refine({7:X},{7:xi},{7:go},C,2,scale)
 assert all(a.tobytes()==b.tobytes() for a,b in zip(expected,result['trajectory']))
 details=[]
 for centers in result['trajectory']:
  v,lab,meta=score(X,xi,go,centers,scale);q=scalar_score(X,go,centers)
  assert np.array_equal(lab,scalar_labels(X,centers)) and [v['Phi_A'],v['Phi_B']]==q
  assert np.array_equal(lab,assign_labels_only(X,centers));details.append(dict(values={k:str(v) for k,v in v.items()},**meta))
 if name=='unequal_groups_genuine_difference':
  N,S,SS=accumulate_stats(xi,go,np.zeros(4,dtype=np.int64),2,1);fair,_=guarded_fair_update(C,N,S,SS,3,1,1,6,scale)
  assert fair.tobytes()==np.array([[5.]]).tobytes() and result['trajectory'][1].tobytes()==np.array([[2.5]]).tobytes()
  assert scalar_score(X,go,fair)==[F(25),F(25)] and scalar_score(X,go,result['trajectory'][1])==[F(25,4),F(225,4)]
 out.append(dict(name=name,status='PASS',witness=exact_witness(result),quality=details))
# Aggregate-only exactly halfway means in the allowed b=30 input lattice.
n=2**23;scale=2**30
for offset,expected in [(1,1.0),(3,float.fromhex('0x1.0000000000002p+0'))]:
 N=[[n-1],[1]];S=[[[n*scale+offset]],[[0]]]
 c=update(np.array([[0.]]),N,S,scale);assert c[0,0].hex()==expected.hex()
 out.append(dict(name=f'halfway_aggregate_{offset}',status='PASS',exact_mean=str(F(n*scale+offset,n*scale)),expected_hex=expected.hex(),observed_hex=c[0,0].hex(),scope='aggregate rounding fixture, not new raw dataset'))
(W/'fixtures').mkdir(exist_ok=True)
dump(W/'fixtures/results.json',dict(status='PASS',fixtures=out,source_bindings=bindings(),source_manifest_sha256=sha(W/'SOURCE_MANIFEST.json'),notes='Independent pointwise Fraction oracle; shared Python binary64 conversion only. Aggregate halfway fixtures check ties-to-even explicitly.'))
print('PASS: 5 scalar trajectory/scoring fixtures plus 2 halfway-rounding fixtures.')
