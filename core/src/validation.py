"""Public input and checkpoint-scoped request validation."""
import numpy as np
from exact_numeric import finite_matrix


def integer(value,name,minimum=0,maximum=None):
    if isinstance(value,(bool,np.bool_)) or not isinstance(value,(int,np.integer)) or value<minimum or (maximum is not None and value>maximum):
        raise ValueError(f'invalid {name}')


def training_inputs(data,groups,seed,k,T,L,gamma,cfg,anchor_iters):
    if not isinstance(data,dict) or not data or set(data)!=set(groups):raise ValueError('client/group keys mismatch')
    integer(seed,'seed');integer(k,'k',1);integer(T,'T');integer(L,'L',0,256);integer(anchor_iters,'anchor iterations')
    if not np.isfinite(gamma) or gamma<0:raise ValueError('invalid gamma')
    dimension=None;counts=[0,0]
    for c,x in data.items():
        integer(c,'client ID');x=finite_matrix(x,'features');cfg.validate_dimension(x.shape[1])
        if dimension is not None and dimension!=x.shape[1]:raise ValueError('client dimensions differ')
        dimension=x.shape[1];g=np.asarray(groups[c])
        if g.shape!=(len(x),) or not np.issubdtype(g.dtype,np.integer) or not np.all((g==0)|(g==1)):
            raise ValueError('group IDs must be integer 0/1')
        for group in (0,1):counts[group]+=int(np.sum(g==group))
    if min(counts)==0:raise ValueError('both global groups must be nonempty')


def removal_request(checkpoint,removed,mode,threshold):
    if checkpoint.get('map_version')!='FTF-1' or not checkpoint.get('cache_valid',False):
        raise ValueError('requires a valid FTF-1 training checkpoint')
    if mode not in ('none','basic','runnerup'):raise ValueError('unknown certificate mode')
    if not np.isfinite(threshold) or threshold<0:raise ValueError('invalid abandonment threshold')
    if not isinstance(removed,dict):raise ValueError('request must be a client-index dictionary')
    out={}
    for c,ids in removed.items():
        integer(c,'request client ID')
        if c not in checkpoint['client_data']:raise ValueError('unknown request client')
        ids=np.asarray(ids)
        if ids.ndim!=1 or (ids.size and (not np.issubdtype(ids.dtype,np.integer) or np.any(ids<0) or np.any(ids>=len(checkpoint['client_data'][c])))):
            raise ValueError('invalid deletion row index')
        if len(np.unique(ids))!=len(ids):raise ValueError('duplicate deletion row')
        out[c]=np.sort(ids.astype(np.int64))
    return out
