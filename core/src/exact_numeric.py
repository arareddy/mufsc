"""Exact dyadic arithmetic and outward bounds for FTF-1.

The floating filter only proves disjoint intervals; it never defines ties.
"""
from fractions import Fraction
from math import gcd, lcm
import numpy as np

TINY = np.nextafter(0.0, 1.0)


def rational(x):
    if isinstance(x, Fraction): return x
    if isinstance(x, (int, np.integer)): return Fraction(int(x))
    return Fraction.from_float(float(x))


def finite_matrix(x, name='array'):
    a=np.asarray(x, dtype=np.float64)
    if a.ndim != 2 or a.shape[1] == 0 or not np.isfinite(a).all():
        raise ValueError(f'{name} must be a finite matrix with positive dimension')
    if a.size and np.max(np.abs(a)) > 2.0**450:
        raise ValueError(f'{name} exceeds supported bound 2^450')
    if a.shape[1] > 4096: raise ValueError('dimension exceeds 4096')
    return a


def integer_weights(weights):
    f=[rational(w) for w in weights]
    if any(w<0 for w in f):raise ValueError('negative weight')
    den=1
    for w in f:den=lcm(den,w.denominator)
    nums=[w.numerator*(den//w.denominator) for w in f]
    divisor=0
    for v in nums:divisor=gcd(divisor,v)
    return [v//divisor for v in nums] if divisor else nums


def dyadic_matrix(X):
    """Exact common integer representation; scale cancels in D² sampling."""
    X=finite_matrix(X)
    for bits in (0,12,16,24,30):
        scaled=np.ldexp(X,bits)
        if np.max(np.abs(scaled), initial=0)<=2**52 and np.equal(scaled,np.rint(scaled)).all():
            a=scaled.astype(np.int64)
            bound=int(np.max(np.abs(a),initial=0))
            if 4*X.shape[1]*bound*bound < 2**62:return a
            return a.astype(object)
    vals=[float(x).as_integer_ratio() for x in X.flat]
    den=max((d for _,d in vals),default=1)
    return np.array([n*(den//d) for n,d in vals],dtype=object).reshape(X.shape)


def squared_exact(x,c):
    return sum((rational(a)-rational(b))**2 for a,b in zip(x,c))


class Bounds(np.ndarray):
    """Display estimate with rigorous lower/upper arrays, including slicing."""
    def __new__(cls, lower, upper):
        lo=np.asarray(lower,dtype=float);hi=np.asarray(upper,dtype=float)
        with np.errstate(invalid='ignore'):
            midpoint=np.where(lo==hi,lo,lo+(hi-lo)*0.5)
        obj=np.asarray(midpoint).view(cls)
        obj.lower=lo;obj.upper=hi
        return obj
    def __array_finalize__(self,obj):
        if obj is not None:
            self.lower=getattr(obj,'lower',None); self.upper=getattr(obj,'upper',None)
    def __getitem__(self,key):
        if self.lower is None: return super().__getitem__(key)
        return Bounds(self.lower[key],self.upper[key])
    def __reduce__(self):
        return (Bounds,(self.lower,self.upper))
    def copy(self,order='C'):
        return Bounds(self.lower.copy(),self.upper.copy())


def ends(x):
    if isinstance(x,Bounds):return x.lower,x.upper
    a=np.asarray(x,dtype=float)
    # Plain numeric certificate inputs denote exact represented scalars.
    return a,a


def down(x):return np.nextafter(x,-np.inf)
def up(x):return np.nextafter(x,np.inf)


def squared_bounds(a,b):
    """Enclose exact squared distance with a proved floating filter.

    For binary64 inputs, a subnormal subtraction is exact on the dyadic
    lattice; other subtraction has relative error <=u=2^-53. Each square
    has relative error <=u plus absolute tau/2 (tau=min_subnormal).
    A nonnegative sum of d terms has gamma_(d-1) relative error (a
    subnormal sum is exact). For d<=4096, combining these errors is bounded
    by g=(d+8)*2^-52, with d*tau absolute slack. Thus exact squared norm is
    in [(s-d*tau)/(1+g), (s+d*tau)/(1-g)]. Every final operation rounds
    outward. Accepted geometry bounds prevent overflow. Intersecting
    intervals always fall back to exact rational distances in assignment.
    """
    a=np.asarray(a,dtype=float);b=np.asarray(b,dtype=float)
    d=a.shape[-1]
    if not 1<=d<=4096:raise ValueError('dimension exceeds filter domain')
    with np.errstate(under='ignore',over='raise',invalid='raise'):
        diff=a-b
        squared=np.sum(diff*diff,axis=-1)
        g=(d+8)*2.0**-52
        low=np.maximum(0.,down(down(squared-d*TINY)/(1+g)))
        high=up(up(squared+d*TINY)/(1-g))
        equal=np.all(a==b,axis=-1)
        low=np.where(equal,0.,low);high=np.where(equal,0.,high)
    return low,high


def norm_bounds(a,b):
    lo,hi=squared_bounds(a,b)
    with np.errstate(under='ignore'):
        l=np.maximum(0.,down(np.sqrt(lo)));h=up(np.sqrt(hi))
    return Bounds(np.where(lo==0,0.,l),np.where(hi==0,0.,h))
