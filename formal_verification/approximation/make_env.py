#!/usr/bin/env python3
"""Inspect an existing pinned installation; never install or download anything."""
import argparse,json,pathlib,subprocess
p=argparse.ArgumentParser();p.add_argument('--lean',required=True);p.add_argument('--mathlib',required=True);p.add_argument('--output',required=True);p.add_argument('--lock',default='/private/tmp/ftf_benchmark_20260926.lock');a=p.parse_args()
lean=pathlib.Path(a.lean).resolve();m=pathlib.Path(a.mathlib).resolve()
v=subprocess.check_output([str(lean),'--version'],text=True).strip();assert 'version 4.19.0' in v,v
rev=subprocess.check_output(['git','-C',str(m),'rev-parse','HEAD'],text=True).strip();assert rev=='c44e0c8ee63ca166450922a373c7409c5d26b00b',rev
manifest=json.loads((m/'lake-manifest.json').read_text())
paths=[m/'.lake/build/lib/lean']+[m/'.lake/packages'/x['name']/'.lake/build/lib/lean' for x in manifest['packages']]
assert paths[0].exists(),'Compile/fetch the pinned mathlib modules with the environment owner first.'
paths=[x for x in paths if x.exists()]
result={'lean':str(lean),'lean_version':v,'mathlib':str(m),'mathlib_revision':rev,'lean_path':':'.join(map(str,paths)),'benchmark_lock':a.lock,'dependencies':manifest}
pathlib.Path(a.output).write_text(json.dumps(result,indent=2)+'\n');print('Pinned existing environment recorded.')
