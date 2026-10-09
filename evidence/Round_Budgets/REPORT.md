# Fairness versus runtime across C0/C1/C2

Run `round-budget-20260926T064431Z` | FTF-1D-descriptor-v1 | completed 2026-09-26T07:13:22.806774+00:00

**Complete: 180/180 method keys, 135/135 same-budget replay comparisons, 720/720 timing observations. No missing or duplicate keys.** All exact indexed trajectories, integer N/S/SS and retained-population quality agree. Each of 180 gate outputs also agrees with its corresponding accepted T=15 prefix; every measured witness agrees with its gate. Four repeats per key are timing repetitions, not new seeds.

**Reporting correction (26 September):** The initial figures and quality summaries mistakenly used saved G (the sum of group-normalized costs) as the worst-group objective. This version uses saved exact Phi throughout. All raw run evidence and timing results are unchanged; see REPORTING_CORRECTION.md.

## Main finding

- **Adult:** Direct's ratios of total measured algorithm times for C0/C1/C2 are 4.12x / 1.74x / 1.42x; E2E ratios are 3.30x / 1.65x / 1.37x.
- **Bank:** Direct's ratios of total measured algorithm times for C0/C1/C2 are 1.39x / 1.23x / 1.16x; E2E ratios are 1.34x / 1.20x / 1.14x.
- **Credit:** Direct's ratios of total measured algorithm times for C0/C1/C2 are 3.70x / 1.97x / 1.59x; E2E ratios are 3.20x / 1.85x / 1.53x.

Reducing the refinement budget exposes savings from reusing untouched group summaries. At C0, all three replay modes have the same computational path and no certificate attempts; their timing differences do not establish a certificate gain. At positive budgets, both certificate variants reject every attempted certificate and fall back in round zero in all 30 dataset/seed/budget settings per variant. They are slower than Direct throughout and slower than Fresh on Bank. Their remaining Adult/Credit gains over Fresh come from summary reuse despite the fallback overhead. A speedup compares replay and Fresh at the SAME budget. Cross-budget moves also change the learner and its fairness cost.

## Design and timing

Frozen Adult/Bank/Credit processed inputs, original partitions and persistent record IDs, k=10, original seeds 10000-10004, and the original independent record batches (30/45/30 deleted records). T=0,1,2; L=6; b=12; preserved clip; gamma=0; no anchor Lloyd. The upstream preprocessing remains fixed and outside the deletion guarantee. Adult/Credit raw provenance gaps remain inherited. No new seed or deletion campaign was added.

Every setting has its own cache-enabled original-population checkpoint. A four-method correctness pass precedes four separate-process measurement passes. Within each setting, cyclic orders place every method in every execution position once. Each setting holds the shared exclusive OS lock; it releases between batches. All five numerical-library thread limits are one. The same existing Python 3.12.14 / NumPy 2.3.5 environment is reused read-only. Source modules and training map are byte-identical to the corrected baseline.

**Algorithm:** full public method call, including validation, internal encoding/materialization, allocations and instrumentation. Fresh uses build_cache=False. **E2E:** contiguous wall time from opening the input bundle through deletion materialization, checkpoint load for replay, pre-call GC, method call, exact-witness construction and equal-schema JSON output. Receipt metadata, quality scoring and verification are outside the request boundary. Startup is separately measured, with a startup-inclusive table view. No disk cache is flushed and no cold-storage latency is claimed.

Compared with September19 E2E, this stricter request timer explicitly adds witness construction and pre-call GC and captures small intervening overhead. Quality is computed exactly on gate outputs; repeated outputs are byte/integers-equal and inherit the same quality. Initial cache construction is a separately reported setup cost, never charged to Fresh request time. Encoded data, input arrays, serialized state and per-call allocations remain in their actual measured boundaries.

Existing T=15 evidence cannot reconstruct these timings because server refinement time is aggregate-only; no time is prorated. The new calls measure cumulative processing through each budget from request start. These curves are budget trajectories, not a proved Pareto frontier or accumulated sequential-deletion service.

## Paired speedups

Ratios are Fresh/method; >1 favors replay. Mean paired ratio and wins use each seed's median of four repetitions. Total ratio sums all 20 observations within dataset/T/method. Seed range is the range of five paired median ratios. These are descriptive five-seed results; no repeats-as-IID intervals. The CSV also supplies ratios of total seed medians and the startup-inclusive and idealized-compute views.

| Dataset | Budget | Method | Algorithm mean pair | Algorithm total | Seed ratio range | Wins/5 | E2E total | E2E wins/5 |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| Adult | C0 | Direct | 4.116 | 4.119 | 3.900-4.213 | 5 | 3.304 | 5 |
| Adult | C0 | Basic | 4.105 | 4.101 | 3.920-4.215 | 5 | 3.284 | 5 |
| Adult | C0 | Runner-up | 4.119 | 4.110 | 3.915-4.242 | 5 | 3.296 | 5 |
| Adult | C1 | Direct | 1.741 | 1.741 | 1.709-1.763 | 5 | 1.647 | 5 |
| Adult | C1 | Basic | 1.049 | 1.050 | 1.038-1.056 | 5 | 1.024 | 5 |
| Adult | C1 | Runner-up | 1.043 | 1.044 | 1.030-1.056 | 5 | 1.019 | 5 |
| Adult | C2 | Direct | 1.419 | 1.421 | 1.403-1.429 | 5 | 1.374 | 5 |
| Adult | C2 | Basic | 1.033 | 1.033 | 1.023-1.038 | 5 | 1.014 | 5 |
| Adult | C2 | Runner-up | 1.031 | 1.031 | 1.020-1.037 | 5 | 1.012 | 5 |
| Bank | C0 | Direct | 1.395 | 1.390 | 1.314-1.453 | 5 | 1.345 | 5 |
| Bank | C0 | Basic | 1.399 | 1.394 | 1.306-1.465 | 5 | 1.349 | 5 |
| Bank | C0 | Runner-up | 1.394 | 1.394 | 1.308-1.460 | 5 | 1.348 | 5 |
| Bank | C1 | Direct | 1.230 | 1.228 | 1.197-1.273 | 5 | 1.203 | 5 |
| Bank | C1 | Basic | 0.889 | 0.889 | 0.869-0.904 | 0 | 0.881 | 0 |
| Bank | C1 | Runner-up | 0.892 | 0.890 | 0.868-0.924 | 0 | 0.882 | 0 |
| Bank | C2 | Direct | 1.164 | 1.161 | 1.140-1.189 | 5 | 1.142 | 5 |
| Bank | C2 | Basic | 0.917 | 0.917 | 0.904-0.932 | 0 | 0.908 | 0 |
| Bank | C2 | Runner-up | 0.914 | 0.914 | 0.901-0.919 | 0 | 0.905 | 0 |
| Credit | C0 | Direct | 3.705 | 3.696 | 3.501-3.927 | 5 | 3.200 | 5 |
| Credit | C0 | Basic | 3.722 | 3.709 | 3.526-3.958 | 5 | 3.214 | 5 |
| Credit | C0 | Runner-up | 3.705 | 3.687 | 3.503-3.909 | 5 | 3.187 | 5 |
| Credit | C1 | Direct | 1.964 | 1.967 | 1.927-2.002 | 5 | 1.853 | 5 |
| Credit | C1 | Basic | 1.196 | 1.195 | 1.186-1.222 | 5 | 1.161 | 5 |
| Credit | C1 | Runner-up | 1.189 | 1.189 | 1.169-1.206 | 5 | 1.155 | 5 |
| Credit | C2 | Direct | 1.589 | 1.592 | 1.575-1.614 | 5 | 1.527 | 5 |
| Credit | C2 | Basic | 1.143 | 1.144 | 1.132-1.153 | 5 | 1.115 | 5 |
| Credit | C2 | Runner-up | 1.136 | 1.137 | 1.128-1.145 | 5 | 1.108 | 5 |

Full wins, losses and ties for every timing boundary are in tables/aggregate_ratios.csv. Individual paired ratios and seconds are in tables/paired_seed_ratios.csv.

## Retained-population fairness

Phi = max(Phi_A, Phi_B) is the maximum group-average squared nearest-center distance on the fixed-point represented survivors. The saved field G = Phi_A + Phi_B is the sum of group-normalized costs; it is not the fairness objective. Tables explicitly label that auxiliary sum as sum_group_normalized_costs. It is identical across methods at each seed/T, including exact rational numerators/denominators. Values below are mean +/- sample SD across five seeds, not confidence intervals.

| Dataset | C0 | C1 | C2 | Mean paired C0-to-C2 decrease |
|---|---:|---:|---:|---:|
| Adult | 119.594 +/- 3.048 | 97.941 +/- 1.184 | 95.931 +/- 1.391 | 19.8% (seed range 17.1-21.0%) |
| Bank | 47.959 +/- 0.757 | 34.016 +/- 1.106 | 33.010 +/- 0.929 | 31.2% (seed range 28.8-33.0%) |
| Credit | 18.303 +/- 0.876 | 13.461 +/- 0.219 | 12.973 +/- 0.146 | 29.0% (seed range 26.1-34.9%) |

No policy threshold for acceptable fairness loss was specified. The experiment does not declare C0 or C1 sufficient for an application. Group-average cost does not establish individual, intersectional or downstream fairness.

## Certificate accounting and fallback

N counts eligible retained point-rounds; A attempts, P passes, S passing point-rounds retained after same-round fallback, and J failed assignments repeated in the full fallback rebuild. Attempted pass rate P/A differs from useful coverage S/N; actual assignment point-units are N-S+J. Totals below count each seed once, never multiply by timing repetitions. At T=0 all counters are zero and both rates are undefined.

| Dataset | Budget | Method | N | A | P | S | J | P/A | S/N | Fallback seeds/5 |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Adult | C1 | Basic | 150660 | 150660 | 0 | 0 | 150660 | 0.000% | 0.000% | 5 |
| Adult | C1 | Runner-up | 150660 | 150660 | 0 | 0 | 150660 | 0.000% | 0.000% | 5 |
| Adult | C2 | Basic | 301320 | 150660 | 0 | 0 | 150660 | 0.000% | 0.000% | 5 |
| Adult | C2 | Runner-up | 301320 | 150660 | 0 | 0 | 150660 | 0.000% | 0.000% | 5 |
| Bank | C1 | Basic | 225830 | 225830 | 0 | 0 | 225830 | 0.000% | 0.000% | 5 |
| Bank | C1 | Runner-up | 225830 | 225830 | 0 | 0 | 225830 | 0.000% | 0.000% | 5 |
| Bank | C2 | Basic | 451660 | 225830 | 0 | 0 | 225830 | 0.000% | 0.000% | 5 |
| Bank | C2 | Runner-up | 451660 | 225830 | 0 | 0 | 225830 | 0.000% | 0.000% | 5 |
| Credit | C1 | Basic | 149850 | 149850 | 0 | 0 | 149850 | 0.000% | 0.000% | 5 |
| Credit | C1 | Runner-up | 149850 | 149850 | 0 | 0 | 149850 | 0.000% | 0.000% | 5 |
| Credit | C2 | Basic | 299700 | 149850 | 0 | 0 | 149850 | 0.000% | 0.000% | 5 |
| Credit | C2 | Runner-up | 299700 | 149850 | 0 | 0 | 149850 | 0.000% | 0.000% | 5 |

Raw rows retain failed-assignment, sunk-fallback, rebuild, server, encoding, internal materialization and certificate timers. These timers are nested; do not sum fallback/failed-work columns with client/server totals. tables/component_means.csv reports observed component means. The strict-majority fallback and its duplicated assignments are unchanged.

## Repetition noise, setup and background load

- Adult: within-key algorithm CV median 0.47%, maximum 2.83%; E2E CV median 0.52%, maximum 2.95%. All four observations remain saved.
- Bank: within-key algorithm CV median 0.60%, maximum 2.29%; E2E CV median 0.60%, maximum 2.26%. All four observations remain saved.
- Credit: within-key algorithm CV median 0.79%, maximum 2.72%; E2E CV median 0.80%, maximum 2.85%. All four observations remain saved.

The one-minute system load averages at batch boundaries ranged from 3.74 to 5.17; all top-process snapshots are retained. Total lock queue time was 23.1 seconds. The lock coordinates only the two authorized experimental tasks; other desktop processes remain uncontrolled. No dedicated-host claim or causal attribution of small differences is justified.

Across 45 checkpoints, offline setup wall time totaled 17.08 seconds; cache-enabled algorithm time totaled 16.26 seconds. Checkpoint serialized sizes range from 12.51 to 58.01 MB. tables/checkpoint_setup.csv gives every setup, serialization and startup cost. The full checkpoint payload includes original data and exact evidence; loading is charged to replay in E2E.

**Idealized parallel-client compute** is stored only as a separate derived estimate: maximum client work per round plus server totals. It omits measured request overhead and all network/secure-aggregation/straggler costs. C0 still requires client group summaries and counts and server initialization; it is not zero communication. There are no real communication measurements, so no deployed speedup or communication guarantee follows.

## Scope and reproducibility

Full-grid replay equality uses the same production numerical kernels for Fresh and replay; it is not an independent arithmetic proof. The independently implemented artifact verifier checks indexed bytes, exact integers, source/identity hashes, witness lengths, count conservation and the accepted historical prefixes. The earlier independent arithmetic/oracle gate is referenced as historical lineage, not falsely claimed rerun. The immutable source and unchanged map retain their prior guarantees only within their stated scope.

No pooling with Task B whole-client deletions, no direct numerical Pan speedup comparison, no locally balanced MERGED adaptation, and no manuscript or Overleaf changes. The reference manuscript is read-only. The three PDF figures are in figures/. PROTOCOL.md contains the frozen plan; CORRECTNESS.md records validation; INTEGRATION_NOTES.md supplies evidence-supported wording only. REPRODUCE.md provides exact commands. All raw witnesses, failed-case slots, source copies and resumable batch receipts stay in this local workspace. No downloads or archive restoration were needed. Local-only files are not automatically backed up by iCloud.
