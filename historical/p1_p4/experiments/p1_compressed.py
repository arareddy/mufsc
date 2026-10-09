"""P1-only run-length evaluation of the literal replicated witness.

This preserves per-record masses, mass gcd, rejection total, raw-word order,
selected row identities and canonical completion. It compresses contiguous
identical rows for the declared 0/10 one-dimensional witness only; it is not
a replacement production training/seeding kernel. Use requires an independent
literal-array comparison gate matching this module's hash.
"""
from __future__ import annotations
from fractions import Fraction
from math import gcd, lcm
import numpy as np
from rng import canonical_tape, random_below
from kmeanspp import weighted_kmeanspp


class CountedTape:
    def __init__(self,seed,role,*entities):
        self.generator=canonical_tape(seed,role,*entities)
        self.bit_generator=self
        self.words=0
    def random_raw(self):
        self.words+=1
        return self.generator.bit_generator.random_raw()


def choose_blocks(blocks,masses,tape):
    """blocks=(count,value,group), masses=exact per-record masses."""
    den=lcm(*(m.denominator for m in masses))
    values=[m.numerator*(den//m.denominator) for m in masses]
    divisor=gcd(*values)
    if divisor==0:return None
    weights=[x//divisor for x in values]
    total=sum(b[0]*w for b,w in zip(blocks,weights))
    draw=random_below(total,tape)
    offset=0
    for block,weight in zip(blocks,weights):
        mass=block[0]*weight
        if draw<mass:return offset+draw//weight
        draw-=mass;offset+=block[0]
    raise AssertionError('block categorical range')


def value_at(blocks,index):
    for count,value,group in blocks:
        if index<count:return value
        index-=count
    raise IndexError(index)


def seed_blocks(blocks,weights,k,tape):
    n=sum(b[0] for b in blocks)
    if k>=n:return list(range(n))+[i%n for i in range(k-n)]
    first=choose_blocks(blocks,weights,tape)
    selected=[] if first is None else [first]
    while selected and len(selected)<k:
        locations=[value_at(blocks,i) for i in selected]
        masses=[w*min((value-z)**2 for z in locations) for (_,value,_),w in zip(blocks,weights)]
        idx=choose_blocks(blocks,masses,tape)
        if idx is None:break
        selected.append(idx)
    for i in range(n):
        if len(selected)>=k:break
        if i not in selected:selected.append(i)
    while len(selected)<k:selected.append((len(selected)-n)%n)
    return selected


def compressed_seed(kappa,seed,method,unit=150,distance=10):
    if kappa not in [1,2,4,8,16,32,64,128] or unit!=150 or distance!=10:
        raise ValueError('compression is validated only for the declared P1 witness')
    n=(kappa+1)*unit
    client_blocks={0:[(kappa*unit,0,0),(unit,distance,1)],
                   1:[(unit,0,0),(kappa*unit,0,1)]}
    trace={};anchors=[];server_weights=[]
    if method=='centralized':
        blocks=client_blocks[0]+client_blocks[1]
        tape=CountedTape(seed,'centralized')
        selected=seed_blocks(blocks,[Fraction(1,n)]*4,1,tape)
        trace['centralized']={'selected_idx':selected,'raw_words':tape.words}
        return np.array([[value_at(blocks,selected[0])]],dtype=float),trace
    if method=='splitgroup_2k':
        for c,blocks in client_blocks.items():
            for count,value,group in blocks:
                tape=CountedTape(seed,'local',c,group)
                selected=seed_blocks([(count,value,group)],[Fraction(1)],1,tape)
                anchors.append([value]);server_weights.append(Fraction(count,n))
                trace[f'local:{c}:{group}']={'selected_idx':selected,'raw_words':tape.words,'mult':[count]}
        role='server'
    elif method in ('merged_1k','merged_2k'):
        budget=1 if method=='merged_1k' else 2
        for c,blocks in client_blocks.items():
            tape=CountedTape(seed,'merged_local',c)
            weights=[Fraction(1,b[0]) for b in blocks]
            selected=seed_blocks(blocks,weights,budget,tape)
            reps=[value_at(blocks,i) for i in selected]
            counts=[[0]*budget,[0]*budget]
            for count,value,group in blocks:
                label=min(range(budget),key=lambda j:((value-reps[j])**2,j))
                counts[group][label]+=count
            trace[f'merged_local:{c}']={'selected_idx':selected,'raw_words':tape.words,'h_A':counts[0],'h_B':counts[1]}
            for j,rep in enumerate(reps):
                anchors.append([rep]);server_weights.append(Fraction(counts[0][j]+counts[1][j],n))
        role='merged_server'
    else:raise ValueError(method)
    tape=CountedTape(seed,role)
    anchor_array=np.asarray(anchors,dtype=float)
    selected=weighted_kmeanspp(anchor_array,server_weights,1,tape)
    trace[role]={'selected_idx':selected.tolist(),'raw_words':tape.words,
                 'anchors':anchors,'weights':[str(v) for v in server_weights]}
    return anchor_array[selected].copy(),trace
