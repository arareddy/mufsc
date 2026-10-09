# Matched-start ordinary Lloyd versus guarded fair refinement

**Complete: all 30 frozen cases passed, with no exclusions or unresolved correctness issue.** Both methods start from identical indexed fair-initialized centers on the same survivors. At T=1 and T=2, fair refinement has lower worst-group cost in all 15 record-deletion cases and all 15 whole-client-deletion cases. At each budget it also has higher population-average cost and higher group 1 cost in every case. The result supports an objective tradeoff, not simultaneous improvement of all groups.

## What was executed

Two separate populations x Adult/Bank/Credit x seeds 10000-10004; k=10; T=0,1,2 **refinement rounds**. Record cases retain their original 30/45/30-record requests; whole-client cases retain their one prespecified client0 request (300/2259/299 records). No populations, requests, seeds or parameters changed. Fixed group semantics: Adult 0=complement of stored male mask, 1=male mask; Bank 0=not married, 1=married; Credit 0=other stored education codes, 1=EDUCATION in {1,2}. Adult/Credit upstream raw-provenance limitations remain.

Lloyd is a separate unweighted-mean update with exact integer sums, one binary64 rounding of each rational mean, indexed nearest-center ties, and unchanged empty centers. It has **no acceptance guard**. Both methods use the same represented coordinates; updated centers are not snapped back to the data grid. Fair refinement uses the unmodified canonical learner. Details and the independently written scorer are in NUMERICAL_CONTRACT.md. This isolates update choice conditional on FTF initialization; it is not an end-to-end ordinary-k-means baseline, initialization comparison, runtime benchmark or new unlearning result.

## Paired quality differences

Each percentage below is first computed within a seed as 100*(fair-Lloyd)/Lloyd, then averaged over five seeds. Negative favors fair for the indicated cost. Values show mean +/- sample SD [min, max], not confidence intervals. T0 differences are exactly zero by construction.

| Population | Dataset | T | Worst-group Phi difference (%) | Population-average difference (%) |
|---|---|---:|---:|---:|
| record | Adult | 1 | -3.57 +/- 0.35 [-3.93, -3.18] | +4.80 +/- 0.76 [+3.81, +5.92] |
| record | Adult | 2 | -4.75 +/- 1.12 [-6.14, -3.27] | +4.72 +/- 1.18 [+2.83, +5.84] |
| record | Bank | 1 | -2.54 +/- 1.36 [-4.93, -1.69] | +0.57 +/- 0.67 [+0.07, +1.75] |
| record | Bank | 2 | -3.15 +/- 2.04 [-6.74, -1.87] | +0.55 +/- 0.35 [+0.16, +1.08] |
| record | Credit | 1 | -3.26 +/- 2.20 [-6.30, -0.86] | +0.59 +/- 0.26 [+0.33, +1.00] |
| record | Credit | 2 | -5.07 +/- 1.47 [-7.50, -3.90] | +0.71 +/- 0.36 [+0.46, +1.33] |
| client | Adult | 1 | -2.93 +/- 0.53 [-3.55, -2.19] | +4.02 +/- 1.08 [+2.12, +4.78] |
| client | Adult | 2 | -3.92 +/- 0.56 [-4.70, -3.24] | +4.47 +/- 1.73 [+2.00, +6.43] |
| client | Bank | 1 | -4.25 +/- 1.45 [-5.47, -1.76] | +1.62 +/- 0.83 [+0.28, +2.49] |
| client | Bank | 2 | -4.24 +/- 1.42 [-5.32, -1.78] | +1.87 +/- 0.96 [+0.30, +2.80] |
| client | Credit | 1 | -3.06 +/- 3.48 [-8.99, -0.32] | +0.45 +/- 0.43 [+0.05, +1.18] |
| client | Credit | 2 | -4.93 +/- 2.80 [-9.60, -2.04] | +0.53 +/- 0.43 [+0.17, +1.28] |

At T2 the mean paired worst-group reductions are 4.75%/3.15%/5.07% for record deletions and 3.92%/4.24%/4.93% for whole-client deletions (Adult/Bank/Credit). Corresponding population-average increases are 4.72%/0.55%/0.71% and 4.47%/1.87%/0.53%. These are descriptive results on these cases, not universal bounds. Group 0 improves and group 1 worsens relative to Lloyd in every positive-budget case; group 1 is the larger retained group in these datasets. This does not imply every demographic setting behaves similarly.

## Absolute quality at every budget

Five-seed mean +/- sample SD. Phi is computed as max(Phi_0,Phi_1) **inside each seed** before averaging. Population mean is (n0*Phi_0+n1*Phi_1)/(n0+n1), again computed before seed averaging. G is the sum of group means; pooled SSE is the count-weighted sum and has a distinct scale. Exact per-case fractions, all ranges and all six metric summaries are in the CSVs. Shared T0 is printed once.

### Record-deletion survivors

| Dataset | T | Update | Group 0 | Group 1 | Phi | Population mean |
|---|---:|---|---:|---:|---:|---:|
| Adult | 0 | shared | 119.594 +/- 3.048 | 105.088 +/- 4.964 | 119.594 +/- 3.048 | 109.793 +/- 3.633 |
| Adult | 1 | fair | 97.832 +/- 1.298 | 95.950 +/- 0.958 | 97.941 +/- 1.184 | 96.560 +/- 0.554 |
| Adult | 1 | lloyd | 101.571 +/- 1.255 | 87.616 +/- 0.331 | 101.571 +/- 1.255 | 92.142 +/- 0.521 |
| Adult | 2 | fair | 95.880 +/- 1.421 | 95.754 +/- 1.428 | 95.931 +/- 1.391 | 95.794 +/- 1.420 |
| Adult | 2 | lloyd | 100.717 +/- 1.384 | 87.033 +/- 0.324 | 100.717 +/- 1.384 | 91.472 +/- 0.601 |
| Bank | 0 | shared | 47.959 +/- 0.757 | 42.934 +/- 1.605 | 47.959 +/- 0.757 | 44.934 +/- 1.058 |
| Bank | 1 | fair | 33.984 +/- 1.126 | 33.875 +/- 0.933 | 34.016 +/- 1.106 | 33.918 +/- 1.008 |
| Bank | 1 | lloyd | 34.919 +/- 1.590 | 32.935 +/- 0.551 | 34.919 +/- 1.590 | 33.724 +/- 0.826 |
| Bank | 2 | fair | 32.996 +/- 0.930 | 32.986 +/- 0.907 | 33.010 +/- 0.929 | 32.990 +/- 0.916 |
| Bank | 2 | lloyd | 34.112 +/- 1.674 | 31.944 +/- 0.383 | 34.112 +/- 1.674 | 32.807 +/- 0.808 |
| Credit | 0 | shared | 16.424 +/- 1.131 | 18.303 +/- 0.876 | 18.303 +/- 0.876 | 17.966 +/- 0.885 |
| Credit | 1 | fair | 13.338 +/- 0.188 | 13.427 +/- 0.244 | 13.461 +/- 0.219 | 13.411 +/- 0.226 |
| Credit | 1 | lloyd | 13.917 +/- 0.279 | 13.205 +/- 0.282 | 13.917 +/- 0.279 | 13.333 +/- 0.228 |
| Credit | 2 | fair | 12.925 +/- 0.154 | 12.965 +/- 0.155 | 12.973 +/- 0.146 | 12.958 +/- 0.154 |
| Credit | 2 | lloyd | 13.667 +/- 0.218 | 12.692 +/- 0.198 | 13.667 +/- 0.218 | 12.867 +/- 0.161 |

### Whole-client-deletion survivors

| Dataset | T | Update | Group 0 | Group 1 | Phi | Population mean |
|---|---:|---|---:|---:|---:|---:|
| Adult | 0 | shared | 117.753 +/- 3.611 | 106.843 +/- 9.325 | 117.957 +/- 3.952 | 110.381 +/- 7.135 |
| Adult | 1 | fair | 97.816 +/- 2.160 | 95.228 +/- 0.516 | 97.816 +/- 2.160 | 96.067 +/- 0.839 |
| Adult | 1 | lloyd | 100.763 +/- 1.736 | 88.324 +/- 1.304 | 100.763 +/- 1.736 | 92.358 +/- 0.586 |
| Adult | 2 | fair | 95.997 +/- 1.874 | 95.047 +/- 1.327 | 95.997 +/- 1.874 | 95.355 +/- 1.415 |
| Adult | 2 | lloyd | 99.907 +/- 1.685 | 87.141 +/- 1.032 | 99.907 +/- 1.685 | 91.282 +/- 0.230 |
| Bank | 0 | shared | 45.553 +/- 2.625 | 42.479 +/- 1.737 | 45.898 +/- 2.300 | 43.703 +/- 0.503 |
| Bank | 1 | fair | 33.527 +/- 0.258 | 33.423 +/- 0.156 | 33.544 +/- 0.241 | 33.464 +/- 0.193 |
| Bank | 1 | lloyd | 35.039 +/- 0.611 | 31.542 +/- 0.761 | 35.039 +/- 0.611 | 32.934 +/- 0.290 |
| Bank | 2 | fair | 32.631 +/- 0.167 | 32.582 +/- 0.156 | 32.634 +/- 0.166 | 32.601 +/- 0.159 |
| Bank | 2 | lloyd | 34.085 +/- 0.541 | 30.627 +/- 0.809 | 34.085 +/- 0.541 | 32.004 +/- 0.308 |
| Credit | 0 | shared | 16.833 +/- 1.744 | 20.124 +/- 0.948 | 20.124 +/- 0.948 | 19.533 +/- 1.063 |
| Credit | 1 | fair | 13.716 +/- 1.064 | 13.763 +/- 0.986 | 13.798 +/- 1.012 | 13.755 +/- 0.998 |
| Credit | 1 | lloyd | 14.240 +/- 1.015 | 13.576 +/- 1.067 | 14.240 +/- 1.015 | 13.695 +/- 1.020 |
| Credit | 2 | fair | 12.970 +/- 0.133 | 12.980 +/- 0.123 | 13.009 +/- 0.133 | 12.978 +/- 0.119 |
| Credit | 2 | lloyd | 13.695 +/- 0.503 | 12.738 +/- 0.115 | 13.695 +/- 0.503 | 12.910 +/- 0.089 |

## Every unfavorable stepwise exception

The following are all increases among the four primary costs over adjacent steps; all occur at T1->T2. No T0->T1 increase occurs. Fair has five group-1 increases and two population-average increases; Lloyd has one group-0/worst-group increase. Pooled SSE duplicates the two fair population-average increases under fixed counts. Full exact changes, before/after costs and endpoint comparisons are preserved in `within_method_changes.csv` and `step_increases.csv`.

| Population | Dataset | Seed | Method | Metric | Absolute increase | Relative increase |
|---|---|---:|---|---|---:|---:|
| record | Adult | 10000 | fair | Phi_B | 1.133824 | 1.1787% |
| record | Adult | 10000 | fair | population_average | 0.039075 | 0.0402% |
| record | Adult | 10002 | fair | Phi_B | 0.252469 | 0.2624% |
| record | Adult | 10004 | fair | Phi_B | 1.963013 | 2.0775% |
| record | Adult | 10004 | fair | population_average | 0.593167 | 0.6183% |
| client | Adult | 10002 | fair | Phi_B | 0.955148 | 0.9949% |
| client | Adult | 10003 | fair | Phi_B | 0.591082 | 0.6245% |
| client | Credit | 10004 | lloyd | Phi_A | 0.039865 | 0.2977% |
| client | Credit | 10004 | lloyd | Phi | 0.039865 | 0.2977% |

Lloyd pooled SSE decreased in all 60 adjacent case steps; fair Phi decreased in all 60. These are observed exact-fraction checks, not a broad convergence theorem. At matched positive budgets there is no exception to lower fair Phi or to higher fair population cost; the latter is an unfavorable result for total distortion and is retained, not hidden. G favors fair in 15/30 cases at T1 and 14/30 at T2; it must not be relabeled as Phi.

## Interpretation for the paper

This adds the previously missing controlled **update-choice comparator**. From the same FTF-initialized centers, minimizing ordinary population-weighted distortion can leave higher worst-group cost than guarded fair refinement. It therefore strengthens motivation for declaring a worst-group objective when that is the application aim. It also makes the tradeoff explicit: group 1 and total population distortion are worse under fair refinement here. The evidence supports a choice between objectives, not a claim that the method improves everyone, equalizes costs, reaches a global optimum, or beats optimized conventional k-means from its own initialization. No quality-adequacy threshold was supplied.

## Newly executed verification and inherited scope

New checks: seven fixed fixtures (five direct scalar Fraction trajectory/objective fixtures, including unequal groups, genuine tradeoff, ties, duplicates, empty clusters and thirds; two exact halfway binary64 aggregate fixtures); 30 full-population reruns; all 90 saved fair center/statistic prefixes reproduced exactly; all 90 saved fair objective sets recomputed; 150 independently scored center tuples agreed exactly with canonical objectives and full nearest-center label arrays; same indexed C0 and first-round statistics for each method pair; actual retained group counts and ordered row-identity hashes; all 209 input files and 27 frozen source files unchanged. Real-data independent assignment intervals resolved all points without fallback; fixtures exercised ambiguity and exact tie fallback. There were no failed cases, retries, exclusions, or scientific source changes after freeze.

The independent scorer computes new assignments and group objectives from represented records; it does not import production assignment/objective/accumulator functions. Its scalar test oracle sums pointwise rational squared distances. Shared Python/NumPy and binary64 conversion remain a dependency; this is separately written executed checking, not independent human validation. Canonical numerical-kernel guarantees and the original arithmetic gate are inherited source-bound evidence, distinct from the new reproduction checks. Whole-client T0 unlearning review scope is unchanged. No full-cache equality, erasure or adaptive fresh-independent guarantee follows for Lloyd.

All substantial work held the required parent-owned exclusive flock, with one numerical worker and five library thread limits set to one. Each of the 30 case batches released the lock before the next. Case queue wait totaled 0.0106 s; lock-held work totaled 116.878 s, including data validation, both variants, independent scoring and output. These are operational accounting, not algorithm timing comparisons. Load/process snapshots and separate queue/acquire/release receipts are in LOCK_RECEIPTS.jsonl; unrelated desktop load remains uncontrolled. Rendering is also locked.

## Deliverables and stop

One visually checked six-panel PDF in `figures/matched_start_quality.pdf`; `tables/quality.csv`, `summary.csv`, paired/within-method exact tables and summaries, all higher-cost exceptions and mean-vs-max checks; exact centers and N/S/SS in 30 `runs/matched-start-v1/*/outputs.json` files; per-case completion receipts; frozen protocol/grid/input/source manifests; independent fixture receipts; runnable scripts and REPRODUCE.md; concise LaTeX proposal in INTEGRATION_NOTES.md; final verification and file manifest. The figure displays paired relative differences; the absolute values remain above and in tables. All 30 cases, both populations, all seeds and both rounds are preserved.

The bounded experiment is complete. No manuscript, prior group-quality workspace, canonical source, frozen artifacts or original Git pointer was modified. No data refetch, bulk dataset copy, new environment, task/subagent, usage reset, external share, upload or Overleaf publication. The 11 MB grid retains ordered identity metadata for direct reproducibility, not a copied feature dataset; raw datasets/checkpoints are read in place. Outputs are local-only and need a separately chosen backup. Stop here; no expanded sweep or full conventional baseline was launched.
