#!/usr/bin/env python3
"""Regenerate eleven experiment figures from frozen CSVs; never trains a model."""
from pathlib import Path
import os,sys,argparse,shutil,subprocess,json
R=Path(__file__).resolve().parent
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
for study in ['Round_Budgets','Group_Quality','Client_Sequences','Lloyd_Comparison','Original']:
 w=out/study;w.mkdir();(w/'figures').mkdir()
 if study!='Original':shutil.copytree(R/'evidence'/study/'tables',w/'tables')
 for name in ['verification.json','VERIFICATION.json','SUMMARY.json']:
  if (R/'evidence'/study/name).exists():shutil.copyfile(R/'evidence'/study/name,w/name)
 env=dict(os.environ,FTF_PLOT_OUTPUT=str(w),PYTHONDONTWRITEBYTECODE='1')
 for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):env[key]='1'
 subprocess.run([sys.executable,'-B',str(R/'plotting'/(study+'.py'))],check=True,env=env,cwd=w)
print(json.dumps({'status':'PASS','PDFs':len(list(out.rglob('*.pdf'))),'scope':'frozen-data plot regeneration; PDF metadata/rendering may depend on library version'}))
