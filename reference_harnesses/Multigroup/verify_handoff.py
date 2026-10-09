"""Read-only hash verification of the frozen local handoff and preserved inputs."""
from pathlib import Path
import json,hashlib,sys
ROOT=Path(__file__).resolve().parent

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()

def verify():
    manifest=json.loads((ROOT/'MANIFEST.json').read_text());errors=[]
    for f in manifest['files']:
        p=ROOT/f['path']
        if not p.is_file() or p.stat().st_size!=f['bytes'] or sha(p)!=f['sha256']:errors.append('handoff mismatch: '+f['path'])
    inputs=json.loads((ROOT/'SOURCE_INPUTS.json').read_text());preserved=0;live_changes=[]
    for f in inputs['baseline']:
        if sha(f['path'])!=f['sha256'] or sha(ROOT/f['copy'])!=f['sha256']:errors.append('baseline mismatch: '+f['path'])
        preserved+=1
    for f in inputs['inputs']:
        changed=sha(f['path'])!=f['sha256']
        # The live author task may edit its current source; the snapshot is bound.
        if '/Fair_to_Forget_Live/' in f['path'] and '/evidence/' not in f['path']:
            if changed:live_changes.append(f['path'])
        else:
            if changed:errors.append('completed input changed: '+f['path'])
            preserved+=1
    for f in json.loads((ROOT/'INPUTS.json').read_text())['files']:
        if sha(f['path'])!=f['sha256']:errors.append('dataset dependency changed: '+f['path'])
    ready=ROOT/'READY_FOR_REVIEW.json'
    if ready.exists():
        r=json.loads(ready.read_text())
        if sha(ROOT/'MANIFEST.json')!=r['manifest_sha256']:errors.append('manifest pointer mismatch')
        if sha(ROOT/'HANDOFF_VERIFICATION.json')!=r['handoff_verification_sha256']:errors.append('verification pointer mismatch')
        for name,h in r['frozen_hashes'].items():
            if sha(ROOT/name)!=h:errors.append('frozen pointer mismatch: '+name)
    result={'status':'PASS' if not errors else 'FAIL','manifest_files_checked':len(manifest['files']),'manifest_bytes_checked':sum(f['bytes'] for f in manifest['files']),
            'upstream_baseline_and_completed_inputs_checked':preserved,'read_only_data_dependency_files_checked':len(json.loads((ROOT/'INPUTS.json').read_text())['files']),
            'live_files_changed_by_other_task_since_snapshot':live_changes,'errors':errors}
    return result
if __name__=='__main__':
    result=verify();print(json.dumps(result,sort_keys=True));sys.exit(bool(result['errors']))
