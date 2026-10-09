from common import np
from multigroup import Config

def cases():
    out=[]
    for m in (3,5):
        data={};groups={}
        for c in (0,7,23):
            n=2*m+3;data[c]=np.array([[((i*7+c*3)%17-8)/4,((i*i+2*c)%13-6)/4] for i in range(n)],float);groups[c]=np.array([(i+c)%m for i in range(n)],np.int64)
        out.append(('mixed_gaps',data,groups,Config(m,k=3,scale_bits=2)))
        data={2:np.array([[0.,0.],[.25,.5],[.5,1.]]),11:np.array([[g/2,i/4] for g in range(1,m) for i in range(3)]),41:np.array([[-g/2,i/2] for g in range(m) for i in range(2)])}
        groups={2:np.zeros(3,dtype=np.int64),11:np.repeat(np.arange(1,m),3),41:np.repeat(np.arange(m),2)}
        out.append(('absent_local',data,groups,Config(m,k=2,scale_bits=2)))
        data={1:np.zeros((2*m+1,2)),8:np.zeros((m+1,2))};groups={c:np.arange(len(x),dtype=np.int64)%m for c,x in data.items()}
        out.append(('coincident_zero_mass',data,groups,Config(m,k=3,scale_bits=2)))
        data={3:np.array([[g/4] for g in range(m)]),9:np.array([[1-g/4] for g in range(m)])};groups={c:np.arange(m,dtype=np.int64) for c in data}
        out.append(('saturation',data,groups,Config(m,k=2*m+3,scale_bits=2)))
        data={0:np.array([[.25+g/2,(g%2)*.5] for g in range(m)]),12:np.array([[.75-g/2,-(g%2)*.5] for g in range(m)])};groups={c:np.arange(m,dtype=np.int64) for c in data}
        out.append(('snap_ties_anchor_lloyd',data,groups,Config(m,k=3,scale_bits=2,gamma=.5,anchor_lloyd_iters=1)))
        data={0:np.array([[g/2] for g in range(m)]),7:np.array([[-g/2] for g in range(1,m)]),99:np.empty((0,1))};groups={0:np.arange(m,dtype=np.int64),7:np.arange(1,m,dtype=np.int64),99:np.empty(0,dtype=np.int64)}
        out.append(('empty_and_boundary',data,groups,Config(m,k=2,scale_bits=2)))
    return out
