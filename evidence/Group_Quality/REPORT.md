# Group quality across zero, one and two refinement rounds

Completed 26 September 2026. **Saved-evidence first pass complete: 90/90 quality rows, 180 group rows, 30 dataset/seed/population cases, no exclusions, no new training or timing.** Two populations remain separate. `VERIFICATION.json` binds the exact inputs and analysis.

Worst-group cost decreased for every seed in both adjacent steps (60/60) and every T0-to-T2 comparison (30/30). Both individual group costs and population-average cost decreased from T0 to T2 in all 30 cases. However, T1-to-T2 increased Adult group 1 cost in **3/5 record-deletion seeds and 2/5 whole-client seeds**. Two of those record-deletion seeds also had higher population-average cost. Thus the observed decrease in Phi does not imply each group or the population average improves at every step.

## Scope and definitions

For a fixed seed s, retained represented population and T, Phi_g is the mean squared nearest-center distance in group g. All arithmetic begins with the saved exact integer fractions. Phi=max_g Phi_g; G=sum_g Phi_g; pooled SSE=sum_g n_g Phi_g; population-average cost=pooled SSE/sum_g n_g. G is neither Phi nor pooled SSE nor population-average cost. No training/timing repetitions are added as scientific seeds.

For each dataset/population/T, tables and bold plotted curves show (1/5) sum_s of the corresponding **case-level** metric, plus sample SD with divisor 4. In particular plotted worst-group mean=(1/5) sum_s max_g Phi_sg; this can exceed max_g[(1/5) sum_s Phi_sg]. Every case, exact rational mean and variance, range and group identity is in the CSVs. SD is descriptive variability, not a confidence interval. Counts are applied inside each seed before averaging; record-deletion group counts can vary across seeds.

Group meanings follow the frozen binary masks, not inferred membership: Adult group 0 is the complement of the stored male mask and group 1 is that male mask; Bank group 0 is not married and group 1 is married; Credit group 0 is other stored education codes and group 1 is EDUCATION in {1,2}. The intended Adult label for the complement is female, but we retain literal mask wording because Adult/Credit upstream raw files, fitted transforms and some semantic feature identities remain unverified. Source `src/datasets.py` and captured `context/stage1_protocol.tex` bind this interpretation. Preprocessing stays fixed, with b=12, clips 175/121/74, L=6, gamma=0, k=10 and no anchor Lloyd. T means **refinement rounds**; T0 still includes initialization.

## Separate populations and retained counts

A uses the CURRENT corrected record-deletion run `round-budget-20260926T064431Z`. The five original seeds 10000..10004 have their own preserved independent record requests: Adult/Credit delete 30, Bank deletes 45. All four saved gate methods have exactly equal indexed model witnesses and objective fractions at matched seed/T; quality is counted once using Fresh.

B uses completed `client-c0-20260926-v1` quality references for the same selected whole-client-deleted population as its core T0 experiment. Client 0 was prespecified by closeness to median client size with persistent-ID tie-breaking. All five seeds use this same request within a dataset. Saved fresh T1/T2 quality references are complete even though positive-T unlearning is outside this task. No result from the separate positive-refinement workspace was accessed.

| Population | Dataset | Original n | Deleted n | Retained group 0 | Retained group 1 | Retained total |
|---|---|---:|---:|---:|---:|---:|
| record | Adult | 30162 | 30 | 9770-9775 | 20357-20362 | 30132 |
| record | Bank | 45211 | 45 | 17978-17983 | 27183-27188 | 45166 |
| record | Credit | 30000 | 30 | 5374-5380 | 24590-24596 | 29970 |
| client | Adult | 30162 | 300 | 9685 | 20177 | 29862 |
| client | Bank | 45211 | 2259 | 17098 | 25854 | 42952 |
| client | Credit | 30000 | 299 | 5332 | 24369 | 29701 |

Group count ranges summarize the five seeds; `identity_counts.csv` supplies every exact count and retained ordered-identity hash. Source-client/full-row IDs are preserved and survivors are never renumbered. Population identity consists of processed-source bytes, persistent ownership, original order and retained row identities. These are processed-array IDs, not newly validated native UCI IDs.

## A. Record-deletion quality

Absolute costs: mean +/- one sample SD over five seeds. Phi is the mean of within-seed maxima.

| Dataset | T | Group 0 | Group 1 | Worst group Phi | Population average |
|---|---:|---:|---:|---:|---:|
| Adult | 0 | 119.594 +/- 3.048 | 105.088 +/- 4.964 | 119.594 +/- 3.048 | 109.793 +/- 3.633 |
| Adult | 1 | 97.832 +/- 1.298 | 95.950 +/- 0.958 | 97.941 +/- 1.184 | 96.560 +/- 0.554 |
| Adult | 2 | 95.880 +/- 1.421 | 95.754 +/- 1.428 | 95.931 +/- 1.391 | 95.794 +/- 1.420 |
| Bank | 0 | 47.959 +/- 0.757 | 42.934 +/- 1.605 | 47.959 +/- 0.757 | 44.934 +/- 1.058 |
| Bank | 1 | 33.984 +/- 1.126 | 33.875 +/- 0.933 | 34.016 +/- 1.106 | 33.918 +/- 1.008 |
| Bank | 2 | 32.996 +/- 0.930 | 32.986 +/- 0.907 | 33.010 +/- 0.929 | 32.990 +/- 0.916 |
| Credit | 0 | 16.424 +/- 1.131 | 18.303 +/- 0.876 | 18.303 +/- 0.876 | 17.966 +/- 0.885 |
| Credit | 1 | 13.338 +/- 0.188 | 13.427 +/- 0.244 | 13.461 +/- 0.219 | 13.411 +/- 0.226 |
| Credit | 2 | 12.925 +/- 0.154 | 12.965 +/- 0.155 | 12.973 +/- 0.146 | 12.958 +/- 0.154 |

Paired T0-to-T2 relative decreases: first compute (cost_0-cost_2)/cost_0 within each seed, then mean and range across five seeds. These differ from a ratio of dataset means and from T0 excess relative to T2, which uses a different denominator.

| Dataset | Group 0 mean [range] | Group 1 mean [range] | Phi mean [range] | Population mean [range] |
|---|---:|---:|---:|---:|
| Adult | 19.80% [17.12, 21.13] | 8.74% [4.30, 14.97] | 19.76% [17.12, 21.01] | 12.69% [10.45, 16.56] |
| Bank | 31.20% [28.77, 33.05] | 23.04% [15.20, 27.88] | 31.17% [28.77, 33.05] | 26.53% [21.19, 30.03] |
| Credit | 21.02% [14.87, 28.18] | 29.03% [26.12, 35.12] | 28.99% [26.12, 34.92] | 27.74% [25.31, 33.97] |

All three transitions (0->1, 1->2, 0->2) and all eight descriptive metrics have exact paired changes, mean, SD, min/max and decrease/increase/tie counts in `paired_changes.csv` and `paired_summary.csv`. Percentages are descriptive; no threshold was selected or tested.

## B. Whole-client-deletion quality

Absolute costs: mean +/- one sample SD over five seeds. Phi is the mean of within-seed maxima.

| Dataset | T | Group 0 | Group 1 | Worst group Phi | Population average |
|---|---:|---:|---:|---:|---:|
| Adult | 0 | 117.753 +/- 3.611 | 106.843 +/- 9.325 | 117.957 +/- 3.952 | 110.381 +/- 7.135 |
| Adult | 1 | 97.816 +/- 2.160 | 95.228 +/- 0.516 | 97.816 +/- 2.160 | 96.067 +/- 0.839 |
| Adult | 2 | 95.997 +/- 1.874 | 95.047 +/- 1.327 | 95.997 +/- 1.874 | 95.355 +/- 1.415 |
| Bank | 0 | 45.553 +/- 2.625 | 42.479 +/- 1.737 | 45.898 +/- 2.300 | 43.703 +/- 0.503 |
| Bank | 1 | 33.527 +/- 0.258 | 33.423 +/- 0.156 | 33.544 +/- 0.241 | 33.464 +/- 0.193 |
| Bank | 2 | 32.631 +/- 0.167 | 32.582 +/- 0.156 | 32.634 +/- 0.166 | 32.601 +/- 0.159 |
| Credit | 0 | 16.833 +/- 1.744 | 20.124 +/- 0.948 | 20.124 +/- 0.948 | 19.533 +/- 1.063 |
| Credit | 1 | 13.716 +/- 1.064 | 13.763 +/- 0.986 | 13.798 +/- 1.012 | 13.755 +/- 0.998 |
| Credit | 2 | 12.970 +/- 0.133 | 12.980 +/- 0.123 | 13.009 +/- 0.133 | 12.978 +/- 0.119 |

Paired T0-to-T2 relative decreases: first compute (cost_0-cost_2)/cost_0 within each seed, then mean and range across five seeds. These differ from a ratio of dataset means and from T0 excess relative to T2, which uses a different denominator.

| Dataset | Group 0 mean [range] | Group 1 mean [range] | Phi mean [range] | Population mean [range] |
|---|---:|---:|---:|---:|
| Adult | 18.41% [15.40, 23.67] | 10.49% [5.02, 24.48] | 18.53% [15.40, 24.30] | 13.30% [9.35, 24.22] |
| Bank | 28.18% [23.79, 33.29] | 23.20% [18.68, 27.21] | 28.76% [24.78, 33.29] | 25.40% [24.39, 26.37] |
| Credit | 22.31% [13.83, 30.24] | 35.40% [31.52, 38.32] | 35.26% [31.51, 38.32] | 33.42% [28.98, 37.02] |

All three transitions (0->1, 1->2, 0->2) and all eight descriptive metrics have exact paired changes, mean, SD, min/max and decrease/increase/tie counts in `paired_changes.csv` and `paired_summary.csv`. Percentages are descriptive; no threshold was selected or tested.

## Exceptions: improvements differ by group

Every event below is Adult T1->T2, with Phi decreasing. No such event occurs in Bank or Credit or for T0->T1/T0->T2. These are five distinct seed/population cases, not timing repeats; overlapping transitions are not counted as independent trials.

| Population | Seed | Group 1 before -> after | Group 1 change (%) | Phi before -> after | Population-average change |
|---|---:|---:|---:|---:|---:|
| record | 10000 | 96.192670 -> 97.326494 | +1.133824 (+1.1787%) | 99.463061 -> 97.326494 | +0.039075 |
| record | 10002 | 96.224892 -> 96.477361 | +0.252469 (+0.2624%) | 97.315802 -> 96.639371 | -0.048872 |
| record | 10004 | 94.487752 -> 96.450765 | +1.963013 (+2.0775%) | 98.958392 -> 96.696614 | +0.593167 |
| client | 10002 | 96.002141 -> 96.957289 | +0.955148 (+0.9949%) | 99.784660 -> 97.241930 | -0.179302 |
| client | 10003 | 94.642231 -> 95.233313 | +0.591082 (+0.6245%) | 100.017187 -> 98.304784 | -0.155996 |

The guarded learner targets Phi; its stated monotonicity guarantee does not require a coordinatewise reduction of both group costs or population SSE. Reassignment alone weakly reduces group costs for fixed updated centers, but the preceding fair center update can trade one group's cost against another. This explanation invokes the existing guarded-update contract; the current task only verifies saved observations.

## Mean versus maximum, descriptive gaps and auxiliary objectives

Twelve of the 18 dataset/population/T rows have a strict difference between mean of seed maxima and maximum of group means. The complete check, with worst-group switching counts, is `mean_vs_max.csv`. For example:

| Population | Dataset | T | Mean of seed maxima | Max of group means | Difference |
|---|---|---:|---:|---:|---:|
| record | Adult | 1 | 97.941105 | 97.832474 | 0.108631 |
| record | Adult | 2 | 95.931218 | 95.879553 | 0.051665 |
| record | Bank | 1 | 34.015771 | 33.983739 | 0.032032 |
| record | Bank | 2 | 33.009510 | 32.996054 | 0.013456 |
| record | Credit | 1 | 13.460590 | 13.426633 | 0.033957 |
| record | Credit | 2 | 12.972986 | 12.965168 | 0.007819 |
| client | Adult | 0 | 117.956649 | 117.753299 | 0.203350 |
| client | Bank | 0 | 45.898366 | 45.553316 | 0.345050 |
| client | Bank | 1 | 33.544331 | 33.526817 | 0.017514 |
| client | Bank | 2 | 32.634233 | 32.630534 | 0.003699 |
| client | Credit | 1 | 13.798158 | 13.763168 | 0.034989 |
| client | Credit | 2 | 13.009314 | 12.980257 | 0.029058 |

Absolute group gap=|Phi_0-Phi_1| and max/min group-cost ratio are included only as descriptive statistics. Ratio is undefined when the minimum group cost is zero; relative change is undefined when its initial denominator is zero. Undefined values use empty numerical fields plus status/count columns, not zero or infinity. There are no zero-denominator observations here; dedicated zero fixtures exercise this branch. These quantities are not new fairness definitions, guarantees of equalization or tests of downstream fairness.

Auxiliary G and pooled SSE below are on different scales and are deliberately absent from the per-record figure axes. Absolute five-seed mean +/- SD follows; exact means, variances and ranges are in `summary.csv`.

| Population | Dataset | T | G: sum of group means | Pooled SSE |
|---|---|---:|---:|---:|
| record | Adult | 0 | 224.682 +/- 6.193 | 3308283.983 +/- 109466.836 |
| record | Adult | 1 | 193.782 +/- 1.132 | 2909551.939 +/- 16693.630 |
| record | Adult | 2 | 191.633 +/- 2.837 | 2886476.565 +/- 42797.047 |
| record | Bank | 0 | 90.893 +/- 1.882 | 2029494.184 +/- 47767.674 |
| record | Bank | 1 | 67.859 +/- 2.056 | 1531962.509 +/- 45533.009 |
| record | Bank | 2 | 65.982 +/- 1.836 | 1490016.598 +/- 41353.851 |
| record | Credit | 0 | 34.727 +/- 1.891 | 538435.304 +/- 26512.293 |
| record | Credit | 1 | 26.764 +/- 0.402 | 401917.269 +/- 6765.217 |
| record | Credit | 2 | 25.890 +/- 0.305 | 388347.974 +/- 4607.580 |
| client | Adult | 0 | 224.596 +/- 12.037 | 3296207.053 +/- 213065.428 |
| client | Adult | 1 | 193.043 +/- 2.312 | 2868748.939 +/- 25040.602 |
| client | Adult | 2 | 191.045 +/- 3.010 | 2847499.498 +/- 42262.748 |
| client | Bank | 0 | 88.032 +/- 1.359 | 1877121.026 +/- 21622.218 |
| client | Bank | 1 | 66.950 +/- 0.406 | 1437354.772 +/- 8280.904 |
| client | Bank | 2 | 65.212 +/- 0.320 | 1400286.305 +/- 6816.791 |
| client | Credit | 0 | 36.956 +/- 2.613 | 580147.858 +/- 31561.201 |
| client | Credit | 1 | 27.479 +/- 2.043 | 408528.690 +/- 29638.593 |
| client | Credit | 2 | 25.951 +/- 0.236 | 385473.612 +/- 3531.370 |

## Figures and existing baseline evidence

`figures/record_group_quality.pdf` and `figures/client_group_quality.pdf` each show six panels. Upper row: individual group-average costs; lower row: within-seed worst-group and count-weighted population-average costs. Thin paths preserve all five seeds; bold markers and error bars show their mean and sample SD. Each dataset uses its own absolute cost axis with visibly nonzero origin, shared between its upper/lower panels. Seed IDs and exact values remain in the CSVs. The figures intentionally do not pool populations or overlay raw SSE.

Ghadiri, Samadi and Vempala, *Socially Fair k-Means Clustering*, Section 4/Figure 5 motivates showing both demographic-group costs. Figure 9 distinguishes population-average and worst-group objectives and reports variability. The supplied primary-paper extracted text is captured at `context/ghadiri2021socially.author_fulltext.txt` (PDF page markers 7-9); its numerical results, preprocessing choices, counts and convergence behavior are not targets or imported results. Section 3 already treats m groups; no multi-group novelty claim is made here.

**No valid ordinary-Lloyd versus fair-update comparator was found in the inspected P4/centralized evidence.** `context/stage1_protocol.tex`, paragraph P4 and baselines, says all initializers receive the same 15 guarded rounds on full cohorts without deletion. `context/corrected_p4_full_table.tex` identifies initialization-method/quantization comparisons at seed 42. `context/centralized.py` assigns each pooled point weight 1/n_g and samples weighted k-means++; it is a fair-weighted initializer. `context/p4_corrected.py` applies `guarded_fair_update` in the common refinement loop. Thus centralized does not mean ordinary k-means, and these full-population P4 rows are not matched to either survivor population here. Inspection scope is those evidence metadata and source files, not an exhaustive claim about every historical archive. No P4 runtime values were imported or rerun.

Optional future experiment only: freeze a matched same-survivor, same-seed and **identical initial-center** comparison of ordinary unweighted Lloyd mean updates versus guarded fair updates at equal T, with the same represented coordinates, assignments/ties and empty-cluster rules. Report both groups, Phi and count-weighted population cost for every case. Such a test would isolate update choice; an end-to-end ordinary initialization comparison is a separate question. This task stops at existing evidence and does not launch either experiment.

## Verification, concurrency and limitations

Executed checks: 702 frozen file SHA256/size/mtime comparisons; 51 source-copy checks for 17 canonical modules; original processed input/bundle hashes; complete source and row-identity registries; 15 record request mappings and 15 whole-client grid mappings; retained count conservation; 180 record gate model/exact-quality checks; 45 whole-client quality checks and 15 exact T0-core links; 60 cross-budget prefix checks; 90 scientific rows and 90 descriptive paired transitions; exact Phi/G identities and B saved SSE; saved-float consistency; 45 B CSV rows cross-checked; negative Phi, mean-vs-max, unequal-count and zero-denominator fixtures. A takes group counts from saved positive-T N statistics, checks original N against metadata and shares retained counts across exact prefixes. B cross-checks counts against frozen grid, saved core state and all quality witnesses. This is **saved-evidence verification and recombination, not independent raw-coordinate objective rescoring**. Raw arrays/checkpoints were not unpickled.

All substantial freeze/hash, analysis and render work ran as one worker under the parent-held exclusive flock at `/private/tmp/ftf_benchmark_20260926.lock`; lockfile preserved and released between batches. `LOCK_RECEIPTS.jsonl` records actual queue/acquire/release times, worker commands, exit codes, system load and top processes. Five numerical-library thread settings were fixed to one. No comparative timings were measured, so balanced timing order is not applicable; lock durations are operational receipts only. The lock does not control unrelated desktop load. Existing training environments were reused read-only.

| Claim status | What this task supports |
|---|---|
| Algebraically established | Phi/max, G/sum, count-weighted population mean/SSE, and the noncommutation of averaging and maximum follow their definitions; exact saved fractions satisfy them. |
| Tested on completed evidence | All stated row counts, model links/prefixes, objective identities, paired decreases and exceptions, hashes and count conservation passed the documented checks. |
| Conditional, inherited | The frozen map's guarded-Phi monotonicity and fixed-seed replay arguments require their stated arithmetic, fixed preprocessing, persistent identity, valid request and trusted-state assumptions. The whole-client review is source/snapshot-specific, not an independent endorsement of these quality summaries. |
| Unresolved or untested | Ordinary-Lloyd advantage, optimum closeness, universal group improvement/equalization, an application quality threshold, personal-data erasure, identical full caches, model-adaptive fresh-independent distributional guarantees, cold/deployed runtime and new positive-T client-unlearning timings. |

## Deliverables and stop condition

`PROTOCOL.md`, `PROTOCOL_FREEZE.json`, `INPUT_MANIFEST.json`; `VERIFICATION.json`, `VISUAL_QA.json`, `FIGURE_RECEIPTS.json`, `LOCK_RECEIPTS.jsonl`, `FINAL_VERIFICATION.json`; all compact tables; `freeze.py`, `analyze.py`, `plot.py`, `with_lock.py`, `make_report.py`, `finalize.py`; `REPRODUCE.md`, `INTEGRATION_NOTES.md`, `MANIFEST.json`. One final PDF text-extraction check failed because its assumed executable path was absent; the installed bundled Poppler executable was then located and the final check repeated. That operational failure is preserved in FAILURE_RECEIPTS.json and the lock log. No scientific case, analysis outcome or figure was changed or selected by retry. Context snapshots preserve reading-time manuscript source and are not a restore source. The live manuscript, completed studies and frozen evidence were never written. No data download, archive duplication, iCloud export, external share, upload, submission or usage reset occurred. Outputs remain in the explicitly requested local workspace, outside iCloud; a separate backup choice is still needed. No disk-savings claim is made. The optional comparator remains unrun.
