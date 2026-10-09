#!/usr/bin/env python3
import argparse,json,pathlib,subprocess,sys
p=argparse.ArgumentParser();p.add_argument('--env',required=True);p.add_argument('--tag',default='final');a=p.parse_args()
r=pathlib.Path(__file__).resolve().parent
modules=['FiniteLaw','WeightedRoot','Geometry','Transfer','Corollaries','SplitSlices','MergedClients','Quantization','GroupComparison','RationalCopies','AnchorAggregation','Normalization','TouchedMass','WarmStart','Audit']
for mod in modules:
 ret=subprocess.run([sys.executable,str(r/'build.py'),'--env',a.env,'--source','proof/'+mod+'.lean','--tag',a.tag+'_'+mod],capture_output=True,text=True)
 print(mod+': exit '+str(ret.returncode),flush=True)
 if ret.returncode: print(ret.stdout+ret.stderr);sys.exit(ret.returncode)
print('All 15 compilation/audit units passed.',flush=True)
