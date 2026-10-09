from common import *
import csv,statistics
from datetime import datetime,timezone
read=lambda f:list(csv.DictReader((ROOT/'tables'/f).open()))
a=read('aggregate_timings.csv');p=read('paired_ratios.csv');c=read('case_method_timings.csv');q=read('quality_exact.csv');w=read('aggregate_work.csv');setup=read('setup_costs.csv');raw=read('raw_timings.csv')
assert len(c)==120 and len(p)==90 and len(raw)==480 and len(q)==45
lookup={(r['T'],r['dataset'],r['method'],r['scope']):r for r in a}
num=lambda r,k:float(r[k])
mean=lambda rows,key:statistics.mean(num(r,key) for r in rows)

def table(headers,rows):return '| '+' | '.join(headers)+' |\n| '+' | '.join('---' for _ in headers)+' |\n'+'\n'.join('| '+' | '.join(str(v) for v in row)+' |' for row in rows)+'\n'
lines=['# Whole-client deletion with one or two fair-refinement rounds','',
'**Useful positive-T speedups survive, with a substantial reduction from C0.** Canonical Direct is **2.357x faster at T=1** and **1.696x faster at T=2** by the ratio of total resident-request times against matched-budget fresh. It wins all 15 cases at each budget. Basic and Runner-up also beat matched fresh in every case, but are slower than Direct: both trigger fallback in the first round in all 30 settings, with zero certificate passes. No positive-budget 10x result was observed or sought.','',
'All 30 settings completed: **120 distinct method outputs, 90 distinct replay-versus-fresh comparisons, 480 timing observations**. Four repeats provide timing variation; they do not create new scientific trials. Every indexed center in C0..CT, final center, and exact N/S/SS matches matched fresh. All 30 new fresh witnesses also match the previously saved same-population T1/T2 quality witnesses.','',
'This experiment uses the unchanged FTF-1D-descriptor-v1 Fresh/Direct/Basic/Runner-up paths. The compact-summary C0 candidate was neither imported nor called at positive T. Its proof and independent review do not certify this new measurement harness. Evidence is delivered for orchestrator review, without editing the live manuscript or publishing.','',
'## Fixed design and timing contract','',
'Run `client-refinement-20260926-v1`; source aggregate d76d7c0606512c458147955aff2a0afea992c87246ce30e4c43cc28003602c31. The frozen protocol extends exactly the 15 accepted C0 cases to T=1,2: Adult/Bank/Credit, k=10, seeds 10000-10004, identical canonical partition seed 0 and departing original client 0. Original client IDs are never renumbered. Removed populations are 300/30162 (Adult), 2259/45211 (Bank), and 299/30000 (Credit). Both global groups remain nonempty. b=12, L=6, gamma=0, no anchor Lloyd and fixed clips 175/121/74. The existing source, data, preprocessing and identity hashes are verified; no refit or download occurred.','',
'Each setting builds its required original-population checkpoint at the same T, with full round caches. All method inputs/checkpoints are resident. Fresh uses build_cache=False and receives survivor dictionary views; replay receives the original checkpoint and a departing-client row-index vector. The public-call algorithm timer includes encoding/materialization, Phase I and refinement. The broader request timer includes actual request preparation and identical full witness projection/serialization/local write, without fsync. Setup, initial data load, pre-call garbage collection, quality/reference checks and result verification are outside request time and separately reported. There is no cold-fresh/warm-replay, durable-state, physical erasure or network-service claim.','',
'Four method-order rotations per setting place each method in every timing position exactly once. No failures, exclusions, numerical mismatches, hidden retries or timing-based case choices occurred.','',
'## Matched-budget runtime results','']
rows=[]
for T in ('1','2'):
 for ds in ('adult','bank','credit','all'):
  vals=[]
  for method in ('direct','basic','runnerup'):
   ar=lookup[T,ds,method,'algorithm'];er=lookup[T,ds,method,'request'];vals.extend([f"{num(ar,'ratio_of_total_times'):.3f}",f"{num(er,'ratio_of_total_times'):.3f}"])
  rows.append([ds.title(),T,*vals])
lines.append(table(['Dataset','T','Direct alg.','Direct request','Basic alg.','Basic request','Runner-up alg.','Runner-up request'],rows))
lines+=['Every ratio is fresh/method with the SAME refinement budget. Values above 1 favor replay. Dataset rows have five seed cases, and each pooled budget has 15; all methods have 15 wins, zero losses and zero ties at each budget.','']
rows=[]
for T in ('1','2'):
 for method in ('direct','basic','runnerup'):
  r=lookup[T,'all',method,'request']
  rows.append([T,method,f"{num(r,'fresh_total_seconds'):.6f}",f"{num(r,'method_total_seconds'):.6f}",f"{num(r,'paired_mean'):.3f}",f"{num(r,'paired_median'):.3f}",f"{num(r,'paired_sd'):.3f}",f"{num(r,'paired_min'):.3f}-{num(r,'paired_max'):.3f}"])
lines.append(table(['T','Method','Fresh total s','Method total s','Paired mean','Median','SD','Paired range'],rows))
lines+=['Totals contain all 60 observations per method/budget. Paired ratios divide four-repetition mean fresh time by mean replay time within each seed/dataset/budget. Means of ratios differ from ratios of sums. `tables/paired_ratios.csv` has all 90 distinct paired comparisons, including both algorithm and request ratios; `repetition_ratios.csv` contains the 360 timing-repeat ratios, explicitly labeled as repeats. No heterogeneous-suite IID confidence interval is claimed.','',
'All 30 settings appear below. Times are mean resident-request milliseconds; ratios are fresh/method for the same T.','']
cm={(r['case_id'],r['method']):r for r in c};pm={(r['case_id'],r['method']):r for r in p}
rows=[]
for s in json.loads((ROOT/'FROZEN_GRID.json').read_text())['cases']:
 cid=s['case_id'];rows.append([s['dataset'].title(),s['seed'],s['T'],f"{1000*num(cm[cid,'fresh'],'mean_request_e2e_seconds'):.2f}",f"{1000*num(cm[cid,'direct'],'mean_request_e2e_seconds'):.2f}",f"{num(pm[cid,'direct'],'request_ratio'):.3f}",f"{num(pm[cid,'basic'],'request_ratio'):.3f}",f"{num(pm[cid,'runnerup'],'request_ratio'):.3f}"])
lines.append(table(['Dataset','Seed','T','Fresh ms','Direct ms','Direct ratio','Basic ratio','Runner-up ratio'],rows))
cv=[]
for method in ('fresh','direct','basic','runnerup'):
 v=[num(r,'cv_request_e2e_seconds') for r in c if r['method']==method];cv.append(f'{method} {100*min(v):.2f}-{100*max(v):.2f}%')
lines+=['Within-setting request-time coefficients of variation across four repetitions: '+ '; '.join(cv)+'. All means, standard deviations, min/max values, components and observations are retained. These local short measurements on a single workstation are not general deployment guarantees.','',
'## Refinement, certificates and fallback','',
'Phase-II costs were audited explicitly. The additive decomposition includes encoding, materialization, cache construction, Phase-I client/server work, shift bounds, Phase-II client certificate checks, Phase-II client recomputation and Phase-II server work, plus an unclassified residual. Sums cover every client AND every round. Modeled client-parallel maxima are not used as measured denominators. The residual includes validation, count bookkeeping, digests and timer/object overhead; it is not silently labeled as refinement.','',
'`certificate_scan`, `failed_assignment`, `fallback_sunk` and `fallback_rebuild` are overlapping diagnostics. Their underlying operations already occur in additive client/server/shift buckets, so these diagnostic timers are never added again. `accounting.py`, the synthetic timer fixture and per-observation arithmetic checks establish the reporting boundary.','',
'Mean milliseconds below show Phase-I versus instrumented refinement costs. Other encoding/materialization/output/residual costs are separately retained in the full table.','']
rows=[]
for ds in ('adult','bank','credit'):
 for T in ('1','2'):
  vals=[]
  for method in ('fresh','direct','basic','runnerup'):
   r=[x for x in c if x['dataset']==ds and x['T']==T and x['method']==method]
   vals.extend([f"{1000*mean(r,'mean_derived_nonadditive_phase1_seconds'):.2f}",f"{1000*mean(r,'mean_derived_nonadditive_refinement_instrumented_seconds'):.2f}"])
  rows.append([ds.title(),T,*vals])
lines.append(table(['Dataset','T','Fresh I','Fresh II','Direct I','Direct II','Basic I','Basic II','Runner-up I','Runner-up II'],rows))
lines+=['Direct saves most original local-summary recomputation, but must redo survivor refinement. Its refinement time closely tracks fresh. A component model F(T)=L+S+T*R+overhead versus D(T)=B+S+T*R+overhead explains the falling ratio: shared raw-data refinement grows with T, while the avoided local Phase-I work remains roughly fixed. This measured grid establishes T=1/2 only; it is not a theorem about arbitrary T or another optimized implementation.','',
'Each certificate method attempts every survivor in round 0, obtains P=0, exceeds the strict-majority threshold, and rebuilds that round. At T=2, round 1 starts direct. Therefore certification repeats one full survivor assignment round without saving any assignments. It still beats fresh here because it retains the Phase-I reuse saving, but it offers no advantage over Direct. No fallback-policy optimization was attempted.','',
'Pooled point-work counts below are counted ONCE per setting/method, not four times. N is survivor point-rounds; A attempted certificate point-rounds; P passes including abandoned-round passes; S useful passes; J failed assignments repeated by the triggering rebuild. For A=0, P/A is undefined. Direct starting in direct mode is not a threshold-triggered fallback.','']
rows=[]
for r in w:
 if r['dataset']=='all':rows.append([r['T'],r['method'],r['N'],r['A'],r['P'],r['S'],r['J'],'undefined' if not r['pooled_P_over_A'] else f"{100*num(r,'pooled_P_over_A'):.3f}%",f"{100*num(r,'pooled_S_over_N'):.3f}%",r['threshold_fallback_settings'],r['modeled_point_assignments']])
lines.append(table(['T','Method','N','A','P','S','J','P/A','S/N','Fallback /15','N-S+J'],rows))
lines+=['The Basic/Runner-up modeled assignment count is 2N at T=1 and 1.5N at T=2. `aggregate_work.csv` also preserves mean case fractions separately from pooled fractions, and `round_work_counters.csv` records each round. Overlapping sunk/rebuild timing diagnostics remain in `raw_timings.csv` and `case_method_timings.csv`; they are not added to these point counts or to elapsed totals.','',
'## Fairness/quality on the identical retained populations','',
'Phi=max(Phi_A,Phi_B) is worst-group mean squared cost. Canonical G=Phi_A+Phi_B is the SUM of group-normalized costs, not the max. Every saved exact fraction was checked against these identities and pooled SSE=n_A*Phi_A+n_B*Phi_B. All 45 T0/T1/T2 quality rows are reused from the accepted whole-client run, with source/input/identity/full-witness/center hashes checked; every newly measured fresh T1/T2 witness agrees exactly. No quality values from the different record-deletion task are used, and no new scoring run is disguised as a validation pass.','',
'The following are averages over five seed cases. Mean Phi averages each case maximum, so it need not equal the maximum of the two displayed mean group columns.','']
rows=[]
for ds in ('adult','bank','credit'):
 for T in ('0','1','2'):
  r=[x for x in q if x['dataset']==ds and x['T']==T];rows.append([ds.title(),T,f"{mean(r,'Phi_A'):.4f}",f"{mean(r,'Phi_B'):.4f}",f"{mean(r,'G'):.4f}",f"{mean(r,'Phi'):.4f}"])
lines.append(table(['Dataset','T','Mean Phi_A','Mean Phi_B','Mean G (sum)','Mean Phi (max)'],rows))
lines+=['Across the 15 paired cases, T=1 reduces Phi by 14.2-35.9% relative to T=0; T=2 reduces it by 15.4-38.3%. All budgets refer to fair-refinement rounds: initialization already communicates local summaries and initializes the server at T=0. These are empirical utility differences, with no author-specified adequacy threshold. T1/T2 quality is not a license to change an existing T15 learner claim.','',
'## Historical C0 performance context','',
'For context only, accepted run `client-c0-20260926-v1` used three repetitions and the same resident-request boundary on the same cases. Its request ratios of total times were:','',
table(['Dataset','Canonical Direct T0','Compact-fast T0'],[['Adult','14.09x','26.96x'],['Bank','35.58x','115.53x'],['Credit','13.96x','25.03x'],['All','17.79x','35.79x']]),
'These are historical results, not new T0 measurements or cross-budget speedup denominators. The C0 compact candidate has no T1/T2 point or curve here. Timing comparability is limited by separate runs/background loads and three versus four repeats; output grows to include actual positive-round statistics at T1/T2, equally for every matched method. `historical_c0_context.csv` preserves the labels and run identity. The appendix PDF plots only current canonical T1/T2 speedups and the separately labeled verified quality budgets.','',
'## Setup, environment, validation and handoff','',
'Original-population checkpoint construction, cache construction, serialization-size measurement, input/reference loading and equality checking were separately charged in `tables/setup_costs.csv`. Full checkpoints existed only in each worker; serialized sizes were measured in memory and no new full checkpoint was persisted. `SETUP_COST_INVENTORY.md` gives the lifecycle and measured per-dataset/budget summary. There is no disk-savings or actual RAM-reduction claim.','',
'All substantial gate/grid workers used the exclusive shared fcntl lock at `/private/tmp/ftf_benchmark_20260926.lock`, held by the parent across the subprocess and released between settings. Each worker set OMP/OpenBLAS/MKL/NumExpr/vecLib limits to one before importing NumPy. The read-only environment is Python 3.12.14 / NumPy 2.3.5, macOS 27.0 arm64 on Apple M3 Max/48 GiB. Native pool introspection is unavailable because threadpoolctl is absent; environment controls and one-worker execution are recorded. Background load/top CPU processes and queue/held times remain in lock.jsonl. No machine-wide settings were changed.','',
'The three targeted harness tests passed (12 fixture replay comparisons), followed by the complete fixed grid. `CORRECTNESS.md`, `HARNESS_GATE.json` and `RESULTS_VERIFICATION.json` distinguish actual execution, saved-byte verification and historical quality reuse. Baseline and every accepted C0 artifact are rehashed at delivery. No new independent numerical oracle or third-party review of this extension is claimed. Prior Task C approval applied only to the compact C0 snapshot.','',
'For review: `REPORT.md`, `PROTOCOL.md`, `CORRECTNESS.md`, all `tables/`, `SETUP_COST_INVENTORY.md`, `REPRODUCE.md`, `INTEGRATION_NOTES.md`, and `output/whole_client_refinement_appendix.pdf`. `MANIFEST.json` binds delivered source/evidence files. Full indexed witnesses and all raw observations remain under `runs/client-refinement-20260926-v1`. No requested setting is pending.','',
'All new work remains in this local directory. Accepted C0 sources/snapshots/results/reports, live manuscript, shared Git and Overleaf were not modified. No additional agents, downloads, archive restores, usage resets or external shares were used.']
(ROOT/'REPORT.md').write_text('\n'.join(lines)+'\n')
# Numeric lifecycle summary from measured setup receipts.
lines=['# Setup and cost inventory','',
'The current experiment uses full canonical original-population checkpoints at each positive T. It does not use the C0 compact state. All figures below are five-seed means, measured once per distinct setting; the four request repetitions do not replicate setup counts.','']
rows=[]
for ds in ('adult','bank','credit'):
 for T in ('1','2'):
  r=[x for x in setup if x['dataset']==ds and x['T']==T]
  rows.append([ds.title(),T,f"{1000*mean(r,'canonical_original_training_seconds'):.3f}",f"{1000*mean(r,'checkpoint_cache_construction_seconds'):.3f}",f"{mean(r,'checkpoint_pickle_bytes')/1048576:.3f}",f"{1000*mean(r,'checkpoint_serialization_seconds'):.3f}",f"{1000*mean(r,'input_load_verify_seconds'):.3f}",f"{1000*mean(r,'output_verification_seconds'):.3f}"])
lines.append(table(['Dataset','T','Original train ms','Included cache construction ms','Checkpoint MiB','Serialization ms','Input load/verify ms','All-repeat verification ms'],rows))
lines+=['Cache construction is nested in original training cost; do not add it again. Serialized checkpoint sizes use pickle protocol 5 in memory; no full checkpoint files were written. Original checkpoints include represented/encoded raw arrays, group arrays, local summaries, trajectory, exact statistics and per-point label/distance/runner-up caches for each round. State scales with raw data and refinement budget, unlike compact C0-only summaries.','',
'Fresh requests use build_cache=False; fresh cache-construction timers are zero. It still executes the unchanged canonical assignment kernel, which may calculate intermediate runner-up information; no asymmetrical kernel optimization is introduced. Replay uses required already-resident original checkpoints. New requests do not require disk checkpoint loading or durable next-state persistence.','',
'Request timers include request vector/survivor dictionary preparation, the public algorithm, exact full model projection and equal JSON/local write. Initial input verification, checkpoint production and size serialization, historical quality loading/checks, pre-call garbage collection and equality checks are outside these timers and separately recorded. Quality is reused only after complete output/source/identity hashes match, with no new scoring run. Historical scoring costs appear only with their historical label in quality_exact.csv; new scoring cost is zero.','',
'Disjoint refinement cost includes shift bounds, Phase-II certificate checks, Phase-II recomputation and server aggregation/update. certificate_scan, failed_assignment, fallback_sunk and fallback_rebuild overlap those operations. The raw observations retain both families; never sum the diagnostic family into additive totals. All additive sums and request sums were checked.','',
'Original data, historical checkpoints, model witnesses and experiment outputs may retain personal information. No secure-erasure or cache-equality guarantee follows from model equality. No cloud export, disk savings, native pool introspection or measured network service is claimed. Local evidence needs a separately chosen backup.']
(ROOT/'SETUP_COST_INVENTORY.md').write_text('\n'.join(lines)+'\n')
print('REPORT.md and SETUP_COST_INVENTORY.md generated from all 480 observations.')
