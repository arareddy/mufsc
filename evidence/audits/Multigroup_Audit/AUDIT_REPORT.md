# Independent bounded audit: multi-group whole-client prototype

**Decision: SCOPED PASS. No blocking or actionable correctness defect was found in the audited frozen implementation and evidence.** This approves only the stated deterministic map and bounded pilot, with the limits below. It is not a full software/security audit, a global optimization guarantee, a new fairness theorem, or approval inherited from the earlier binary review. No implementation repair is requested. An additive manuscript description is supportable if it preserves these boundaries; manuscript integration itself was not performed by this audit.

Audit run: `mg-audit-20260926T082918Z`, 26 September 2026. Inputs stayed read-only; all new scripts, small evidence and reports are in this local nonsynced directory. No experiment repair, real training/timing rerun, download, manuscript edit, or subagent was used.

## Frozen identity and evidence integrity

Source: `study://Multigroup`; handoff `multigroup-review-v1`; numerical map `FTF-MG-FW12-B6-v1`.

| Identity | SHA-256 |
| --- | --- |
| MANIFEST.json | `98a51b5391fff46dae2ab37a5fe7a0870e61a2a2417034c10048186ca9705917` |
| multigroup.py | `b7ff301f3fbcbc79b846c2969525612e471d71a5cf702d090ff6c1bf2e3f0c3a` |
| THEORY.md | `663c285567d3fc6fb50c52fb4a322d3504a2e7952dfc56a1a698672464fa5e04` |
| READY_FOR_REVIEW.json | `299deb6a148b0011b55da655fe57f69a0c4a53b0ce6513dbaecbdd42b9bcd397` |

All **335 manifested files (27,888,537 bytes)** and ten referenced data files match their recorded bytes and hashes. The 17 baseline Python modules match their frozen originals. READY, its named code/protocol/test/report bindings, and HANDOFF_VERIFICATION also match. A final recheck confirmed the same identity after the numerical audit. These checks establish consistency with the supplied freeze, not independent proof of the historical creation time or completeness of unrecorded experiments.

Evidence: [initial integrity check](study://Multigroup_Audit/results/hash_verification.json), [final integrity check](study://Multigroup_Audit/results/final_hash_verification.json), [audit protocol](study://Multigroup_Audit/AUDIT_PROTOCOL.md).

## Findings and required claim boundaries

P0/P1 blocking defects: **none found**. P2 actionable implementation defects: **none found**. The following are nonblocking scope restrictions, already substantially disclosed by the author. They are not repair requests.

| ID / severity | Finding and exact locator | Minimum integration action |
| --- | --- | --- |
| S1 / informational | The certified gap bounds the convex problem for the current fixed partition; it does not bound the global clustering optimum. The search is finite and all ten distinct real updates reached its iteration limit. [multigroup.py:119](study://Multigroup/multigroup.py:119), [THEORY.md:37](study://Multigroup/THEORY.md:37), [REPORT.md:56](study://Multigroup/REPORT.md:56). | Retain “fixed-partition weak-duality certificate” and “bounded solver.” Omit any exact/global optimum or convergence-rate claim. |
| S2 / informational | Compact replay is T=0 only. Frozen dataclasses and non-writable arrays do not make nested dictionaries authenticated or deeply immutable; new compact states share surviving summaries. [multigroup.py:232](study://Multigroup/multigroup.py:232), lines 243–267; [STATE_INVENTORY.md:6](study://Multigroup/STATE_INVENTORY.md:6). | State the trusted-state, whole-client, raw-free T0 API. Do not claim erasure, privacy, full-cache equality, hostile-state validation, or a maintained positive-T sequential checkpoint service. |
| S3 / informational | The pilot has one selected population/request, five training seeds and technical timing repeats. The smallest retained group has seven rows; RAC1P remains one of 16 features. [REPORT.md:19](study://Multigroup/REPORT.md:19), lines 21–35, 110–132; independent membership result below. | Keep sample/request, rare-group, included-feature and no-survey-weighting disclosures. Do not infer population, downstream or intersectional fairness adequacy. |
| S4 / informational | Times are matched resident requests with model-witness serialization/local write. Setup, loading, state persistence, network, quality evaluation and erasure are excluded. T0 direct and compact are essentially equal in runtime. [benchmark.py:15](study://Multigroup/benchmark.py:15), lines 27–40, 58–77; [REPORT.md:75](study://Multigroup/REPORT.md:75). | Report ratios only at the same T and this cost boundary. Omit universal speed, cold/durable service speed and extra compact runtime advantage claims. |
| S5 / residual verification limit | Full real-data replay gates share production assignment kernels. This audit checked every processed row's membership/alignment/encoding and independently recomputed saved moment-based certificates, but did not independently reassign every real row for every real model. [verify_results.py:1](study://Multigroup/verify_results.py:1), [saved audit result](study://Multigroup_Audit/results/saved_evidence_audit.json). | Describe independent tiny raw-row checks separately from real saved-evidence checks. Do not label the entire real training pipeline independently reproduced. |

## Independent mathematical assessment

Fix a partition of represented rows, positive global group counts `n_g`, and integer moments `N_gj, S_gj, SS_gj` with scale `s`. Direct expansion of each squared distance gives

\[
f_g(C)=q_g+\sum_j(a_{gj}\|c_j\|^2-2b_{gj}^{\mathsf T}c_j),\qquad
a_{gj}=N_{gj}/n_g,\quad b_{gj}=S_{gj}/(n_gs),\quad q_g=\sum_jSS_{gj}/(n_gs^2).
\]

For simplex weights `lambda`, the weighted quadratic has cluster coefficients `A_j=sum_g lambda_g a_gj`, `B_j=sum_g lambda_g b_gj`. If `A_j>0`, completing the square gives minimizer `B_j/A_j` and contribution `-||B_j||²/A_j` to the minimum. If `A_j=0`, nonnegative counts imply every positively weighted cell has zero count and sum; therefore `B_j=0`. The weighted objective is then independent of that center. Choosing the sole occupied group's mean or the incumbent is valid even if another unweighted group occupies the cluster; fully empty clusters need no mean.

Thus

\[
D(\lambda)=\sum_g\lambda_gq_g-\sum_{j:A_j>0}\|B_j\|^2/A_j
=\inf_C\sum_g\lambda_gf_g(C)
\]

is concave, being an infimum of affine functions of `lambda`. Costs `f_g(C_lambda)` at any chosen exact minimizer form a supergradient: evaluating the infimum for another weight vector at `C_lambda` proves the defining inequality directly. This remains true at simplex boundaries and zero denominators. The segment derivative used at interior bisection points is justified by these minimizing quadratics; a cluster with zero mass throughout the segment contributes no directional term. No convexity assumption on the composed primal value `max_g f_g(C_lambda)` is needed.

Every evaluated dual value is a weak-duality lower bound on the fixed-partition optimum `P*`. For the actually returned represented center tuple `C_hat`, `Phi(C_hat)>=P*`, so

\[
0\leq\Phi(C_{\rm hat})-P^*\leq\Phi(C_{\rm hat})-\max_{\lambda\;\rm evaluated}D(\lambda).
\]

The certificate needs neither successful optimization nor strong duality. Candidate rejection, inactive optimum groups, search stalls and an iteration limit do not invalidate it. The “FW gap” concerns the exact unrounded minimizer; a zero value does not remove the need to evaluate rounding and the represented guard.

The implementation computes candidate costs by converting each returned binary64 coordinate back to its exact rational value, after rounding the exact weighted mean once. Its acceptance guard compares that actual represented fixed-partition maximum with the incumbent's exact maximum. After either acceptance or rejection, nearest-center reassignment weakly decreases each group's cost against that partition. Because the incumbent's partition was its nearest assignment, the nearest-center maximum cannot increase over a refinement round. This is not merely a statement about an unreturned rational mean.

Code correspondence: [Partition, lines 66–99](study://Multigroup/multigroup.py:66); [candidate evaluation, lines 102–118](study://Multigroup/multigroup.py:102); [search and guard, lines 119–153](study://Multigroup/multigroup.py:119); [assignment/refinement, lines 156–183](study://Multigroup/multigroup.py:156). The inspected author's primal box oracle also has a valid lower bound `max_g min_box f_g` and valid coordinate mean-hull restriction; its six reported runs were not rerun by this audit ([oracle.py:89](study://Multigroup/oracle.py:89)).

## Replay and state assessment

Whole-client deletion preserves the ordered represented rows of every surviving `(client,group)` slice. With fixed configuration and persistent IDs, its keyed local stream, selected indices, unsnapped assignment multiplicities and snapped anchors are unchanged. Local computation does not use global group counts. Rebuilding exact positive `n'_g`, rational weights `h/n'_g` and the canonical `(client,group,slot)` order produces the same fresh server input; restarting the same keyed server stream produces the same indexed C0. Locally absent slices are omitted without renumbering groups.

At each positive round, identical centers and retained rows produce the same exact nearest assignment, integer moments, rational solver decisions and represented guard result. Induction supports pointwise same-seed model equality for a fixed finite supported T under the stated primitives. Execution here covers T=0,1,2, not every configuration. DIRECT still performs all surviving raw-coordinate assignment/moment work in positive rounds. Its return value is a model, not a next positive-round deletion checkpoint.

T0 compact state contains counts, persistent IDs, config/seed and copied summaries, without raw coordinate/group arrays. Its returned next state preserves the same invariant for a sequence of valid deletions. The independent tests include an empty client deletion and persistent-ID gaps. Invalid or globally emptying requests are rejected. In-process trusted state is essential: compact representatives may equal individual records; old state and backing data persist.

Locators: [validation and local summary](study://Multigroup/multigroup.py:42), [training/state](study://Multigroup/multigroup.py:186), [retained metadata/DIRECT](study://Multigroup/multigroup.py:207), [compact API](study://Multigroup/multigroup.py:243). Same-seed replay does not imply a fresh independent seed law conditional on a model-adaptive deletion; finite PCG64 streams do not prove ideal independent-tape assumptions. This new positive-round map does not inherit binary bit identity or the earlier binary audit's approval.

## Executed independent checks

| New check | Executed result |
| --- | --- |
| Direct-row exact optimizer checks | Eight updates over four independent fixture families at zero/default iteration budgets; 192 candidate evaluations; 600 supergradient inequalities; 34 evaluations with zero denominators; two guard rejections; 113 evaluations where rounding changes exact costs. Inactive-group and coincident-data analytic optima checked. PASS. |
| Tiny replay reconstruction | m=3,5; seeds 0,7,19; T=0,1,2: 18 fresh/DIRECT cases and 18 independently reconstructed positive rounds, with exact indexed centers and integer moments. Includes nonzero snapping and optional anchor Lloyd. PASS. |
| Compact/domain checks | 18 sequence steps and 36 invalid requests; traps reject surviving local reseeding and raw access during compaction/deletion. PASS. Copy/non-writable behavior also inspected in source and author tests; no new hostile mutation test. |
| Processed membership/identity | All 100,000 rows, all native IDs/offsets/source-row metadata, exact forward RAC1P levels and legacy SEX alignment; all 1,600,000 encoded coordinates checked. PASS. |
| Frozen real evidence | All 35 gate model files and 105 timed output files compared exactly; saved exact moment/guard/gap formulas and all 778 candidate evaluations across ten distinct partitions independently rederived, including 120 FW steps and their six branches. PASS. |
| Reporting/timing | Matched ratios, five-seed ranges/SD/wins/losses, quality expressions/aggregates, output hashes, timing sums/orders and all 16 benchmark lock receipts checked. PASS. |

The new optimizer checks use direct row-level Fraction formulas and a separately implemented bounded candidate policy, not the author's `oracle.py`, fixtures or test driver. Independent T0 seeding uses the scalar oracle written during this auditor's previous review (SHA-256 `87436e1318dc35f4461fa58988df6b95631163c70c3220c3f6a95e0ae890e9aa`), generalized by its already generic group inputs. NumPy PCG64/SeedSequence and binary64 conversion remain shared primitives. This reuse does not transfer the binary review's conclusion to the new implementation.

Evidence: [independent checks](study://Multigroup_Audit/results/independent_checks.json), [membership](study://Multigroup_Audit/results/membership_audit.json), [saved evidence](study://Multigroup_Audit/results/saved_evidence_audit.json). The author's larger reported suites remain author self-validation; their counts are not added to these independent counts.

## Data, counts and numerical results suitable for integration

RAC1P was recovered from the saved unquantized standardized column (zero-based 15) using exact forward binary64 values for codes 1–9, with no fuzzy matching. Membership order matches its frozen hash. Persistent client 1 (MO) is independently reproduced by the frozen closest-to-median valid-client rule: 6,799 removed, 93,201 retained. Retained counts in code order are **66,577; 7,489; 1,059; 7; 162; 8,240; 168; 5,969; 3,530**. All nine are positive; the seven-row group stays in the objective. The numeric/schema recovery is verified, not the original Census CSV bytes or a new external verification of category-name semantics. Fixed preprocessing and all 16 features, including RAC1P, remain in use; no survey weights are used. See [prepare.py:15](study://Multigroup/prepare.py:15) and [common.py:58](study://Multigroup/common.py:58).

Count distinctness precisely: **one population/request; five training seeds; 15 seed/budget cases; 20 configured replay-versus-fresh gate comparisons across 35 gate files**. The **105 timed outputs are 45 fresh plus 60 replay technical repetitions**, not 105 new deletion cases. The 15 saved update records contain **ten distinct seed/round partitions** because round 0 is shared by T1/T2. They store 1,164 evaluation records including repeats, corresponding to **778 evaluations across distinct partitions** checked here.

| Matched T / method | Ratio of total algorithm times | Ratio of total resident request times |
| --- | ---: | ---: |
| 0 / DIRECT | 164.5524 | 138.6954 |
| 0 / compact | 164.5195 | 139.1404 |
| 1 / DIRECT | 1.6015 | 1.6005 |
| 2 / DIRECT | 1.2959 | 1.2955 |

All five seed ratios favor replay for each row. Three repeats per seed were averaged before pairing; T0 order is balanced, while each positive-T case necessarily has a 2:1 order imbalance, complementary across T1/T2. Aggregate display comparisons use a 2e-12 numerical tolerance; model bytes, integer moments and rational certificates are exact comparisons. The measurement wrapper and saved logs support this boundary, not a new timing reproduction or assurance about unrelated desktop activity/native pool sizes.

From saved exact moments, mean nearest-center Phi is **16.374037 (T0), 9.994114 (T1), 9.445412 (T2)**. Mean paired T0-to-T2 decrease is **42.0241%**. Absolute fixed-partition gaps span **0.0411486–0.153621**, or **0.414182%–1.730195% of returned fixed-partition Phi**. The latter are distinct from final nearest-assignment quality and do not certify global optimality. The illustrative growth probe and protocol-5 state byte sizes were source/hash inspected but not independently benchmarked or reserialized; avoid attributing a new independent empirical scaling validation to this audit.

## Reproduction and handoff

[README](study://Multigroup_Audit/README.md) records the three independent commands. All three numerical batches used the parent-held exclusive lock `/private/tmp/ftf_benchmark_20260926.lock`, with one child and five thread environment settings equal to one; the lock was never unlinked. Total logged held time was about 17.27 seconds. No timing claim is made from audit runtime. Python 3.12.14 and the existing NumPy 2.3.5 environment were reused. New evidence is small and local; no new dataset/environment copy was made.

The current manuscript writer is task `[coordination-id-omitted]`; the old integrator is no longer the destination. Automatic approval review rejected two earlier cross-task messages and the final notification to the new writer, citing nonpublic audit details/filesystem paths and destination authorization. The new writer was independently confirmed as an active local task; the review still rejected the send. No further send or bypass was attempted. The orchestrator explicitly authorized these local reports/status as the coordination fallback and told the new writer where to read them. See [CLAIMS_DISPOSITION](study://Multigroup_Audit/CLAIMS_DISPOSITION.md) and [AUDIT_STATUS](study://Multigroup_Audit/AUDIT_STATUS.json) for the concise integration decision.
