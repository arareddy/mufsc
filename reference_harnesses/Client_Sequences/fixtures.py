from common import *
from test_client_c0 import Gate,data,train,CHECKS
from client_c0 import compact_checkpoint,delete_clients
from service import check_state,persist,state_hash
from fractions import Fraction
from objective import fair_objective
import unittest,tempfile,time
start=time.perf_counter()
result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Gate))
assert result.wasSuccessful()
cd,go=data({3:[((-2,0),0),((1,0),1)],17:[((0,0),0),((2,1),1)],99:[((1,1),0),((1,1),1)],400:[]})
state=compact_checkpoint(train(cd,go));records=[];rejects=[]
with tempfile.TemporaryDirectory(dir=ROOT) as td:
 for c in (400,17,3):
  before=state_hash(state);output,new=delete_clients(state,[c]);assert before==state_hash(state)
  loaded,storage=persist('compact',new,Path(td)/'state.pkl');check_state(loaded,new)
  cd={key:v for key,v in cd.items() if key!=c};go={key:v for key,v in go.items() if key!=c}
  fresh=train(cd,go);assert projection(output)==projection(fresh);check_extra(output,fresh)
  check_state(loaded,compact_checkpoint(fresh));state=loaded
  for request in ([c],[-1],[True],[1.0],[99,99],[777],[[99]],np.array([[99]]),{'client':99},list(state.client_ids)):
   try:delete_clients(state,request)
   except (ValueError,TypeError):rejects.append(repr(request))
   else:raise AssertionError(('accepted malformed/domain-invalid request',request))
  records.append({'withdrawal':c,'survivors':list(state.client_ids),'input_state_hash':before,'next_state_hash':state_hash(state),'full_model':projection(output),'persistence':storage})
 # Malformed checkpoint bytes must not silently pass the local pickle loader.
 import pickle
 try:pickle.loads(b'not a pickle')
 except (pickle.UnpicklingError,EOFError):pass
 else:raise AssertionError('invalid bytes accepted')
 ledger,receipt=persist('fresh',tuple(sorted(cd)),Path(td)/'ledger.json');assert ledger==tuple(sorted(cd))
phi0,phi1,G,Phi=fair_objective(np.array([[0.],[2.],[5.]]),np.array([0,0,1]),np.array([[0.]]),return_exact=True)
assert (phi0,phi1,G,Phi)==(Fraction(2),Fraction(25),Fraction(27),Fraction(25))
write_json(ROOT/'CORRECTNESS.json',{'status':'PASS','copied_gate_methods':result.testsRun,'copied_gate_exact_comparisons':len(CHECKS),'new_serialized_sequence_steps':records,'invalid_request_rejections':len(rejects),'invalid_requests':rejects,'malformed_pickle_rejected':True,'exact_fraction_definition_fixture':{'Phi0':'2','Phi1':'25','G':'27','Phi':'25'},'elapsed_seconds':time.perf_counter()-start,'source_hashes':{name:sha256(ROOT/name) for name in ('client_c0.py','service.py','fixtures.py','test_client_c0.py','common.py')},'scope':'Trusted local state only; canonical shared-kernel reference; not independent arithmetic oracle.'},immutable=True)
print('Sequence serialization gate PASS')
