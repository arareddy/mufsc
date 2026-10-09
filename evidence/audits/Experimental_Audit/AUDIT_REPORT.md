# Independent experimental audit — 26 September 2026

**Disposition: qualified acceptance; no blocking computational defect found.** One medium-priority wording correction is required before integration: explicitly disclose that half of the client-diversity cases repeat the original client0 cases. No repair or campaign rerun is required by this audit. The scope restrictions below are essential to the supported claims.

Completed at 2026-09-26T08:46:35.959709+00:00. This was an independent bounded audit of the eight requested folders. The multigroup prototype, manuscript editing, publishing, benchmark reruns and scientific repairs were excluded. Existing experiment directories, source and manuscript were read-only. Git was not initialized, repaired or queried. Numerical checks used one child worker at a time under a parent-held exclusive `fcntl.flock` on `/private/tmp/ftf_benchmark_20260926.lock`, with five library thread controls set to one and lock release between batches. `AUDIT_LOCK.jsonl` records every batch; no lock was unlinked.

## Per-study disposition

| Study | Outcome | Supported result and qualification |
|---|---|---|
| Round_Budgets | QUALIFIED | Corrected Phi reporting and 720 timed witnesses pass. Use only current corrected tables; request E2E includes loading/materialization/GC and differs from resident client studies. |
| Client_Deletion | PASS within scope | All 135 saved output files and original 15 matched T0 cases pass; pooled compact request speedup 35.79x is implementation- and boundary-specific. |
| Client_Deletion_Review | PASS as source-bound inherited review | Reviewed compact module hash remains identical across C0/diversity/sequences. Its prior 196/84 oracle/sequence results are inherited, not newly executed by this audit; they do not certify the positive-T harness. |
| Client_Refinement | PASS within scope | All 480 outputs, complete same-seed trajectories/statistics, component arithmetic, matched totals and unique work counters pass. Direct request ratios are 2.357x at T1 and 1.696x at T2. |
| Client_Diversity | QUALIFIED — wording action | Metadata-only selection and deduplication pass. Two clients per dataset; client0 repeats prior evidence. Only three additional dataset/client identities, or 15 additional identity/seed cases, are introduced. |
| Client_Sequences | PASS within scope | 135 state-chain comparisons, 270 outputs and persistence accounting pass; 15 sequences have three correlated requests each. Matched ratio 34.99x; separately charged buffered persistence/reload ratio 22.27x. |
| Group_Quality | PASS as saved-evidence analysis | 90 quality rows and exact paired calculations pass; this recombines existing populations, not 90 new trials. Five adverse group transitions and two population-cost increases are retained. |
| Lloyd_Comparison | PASS as matched-start comparator | Same retained population, indexed C0, initial assignments/statistics and T; exact unweighted means, unchanged empty centers, no fair guard. All paired objective calculations pass. Not optimized conventional k-means. |

## Severity-ranked findings and required actions

### A1 — Medium / P2: explicit cross-study client0 overlap is missing from the proposed diversity paragraph

[Client_Diversity/INTEGRATION_NOTES.md](study://Client_Diversity/INTEGRATION_NOTES.md:3) and [Client_Diversity/APPENDIX_PARAGRAPH.md](study://Client_Diversity/APPENDIX_PARAGRAPH.md:1) disclose overlapping selection roles and 30 within-study unique cases, but do not state that 15 cases repeat the original Client_Deletion dataset/client0/seed combinations. [Client_Diversity/prepare.py](study://Client_Diversity/prepare.py:20) selects solely from counts/composition, and line 29 correctly deduplicates roles. Selection is valid; the evidentiary breadth needs explicit qualification.

The audit reconstructed all six roles from SELECTION.json using exact fractions and median-size tie-breaking. The results are clients 0/99 for Adult, 0/19 for Bank and 0/99 for Credit. We matched original client0 counts, source-client IDs and removed-row hashes, and sequence step-1 row IDs. The original C0 quality, diversity client0 quality and sequence first-step quality also agree exactly. The extra timings are new measurements on overlapping scientific cases.

**Minimum action:** add: “The two selected identities per dataset include the previously tested client0 and one additional client; 15 of the 30 identity/seed cases therefore overlap the original single-client study.” Do not sum role rows, timing repeats, prior client0 cases or sequence prefixes into an independent sample size. **Rerun: none.** This correction was sent to the orchestrator and current sole integrator.

### A2 — Low / P3: startup-inclusive round timing loses sub-microsecond precision

[Round_Budgets/worker.py](study://Round_Budgets/worker.py:53) computes `request + ready - launched` using epoch-sized floats. This differs from `request + (ready - launched)` by less than 0.25 microseconds in all saved rows (first row about 0.106 microseconds). The original audit checker’s 1e-11-second equality tolerance exposed this arithmetic-order effect; a 2.5e-7-second bound passes all rows. Algorithm and request timings and published rounded ratios are unaffected.

**Minimum action:** none for this paper; retain realistic timing precision. If maintaining the harness later, parenthesize the elapsed startup difference. **Rerun: none.** No source was repaired during this audit.

## Timing and comparator scope that integration must retain

These are existing, correctly disclosed boundaries rather than newly found code defects:

- Record-budget request E2E includes input loading, survivor materialization, replay checkpoint loading, pre-call GC and output; see [Round_Budgets/REPORT.md](study://Round_Budgets/REPORT.md:23) and worker lines 17–44. Resident client request timing starts after loading/checkpoint preparation and after pre-call GC; see [Client_Refinement/benchmark.py](study://Client_Refinement/benchmark.py:24). Do not pool these E2E ratios or draw a common deployment-latency claim. Keep original P2/P3 evidence separate.
- Positive-T Fresh uses `build_cache=False`; all replay paths receive a matching original T checkpoint. Preparation, public algorithm (including internal encoding/materialization/refinement), and identical full output write are charged. Setup, loading and reference checks are separately disclosed. `accounting.py` lines 5–13 sum every client/round once and keep certificate/fallback diagnostics separate. The audit independently reconstructed all 120 distinct method/setting counters and their pooled totals; four repeats are not four scientific trials. Canonical Basic/Runner-up fallback has no certificate passes in this grid; it does not outperform Direct.
- Sequence primary timing is resident model output. Secondary operational time is primary plus method-appropriate serialization/write/read/validation: compact next state versus fresh active-ID ledger. [Client_Sequences/service.py](study://Client_Sequences/service.py:35) includes both methods’ required state work. [Client_Sequences/benchmark.py](study://Client_Sequences/benchmark.py:88) assigns the validated reloaded result as next input; resetting to original occurs only at the repetition boundary, line 68. Buffered write/close/read is not fsync durability, atomic commit, recovery, physical erasure or network service. Cumulative prefixes are overlapping views, never additive independent cases.
- Lloyd means weight each retained record equally: sum group integer coordinate sums divided by total cluster count and encoding scale, followed by one binary64 conversion. [Lloyd_Comparison/lloyd.py](study://Lloyd_Comparison/lloyd.py:7) contains no fairness or SSE acceptance guard; zero-count clusters preserve the old indexed center. The trajectory shares canonical indexed assignment/statistics and starts at the fresh fair trajectory’s C0 ([Lloyd_Comparison/worker.py](study://Lloyd_Comparison/worker.py:40), lines 60–61). It isolates update choice conditional on FTF initialization. Do not claim superiority over optimized conventional k-means, compare initialization strategies, or infer a new Lloyd unlearning theorem.
- Only the corrected record-budget Phi report is valid: [Round_Budgets/REPORTING_CORRECTION.md](study://Round_Budgets/REPORTING_CORRECTION.md:3). Use Phi=max of group means inside each seed, G=sum of group means, and count-weighted population cost. Never maximize already-averaged group columns. “T0 excess over T2” uses T2 in the denominator (18.207–62.136%); “T2 reduction from T0” uses T0 (15.403–38.323%). Both reported ranges are correct and are different statistics.

## Independent fresh checks executed

`ARITHMETIC_CHECKS.json`, `ADDITIONAL_CHECKS.json` and runnable `check_evidence.py`/`check_additional.py` preserve the audit results. These scripts do not import the studies’ aggregation code.

1. **Saved evidence and aggregates:** rehashed 135 C0, 480 refinement, 270 diversity, 270 sequence and 720 round-budget model witnesses; checked same-setting equality and timing arithmetic. Recomputed applicable ratios of total times from saved observations, positive-T balanced order, full historical same-seed witness links, exact work/fallback totals, 135 sequence state chains, final state-file hashes and all 45 sequence cumulative rows from unique steps. No timing measurement campaign was rerun.
2. **Exact quality arithmetic:** recomputed all 540 Lloyd paired metric rows, 1,080 within-method metric rows, exact summary means/variances, signed adverse filters and paired percentage denominators. Checked 90 Group_Quality rows and all six fair metrics against the Lloyd fair evidence; independently recomputed Group_Quality means, sample SDs and paired changes. Checked 180 corrected record Phi/G definitions and all nine corrected quality summary rows; checked 45 C0, 30 diversity and 45 sequence quality identities and client0 links. Raw counts and exact fractions determine the arithmetic, not report rounding.
3. **Every real Lloyd update:** independently reconstructed all 33,600 saved center-coordinate updates from N/S and scale using Python Fraction and binary64 packing. This confirms unweighted means and exact saved center bytes for both updates in all 30 cases. Four newly written tiny scalar fixtures cover unequal groups, ties, duplicate/empty centers, negative thirds and two dimensions; four midpoint aggregate cases exercise rounding.
4. **Fresh independent full-population scoring:** for seed 10000 in all six dataset/population combinations, rescored fair and Lloyd T2 outputs using a new direct arbitrary-precision integer squared-distance implementation. Coordinates and centers are lifted to a common power-of-two denominator; every point-to-center distance and group sum is exact, with first-index ties. All **12 output tuples** match every exact objective fraction and full saved label hash. This code imports no production assignment, objective or accumulator and does not use the study’s interval scorer. Input loading/fixed-point representation and Python/NumPy runtime remain shared dependencies. Ordered survivor hashes, counts and encoded array hashes also match. This deliberately bounded sample is **not** an independent rescoring of all 150 unique output tuples; that larger existing scorer receipt is inherited evidence.
5. **Actual request wrappers:** a new sparse-ID, single-group-client T2 fixture calls Fresh/Direct/Basic/Runner-up public measured wrappers, compares all C0..C2 and exact N/S/SS and checks timing components and checkpoint preservation. The three existing harness tests were also freshly executed (12 replay fixture comparisons), separately from historical HARNESS_GATE. A new sparse-ID two-step sequence fixture advances through actual serialized/reloaded compact state and fresh ledger, checks complete next state against fresh compaction, rejects repeated removal and preserves the original state. These fixture durations are not speed measurements.
6. **Source/input identity:** checked baseline copies and originals, current run bindings, Lloyd source/frozen input manifests, processed artifact/identity hashes and reviewed compact candidate hash. `BINDINGS_CHECKS.json` records 525 unique file hashes including report/table snapshots. Candidate hash is `6d7b8d993ed9e9fcda896192ee6e6299a434ab7cdc25ab9907fc6b4bc1cf3dde`. No mismatch was found.

The initial audit script used the wrong C0 directory depth and too-tight mixed-clock arithmetic tolerance; an auxiliary check initially assumed an absent grid hash field. These were audit-code issues, not experimental failures. Initial diagnostic output and lock return codes are retained. Corrected checks passed; no study output changed or scientific case was replaced.

## Recomputed substantive outcomes

At T2, mean paired fair-minus-Lloyd changes use Lloyd as denominator:

| Population | Dataset | Worst-group change | Population-average change |
|---|---|---:|---:|
| Record | Adult | -4.7475% | +4.7236% |
| Record | Bank | -3.1546% | +0.5510% |
| Record | Credit | -5.0674% | +0.7078% |
| Client | Adult | -3.9159% | +4.4651% |
| Client | Bank | -4.2391% | +1.8735% |
| Client | Credit | -4.9261% | +0.5330% |

Fair Phi is lower, and population-average and group-1 costs higher, in every positive-budget paired case. Preserve that unfavorable distortion result. Fair T1→T2 raises Adult group-1 cost in record seeds 10000/10002/10004 and client seeds 10002/10003. Record Adult seeds 10000/10004 also raise population-average cost. Lloyd client Credit seed 10004 raises group-0/Phi at T1→T2. The 11 metric rows in step_increases include duplicated population-average/SSE events; they are not 11 independent adverse cases. The report’s nine primary-cost rows correctly omit the two redundant SSE rows.

The positive-T and sequential headline ratios independently reproduce: Direct resident request 2.357011953x (T1) and 1.695734955x (T2); sequence matched 34.988879791x and operational 22.272935955x. Use exact values from the JSON/CSV evidence for additional digits, and the existing report rounding in manuscript prose.

## Limits and handoff

This audit establishes no global optimum, broad convergence, application quality adequacy, raw-data erasure, untrusted-state safety, model-adaptive fresh-independent guarantee, network/durable-service speed or new original P2/P3 result. Upstream Adult/Credit raw-provenance and fixed-preprocessing limits remain. It reviews local evidence and selected fresh checks, not every historical archive, all arithmetic proofs, visual PDF layout or actual native backend thread counts. Prior review PASS records remain clearly separate from newly executed checks.

No benchmark rerun is needed for the supported claims. Deliverables are `AUDIT_REPORT.md`, `CLAIMS_DISPOSITION.md`, `AUDIT_STATUS.json`, compact JSON receipts and the audit scripts in study://Experimental_Audit. These local-only artifacts are outside iCloud and require a separately selected backup. Final findings go to sole manuscript integrator task `[coordination-id-omitted]` and orchestrator `[coordination-id-omitted]`; the earlier integrator was superseded during the audit.
