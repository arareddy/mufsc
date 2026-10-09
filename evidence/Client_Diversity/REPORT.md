# Client identity robustness of reviewed compact T0 deletion

Completed all 30 frozen cases (six distinct dataset/client requests × five seeds) and 270 timed requests. The unchanged compact method matches canonical fresh T0 indexed models and declared compact state throughout. Across all requests, Fresh/Fast is 35.58× and Direct/Fast is 1.76×. All 30 case means favor fast; no losses or ties were discarded. This supports the speedup across these selected original-partition endpoints, not arbitrary client populations or a general 10× guarantee.

## Selection and actual diversity

Only original metadata determined selection. Empty-group requests were filtered before selection; none were excluded. Smallest, nearest median, minimum group-0 fraction select client 0 in each dataset. Largest, maximum group-0 fraction, minimum smaller surviving group select the last client. Six roles therefore collapse into two clients per dataset; no replacements were made. All ties use the smallest persistent original run ID, which here equals the source client ID. Median uses doubled integer distance over valid clients. Exact fractions and every original client metadata record are in SELECTION.json.

| Dataset / client | Removed n | Group 0 / 1 | Group-0 fraction | Remaining group 0 / 1 |
|---|---:|---:|---:|---:|
| adult / 0 | 300 | 97 / 203 | 97/300 | 9685 / 20177 |
| adult / 99 | 462 | 179 / 283 | 179/462 | 9603 / 20097 |
| bank / 0 | 2259 | 899 / 1360 | 899/2259 | 17098 / 25854 |
| bank / 19 | 2290 | 916 / 1374 | 2/5 | 17081 / 25840 |
| credit / 0 | 299 | 53 / 246 | 53/299 | 5332 / 24369 |
| credit / 99 | 399 | 138 / 261 | 46/133 | 5247 / 24354 |

The metadata show 99 equal-sized clients plus one remainder client for Adult and Credit, and 19 plus one for Bank. Bank differs little in either size or composition (2259 versus 2290 rows, group-0 share about 39.80% versus 40%). Credit changes group-0 share from about 17.73% to 34.59%; Adult changes from 32.33% to 38.74%. These requests cover the prespecified extremes but do not create six independent client types. Clients, roles and seeds are correlated; repetitions are technical repeats.

## Matched request latency

Means below are milliseconds over five seeds and three repetitions per seed. Ratios are ratios of summed request times, not means of paired ratios. The request includes preparation, complete method call, exact model projection/serialization and local file write without fsync. All methods start resident and emit the same bytes for a given case.

| Dataset / departed client | Fresh ms | Direct ms | Compact ms | Fresh/Compact | Direct/Compact | Paired Fresh/Compact range |
|---|---:|---:|---:|---:|---:|---:|
| adult/c0 | 236.870 | 15.022 | 8.766 | 27.02× | 1.71× | 26.70–27.43 |
| adult/c99 | 235.588 | 14.906 | 8.960 | 26.29× | 1.66× | 25.89–26.64 |
| bank/c0 | 214.146 | 4.989 | 1.860 | 115.12× | 2.68× | 111.19–118.93 |
| bank/c19 | 214.432 | 4.474 | 1.849 | 115.95× | 2.42× | 113.22–117.80 |
| credit/c0 | 162.703 | 10.657 | 6.464 | 25.17× | 1.65× | 24.86–25.68 |
| credit/c99 | 162.588 | 10.462 | 6.564 | 24.77× | 1.59× | 24.56–25.05 |

Total request seconds: Fresh 18.394907, Direct 0.907645, Compact 0.516957. Fresh/Direct is 20.27×. Algorithm-only Fresh/Compact is 39.07×. The Fresh/Compact paired-case mean/median/sample SD is 55.74/26.67/43.07, range 24.56–118.93. Dataset heterogeneity explains why the paired mean differs from the pooled total-time ratio.

All 30 mean Fresh/Compact ratios exceed 10; all 30 Direct/Compact ratios exceed 1. These are observations, not a threshold-conditioned selection or guarantee. No failed scientific case, timing retry, dropped observation, tie, or speed loss occurred. Each method occupies each position once in each case.
Within-case fresh request-time CV across three repeats ranges 0.11%–1.45%.
Within-case direct request-time CV across three repeats ranges 0.61%–16.90%.
Within-case fast request-time CV across three repeats ranges 0.46%–8.25%.

tables/summary.csv includes dataset, actual distinct client, overlapping dataset/role, seed, and dataset/seed totals, paired ratio means/medians/SD/ranges and win/loss/tie counts. tables/cases.csv retains every seed/client mean, repeat SD/CV/range, and absolute preparation/algorithm/output costs. tables/raw_timings.csv retains all 270 observations. No IID confidence interval is appropriate for this grid.

## Workload and component explanation

All retained slices in this grid supply ten anchors. Both departing identities leave 1,980 anchors across 198 slices on Adult and Credit, and 380 anchors across 38 slices on Bank. Thus changing client identity changes exact group normalization and sampled model but does not reduce the number of surviving anchors within a dataset. The fast path must rebuild exact weights and sample the server again. Composition differences cannot be interpreted as a separate causal latency effect here.

| Dataset | Fresh local seeding ms | Fresh encoding ms | Direct input materialization ms | Fast metadata ms | Fast table ms | Fast sampler ms | Fast output ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| adult | 218.679 | 5.376 | 3.532 | 0.035 | 1.172 | 6.838 | 0.815 |
| bank | 208.372 | 2.712 | 1.965 | 0.016 | 0.247 | 1.171 | 0.419 |
| credit | 151.910 | 1.768 | 1.432 | 0.034 | 1.125 | 5.001 | 0.351 |

Fast request preparation is only about 0.0004–0.0006 ms. Its substantial costs are table materialization, server sampling and output. Fresh rebuilds local summaries; Direct reuses them but retains raw-input bookkeeping/materialization and phase-one overhead. Component labels come from the actual public API timers; uninstrumented residuals are not pure scanning estimates. Fresh reports zero in the dedicated input-materialization field while its actual conversion/copy work remains inside encoding and residual costs. Table construction and sampler are separate for fast but combined in fresh/direct server time. All component sums reconcile to the full public-call timer.

Bank retains far fewer anchors and has fewer feature dimensions than Adult, making compact server work much cheaper while fresh still processes roughly 43,000 retained rows. Adult/Credit retain the same anchor count but differ in feature dimension (103 versus 23) and data geometry. These explain workload differences; this small observation grid does not isolate causal effects of any one factor.

## Setup, exclusions and concurrency

One original-population T0 checkpoint and one compact state were constructed per dataset/seed, reused for the two independent requests, and verified unmodified. Each request starts from that original state, not the prior deletion result. No full checkpoint was persisted. In-memory pickle size/cost is reported solely as setup information.

| Dataset | Mean load/identity ms | Mean original train ms | Mean compaction ms | Canonical / compact pickle MiB |
|---|---:|---:|---:|---:|
| adult | 41.676 | 242.312 | 1.093 | 52.481 / 3.196 |
| bank | 27.731 | 226.943 | 0.170 | 29.734 / 0.267 |
| credit | 16.358 | 164.665 | 0.804 | 11.929 / 0.754 |

All 15 parent-held shared-lock batches completed, with total lock wait 0.001665 s and hold 73.643 s. Acquisition/release receipts include top CPU processes and load averages; one-minute load ranges 3.48–4.20. Numerical workers were serial with OMP/OpenBLAS/MKL/NumExpr/vecLib limits set to one. The lock cannot eliminate unrelated desktop load. Python 3.12.14, NumPy 2.3.5, macOS 27 arm64; actual executable/platform/thread settings appear in each setup receipt.

Cold input/checkpoint loading, Python startup, initial training/compaction, initial serialization, pre-request GC, untimed correctness gates, comparisons/receipts, quality scoring and durable next-state persistence are outside request timing. Dataset load/identity, training/compaction, serialization and batch wall times are recorded separately. Process-startup and hypothetical durable-service costs were not separately measured. Gates warm the methods before timing. No network or distributed deployment latency is measured.

## Exact T0 quality only

Exact group-average and worst-group costs were scored once per retained population/seed on the represented data. Phi=max(Phi_A,Phi_B), G=Phi_A+Phi_B, verified from exact rational values for all 30 cases. Below are five-seed means; averaging happens after the per-case maximum.

| Dataset / client | Mean group 0 | Mean group 1 | Mean Phi | Phi seed range |
|---|---:|---:|---:|---:|
| adult/c0 | 117.753 | 106.843 | 117.957 | 112.512–123.448 |
| adult/c99 | 119.414 | 106.297 | 119.414 | 116.699–121.550 |
| bank/c0 | 45.553 | 42.479 | 45.898 | 43.358–49.188 |
| bank/c19 | 45.972 | 42.868 | 45.972 | 43.576–47.654 |
| credit/c0 | 16.833 | 20.124 | 20.124 | 18.776–21.336 |
| credit/c99 | 16.756 | 18.342 | 18.396 | 16.834–21.318 |

Total quality materialization/scoring costs were 0.119/7.130 seconds, outside all request ratios. No positive-budget reference was rerun or imported. These values establish neither optimality nor whether unmeasured refinement would be adequate or necessary.

## Correctness and claims

**Previously proved, conditional:** the reviewed whole-client T0 summary invariant gives same-seed indexed equality under fixed preprocessing, original persistent IDs, exact current counts, canonical server replay and trusted unmodified summaries. This study changes no algorithm and supplies additional finite tests; it does not present the tests as a new proof.

**Tested here:** 30 untimed gates, 60 replay-versus-fresh model and declared-state gate comparisons, 30 returned compact-state gate checks; 270 timed model and declared-state comparisons against fresh gates, and 90 returned compact-state comparisons. Declared state includes counts, every retained summary field/byte, ordered anchors and exact rational weights. Output center bytes, shapes, float.hex values and the single indexed C0 trajectory were independently parsed. T0 has no refinement-statistics rounds. The complete original compact state remained unchanged after both requests in each batch. All 270 output files and case receipt hashes passed.

**Conditional empirical conclusion:** whole-client speedup survives the selected identity/seed variations on these three original partitions under the stated warm resident-data output contract. Local timing and source/input bindings are essential. A different optimized baseline, architecture, cold-start/persistence boundary, partition or learner budget can change the result.

**Unresolved or outside scope:** optimality, T0 adequacy relative to unmeasured refinement, arbitrary/adaptive client selection, independent fresh randomness after model-adaptive requests, untrusted/mutated compact state, full internal-cache identity, physical personal-data erasure, and a universal 10× claim. Original datasets/checkpoints and historical states remain; anchors may themselves contain represented records. Upstream fixed-preprocessing/provenance limitations remain those of the accepted inputs. No sensitive material was uploaded or shared.

## Artifacts and preservation

PROTOCOL.md and FROZEN_GRID.json were bound before the first gate/timing. SOURCE_VERIFICATION.json binds the exact reviewed candidate; COMPLETED_INPUT_BINDINGS.json verifies relevant completed inputs remain byte-identical. VERIFICATION.json checks saved witnesses; TABLE_VERIFICATION.json separately recomputes every summary field from raw JSON without importing production or report-generation code. All tables, commands and source are local. Frozen candidate SHA256: `6d7b8d993ed9e9fcda896192ee6e6299a434ab7cdc25ab9907fc6b4bc1cf3dde`. MANIFEST.json inventories final deliverables/evidence. No live manuscript edits, Overleaf push, new environment, downloaded dataset or bulk archive. Local-only files need a separately chosen backup; no disk-saving claim.
