# Exact C0 whole-client deletion: bounded experimental result

Completed 26 September 2026. Run `client-c0-20260926-v1`. **The hypothesis is supported within this fixed whole-client, T=0, resident-data contract:** the compact-summary fast path matches canonical fresh T=0 exactly and is 35.79x faster by the ratio of total request times (39.32x algorithm-only). All 15 prespecified case means exceed 10x. Existing canonical direct T=0 replay already reaches 17.79x request speedup; the new path is 2.01x faster than direct in total request time. These figures describe this small simulation, not the established T=15 P2 learner or a deployed erasure service.

Quality is a material limitation: on these same populations, T=0 worst-group cost is 18.2% to 62.1% above fresh T=2. A correct deletion result reproduces the chosen learner; it does not remove the utility cost of choosing zero refinement. No quality acceptance threshold was specified, and no claim of T=0 adequacy follows.

## What changed and why equality holds

`client_c0.py` is a 95-line additive candidate; `implementation.diff` contains it. All 17 canonical source files remain byte-identical to the corrected September19 manifest. The fast state retains canonical per-slice summaries, original active client IDs, two integer counts per client, global counts and server settings. Counts are recovered from `n_e`, which local training already records. Initial compaction copies compact summaries and checks their multiplicities. It does not scan original records.

For a whole-client request, all surviving ownership slices have the same represented records, original order and keyed local tape. Their cached summaries therefore equal fresh summaries. Removing the departing summaries and subtracting their counts produces fresh global n_g. Rebuilding the sorted (client,group,slot) anchor table creates the same exact h/n_g weights; calling the unchanged server sampler with the original server key creates the same indexed C0. The returned active state preserves this invariant for a valid whole-client sequence. Requests leaving either group empty are rejected. No server centers or weights are frozen.

Fast deletion performs metadata/dictionary work, compact anchor materialization and canonical server sampling. It does not receive surviving raw coordinates, group arrays or row masks. Retaining O(C k d) summaries and O(C) counts avoids the existing direct path's once-per-request survivor scans and coordinate copies. Exact rational arithmetic still depends on count bit lengths; this is not a bit-complexity claim independent of population size.

## Correctness actually checked

- 10 focused test methods passed, with 22 saved exact fixture/sequence comparison records. Tests cover heterogeneous proportions, mixed/single-group departures, tiny/empty slices and empty clients, persistent ID gaps, unequal sizes, coincident coordinates/zero mass, saturation, quantized ties, optional anchor Lloyd, invalid requests, a one-per-group boundary and three sequential client removals.
- The fast API was exercised after replacing original raw/encoded/group dictionaries with access traps. Surviving summary objects are reused and their arrays are read-only; input state remains unchanged.
- All 15 dataset/seed cases completed all three method repetitions: 135 observations, 90 fresh-versus-replay model comparisons, and 90 comparisons of the explicitly claimed extra state. There were no exclusions, numerical mismatches, failed workers or selected reruns.
- Every indexed trajectory/final-center byte is compared, without tolerance or permutation. At T=0 the N/S/SS list is empty; this is not a new nonempty-statistics replay gate. Extra state compared: group counts, every surviving summary field including selected indices/reps/multiplicities, and the ordered anchor table with exact rational weights.
- `RESULTS_VERIFICATION.json` rechecks all 135 saved model files, their hashes, identical output witnesses, component time sums and balanced method positions. The 45 matched quality rows have the same retained counts and C0, and the expected trajectory/statistic lengths.
- Reference arithmetic is shared canonical FTF-1D code. This task's tests are not an independent rational oracle. Full fresh/raw caches are not required to equal the compact state, and model equality does not prove personal-data erasure.

## Frozen cases and data

The grid was frozen before new training or timing (`PROTOCOL.md`, `FROZEN_GRID.json`, SHA-256 `58f62126303df6e813ec76bd1bbab45d3e1c6383fd3bd9ce92ac4dd2be975615`). Canonical dataset-selection seed 0; training seeds 10000-10004; k=10, L=6, b=12, gamma=0, no anchor Lloyd. Fixed clips are 175/121/74. The valid client closest to original median size, tie-broken by its persistent run ID, is client 0 in each dataset. The choice does not vary with runtime, quality or seed. This is five seeds for the same selected whole-client request per dataset, not 15 distinct datasets or a variety of removal sizes.

| Dataset | Original rows / clients / d | Removed rows (% total) | Removed group 0 / 1 | Retained group 0 / 1 |
| --- | --- | --- | --- | --- |
| Adult | 30,162 / 100 / 103 | 300 (0.9946%) | 97 / 203 (32.33% / 67.67%) | 9,685 / 20,177 |
| Bank | 45,211 / 20 / 42 | 2,259 (4.9966%) | 899 / 1360 (39.80% / 60.20%) | 17,098 / 25,854 |
| Credit | 30,000 / 100 / 23 | 299 (0.9967%) | 53 / 246 (17.73% / 82.27%) | 5,332 / 24,369 |

Original run-client IDs and source-client/full-row identities are bound separately in `IDENTITY_REGISTRY.json`; survivors are never renumbered. Processed inputs are reused read-only and hash-matched to the accepted data manifest. Preprocessing is fixed, with the original Adult/Credit provenance limitations; nothing is refit or downloaded.

## Timing contract and results

All methods receive resident inputs; direct has its existing checkpoint and fast its previously prepared compact state. Fresh calls canonical `train_full(..., build_cache=False)` on survivor dictionary views. Direct calls canonical `unlearn(..., certificate_mode="none")` and pays for its existing masks/materialization. Fast takes client IDs only. Algorithm time encloses each public call. Request time adds request preparation and identical exact model-witness serialization/local write, without fsync. Initial data loading, process startup, checkpoint production, compaction, quality scoring and verification are outside request time and reported separately. No cold-fresh/warm-replay comparison, network latency, physical purge or updated-state persistence is claimed.

Three repetitions rotate [fresh,direct,fast] by case index plus repetition; every method occupies every position once in each case. Reported totals use all observations. Paired case ratios divide mean fresh time by mean method time within a dataset/seed; repetitions are not treated as independent research cases.

| Dataset | Cases | Fresh/direct alg. | Fresh/fast alg. | Fresh/direct request | Fresh/fast request | Direct/fast request |
| --- | --- | --- | --- | --- | --- | --- |
| Adult | 5 | 14.77x | 29.58x | 14.09x | 26.96x | 1.91x |
| Bank | 5 | 38.69x | 147.67x | 35.58x | 115.53x | 3.25x |
| Credit | 5 | 14.43x | 26.47x | 13.96x | 25.03x | 1.79x |
| All | 15 | 18.68x | 39.32x | 17.79x | 35.79x | 2.01x |

Across all 45 timed observations per method, fresh/direct/fast request totals are 9.480725 / 0.533040 / 0.264916 seconds. Algorithm totals are 9.451897 / 0.506083 / 0.240401 seconds. The fast paired-case request ratio has mean 55.85, median 26.83, sample SD 43.73, and range 24.90-116.94. Its algorithm counterpart ranges 26.30-149.41. Heterogeneous datasets explain much of the ratio variation; a pooled mean is not the ratio of total times.

All case means follow. Absolute values are request milliseconds (three repetitions per method).

| Dataset | Seed | Fresh ms | Direct ms | Fast ms | F/fast alg. | F/fast request | F/direct request |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Adult | 10000 | 244.925 | 17.138 | 9.019 | 29.80x | 27.16x | 14.29x |
| Adult | 10001 | 243.347 | 17.308 | 9.070 | 29.49x | 26.83x | 14.06x |
| Adult | 10002 | 242.373 | 17.141 | 9.162 | 28.94x | 26.46x | 14.14x |
| Adult | 10003 | 250.312 | 17.690 | 9.403 | 29.25x | 26.62x | 14.15x |
| Adult | 10004 | 248.264 | 17.986 | 8.950 | 30.44x | 27.74x | 13.80x |
| Bank | 10000 | 221.181 | 6.316 | 1.973 | 144.33x | 112.12x | 35.02x |
| Bank | 10001 | 220.752 | 5.801 | 1.893 | 147.31x | 116.61x | 38.06x |
| Bank | 10002 | 219.056 | 6.295 | 1.898 | 148.08x | 115.39x | 34.80x |
| Bank | 10003 | 219.423 | 6.224 | 1.876 | 149.41x | 116.94x | 35.26x |
| Bank | 10004 | 220.003 | 6.288 | 1.884 | 149.36x | 116.77x | 34.99x |
| Credit | 10000 | 166.166 | 11.917 | 6.674 | 26.30x | 24.90x | 13.94x |
| Credit | 10001 | 165.317 | 11.772 | 6.599 | 26.51x | 25.05x | 14.04x |
| Credit | 10002 | 166.679 | 11.925 | 6.675 | 26.42x | 24.97x | 13.98x |
| Credit | 10003 | 166.718 | 12.082 | 6.602 | 26.81x | 25.25x | 13.80x |
| Credit | 10004 | 165.725 | 11.798 | 6.628 | 26.33x | 25.00x | 14.05x |

Within-case request-time coefficients of variation across the three repeats: fresh: 0.25-2.17%; direct: 8.81-37.78%; fast: 1.05-9.90%. Every standard deviation, min/max and observation is retained in `tables/case_method_timings.csv` and `tables/raw_timings.csv`. These are short, millisecond-scale operations on one workstation with only three repeats; no population-level confidence interval or universal 10x claim is made.

## Measured component explanation and break-even

Fresh pays for local seeding/assignment on all survivors; direct and fast reuse the unchanged summaries. Fast additionally removes direct's raw-data bookkeeping and copying. The compact server remains essentially the same cost in all three paths. Below are means over five seeds and three repetitions, in milliseconds; canonical direct's uninstrumented residual includes count scans/validation and timer/object overhead, so it is not labeled as pure scanning time.

| Dataset | Fresh local | Fresh encode | Direct materialize | Direct slice checks | Direct residual | Fast metadata | Fast table + server |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Adult | 226.388 | 6.727 | 4.824 | 1.950 | 1.545 | 0.042 | 8.234 |
| Bank | 213.116 | 3.467 | 2.526 | 0.576 | 1.124 | 0.020 | 1.463 |
| Credit | 154.781 | 2.112 | 1.782 | 1.943 | 1.516 | 0.039 | 6.215 |

Writing the equal model output costs a further approximately 0.84/0.42/0.38 ms for fast Adult/Bank/Credit. The much smaller Bank anchor table (380 surviving slots versus 1,980 for Adult/Credit) explains its particularly small server cost and large fresh/fast ratio. It is a feature of this grid, not a favorable-case replacement rule.

In a component model with common server/output cost S+O, write F=L+E+V+S+O for fresh local/encoding/other/server/output work and Q=M+S+O for fast metadata/server/output. A 10x speedup requires L+E+V >= 10M+9(S+O). Actual output times vary, so the saved observations define the reported ratios; adding refinement or durable purge/storage obligations changes this calculation. Current fast algorithm time is almost entirely rebuilding/sampling the compact server. There is no inference that raw-data Phase-II refinement could disappear at T>0.

Incremental setup break-even is ceil(compaction / (fresh_request - fast_request)); versus direct, replace fresh by direct. It is one request in every measured case for both comparisons. If one charges the entire original training plus compaction to this new service before it serves any request, the analogous arithmetic is two independent requests in every case. This is a cost-accounting calculation using independent-request measurements; long sequential-service timing, erasure and state-persistence costs have not been measured.

## Preparation and storage

| Dataset | Original T0 train ms | Additional compaction ms | Canonical checkpoint MiB | Compact state MiB | Input load/verify ms |
| --- | --- | --- | --- | --- | --- |
| Adult | 251.805 | 1.178 | 52.481 | 3.196 | 44.902 |
| Bank | 231.292 | 0.173 | 29.734 | 0.267 | 30.118 |
| Credit | 167.754 | 0.669 | 11.929 | 0.754 | 17.164 |

These are serialized object sizes measured with pickle protocol 5 in memory, not on-disk deletions or measured RAM savings. Full checkpoints were not saved anew. Compact state retains represented anchors/reps that can equal individual records, multiplicities, selected local indices and counts. Experimental source datasets, historical checkpoints and saved witnesses remain available; new full T=0 comparison checkpoints existed in their workers and were not persisted. `STATE_INVENTORY.md` and `tables/preparation_storage.csv` give the lifecycle/cost details. No actual disk savings are claimed.

## Matched quality references

One fresh T=1 and T=2 run per same client-deleted population, plus exact T=0 scoring, completed for all 15 cases. The table averages costs over five seeds; Phi is max(Phi_A,Phi_B) within each case, then averaged, so the average Phi need not equal the maximum of the two average group columns. Fractions and complete model/statistic witnesses are saved under `runs/.../quality`. These learning budgets are quality references, never denominators for T=0 unlearning ratios.

| Dataset | T | Mean group 0 cost | Mean group 1 cost | Mean worst-group cost | Mean pooled SSE |
| --- | --- | --- | --- | --- | --- |
| Adult | 0 | 117.7533 | 106.8428 | 117.9566 | 3296207.05 |
| Adult | 1 | 97.8155 | 95.2275 | 97.8155 | 2868748.94 |
| Adult | 2 | 95.9975 | 95.0470 | 95.9975 | 2847499.50 |
| Bank | 0 | 45.5533 | 42.4789 | 45.8984 | 1877121.03 |
| Bank | 1 | 33.5268 | 33.4228 | 33.5443 | 1437354.77 |
| Bank | 2 | 32.6305 | 32.5818 | 32.6342 | 1400286.31 |
| Credit | 0 | 16.8327 | 20.1238 | 20.1238 | 580147.86 |
| Credit | 1 | 13.7161 | 13.7632 | 13.7982 | 408528.69 |
| Credit | 2 | 12.9703 | 12.9803 | 13.0093 | 385473.61 |

Paired T=0 excess worst-group cost versus T=2: Adult: 18.2-32.1%; Bank: 32.9-49.9%; Credit: 46.0-62.1%. No full-T=15 reference was run here and no Task A quality values were reused. `tables/quality.csv` reports every dataset/seed/budget and measured T=1/T=2 learning time separately.

## Runtime, concurrency, attribution and limits

The host is an Apple M3 Max with 48 GiB RAM, macOS 27.0 arm64; Python 3.12.14 and NumPy 2.3.5 reused read-only. All five numerical thread environment controls were set to one, and one worker ran at a time. `threadpoolctl` is absent, so native pool sizes were not independently enumerated; `CURRENT_RUNTIME.json` records this limitation. All 30 core/quality case batches acquired the required shared OS flock and released it after the worker finished. Total logged queue wait was 118.724s; total held time was 62.271s. The separate correctness fixture also acquired the same lock.

Batch load averages and top CPU processes are saved in `lock.jsonl`. macOS background processes were active, including uarpd at approximately one full core and variable WindowServer/Spotlight activity. The advisory lock coordinates the experimental tasks, not the entire workstation. No system, network or iCloud settings were altered.

Pan et al. (ICLR 2023), primary supplied paper pp.6-8, motivates reusing unaffected local work and dropping whole-client contributions before server recomputation (Section 5.3/Algorithm 4). Lemma 5.1 concerns local seeding in distribution and Theorem 5.4 has conditional expected local complexity assumptions. Those guarantees are not substituted for this fair learner's same-seed proof. Primary PDF hash and exact source paths are in `REFERENCE_IDENTITIES.json`; relevant pages were text-extracted and visually checked. Locally balanced MERGED-1K is a separate adaptation and was not run. No new literature campaign or cross-paper speed-factor comparison was made.

Limit the result to the unchanged fixed preprocessing/numerical map, trusted state, valid whole-client T=0 requests and specified output projection. There is no record-level prefix repair, arbitrary mutable-state validation, physical erasure, adaptive independent-distribution claim, broad quality acceptance, cold-start/deployed-latency estimate or replacement P2/P3 campaign. Saved original checkpoints, previous states and reports can retain personal information. Local files need a separately chosen backup; they are not claimed to be backed up by iCloud.

## Independent-review handoff and deliverables

`READY_FOR_REVIEW.json` points to immutable `review_snapshots/v1`, manifest SHA-256 `62bab6126a5708acc4d18902fe72bdae960b9d3e6582b0446cbafe7e97ea19c8`. It contains candidate, benchmark, canonical source, protocol and the focused test receipt. The snapshot has not been modified. Task C subsequently returned a scoped pass with no blocking finding for this exact hash: 196 independent valid-subset comparisons, 84 sequence steps and raw-access/timed-wrapper checks. Its source/functional and cost-boundary review does not independently certify the real-data timings, quality or aggregation here. `INDEPENDENT_REVIEW_STATUS.json` binds its separately authored `IMPLEMENTATION_REVIEW.md` and actual check record; no human review endorsement is implied.

- `PROTOCOL.md`, `FROZEN_GRID.json`, `BASELINE_MANIFEST.json`, `INPUTS.json`, `ENVIRONMENT.json`: frozen design/provenance.
- `client_c0.py`, `implementation.diff`, `test_client_c0.py`, `CORRECTNESS.json`: candidate and actual focused test evidence.
- `tables/raw_timings.csv`, `tables/case_method_timings.csv`, `tables/paired_ratios.csv`, `tables/aggregate_timings.csv`, `tables/preparation_storage.csv`, `tables/quality.csv`: all observations and summaries.
- `runs/client-c0-20260926-v1`: individual identical-output model files, extra state witnesses, exact quality fractions, setup receipts and lock logs.
- `STATE_INVENTORY.md`, `REPRODUCE.md`, `INTEGRATION_NOTES.md`, `RESULTS_VERIFICATION.json`: costs, commands, scope and verification.

All requested bounded experiments are complete. No baseline repository, live manuscript or Overleaf publication was changed, and no usage reset, external share, dataset download or bulky iCloud export was used.
