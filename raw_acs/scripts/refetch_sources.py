#!/usr/bin/env python3
"""Restore absent public source files against frozen hashes, without changing provenance."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import zipfile

P3=Path(__file__).resolve().parents[1]


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def check(path,expected_hash,expected_bytes):
    if path.stat().st_size!=expected_bytes or sha(path)!=expected_hash:
        raise RuntimeError(f'Existing bytes do not match frozen source; refusing replacement: {path}')


def restore(state,record,cache,logs):
    archive=cache/Path(record['archive_file']).relative_to('source_cache')
    source_csv=cache/Path(record['csv_file']).relative_to('source_cache')
    for p in (archive.parent,source_csv.parent,logs):p.mkdir(parents=True,exist_ok=True)
    actions=[]
    if archive.exists():check(archive,record['archive_sha256'],record['archive_bytes'])
    else:
        partial=archive.with_suffix('.zip.part')
        initial=partial.stat().st_size if partial.exists() else 0
        if initial>record['archive_bytes']:raise RuntimeError('Partial archive is larger than frozen source')
        if initial!=record['archive_bytes']:
            for attempt in range(2):
                headers=logs/f'{state}.attempt{attempt}.headers'
                command=['curl','--silent','--show-error','--fail','--location','--proto','=https',
                         '--retry','5','--retry-delay','2','--connect-timeout','30','--max-time','900',
                         '--continue-at','-','--dump-header',str(headers),'--output',str(partial),record['url']]
                result=subprocess.run(command,capture_output=True,text=True)
                (logs/f'{state}.attempt{attempt}.stderr').write_text(result.stderr)
                actions.append(dict(action='https_get',url=record['url'],initial_partial_bytes=initial,
                                    attempt=attempt,curl_exit_code=result.returncode,headers_sha256=sha(headers) if headers.exists() else None))
                if result.returncode==0:break
                if result.returncode in (33,36) and initial>0 and attempt==0:
                    partial.rename(logs/f'{state}.range_unavailable.partial');initial=0
                    continue
                raise RuntimeError(f'Authorized source retrieval failed; partial retained: {result.stderr.strip()}')
        check(partial,record['archive_sha256'],record['archive_bytes'])
        os.replace(partial,archive)
        actions.append(dict(action='restored_archive',sha256=record['archive_sha256'],bytes=record['archive_bytes']))
    with zipfile.ZipFile(archive) as zipped:
        member=zipped.getinfo(record['zip_member'])
        if member.CRC!=record['zip_member_crc32'] or member.file_size!=record['csv_bytes']:
            raise RuntimeError('Archive member metadata differs from frozen CRC/size')
        bad=zipped.testzip()
        if bad:raise RuntimeError(f'ZIP CRC check failed: {bad}')
        if source_csv.exists():check(source_csv,record['csv_sha256'],record['csv_bytes'])
        else:
            partial=source_csv.with_suffix('.csv.part')
            with zipped.open(member) as original,partial.open('wb') as restored:shutil.copyfileobj(original,restored,1024*1024)
            check(partial,record['csv_sha256'],record['csv_bytes']);os.replace(partial,source_csv)
            actions.append(dict(action='restored_csv',sha256=record['csv_sha256'],bytes=record['csv_bytes']))
    return dict(state=state,status='PASS',retrieved_or_verified_utc=datetime.now(timezone.utc).isoformat(),
                archive_file=str(archive),csv_file=str(source_csv),archive_sha256=record['archive_sha256'],
                csv_sha256=record['csv_sha256'],actions=actions or [dict(action='verified_existing')])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache-root',type=Path,default=P3/'source_cache')
    parser.add_argument('--states',help='Optional comma-separated subset for a bounded restoration check')
    parser.add_argument('--jobs',type=int,default=3)
    parser.add_argument('--run-id',default=datetime.now(timezone.utc).strftime('refetch-%Y%m%dT%H%M%SZ'))
    args=parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_-]+',args.run_id):parser.error('simple run ID required')
    if not 1<=args.jobs<=4:parser.error('--jobs must be1..4')
    manifest=P3/'manifests/source_manifest_v1.json';protocol=json.loads((P3/'specification/PROTOCOL_v1.json').read_text())
    if sha(manifest)!=protocol['source_manifest_sha256']:raise RuntimeError('Frozen authoritative source manifest changed')
    records=json.loads(manifest.read_text())['states'];states=args.states.split(',') if args.states else list(records)
    if len(set(states))!=len(states) or any(s not in records for s in states):parser.error('unknown or repeated state')
    logs=P3/'logs/refetch'/args.run_id
    if logs.exists():raise RuntimeError('Retain prior retrieval logs; choose a new --run-id for this invocation')
    logs.mkdir(parents=True)
    outcomes={};errors=[]
    with ThreadPoolExecutor(max_workers=args.jobs) as workers:
        futures={workers.submit(restore,s,records[s],args.cache_root,logs):s for s in states}
        for future in as_completed(futures):
            state=futures[future]
            try:outcomes[state]=future.result();print(json.dumps(dict(state=state,status='PASS')),flush=True)
            except Exception as exc:errors.append(dict(state=state,error=str(exc)));print(json.dumps(errors[-1]),flush=True)
    report=dict(status='FAIL' if errors else 'PASS',source_manifest_sha256=sha(manifest),states=outcomes,errors=errors,
                script_sha256=sha(Path(__file__)),original_provenance_modified=False,
                scope='Restoration to frozen public source bytes; new retrieval observations only. Original dates, headers, receipts and data manifests are unchanged.')
    (logs/'report.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    if errors:raise RuntimeError('Some sources were not restored; see retained report/partials')
    print(logs/'report.json')


if __name__=='__main__':main()
