"""Adversarial executable gate; no tolerance or permuted-center comparisons."""
from common import *
from train import train_full
from unlearn import unlearn
from fixedpoint import FixedPointConfig
from client_c0 import compact_checkpoint,delete_clients
import unittest,copy,argparse,time
from datetime import datetime,timezone
CHECKS=[]

def data(rows):
    return {c:np.array([p for p,g in values],dtype=np.float64).reshape(-1,2) for c,values in rows.items()}, {c:np.array([g for p,g in values],dtype=np.int64) for c,values in rows.items()}

def train(cd,go,seed=19,k=3,gamma=0.0,anchor=0,T=0):
    return train_full(cd,go,seed,k,T,4,gamma=gamma,fp_cfg=FixedPointConfig(4,8),anchor_lloyd_iters=anchor,build_cache=True)

def check(cd,go,depart,seed=19,k=3,gamma=0.0,anchor=0):
    checkpoint=train(cd,go,seed,k,gamma,anchor)
    before=projection(checkpoint)
    state=compact_checkpoint(checkpoint)
    result,next_state=delete_clients(state,depart)
    retained={c:v for c,v in cd.items() if c not in depart}; groups={c:v for c,v in go.items() if c not in depart}
    fresh=train(retained,groups,seed,k,gamma,anchor)
    direct=unlearn(checkpoint,{c:np.arange(len(cd[c]),dtype=np.int64) for c in depart},certificate_mode='none')
    assert projection(result)==projection(fresh)==projection(direct)
    check_extra(result,fresh);check_extra(result,direct)
    assert projection(checkpoint)==before
    assert next_state.client_ids==tuple(sorted(retained))
    assert state.client_ids==tuple(sorted(cd))
    assert next_state.group_sizes==fresh['group_sizes']
    assert next_state.client_counts=={c:(int(np.sum(groups[c]==0)),int(np.sum(groups[c]==1))) for c in groups}
    for key in next_state.slice_results:assert next_state.slice_results[key] is state.slice_results[key]
    CHECKS.append({'seed':seed,'k':k,'gamma':gamma,'anchor_lloyd_iters':anchor,'departing':depart,'clients':list(cd),'witness':projection(result),'extra_state_equal':True})
    return checkpoint,state

class Gate(unittest.TestCase):
    def setUp(self):
        self.cd,self.go=data({3:[((-2,0),0),((-1,0),0),((0,0),0),((0,1),0),((1,0),0),((2,0),1)],17:[((0,0),0),((2,1),1),((2,2),1),((3,2),1)],99:[((1,1),0),((1,1),1)],400:[]})
    def test_heterogeneous_mixed_gap_and_empty(self):
        for seed in (0,1,10000):
            for k in (1,3,10):check(self.cd,self.go,[17],seed,k)
    def test_single_group_departures(self):
        cd,go=data({0:[((-1,0),0),((1,0),0)],8:[((0,1),1)]*5,23:[((2,2),0),((3,3),1)]})
        for c in (0,8):check(cd,go,[c])
    def test_valid_one_each_boundary_completion(self):
        check(self.cd,self.go,[3,17],k=10)
    def test_empty_client_and_noop(self):
        check(self.cd,self.go,[400]);check(self.cd,self.go,[])
    def test_repeated_zero_mass(self):
        cd,go=data({2:[((0,0),i%2) for i in range(13)],67:[((0,0),i%2) for i in range(6)],901:[((0,0),0),((0,0),1)]})
        for seed in (0,10004):check(cd,go,[67],seed,k=3)
    def test_quantized_ties_and_anchor_lloyd(self):
        for gamma,anchor in ((0.5,0),(0.5,1),(0,1)):
            check(self.cd,self.go,[17],gamma=gamma,anchor=anchor)
    def test_sequential_metadata_updates(self):
        cd,go=self.cd,self.go
        state=compact_checkpoint(train(cd,go))
        for c in (400,17,3):
            result,state=delete_clients(state,[c]);cd={key:v for key,v in cd.items() if key!=c};go={key:v for key,v in go.items() if key!=c}
            fresh=train(cd,go)
            assert projection(result)==projection(fresh);check_extra(result,fresh)
            assert state.client_ids==tuple(sorted(cd));assert state.group_sizes==fresh['group_sizes']
            with self.assertRaises(ValueError):delete_clients(state,[c])
            CHECKS.append({'sequence_departure':c,'survivors':list(cd),'witness':projection(result),'extra_state_equal':True})
    def test_rejections(self):
        state=compact_checkpoint(train(self.cd,self.go))
        for req in ([777],[-1],[True],[1.0],[3,3],[[3]],np.array([[3]]),{3:[]},'3',[3,17,99]):
            with self.subTest(request=str(req)):
                with self.assertRaises(ValueError):delete_clients(state,req)
        cd,go=data({2:[((0,0),0)],6:[((1,1),1)],10:[]})
        s=compact_checkpoint(train(cd,go,k=10))
        for req in ([2],[6],[2,6]):
            with self.assertRaises(ValueError):delete_clients(s,req)
    def test_checkpoint_rejections(self):
        ck=train(self.cd,self.go);bad=dict(ck,T=1)
        with self.assertRaises(ValueError):compact_checkpoint(bad)
        bad=dict(ck,group_sizes={0:999,1:2})
        with self.assertRaises(ValueError):compact_checkpoint(bad)
        with self.assertRaises(ValueError):delete_clients({},[3])
    def test_no_raw_access_and_survivor_mutation(self):
        ck=train(self.cd,self.go);state=compact_checkpoint(ck)
        class Trap:
            def __getitem__(self,key):raise AssertionError('raw record access')
            def __iter__(self):raise AssertionError('raw record scan')
        for key in ('client_data','encoded_data','group_of'):ck[key]=Trap()
        result,new=delete_clients(state,[17])
        expected=train({c:v for c,v in self.cd.items() if c!=17},{c:v for c,v in self.go.items() if c!=17})
        assert projection(result)==projection(expected)
        for summary in state.slice_results.values():
            for v in summary.values():
                if isinstance(v,np.ndarray):assert not v.flags.writeable

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--receipt',default=str(ROOT/'CORRECTNESS.json'));args=ap.parse_args()
    start=time.perf_counter();suite=unittest.defaultTestLoader.loadTestsFromTestCase(Gate);result=unittest.TextTestRunner(verbosity=2).run(suite)
    receipt={'status':'PASS' if result.wasSuccessful() else 'FAIL','utc':datetime.now(timezone.utc).isoformat(),'tests_run':result.testsRun,'failure_count':len(result.failures),'error_count':len(result.errors),'elapsed_seconds':time.perf_counter()-start,'exact_comparisons':CHECKS,'source_hashes':{p.name:sha256(p) for p in (ROOT/'client_c0.py',ROOT/'test_client_c0.py',ROOT/'common.py')},'claim':'Indexed T=0 model and listed compact summary state equality; no equality of all caches or erasure claim; shared canonical arithmetic reference, not an independent numerical oracle.'}
    write_json(args.receipt,receipt);raise SystemExit(0 if result.wasSuccessful() else 1)
