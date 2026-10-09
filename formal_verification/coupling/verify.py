#!/usr/bin/env python3
"""Run every module serially against an existing pinned mathlib environment."""
import argparse,hashlib,json,pathlib,re,subprocess,sys
p=argparse.ArgumentParser();p.add_argument('--env',required=True);a=p.parse_args()
r=pathlib.Path(__file__).resolve().parent
modules='Coupling WordBlocks Rejection Traces PrefixEvent Deletion Initialization WorkProbability Obstruction InfiniteExpectation JointTrace AxiomAudit'.split()
for m in modules:
 s=r/'proof'/(m+'.lean')
 if re.search(r'\b(sorry|admit|axiom|native_decide|unsafe)\b',s.read_text()):
  raise SystemExit('Forbidden proof construct in '+m)
 cmd=[sys.executable,str(r/'build.py'),'--env',a.env,'proof/'+m+'.lean','--name','final_'+m]
 result=subprocess.run(cmd,cwd=r,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
 print(m+': '+('PASS' if result.returncode==0 else 'FAIL'),flush=True)
 if result.returncode:
  print(result.stdout);raise SystemExit(result.returncode)
 log=(r/'logs'/('final_'+m+'.log')).read_text()
 if 'sorryAx' in log:raise SystemExit('Unexpected placeholder axiom in '+m)
 if m=='AxiomAudit':
  found=[]
  for line in log.splitlines():
   if 'depends on axioms:' in line:
    for ax in line.split('depends on axioms: [',1)[1].rstrip(']').split(', '):
     if ax not in ['propext','Classical.choice','Quot.sound']:
      raise SystemExit('Unexpected axiom: '+ax)
    found.append(line.split("'")[1])
   elif 'does not depend on any axioms' in line:found.append(line.split("'")[1])
  expected=[e['name'] for e in json.loads((r/'THEOREM_INDEX.json').read_text())]
  if sorted(found)!=sorted(expected):raise SystemExit('Incomplete axiom audit')
  (r/'AXIOM_AUDIT.json').write_text(json.dumps(dict(status='pass',theorems=len(found),allowed_axioms=['propext','Classical.choice','Quot.sound'],unexpected_axioms=[],trust=0,threads=1,log='logs/final_AxiomAudit.log'),indent=2)+'\n')
print('All modules and full axiom audit passed.',flush=True)
