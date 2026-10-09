# Whole-client deletion with one or two fair-refinement rounds

**Useful positive-T speedups survive, with a substantial reduction from C0.** Canonical Direct is **2.357x faster at T=1** and **1.696x faster at T=2** by the ratio of total resident-request times against matched-budget fresh. It wins all 15 cases at each budget. Basic and Runner-up also beat matched fresh in every case, but are slower than Direct: both trigger fallback in the first round in all 30 settings, with zero certificate passes. No positive-budget 10x result was observed or sought.

All 30 settings completed: **120 distinct method outputs, 90 distinct replay-versus-fresh comparisons, 480 timing observations**. Four repeats provide timing variation; they do not create new scientific trials. Every indexed center in C0..CT, final center, and exact N/S/SS matches matched fresh. All 30 new fresh witnesses also match the previously saved same-population T1/T2 quality witnesses.

This experiment uses the unchanged FTF-1D-descriptor-v1 Fresh/Direct/Basic/Runner-up paths. The compact-summary C0 candidate was neither imported nor called at positive T. Its proof and independent review do not certify this new measurement harness. Evidence is delivered for orchestrator review, without editing the live manuscript or publishing.

## Fixed design and timing contract

Run `client-refinement-20260926-v1`; source aggregate d76d7c0606512c458147955aff2a0afea992c87246ce30e4c43cc28003602c31. The frozen protocol extends exactly the 15 accepted C0 cases to T=1,2: Adult/Bank/Credit, k=10, seeds 10000-10004, identical canonical partition seed 0 and departing original client 0. Original client IDs are never renumbered. Removed populations are 300/30162 (Adult), 2259/45211 (Bank), and 299/30000 (Credit). Both global groups remain nonempty. b=12, L=6, gamma=0, no anchor Lloyd and fixed clips 175/121/74. The existing source, data, preprocessing and identity hashes are verified; no refit or download occurred.

Each setting builds its required original-population checkpoint at the same T, with full round caches. All method inputs/checkpoints are resident. Fresh uses build_cache=False and receives survivor dictionary views; replay receives the original checkpoint and a departing-client row-index vector. The public-call algorithm timer includes encoding/materialization, Phase I and refinement. The broader request timer includes actual request preparation and identical full witness projection/serialization/local write, without fsync. Setup, initial data load, pre-call garbage collection, quality/reference checks and result verification are outside request time and separately reported. There is no cold-fresh/warm-replay, durable-state, physical erasure or network-service claim.

Four method-order rotations per setting place each method in every timing position exactly once. No failures, exclusions, numerical mismatches, hidden retries or timing-based case choices occurred.

## Matched-budget runtime results

| Dataset | T | Direct alg. | Direct request | Basic alg. | Basic request | Runner-up alg. | Runner-up request |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Adult | 1 | 2.060 | 2.053 | 1.165 | 1.164 | 1.160 | 1.159 |
| Bank | 1 | 2.657 | 2.646 | 1.456 | 1.455 | 1.465 | 1.464 |
| Credit | 1 | 2.658 | 2.647 | 1.427 | 1.425 | 1.408 | 1.407 |
| All | 1 | 2.366 | 2.357 | 1.310 | 1.309 | 1.306 | 1.305 |
| Adult | 2 | 1.547 | 1.544 | 1.108 | 1.107 | 1.104 | 1.103 |
| Bank | 2 | 1.831 | 1.828 | 1.288 | 1.287 | 1.287 | 1.286 |
| Credit | 2 | 1.860 | 1.856 | 1.284 | 1.284 | 1.275 | 1.274 |
| All | 2 | 1.699 | 1.696 | 1.201 | 1.200 | 1.197 | 1.196 |

Every ratio is fresh/method with the SAME refinement budget. Values above 1 favor replay. Dataset rows have five seed cases, and each pooled budget has 15; all methods have 15 wins, zero losses and zero ties at each budget.

| T | Method | Fresh total s | Method total s | Paired mean | Median | SD | Paired range |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | direct | 20.550742 | 8.718981 | 2.449 | 2.631 | 0.290 | 2.041-2.681 |
| 1 | basic | 20.550742 | 15.694792 | 1.348 | 1.422 | 0.136 | 1.153-1.489 |
| 1 | runnerup | 20.550742 | 15.744315 | 1.343 | 1.404 | 0.137 | 1.155-1.493 |
| 2 | direct | 28.607252 | 16.870120 | 1.742 | 1.830 | 0.147 | 1.538-1.868 |
| 2 | basic | 28.607252 | 23.836529 | 1.226 | 1.277 | 0.088 | 1.102-1.307 |
| 2 | runnerup | 28.607252 | 23.920129 | 1.221 | 1.266 | 0.087 | 1.099-1.296 |

Totals contain all 60 observations per method/budget. Paired ratios divide four-repetition mean fresh time by mean replay time within each seed/dataset/budget. Means of ratios differ from ratios of sums. `tables/paired_ratios.csv` has all 90 distinct paired comparisons, including both algorithm and request ratios; `repetition_ratios.csv` contains the 360 timing-repeat ratios, explicitly labeled as repeats. No heterogeneous-suite IID confidence interval is claimed.

All 30 settings appear below. Times are mean resident-request milliseconds; ratios are fresh/method for the same T.

| Dataset | Seed | T | Fresh ms | Direct ms | Direct ratio | Basic ratio | Runner-up ratio |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Adult | 10000 | 1 | 435.95 | 211.98 | 2.057 | 1.175 | 1.158 |
| Adult | 10000 | 2 | 632.13 | 410.97 | 1.538 | 1.102 | 1.099 |
| Adult | 10001 | 1 | 439.20 | 213.57 | 2.056 | 1.153 | 1.161 |
| Adult | 10001 | 2 | 628.16 | 404.12 | 1.554 | 1.109 | 1.106 |
| Adult | 10002 | 1 | 433.14 | 211.46 | 2.048 | 1.163 | 1.157 |
| Adult | 10002 | 2 | 635.61 | 410.87 | 1.547 | 1.108 | 1.103 |
| Adult | 10003 | 1 | 438.53 | 214.91 | 2.041 | 1.153 | 1.155 |
| Adult | 10003 | 2 | 635.30 | 412.24 | 1.541 | 1.112 | 1.102 |
| Adult | 10004 | 1 | 436.67 | 211.71 | 2.063 | 1.178 | 1.166 |
| Adult | 10004 | 2 | 628.59 | 408.82 | 1.538 | 1.105 | 1.106 |
| Bank | 10000 | 1 | 337.55 | 128.28 | 2.631 | 1.433 | 1.442 |
| Bank | 10000 | 2 | 467.73 | 253.55 | 1.845 | 1.307 | 1.288 |
| Bank | 10001 | 1 | 339.28 | 129.52 | 2.620 | 1.449 | 1.444 |
| Bank | 10001 | 2 | 479.07 | 263.69 | 1.817 | 1.289 | 1.290 |
| Bank | 10002 | 1 | 336.84 | 127.67 | 2.638 | 1.445 | 1.455 |
| Bank | 10002 | 2 | 469.60 | 254.86 | 1.843 | 1.257 | 1.265 |
| Bank | 10003 | 1 | 351.95 | 132.20 | 2.662 | 1.489 | 1.493 |
| Bank | 10003 | 2 | 460.38 | 256.57 | 1.794 | 1.288 | 1.296 |
| Bank | 10004 | 1 | 350.48 | 130.82 | 2.679 | 1.456 | 1.482 |
| Bank | 10004 | 2 | 471.26 | 256.04 | 1.841 | 1.296 | 1.291 |
| Credit | 10000 | 1 | 250.12 | 94.92 | 2.635 | 1.421 | 1.414 |
| Credit | 10000 | 2 | 325.96 | 178.10 | 1.830 | 1.267 | 1.266 |
| Credit | 10001 | 1 | 246.73 | 92.03 | 2.681 | 1.422 | 1.423 |
| Credit | 10001 | 2 | 328.15 | 176.67 | 1.857 | 1.286 | 1.275 |
| Credit | 10002 | 1 | 246.12 | 92.60 | 2.658 | 1.434 | 1.392 |
| Credit | 10002 | 2 | 326.70 | 174.86 | 1.868 | 1.292 | 1.285 |
| Credit | 10003 | 1 | 243.80 | 92.17 | 2.645 | 1.416 | 1.404 |
| Credit | 10003 | 2 | 328.96 | 177.08 | 1.858 | 1.277 | 1.262 |
| Credit | 10004 | 1 | 251.30 | 95.92 | 2.620 | 1.434 | 1.401 |
| Credit | 10004 | 2 | 334.23 | 179.10 | 1.866 | 1.296 | 1.285 |

Within-setting request-time coefficients of variation across four repetitions: fresh 0.06-3.25%; direct 0.13-4.39%; basic 0.21-2.64%; runnerup 0.25-2.31%. All means, standard deviations, min/max values, components and observations are retained. These local short measurements on a single workstation are not general deployment guarantees.

## Refinement, certificates and fallback

Phase-II costs were audited explicitly. The additive decomposition includes encoding, materialization, cache construction, Phase-I client/server work, shift bounds, Phase-II client certificate checks, Phase-II client recomputation and Phase-II server work, plus an unclassified residual. Sums cover every client AND every round. Modeled client-parallel maxima are not used as measured denominators. The residual includes validation, count bookkeeping, digests and timer/object overhead; it is not silently labeled as refinement.

`certificate_scan`, `failed_assignment`, `fallback_sunk` and `fallback_rebuild` are overlapping diagnostics. Their underlying operations already occur in additive client/server/shift buckets, so these diagnostic timers are never added again. `accounting.py`, the synthetic timer fixture and per-observation arithmetic checks establish the reporting boundary.

Mean milliseconds below show Phase-I versus instrumented refinement costs. Other encoding/materialization/output/residual costs are separately retained in the full table.

| Dataset | T | Fresh I | Fresh II | Direct I | Direct II | Basic I | Basic II | Runner-up I | Runner-up II |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Adult | 1 | 230.60 | 195.00 | 9.96 | 195.77 | 9.96 | 355.89 | 9.92 | 357.92 |
| Adult | 2 | 228.88 | 391.47 | 9.98 | 391.53 | 9.89 | 550.50 | 9.94 | 552.61 |
| Bank | 1 | 213.59 | 124.31 | 2.02 | 123.99 | 2.05 | 229.49 | 2.03 | 228.50 |
| Bank | 2 | 213.67 | 250.38 | 2.02 | 250.81 | 2.03 | 358.16 | 2.04 | 358.34 |
| Credit | 1 | 160.22 | 81.96 | 8.11 | 81.95 | 8.13 | 160.04 | 8.12 | 162.57 |
| Credit | 2 | 159.16 | 164.09 | 8.10 | 165.02 | 8.05 | 242.35 | 8.08 | 243.94 |

Direct saves most original local-summary recomputation, but must redo survivor refinement. Its refinement time closely tracks fresh. A component model F(T)=L+S+T*R+overhead versus D(T)=B+S+T*R+overhead explains the falling ratio: shared raw-data refinement grows with T, while the avoided local Phase-I work remains roughly fixed. This measured grid establishes T=1/2 only; it is not a theorem about arbitrary T or another optimized implementation.

Each certificate method attempts every survivor in round 0, obtains P=0, exceeds the strict-majority threshold, and rebuilds that round. At T=2, round 1 starts direct. Therefore certification repeats one full survivor assignment round without saving any assignments. It still beats fresh here because it retains the Phase-I reuse saving, but it offers no advantage over Direct. No fallback-policy optimization was attempted.

Pooled point-work counts below are counted ONCE per setting/method, not four times. N is survivor point-rounds; A attempted certificate point-rounds; P passes including abandoned-round passes; S useful passes; J failed assignments repeated by the triggering rebuild. For A=0, P/A is undefined. Direct starting in direct mode is not a threshold-triggered fallback.

| T | Method | N | A | P | S | J | P/A | S/N | Fallback /15 | N-S+J |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | fresh | 512575 | 0 | 0 | 0 | 0 | undefined | 0.000% | 0 | 512575 |
| 1 | direct | 512575 | 0 | 0 | 0 | 0 | undefined | 0.000% | 0 | 512575 |
| 1 | basic | 512575 | 512575 | 0 | 0 | 512575 | 0.000% | 0.000% | 15 | 1025150 |
| 1 | runnerup | 512575 | 512575 | 0 | 0 | 512575 | 0.000% | 0.000% | 15 | 1025150 |
| 2 | fresh | 1025150 | 0 | 0 | 0 | 0 | undefined | 0.000% | 0 | 1025150 |
| 2 | direct | 1025150 | 0 | 0 | 0 | 0 | undefined | 0.000% | 0 | 1025150 |
| 2 | basic | 1025150 | 512575 | 0 | 0 | 512575 | 0.000% | 0.000% | 15 | 1537725 |
| 2 | runnerup | 1025150 | 512575 | 0 | 0 | 512575 | 0.000% | 0.000% | 15 | 1537725 |

The Basic/Runner-up modeled assignment count is 2N at T=1 and 1.5N at T=2. `aggregate_work.csv` also preserves mean case fractions separately from pooled fractions, and `round_work_counters.csv` records each round. Overlapping sunk/rebuild timing diagnostics remain in `raw_timings.csv` and `case_method_timings.csv`; they are not added to these point counts or to elapsed totals.

## Fairness/quality on the identical retained populations

Phi=max(Phi_A,Phi_B) is worst-group mean squared cost. Canonical G=Phi_A+Phi_B is the SUM of group-normalized costs, not the max. Every saved exact fraction was checked against these identities and pooled SSE=n_A*Phi_A+n_B*Phi_B. All 45 T0/T1/T2 quality rows are reused from the accepted whole-client run, with source/input/identity/full-witness/center hashes checked; every newly measured fresh T1/T2 witness agrees exactly. No quality values from the different record-deletion task are used, and no new scoring run is disguised as a validation pass.

The following are averages over five seed cases. Mean Phi averages each case maximum, so it need not equal the maximum of the two displayed mean group columns.

| Dataset | T | Mean Phi_A | Mean Phi_B | Mean G (sum) | Mean Phi (max) |
| --- | --- | --- | --- | --- | --- |
| Adult | 0 | 117.7533 | 106.8428 | 224.5961 | 117.9566 |
| Adult | 1 | 97.8155 | 95.2275 | 193.0430 | 97.8155 |
| Adult | 2 | 95.9975 | 95.0470 | 191.0445 | 95.9975 |
| Bank | 0 | 45.5533 | 42.4789 | 88.0323 | 45.8984 |
| Bank | 1 | 33.5268 | 33.4228 | 66.9496 | 33.5443 |
| Bank | 2 | 32.6305 | 32.5818 | 65.2123 | 32.6342 |
| Credit | 0 | 16.8327 | 20.1238 | 36.9564 | 20.1238 |
| Credit | 1 | 13.7161 | 13.7632 | 27.4792 | 13.7982 |
| Credit | 2 | 12.9703 | 12.9803 | 25.9506 | 13.0093 |

Across the 15 paired cases, T=1 reduces Phi by 14.2-35.9% relative to T=0; T=2 reduces it by 15.4-38.3%. All budgets refer to fair-refinement rounds: initialization already communicates local summaries and initializes the server at T=0. These are empirical utility differences, with no author-specified adequacy threshold. T1/T2 quality is not a license to change an existing T15 learner claim.

## Historical C0 performance context

For context only, accepted run `client-c0-20260926-v1` used three repetitions and the same resident-request boundary on the same cases. Its request ratios of total times were:

| Dataset | Canonical Direct T0 | Compact-fast T0 |
| --- | --- | --- |
| Adult | 14.09x | 26.96x |
| Bank | 35.58x | 115.53x |
| Credit | 13.96x | 25.03x |
| All | 17.79x | 35.79x |

These are historical results, not new T0 measurements or cross-budget speedup denominators. The C0 compact candidate has no T1/T2 point or curve here. Timing comparability is limited by separate runs/background loads and three versus four repeats; output grows to include actual positive-round statistics at T1/T2, equally for every matched method. `historical_c0_context.csv` preserves the labels and run identity. The appendix PDF plots only current canonical T1/T2 speedups and the separately labeled verified quality budgets.

## Setup, environment, validation and handoff

Original-population checkpoint construction, cache construction, serialization-size measurement, input/reference loading and equality checking were separately charged in `tables/setup_costs.csv`. Full checkpoints existed only in each worker; serialized sizes were measured in memory and no new full checkpoint was persisted. `SETUP_COST_INVENTORY.md` gives the lifecycle and measured per-dataset/budget summary. There is no disk-savings or actual RAM-reduction claim.

All substantial gate/grid workers used the exclusive shared fcntl lock at `/private/tmp/ftf_benchmark_20260926.lock`, held by the parent across the subprocess and released between settings. Each worker set OMP/OpenBLAS/MKL/NumExpr/vecLib limits to one before importing NumPy. The read-only environment is Python 3.12.14 / NumPy 2.3.5, macOS 27.0 arm64 on Apple M3 Max/48 GiB. Native pool introspection is unavailable because threadpoolctl is absent; environment controls and one-worker execution are recorded. Background load/top CPU processes and queue/held times remain in lock.jsonl. No machine-wide settings were changed.

The three targeted harness tests passed (12 fixture replay comparisons), followed by the complete fixed grid. `CORRECTNESS.md`, `HARNESS_GATE.json` and `RESULTS_VERIFICATION.json` distinguish actual execution, saved-byte verification and historical quality reuse. Baseline and every accepted C0 artifact are rehashed at delivery. No new independent numerical oracle or third-party review of this extension is claimed. Prior Task C approval applied only to the compact C0 snapshot.

For review: `REPORT.md`, `PROTOCOL.md`, `CORRECTNESS.md`, all `tables/`, `SETUP_COST_INVENTORY.md`, `REPRODUCE.md`, `INTEGRATION_NOTES.md`, and `output/whole_client_refinement_appendix.pdf`. `MANIFEST.json` binds delivered source/evidence files. Full indexed witnesses and all raw observations remain under `runs/client-refinement-20260926-v1`. No requested setting is pending.

All new work remains in this local directory. Accepted C0 sources/snapshots/results/reports, live manuscript, shared Git and Overleaf were not modified. No additional agents, downloads, archive restores, usage resets or external shares were used.
