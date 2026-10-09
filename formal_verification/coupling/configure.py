#!/usr/bin/env python3
"""Describe an existing pinned environment; never download or install dependencies."""
import argparse,json,os,pathlib,subprocess
p=argparse.ArgumentParser();p.add_argument('--lean',required=True);p.add_argument('--mathlib',required=True);p.add_argument('--env',required=True);p.add_argument('--lock',default='/tmp/ftf_benchmark_20260926.lock');a=p.parse_args()
lean=pathlib.Path(a.lean).resolve();mathlib=pathlib.Path(a.mathlib).resolve()
version=subprocess.check_output([str(lean),'--version'],text=True).strip()
if 'version 4.19.0,' not in version:raise SystemExit('Expected Lean 4.19.0')
rev=subprocess.check_output(['git','-C',str(mathlib),'rev-parse','HEAD'],text=True).strip()
if rev!='c44e0c8ee63ca166450922a373c7409c5d26b00b':raise SystemExit('Unexpected mathlib revision')
paths=[mathlib/'.lake/build/lib/lean']+sorted((mathlib/'.lake/packages').glob('*/.lake/build/lib/lean'))
if not paths[0].is_dir():raise SystemExit('Existing compiled mathlib is required')
obj=dict(lean=str(lean),lean_path=os.pathsep.join(map(str,paths)),mathlib=str(mathlib),mathlib_revision=rev,lean_version=version,benchmark_lock=a.lock)
pathlib.Path(a.env).write_text(json.dumps(obj,indent=2)+'\n')
print('Pinned existing environment recorded; no downloads performed.')
