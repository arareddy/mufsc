#!/usr/bin/env python3
"""Optional ACS source acquisition and numerical regeneration. Not needed for reproduction with packaged data."""
from pathlib import Path
import argparse,sys,os,json,shutil,importlib.util,hashlib
R=Path(__file__).resolve().parent
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):os.environ[key]='1'
sys.dont_write_bytecode=True
p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['fetch','rebuild']);p.add_argument('--workspace',type=Path,required=True);p.add_argument('--states',help='Comma-separated state abbreviations for fetch only');a=p.parse_args();w=a.workspace.resolve();w.mkdir(parents=True,exist_ok=True)
def module(name,file):
 spec=importlib.util.spec_from_file_location(name,file);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
manifest=json.loads((R/'raw_acs/manifests/source_manifest_v1.json').read_text())
if a.action=='fetch':
 m=module('fetch_reference',R/'raw_acs/scripts/refetch_sources.py');states=a.states.split(',') if a.states else sorted(manifest['states']);assert all(s in manifest['states'] for s in states)
 logs=w/'fetch-logs';logs.mkdir(exist_ok=True)
 for state in states:
  receipt=m.restore(state,manifest['states'][state],w/'source_cache',logs);(logs/(state+'.json')).write_text(json.dumps(receipt,indent=2)+'\n');print(state,receipt['status'],flush=True)
else:
 import numpy as np,folktables
 assert np.__version__=='2.3.5','Use the frozen NumPy version for the pooled transform.'
 assert folktables.__version__=='0.0.12','Use frozen Folktables version.'
 sys.path[:0]=[str(R/'core/src'),str(R/'core/experiments')]
 import pandas as pd
 assert pd.__version__=='2.3.3'
 for part in ['manifests','specification']:
  (w/part).mkdir(exist_ok=True)
  for f in (R/'raw_acs'/part).iterdir():
   dest=w/part/f.name
   if dest.exists():assert dest.read_bytes()==f.read_bytes()
   else:shutil.copyfile(f,dest)
 m=module('prepare_reference',R/'raw_acs/scripts/prepare_acs2018_v1.py');m.P3=w;m.DATA=w/'rebuilt';m.PROTOCOL=w/'specification/PROTOCOL_v1.json';m.DATA.mkdir(exist_ok=False)
 # These wrappers replace machine/source provenance paths only. Original build_pool arithmetic is unchanged.
 pool,native,source=m.build_pool(json.loads(m.PROTOCOL.read_text()))
 from p3_acs import prepare_federation
 receipts=[]
 for meta in sorted((R/'data/acs').glob('*.json')):
  name=meta.stem;n,C=map(int,name.replace('n','').split('_C'));f,reason=prepare_federation(pool,n,C);assert not reason
  keys=sorted(f.client_data);offsets=np.cumsum([0]+[len(f.client_data[c]) for c in keys],dtype=np.int64)
  arrays={'X':np.concatenate([f.client_data[c] for c in keys]),'groups':np.concatenate([f.group_of[c] for c in keys]),'offsets':offsets,'client_ids':np.array(keys,dtype=np.int64),'row_ids':np.concatenate([f.source_record_ids[c] for c in keys])}
  expected=json.loads(meta.read_text())['arrays']
  for k,x in arrays.items():assert hashlib.sha256(x.tobytes(order='C')).hexdigest()==expected[k]['raw_C_order_sha256'],name+'/'+k
  np.savez_compressed(m.DATA/(name+'.npz'),**arrays);receipts.append({'population':name,'exact_arrays_match':True});print(name,'PASS',flush=True)
 (m.DATA/'receipt.json').write_text(json.dumps(receipts,indent=2)+'\n')
