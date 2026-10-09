# Frozen matched-start refinement protocol

26 September 2026. New experiment `matched-start-v1`; frozen before any full-population execution. Preserve completed Group_Quality, canonical source, historical evidence and live manuscript unchanged. No new tasks, usage reset, download, archive restore, manuscript integration or publication.

## Grid and question

Exactly 30 cases: record-deletion and whole-client-deletion populations x Adult/Bank/Credit x seeds 10000..10004. Use the exact retained identity/count cases bound in `study://Group_Quality/tables/identity_counts.csv`. k=10, b=12, clips 175/121/74, L=6, gamma=0, no anchor Lloyd. Record populations use their original 30/45/30 removed-record requests; client populations drop the originally selected client0 (300/2259/299 records). Never combine populations. Freeze all 30 keys/identity hashes in FROZEN_GRID.json, source paths/hashes in SOURCE_MANIFEST.json and input hashes in INPUT_MANIFEST.json.

The question is update choice conditional on identical indexed fair-initialized C0 and identical survivors. Compare canonical guarded fair refinement with ordinary population-unweighted Lloyd mean updates through T=1 and T=2 REFINEMENT ROUNDS. T0 is shared. This is not a comparison of initialization algorithms or a fully optimized end-to-end ordinary-k-means baseline. No runtime ratio or timing repetitions.

Expected: 30 completed cases; 60 method trajectories; 180 method/budget rows (T0 duplicated only for method presentation); 150 distinct method/center evaluations, each scored independently plus compared to canonical scoring. All 90 saved fair budget witnesses/objectives must reproduce exactly before the corresponding Lloyd comparator is trusted. Keep all outcomes, unfavorable cases, failures and source changes. No case replacement, parameter sweep, tolerance/permutation equality or tuning to a desired result.

## Numerical contract

Load existing trusted processed/bundle pickles read-only and verify their hashes. Materialize survivors in memory with persistent client IDs, original local order, frozen group masks and transformations. Use the canonical fixed-point encoding once for both methods; centers are finite binary64 interpreted exactly, and are not re-encoded onto the input grid after each update.

Fair: execute unmodified canonical train_full(T=2, build_cache=False), verify its C0..C2 indexed bytes and N/S/SS against saved prefixes, and rescore each center tuple on represented survivors. Source/hash and past arithmetic gates remain inherited; this task executes new reproduction checks.

Lloyd: separate module. Assign each represented record to the same exact nearest indexed center with smallest-index ties using the canonical assignment routine. Aggregate exact counts and integer coordinate sums; for cluster j use each coordinate sum_g S_gj / (scale * sum_g N_gj), converting this exact Fraction to binary64 once, round-to-nearest ties-to-even. A cluster with zero total count retains its old indexed center. No demographic reweighting, worst-group guard, SSE guard, convergence early stopping or best-of-restarts. Assign before each update, and nearest-center rescore after it, as for fair refinement. Only the center update rule differs. Means are population-unweighted even though statistics are stored by group. Rounded means can differ from the real optimum; do not silently snap them to the input lattice or claim broad textbook convergence/optimality. Record observed SSE changes exactly.

## Independent checks and scoring

Before dataset execution, fixed tiny fixtures cover unequal groups with a genuine fair/Lloyd tradeoff; equal-distance index ties; duplicate centers and empty clusters; rational thirds; and exact half-way binary64 rounding using small aggregate fixtures. A scalar Fraction oracle written separately assigns by direct squared distances, computes pointwise group objectives, and computes unweighted exact means. Compare indexed outputs and fractions; preserve each fixture outcome. Both variants share the canonical assignment/statistics for trajectories, which is explicitly distinct from the independent oracle.

For all real output center tuples, independent scoring code imports no canonical assignment, objective, accumulator or fair-cost function. It encloses coordinate subtraction and square with outward nextafter intervals, encloses nonnegative summation with a conservative d*epsilon/(1-d*epsilon) bound, and resolves any ambiguous winner by scalar exact Fraction distances with indexed ties. It separately forms integer moments (guarded against int64 overflow using n*d*M^2 bounds), evaluates represented-center squared distances with Fraction arithmetic, and averages by actual group counts. Cross-check its labels against canonical assignments and its fractions against canonical fair_objective for every center tuple; compare fair fractions to saved references. Do not equate merely reading saved fractions with this new objective recomputation. Exact nearest-center direct scalar fixtures test the independent scoring path, including its ambiguous branch.

## Outcomes and aggregation

At each case/method/T save Phi_0, Phi_1, Phi=max(Phi_0,Phi_1), G=Phi_0+Phi_1, population-average cost=(n0*Phi0+n1*Phi1)/(n0+n1), pooled SSE=n0*Phi0+n1*Phi1. Preserve exact fractions, indexed centers, integer per-round stats, labels hashes, input/source/row-identity bindings and worker receipts.

Report fair-minus-Lloyd paired absolute differences and relative differences (fair-Lloyd)/Lloyd at each T, plus each method's within-seed changes for 0->1,1->2,0->2. Zero denominators are explicitly undefined, never silently zero/infinite. Maximize group costs inside each seed before averaging. Summarize all five seeds using mean, sample SD, min/max and win/loss/tie counts. Timing repeats are absent. Count all exceptions to lower Phi, higher population cost, any group worsening or stepwise decrease; overlapping transitions are not independent trials. No significance/CI claim, global optimum, equalization, all-groups dominance, application adequacy, erasure, or new exact-unlearning guarantee for Lloyd.

## Coordination and delivery

All substantial numeric/hash work and heavy rendering uses one worker with five numerical-library thread limits=1, under parent-held exclusive fcntl.flock('/private/tmp/ftf_benchmark_20260926.lock'). Never unlink it. Release after each case and bounded setup/fixture/report batch so other studies can proceed. Queue waiting and held execution durations are operational receipts, never compared algorithm performance. Record background load and top processes; the lock cannot eliminate desktop load. Reuse existing environment read-only; no environment or data duplication.

Produce concise REPORT.md, this protocol/freeze/source/input manifests, runnable modules/commands, compact exact outputs and CSVs, one appendix-ready visually checked PDF, receipts and INTEGRATION_NOTES.md with short LaTeX-ready interpretation. One figure may use two population rows and three dataset columns with separate cost scales. Clearly label shared fair initialization and five seeds. Keep implementation details in the technical report, not proposed paper narrative. Stop after this grid; unresolved correctness prevents corresponding scientific claims rather than changing cases or targets.
