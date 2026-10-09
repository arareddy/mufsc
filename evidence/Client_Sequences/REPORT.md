# Three sequential whole-client withdrawals at T=0

Completed 26 September 2026; run `sequences-20260926-v1`. The unchanged reviewed compact-state method passed **135/135 full indexed model comparisons and compact-state checks** over 45 request cases (15 dataset/seed sequences, three correlated steps each), with three timing repeats of each full sequence. **Pooled matched resident model-output speed ratio: 34.99x. Separate operational ratio including each method's buffered state write/reload: 22.27x.** The algorithm-only ratio is 38.68x. No exclusions, failed workers, correctness failures, selected reruns, method revisions or T>0 experiments occurred.

These are same-T0 comparisons against fresh T0 on the current survivors. They establish a bounded local sequential-service result under trusted state, fixed preprocessing and persistent identity. They do not establish quality adequacy, optimality, full-cache identity, independent randomness for model-adaptive requests, physical erasure, durability, network performance, failure recovery or long-sequence performance. Historical immutable datasets and experiment artifacts remain intentionally preserved.

## Frozen input and sequences

Canonical Adult/Bank/Credit seed-0 partitions; k=10; seeds 10000–10004; T=0, L=6, scale bits 12, gamma=0, zero anchor Lloyd; original clips 175/121/74. In ascending original persistent-ID order, choose the first three distinct valid withdrawals, skipping only those emptying a required global group. This selected **0,1,2 for each dataset, with zero skips**. Source-client IDs here also equal 0,1,2. The same sequence is reused across the five seeds. Both original groups remain present; IDs/row order are never renumbered.

| Dataset | Step | Client | Rows removed now | Removed group 0 / 1 | Rows retained | Retained group 0 / 1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Adult | 1 | 0 | 300 | 97 / 203 | 29,862 | 9,685 / 20,177 |
| Adult | 2 | 1 | 300 | 97 / 203 | 29,562 | 9,588 / 19,974 |
| Adult | 3 | 2 | 300 | 97 / 203 | 29,262 | 9,491 / 19,771 |
| Bank | 1 | 0 | 2,259 | 899 / 1,360 | 42,952 | 17,098 / 25,854 |
| Bank | 2 | 1 | 2,259 | 899 / 1,360 | 40,693 | 16,199 / 24,494 |
| Bank | 3 | 2 | 2,259 | 899 / 1,360 | 38,434 | 15,300 / 23,134 |
| Credit | 1 | 0 | 299 | 53 / 246 | 29,701 | 5,332 / 24,369 |
| Credit | 2 | 1 | 299 | 53 / 246 | 29,402 | 5,279 / 24,123 |
| Credit | 3 | 2 | 299 | 53 / 246 | 29,103 | 5,226 / 23,877 |

`FROZEN_GRID.json` preserves every removed processed full-row ID, ordered removed/retained row hashes, current active IDs and group counts. `IDENTITY_REGISTRY.json` binds all original client slices to source clients and ordered row hashes. `INPUTS.json` binds datasets/identity files to the accepted corrected release. The worker revalidates the input hashes, original row maps and every current survivor hash. Upstream fitted preprocessing influence and inherited Adult/Credit raw provenance gaps remain outside this fixed-artifact guarantee.

`INPUT_MANIFEST.json` records completed antecedent reports/review/source hashes and a read-only live manuscript hash snapshot. The separate positive-refinement task was not read or used. The 17 canonical numerical modules and all copied map/driver files match the frozen baseline; `client_c0.py` is byte-identical to reviewed v1 (`6d7b8d993ed9e9fcda896192ee6e6299a434ab7cdc25ab9907fc6b4bc1cf3dde`). The new wrapper does not modify the learning/deletion method.

## What the measurements include

**Primary matched model-output request:** resident input/prior state; request translation and survivor dictionary views; the whole public training/deletion call; full exact indexed model witness serialization and equal-schema buffered local output write/close. Fresh uses `build_cache=False`. Compact returns its next in-memory state within this timer. Both output identical bytes at a given seed/step. Prior checkpoint loads, state persistence, initial preparation, pre-call GC, audit comparison and quality evaluation are outside both primary timers. This is the same output boundary as the completed single-withdrawal T0 study, but the new figures are not pooled with its observations.

**Separate state persistence:** immediately after each primary call, compact serializes the returned next state with protocol-5 pickle, writes/closes a local file, reads/deserializes it, verifies bytes and validates all state fields/arrays and exact counts against the just-returned state. Fresh serializes/writes/reads/validates its current active-client ledger; fixed input and service configuration stay resident/external. Fresh requires no model-dependent checkpoint to retrain its next population. Both paths include their necessary state work. Secondary operational time is primary plus this persistence/reload total; it is a sum of charged components, not a network E2E or a single continuous transaction timer.

**Storage semantics:** ordinary buffered local I/O, no fsync or cache eviction. No durable-write timing or atomic commit is claimed. Pickle files are trusted locally produced data; the reload check is not a malicious-state validator. The worker still holds raw data for fresh references and quality, although compact requests use only compact state and the departing ID. One current state file per method/case is overwritten as this simulation advances; only final checkpoints plus every intermediate hash/receipt are retained. This overwriting does not securely erase old physical bytes or purge original data/history.

At the next step the compact input is the **validated reloaded object returned by the previous step**, and fresh uses its reloaded ledger. Receipt chains bind before/after content hashes and checkpoint-byte hashes. Each timing repetition explicitly resets to the legitimately prepared original state; no previous or original checkpoint is passed as a current state within a sequence. Initial original training/compaction occurs once per dataset/seed, shared across its three timing repetitions; no setup cost is silently multiplied by repeats.

## Per-step timings

Means use all five seeds and all three repeats, in milliseconds. Ratios divide summed fresh time by summed compact time at the same step; all 45 seed/step means favor compact (45/45 matched and 45/45 operational). Matched case-mean ratios range 24.46–113.92x; operational ratios range 15.73–77.89x. These are observed descriptive results, not a guaranteed threshold.

| Dataset | Step | Fresh matched ms | Compact matched ms | Matched ratio | Fresh persistence ms | Compact persistence ms | Operational ratio |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Adult | 1 | 240.536 | 8.908 | 27.00 | 0.313 | 6.044 | 16.11 |
| Adult | 2 | 237.272 | 8.906 | 26.64 | 0.266 | 6.086 | 15.84 |
| Adult | 3 | 235.519 | 8.794 | 26.78 | 0.314 | 6.089 | 15.85 |
| Bank | 1 | 216.050 | 1.971 | 109.60 | 0.239 | 0.905 | 75.20 |
| Bank | 2 | 203.541 | 2.007 | 101.40 | 0.281 | 0.845 | 71.45 |
| Bank | 3 | 192.689 | 1.784 | 107.99 | 0.238 | 0.833 | 73.71 |
| Credit | 1 | 163.150 | 6.502 | 25.09 | 0.318 | 2.951 | 17.29 |
| Credit | 2 | 161.128 | 6.470 | 24.90 | 0.325 | 2.941 | 17.16 |
| Credit | 3 | 159.093 | 6.359 | 25.02 | 0.326 | 2.941 | 17.14 |

Pooled ratios across all 135 timing pairs weight settings by measured time. They are not an average of the displayed ratios. `paired_steps.csv` retains all 45 seed/step means, min/max timing values and the within-case repeat-ratio range. `observations.csv` preserves every duration, order, component, byte count and output/state hash. Timing repeats are not independent scientific sequences.

## Cumulative sequence timings

Each cumulative observation is the actual sum of completed steps within its repetition, then averaged over repetitions/seeds. No unlike refinement budgets are compared.

| Dataset | Through step | Fresh matched ms | Compact matched ms | Matched ratio | Five-seed ratio range | Fresh operational ms | Compact operational ms | Operational ratio |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Adult | 1 | 240.536 | 8.908 | 27.00 | 26.45–27.51 | 240.849 | 14.952 | 16.11 |
| Adult | 2 | 477.807 | 17.814 | 26.82 | 26.68–26.99 | 478.387 | 29.944 | 15.98 |
| Adult | 3 | 713.326 | 26.608 | 26.81 | 26.66–27.02 | 714.219 | 44.826 | 15.93 |
| Bank | 1 | 216.050 | 1.971 | 109.60 | 103.74–113.92 | 216.289 | 2.876 | 75.20 |
| Bank | 2 | 419.591 | 3.979 | 105.46 | 91.68–110.95 | 420.112 | 5.729 | 73.33 |
| Bank | 3 | 612.280 | 5.763 | 106.25 | 97.18–111.68 | 613.038 | 8.346 | 73.45 |
| Credit | 1 | 163.150 | 6.502 | 25.09 | 24.93–25.37 | 163.467 | 9.453 | 17.29 |
| Credit | 2 | 324.277 | 12.971 | 25.00 | 24.79–25.27 | 324.919 | 18.863 | 17.22 |
| Credit | 3 | 483.370 | 19.331 | 25.01 | 24.85–25.26 | 484.338 | 28.164 | 17.20 |

`figures/sequence_cumulative.pdf` is the appendix-ready plot. Lines show ratios of summed times and shading shows five-seed ranges of paired cumulative ratios; the shaded band is not a confidence interval. Axes use separate scales by dataset. Correlated steps and repeated timings are not treated as IID. The fixed early-ID withdrawals have similar group proportions and sizes within each dataset; this is limited client coverage, not a heterogeneous/adaptive removal campaign.

## Setup and storage overhead

Means over five legitimate original preparations per dataset. Full-checkpoint serialization is a size/cost diagnostic performed once; the full raw checkpoint blob is not persisted. It is not necessary per request. The compact serialization diagnostic is also separate from measured per-request persistence. Original compact state sizes and final state sizes are measured protocol-5 bytes, not disk savings or total deployed RAM.

| Dataset | Load/identity ms | Original training ms | Extra compaction ms | Original compact serialization ms | Full-checkpoint serialization ms |
| --- | ---: | ---: | ---: | ---: | ---: |
| Adult | 41.250 | 243.351 | 1.016 | 1.169 | 5.260 |
| Bank | 28.261 | 227.894 | 0.171 | 0.183 | 2.324 |
| Credit | 16.122 | 164.714 | 0.664 | 0.783 | 2.931 |

| Dataset | Original full-checkpoint bytes | Original compact bytes | Compact bytes after step 3 | Fresh active-ledger bytes after step 3 |
| --- | ---: | ---: | ---: | ---: |
| Adult | 55,030,623 | 3,351,441 | 3,250,905 | 308 |
| Bank | 31,178,477 | 280,225 | 238,246 | 68 |
| Credit | 12,508,311 | 791,090 | 767,372 | 308 |

Incremental setup below adds compaction once to compact's three-request operational sum. The second view charges measured original training to **both** systems plus compaction to compact, as an explicit common-original-model scenario. It is not a claim that a fresh-only service must build a cache-enabled original checkpoint. Load/startup/diagnostic serialization remain separately disclosed, outside these illustrative setup views.

| Dataset | Three-request operational ratio with extra compaction | Ratio charging common original training too |
| --- | ---: | ---: |
| Adult | 15.58 | 3.31 |
| Bank | 71.97 | 3.56 |
| Credit | 16.80 | 3.35 |

CSV `cumulative.csv` supplies the actual seconds for these views and each seed. Experimental resets are just assignments to the unchanged prepared original state and original fresh ledger; their recorded durations appear in each completion receipt. These resets are a repeat mechanism, not recovery latency. The initial producer still constructs a full original checkpoint before compacting it, so peak memory is not reduced to compact-state size. `setup.csv` records observed process maximum RSS.

## Exactness and quality

Before the real-data campaign, the copied 10-method gate passed with 22 exact fixture/sequence comparisons; new fixtures added three serialized/reloaded sequence steps, 30 malformed/domain-invalid request rejections, malformed-pickle rejection and the exact objective example Phi0=2, Phi1=25, G=27, Phi=25. These are new executions of focused tests, not relabeled historical gates.

All 135 timed compact calls matched fresh in the complete indexed C0 trajectory/final center bytes, every surviving summary field (representatives, selected indices, multiplicities and metadata), exact per-client/global counts, active client IDs and ordered anchor owner/coordinate/rational-weight table. Returned and reloaded compact states matched fresh compaction. No permutation or tolerance comparison was used. At T=0 the round-statistic list is empty, so no nonempty N/S/SS replay claim follows.

`VERIFICATION.json` independently re-parses all 270 saved model files with standard-library binary64 decoding, exact shapes/finite values/hex representations, checks equal fresh/compact bytes and repeat invariance, 135 state-chain/equality receipts, all artifact/source hashes, 30 final checkpoint-file hashes, 270 reload receipts, 45 exact fraction quality rows, component sums and order balance. Full compact-array comparisons execute in the worker; the reporting verifier rechecks their saved digest/chain receipts rather than independently reconstructing those arrays. Numerical training/quality arithmetic shares the canonical kernel; this is not a newly independent arithmetic oracle or external review of this wrapper.

Quality is scored once per distinct seed/population (45 rows) outside timings. Compact inherits the same score by exact model equality. Every row asserts **Phi=max(Phi0,Phi1)** and **G=Phi0+Phi1** with exact fractions; pooled SSE is separately n0*Phi0+n1*Phi1. The sum G is never labeled worst-group cost.

| Dataset | Step | Mean worst-group Phi | Five-seed Phi range | Mean sum G |
| --- | ---: | ---: | ---: | ---: |
| Adult | 1 | 117.956649 | 112.512298–123.448329 | 224.596058 |
| Adult | 2 | 117.552197 | 114.072871–125.008707 | 220.135292 |
| Adult | 3 | 115.361612 | 114.363762–117.154651 | 222.416160 |
| Bank | 1 | 45.898366 | 43.358093–49.188394 | 88.032253 |
| Bank | 2 | 46.571785 | 43.793133–52.144530 | 90.079215 |
| Bank | 3 | 45.809929 | 43.835994–49.490402 | 88.246266 |
| Credit | 1 | 20.123764 | 18.775794–21.336370 | 36.956445 |
| Credit | 2 | 18.457960 | 17.469643–19.591395 | 34.980010 |
| Credit | 3 | 18.641012 | 17.335501–20.434925 | 35.147743 |

These populations change after every deletion, so changes in Phi are not improvements on one fixed population. No T>0 training was run, no T0 quality adequacy threshold was chosen, and no T0/T1/T2 exact-unlearning ratio is reported. The completed earlier single-client/round-budget studies' quality cautions remain relevant background, not new sequence quality evidence at positive refinement budgets.

## Execution conditions and limitations

Campaign wall time was 130.84 seconds; 15 exclusive-lock dataset/seed batches completed, releasing the shared lock between them. Logged lock wait totaled 11.3433 seconds. One numerical worker at a time; all five numerical-library thread controls were one, with NumPy runtime receipts. The reused environment lacks threadpoolctl, so these receipts verify configured limits and runtime/SIMD information, not introspected actual backend thread counts. Method-first counts are 68/67 as prespecified for 135 pairs; each step experiences both orders across three repeats. No extra warmup or timed retry was selected. Exact quality scoring accounted for 10.75 seconds outside measured request/persistence work; detailed audit durations are in comparison receipts.

One-minute load averages ranged 3.64–6.35. Boundary snapshots show unrelated desktop activity, including uarpd using approximately one CPU core and WindowServer activity. The lock coordinates participating research workers; it does not isolate the machine, control thermal state, guarantee fairness of lock scheduling or establish deployment latency. Small millisecond latencies and buffered page-cache effects are material. No statistical confidence/generalization claim is attached to these five-seed summaries.

An additional new-process verification reloads all 15 final trusted compact files and reconstructs their C0 with the canonical server; all match the saved step-3 models. The first-step full model bytes also match all 15 completed historical single-client T0 cases. No training or timing rerun is used for this check; FINAL_STATE_VERIFICATION.json records its scope.

All work is under this local workspace. No data/environment copies, archive extraction, package installation, cloud export, external sharing, manuscript edits, usage reset or historical source/Git mutation occurred. The new wrapper imports only local copied method code and the read-only frozen dataset/environment; final local-only artifacts need a separately selected backup. Reported serialized reductions are not actual measured disk savings.

## Claim status

- **Proved under the reviewed assumptions:** whole-client removal leaves surviving local slices and keyed local streams unchanged; subtracting exact counts and rebuilding canonical normalized anchors/server input gives fresh-equal indexed C0. Induction gives the returned-state invariant over any valid finite sequence. This proof is inherited from the completed theory/implementation review, not established by timing measurements.
- **Tested here:** three fixed valid withdrawals on three datasets and five seeds, full repeated equality checks, ordinary local checkpoint round trips, exact objective definitions and the specified timing/storage boundaries. All outcomes are preserved.
- **Conditional:** transfer to another dataset/sequence/machine depends on valid groups, fixed preprocessing/identity/configuration, compatible numerical environment and trusted unchanged state; speed depends on fresh local work, server size and persistence overhead.
- **Unresolved/out of scope:** T>0 compact-only service, record-level cached service, longer/adaptive sequences, application quality/optimality, malicious/corrupt-state robustness, fresh-independent adaptive laws, physical erasure, network and durable/recovery behavior.

Pan et al. Section 5.3/Algorithm 4 already provides the whole-client-removal/server-recomputation architecture. Ghadiri et al. Section 3 already treats m groups. This contribution is the scoped group-normalized persistent-ID implementation invariant plus bounded sequential measurements, not novelty for either general idea. Local supplied primary texts were checked; no new literature campaign or cross-paper speed comparison was performed.

See `INTEGRATION_NOTES.md` for an appendix-only proposal and cautions, `REPRODUCE.md` for exact commands, and `DELIVERABLE_MANIFEST.json` for final artifact hashes.
