from common import *
import multigroup as mg
import oracle
from fixtures import cases
from dataclasses import replace
from fractions import Fraction as F
from unittest.mock import patch
import traceback

def expect_value_error(call):
    try:call()
    except ValueError:return
    raise AssertionError('invalid request accepted')
def exact_equal(a,b):
    assert np.asarray(a).shape==np.asarray(b).shape
    assert np.asarray(a,dtype='<f8').tobytes()==np.asarray(b,dtype='<f8').tobytes()
def extra_equal(a,b):assert jsonbytes(extra_witness(a))==jsonbytes(extra_witness(b))

def main():
    records=[];invalid=0;replays=[];sequences=[];quality=[];guard_rejected=0
    for name,data,groups,cfg in cases():
        for seed in (0,7,19):
            original=mg.train(data,groups,seed,cfg,True);state=original['state'];comp=mg.compact(state)
            scalar=oracle.fresh0(data,groups,seed,cfg);extra_equal(original,scalar);exact_equal(original['final_centers'],scalar['final_centers'])
            for removed in [[],*[[c] for c in sorted(data)]]:
                rem=set(removed);d={c:x for c,x in data.items() if c not in rem};g={c:v for c,v in groups.items() if c not in rem}
                counts=[sum(int(np.count_nonzero(v==a)) for v in g.values()) for a in range(cfg.m)]
                if not d or min(counts)==0:
                    expect_value_error(lambda:mg.delete_c0(comp,removed));expect_value_error(lambda:mg.direct(state,removed));invalid+=2;continue
                fresh=mg.train(d,g,seed,cfg);raw=oracle.fresh0(d,g,seed,cfg)
                with patch.object(mg,'local_summary',side_effect=AssertionError('surviving local reseed')):
                    fast,nxt=mg.delete_c0(comp,removed);direct=mg.direct(state,removed)
                for actual in (fresh,fast,direct):extra_equal(actual,raw);exact_equal(actual['final_centers'],raw['final_centers'])
                assert projection(fresh)==projection(direct)==projection(fast)
                records.append({'family':name,'m':cfg.m,'seed':seed,'removed':removed,'witness':objhash(projection(fresh)),'summary':objhash(extra_witness(fresh))})
            active=dict(data);gs=dict(groups);cs=comp
            for c in sorted(data):
                if any(cs.counts[g]==cs.client_counts[c][g] for g in range(cfg.m)):continue
                output,cs=mg.delete_c0(cs,[c]);active.pop(c);gs.pop(c)
                raw=oracle.fresh0(active,gs,seed,cfg);extra_equal(output,raw);exact_equal(output['final_centers'],raw['final_centers'])
                sequences.append({'family':name,'m':cfg.m,'seed':seed,'removed_now':c,'remaining':cs.client_ids})
            for bad in ([9999],[True],[-1],[0.5],[next(iter(data))]*2,'0',{'client':0}):
                expect_value_error(lambda:mg.delete_c0(comp,bad));invalid+=1
            # Compaction must not use raw records, group arrays or refinement outputs.
            class Trap(dict):
                def __getitem__(self,k):
                    if k in ('data','encoded','groups'):raise AssertionError('raw access in compaction')
                    return super().__getitem__(k)
            mg.compact(Trap(state))
            for key,s in comp.slices.items():
                for field,v in s.items():
                    if isinstance(v,np.ndarray):assert not v.flags.writeable and not np.shares_memory(v,state['slices'][key][field])
        # All valid single whole-client T1/T2 replays, two seeds.
        for seed in (0,7):
            for T in (1,2):
                config=replace(cfg,T=T);original=mg.train(data,groups,seed,config,True)
                valid=[c for c in data if all(original['state']['counts'][g]>original['state']['client_counts'][c][g] for g in range(cfg.m))]
                # One fixed valid client per fixture (smallest persistent ID), independent of outputs.
                c=min(valid);d={i:x for i,x in data.items() if i!=c};g={i:v for i,v in groups.items() if i!=c}
                fresh=mg.train(d,g,seed,config)
                with patch.object(mg,'local_summary',side_effect=AssertionError('local reseed')):direct=mg.direct(original['state'],[c])
                assert projection(fresh)==projection(direct);extra_equal(fresh,direct)
                represented=oracle.encode(d,config.scale_bits,config.clip)
                for t in range(T):
                    assert fresh['per_round_stats'][t]==oracle.scalar_stats(represented,g,fresh['trajectory'][t],cfg.m,2**config.scale_bits)
                    info=fresh['updates'][t];assert info['Phi']==max(info['returned_costs']) and info['G']==sum(info['returned_costs'])
                    assert info['gap']==info['Phi']-info['D']>=0 and info['Phi']<=max(info['incumbent_costs'])
                    guard_rejected+=int(not info['accepted'])
                costs=[oracle.scalar_costs(represented,g,centers,cfg.m) for centers in fresh['trajectory']]
                assert all(max(b)<=max(a) for a,b in zip(costs,costs[1:]))
                replays.append({'family':name,'m':cfg.m,'seed':seed,'T':T,'removed':[c],'witness':objhash(projection(fresh)),'costs':costs,'gaps':[u['gap'] for u in fresh['updates']]})
    # Input domain checks (not trusted forged-state validation).
    _,d,g,cfg=cases()[0]
    for bad in (0,True,1.2):expect_value_error(lambda:mg.Config(bad));invalid+=1
    for change in ('float','out_of_range','negative','global_missing'):
        gg={c:v.copy() for c,v in g.items()}
        if change=='float':gg[0]=gg[0].astype(float)
        elif change=='out_of_range':gg[0][0]=cfg.m
        elif change=='negative':gg[0][0]=-1
        else:gg={c:np.where(v==cfg.m-1,0,v) for c,v in gg.items()}
        expect_value_error(lambda:mg.train(d,gg,0,cfg));invalid+=1
    # Separate bounded primal reference, including inactive groups/zero denominators.
    tests=[('inactive3',[[[0]],[[4]],[[1]]],[2],F(4)),('inactive5',[[[-2]],[[-1]],[[0]],[[1]],[[2]]],[0],F(4)),
           ('variance3',[[[-2,2]],[[2,4]],[[0,0]]],[1],None),
           ('two_cluster5',[[[F(-4)+F(g,4)],[F(3)+F(g-2,2)]] for g in range(5)],[-3,3],None),
           ('zero_denominators3',[[[0],[],[]],[[],[2,4],[]],[[],[3,7],[]]],[0,5,100],None),
           ('ties3',[[[0,0],[]],[[0],[]],[[0,0,0],[]]],[0,0],F(0))]
    optim=[];zero_cases=[]
    for name,cells,old,known in tests:
        m=len(cells);k=len(old);scale=4;counts=tuple(sum(map(len,row)) for row in cells)
        N=[[len(p) for p in row] for row in cells];S=[[[sum(int(F(x)*scale) for x in p)] for p in row] for row in cells];SS=[[sum(int(F(x)*scale)**2 for x in p) for p in row] for row in cells]
        config=mg.Config(m,k=k,scale_bits=2,clip=128.);before=np.array(old,dtype=float).reshape(-1,1)
        got,info=mg.guarded_update(before,N,S,SS,counts,config)
        reference=oracle.primal_reference(cells,old)
        vals=tuple(sum((F(x)-F.from_float(float(got[j,0])))**2 for j,p in enumerate(row) for x in p)/counts[g] for g,row in enumerate(cells))
        assert vals==info['returned_costs'];assert reference['lower']<=max(vals) and info['D']<=reference['upper']
        if known is not None:assert reference['lower']<=known<=reference['upper'] and info['D']<=known<=max(vals)
        assert max(vals)-reference['upper']<=info['gap']
        zero_cases.extend(e['zero_denominators'] for e in info['evaluations'] if e['zero_denominators'])
        optim.append({'name':name,'oracle':reference,'known_optimum':known,'returned_Phi':info['Phi'],'D':info['D'],'gap':info['gap'],'accepted':info['accepted'],'trace':info})
    assert zero_cases
    # Actual guard rejection: incumbent at exact minimax optimum, zero search budget.
    cfg=mg.Config(3,k=1,iterations=0,scale_bits=2)
    out,info=mg.guarded_update(np.array([[2.]]),[[1],[1],[1]],[[[0]],[[16]],[[4]]],[[0],[256],[16]],(1,1,1),cfg)
    assert not info['accepted'];exact_equal(out,[[2.]])
    # Small binary initializer regression only; no claim for positive-round map.
    from train import train_full
    binary=mg.Config(2,k=2,scale_bits=2)
    bd={0:np.array([[0.],[1.],[3.]]),8:np.array([[-1.],[2.]])};bg={0:np.array([0,1,1]),8:np.array([0,1])}
    binary_checks=[]
    for s in (0,7,19):
        legacy=train_full(bd,bg,s,2,0,6,fp_cfg=binary.fp,build_cache=False)
        new=mg.train(bd,bg,s,binary);exact_equal(legacy['final_centers'],new['final_centers']);binary_checks.append(s)
    receipt={'status':'PASS','self_validation_only':True,'created_utc':utc(),'t0_comparisons':records,'T1_T2_comparisons':replays,'sequence_steps':sequences,
             'invalid_requests_rejected':invalid,'optimizer_cases':optim,'positive_round_guard_rejections':guard_rejected,'explicit_guard_rejection':True,
             'zero_denominator_cases':len(zero_cases),'binary_T0_only_seeds':binary_checks,
             'code_hashes':{n:sha(ROOT/n) for n in ('multigroup.py','oracle.py','fixtures.py','test_multigroup.py','PROTOCOL.md','FROZEN_GRID.json')}}
    write_json(ROOT/'CORRECTNESS.json',receipt,True)
    print(json.dumps({'status':'PASS','T0':len(records),'T1_T2':len(replays),'sequence_steps':len(sequences),'invalid':invalid,'optimizer_cases':len(optim),'oracle_tolerance_met':[o['oracle']['tolerance_met'] for o in optim]}))
if __name__=='__main__':
    try:main()
    except Exception:
        write_json(ROOT/'TEST_FAILURE.json',{'utc':utc(),'traceback':traceback.format_exc(),'source_sha256':sha(ROOT/'multigroup.py')})
        raise
