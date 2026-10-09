from common import *
import csv,datetime
assert not (W/'FROZEN_GRID.json').exists(),'Refuse to replace frozen grid'
old=load(Q/'INPUT_MANIFEST.json');oldmap={r['path']:r for r in old['files']};counts=list(csv.DictReader((Q/'tables/identity_counts.csv').open()));ai=load(A/'input_manifest.json');bi=load(B/'INPUTS.json')['files'];bg=load(B/'FROZEN_GRID.json')['cases'];cases=[];paths=set([Q/'tables/identity_counts.csv',Q/'MANIFEST.json',Q/'VERIFICATION.json',Q/'INPUT_MANIFEST.json',A/'input_manifest.json',B/'INPUTS.json',B/'FROZEN_GRID.json',B/'IDENTITY_REGISTRY.json'])
for r in counts:
 pop,ds,seed=r['population'],r['dataset'],int(r['seed']);case=dict(case_id=f'{pop}_{ds}_s{seed}',population=pop,dataset=ds,seed=seed,counts=[int(r['n_group0']),int(r['n_group1'])],retained_n=int(r['retained_n']),retained_identity_sha256=r['retained_identity_sha256'],references={})
 if pop=='record':
  inp=next(x for x in ai if x['dataset']==ds and x['settings']['seed']==seed);case['record_input']=inp;paths.update([Path(inp['input']),Path(inp['request'])])
  for T in range(3):
   root=A/'runs'/(A/'RUN_ID').read_text().strip()/f'{ds}_s{seed}_T{T}';case['references'][str(T)]=dict(path=str(root/'gate_fresh.json'),witness=str(root/'gate_fresh.witness.json'));paths.update([root/'gate_fresh.json',root/'gate_fresh.witness.json',root/'complete.json'])
 else:
  c=next(c for c in bg if c['dataset']==ds and c['seed']==seed);case['client_spec']=c;case['client_input']=bi[ds];paths.update([Path(bi[ds]['path']),Path(bi[ds]['identity_path'])]);p=B/'runs/client-c0-20260926-v1/quality'/c['case_id']/'quality.json'
  for T in range(3):case['references'][str(T)]=dict(path=str(p))
  paths.update([p,p.parent/'complete.json'])
 cases.append(case)
assert len(cases)==30 and len({c['case_id'] for c in cases})==30
# Every historical data/reference file comes from the completed quality manifest.
files=[]
for p in sorted(paths):
 h=sha(p)
 if str(p) in oldmap:assert h==oldmap[str(p)]['sha256'],str(p)
 st=p.stat();files.append(dict(path=str(p),sha256=h,bytes=st.st_size,mtime_ns=st.st_mtime_ns))
dump(W/'INPUT_MANIFEST.json',dict(files=files,completed_group_quality_manifest_sha256=sha(Q/'MANIFEST.json')))
dump(W/'FROZEN_GRID.json',dict(frozen_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),run_id='matched-start-v1',expected_cases=30,expected_method_budget_rows=180,expected_unique_scored_centers=150,cases=cases,exclusions=[]))
source=list(sorted((SRC/'src').glob('*.py')))+[SRC/'TRAINING_MAP.md',SRC/'experiments/reproducible.py']+list(sorted(W.glob('*.py')))
dump(W/'SOURCE_MANIFEST.json',dict(files=[dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size) for p in source],canonical_changed=False))
dump(W/'PROTOCOL_FREEZE.json',dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),bindings=bindings()))
print('Frozen 30 cases,',len(files),'input files and',len(source),'source files.')
