#!/usr/bin/env python3
"""Preserved 12-observation administrative m-group growth probe; synthetic data."""
from reproduce import *
setup()
import numpy as np,time,gc,pickle
from datetime import datetime,timezone
sys.path.insert(0,str(ROOT/'variants/multigroup'))
import multigroup as mg
from common import write_json,utc
bindings=lambda:{x['path']:x['sha256'] for x in read(ROOT/'SCIENTIFIC_SOURCE_HASHES.json')}

def growth():
    directory=OUTPUT;directory.mkdir(parents=True,exist_ok=False)
    data={c:np.array([[((i*11+q*3+c)%31-15)/4 for q in range(4)] for i in range(180)],float) for c in (0,3,8,21,33,47)}
    observations=[];ms=[2,3,5,9]
    for rep in range(3):
        order=ms[rep:]+ms[:rep]
        for position,m in enumerate(order):
            groups={c:np.arange(180,dtype=np.int64)%m for c in data};cfg=mg.Config(m,k=10)
            gc.collect();begin=time.perf_counter();trained=mg.train(data,groups,7,cfg,True);train_seconds=time.perf_counter()-begin
            begin=time.perf_counter();compact=mg.compact(trained['state']);compaction=time.perf_counter()-begin
            observations.append({'m':m,'repetition':rep,'position':position,'train_seconds':train_seconds,'compaction_seconds':compaction,
                'state_pickle_bytes':len(pickle.dumps(trained['state'],protocol=5)),'compact_pickle_bytes':len(pickle.dumps(compact,protocol=5)),
                'nonempty_slices':len(compact.slices),'anchor_slots':sum(s['k_e'] for s in compact.slices.values()),'client_group_count_cells':len(compact.client_ids)*m})
    write_json(directory/'observations.json',observations)
    write_json(directory/'complete.json',{'status':'PASS','bindings':bindings(),'artifacts':{'observations.json':sha(directory/'observations.json')},'completed_utc':utc()})
    print('growth PASS',flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();OUTPUT=a.output.resolve();growth()
