# Complete manuscript mathematical coverage inventory

Final inventory: current saved live source, recursively following every uncommented input from main.tex. Labels, not theorem numbers, are stable identifiers. Source SHA-256 hashes are in MANUSCRIPT_INPUTS.json.

Statuses: **verified** = checked proof of stated mathematical model with receipts; **partial** = substantive checked fragment plus named gaps; **unstarted** = no checked result inspected here; **imported** = literature input without its proof; **empirical** = measurements/checks, not a mathematical kernel theorem. Other task ownership never implies success. Statuses below are based on inspected exact statements and receipts; no task ownership alone was counted as evidence.

## Every labelled theorem, lemma, proposition and corollary

| Label(s) | Kind/title | Source | Owner | Status |
|---|---|---|---|---|
| `thm:warmstart`, `eq:warm-phi-zero` | theorem: Split-group warm start | `main.tex` | approximation | partial: original finite transfer and constants verified; conditional on named MRS per-call input; full sampler instantiation open |
| `thm:kappa` | theorem: Tight heterogeneity dependence for \Merged | `main.tex` | approximation upper / matched-budget lower | partial: upper transfer conditional on MRS; finite lower construction verified separately |
| `prop:monotonicity` | proposition: Monotonicity | `main.tex` | fair-update | verified mathematical guard + nearest reassignment model; executable correspondence open |
| `lem:basic-cert`, `eq:basic-cert` | lemma: All-competitor certificate | `main.tex` | replay/certificates | verified finite metric certificate and indexed-label consequence |
| `thm:exactness`, `eq:same-seed` | theorem: Seeded exact batch model-output unlearning | `main.tex` | replay/certificates | verified composed mathematical replay under deterministic-map/authentic-cache contracts; executable correspondence open |
| `prop:central-equivalence` | proposition: Algorithm-relative centralized equivalence | `appendix.tex` | fair-update | verified exact aggregation + shared deterministic statistic-based solver |
| `prop:cert-tight`, `eq:runner-cert` | proposition: Tightness and a stronger constant-time cache | `appendix.tex` | replay/certificates | partial: geometric soundness/tightness/top-three lemma verified; operation-cost model unformalized |
| `prop:stable-replay` | proposition: Locally stable replay | `appendix.tex` | replay/certificates | partial: recurrence and finite failure bound verified; work/asymptotic accounting unformalized |
| `prop:cache-lower`, `prop:cache-upper` | proposition: Direct cache reconstruction upper bound | `appendix.tex` | replay/certificates | unstarted: specified reconstruction query/operation counts not formalized |
| `prop:s2-matched-budget`, `eq:s2-matched-ratios` | proposition: A pre-refinement gap with matched anchor slots | `s2_matched_budget_statement.tex` | matched-budget | partial: finite construction and all ratios verified; every ideal rational fair candidate zero; full finite represented solver bridge open |
| `lem:s2-word-coupling` | lemma: Shared words need not give a stable categorical coupling | `s2_coupling_statement.tex` | coupling | partial: finite-word and normalized rejection-trace result verified; infinite shared-word execution refinement open |
| `prop:s2-deletion-work` | proposition: One legal deletion can force linear discarded point work | `s2_coupling_statement.tex` | coupling | partial: finite witness/event/geometry/policy and conditional expectation verified; full execution-to-law and actual-work linkage open |
| `prop:client-summary` | proposition: Whole-client summary replay at initialization | `generated/september26/client_proposition.tex` | replay/certificates | verified mathematical one-step compact initializer under deterministic interfaces and mass conservation; executable correspondence open |

## Substantive unnumbered claims and equation-level obligations

| Stable anchor / claim | Owner | Status | Required coverage |
|---|---|---|---|
| `eq:stats-identity; eq:fixed-objective` | fair-update | verified: raw finite-coordinate moments and centered decomposition (fair v2) | finite vector sufficient statistics, centered decomposition, empty cells |
| `eq:lambda-center / app:fair-update` | fair-update | verified mathematical quadratic branches and finite-dimensional segment projection (fair extension3) | quadratic minimizer, segment projection weakly decreases both costs, coincident means and one-group branches |
| `app:fair-update ideal lambda curve` | fair-update | verified weak monotonicity, including boundary/zero-mass cases and explicit occupied-cell formula (extension3) | f_A nonincreasing / f_B nondecreasing; finite candidate generation and exact scoring |
| `app:line-counterexample` | fair-update | verified concrete counterexample, unique optimum, rejection and nondyadic 5/9 (v2 + extension3); executable GFU link separate | unique optimum 4/3 and all finite/represented incumbent counterexample values |
| `app:mrs-weighted rational expansion` | approximation | partial: positive integer scale, objective/draw/adaptive finite-law reductions verified; literal k-means++ history/completion instantiation open | common denominator existence, finite copies, objectives and first/subsequent categorical pushforward, sequential path law, saturation/zero potential |
| `eq:dz-mrs` | approximation | verified conditional on named per-slice MRS input; explicit finite records/nearest representatives | finite local outcome law, nearest representatives, slice-constant normalization and summing imported bounds |
| `eq:q-bound; eq:edq-root` | approximation | verified weighted geometry, normalization and finite expectation inequalities | weighted spatial triangle, normalized mass two, finite probability Minkowski |
| `eq:g-h-minkowski` | approximation | verified actual finite nearest-center metric geometry; arbitrary reference centers | nearest-center root costs in finite weighted geometry, comparison optimum existence |
| `eq:conditional-root` | approximation | verified finite conditional law, geometry and MRS input use | finite conditional server kernel, imported guarantee and weighted Minkowski |
| `eq:warm-root; eq:warm-g-zero; eq:warm-phi-zero; eq:warm-phi-additive` | approximation | verified conditional original transfer/constants; optimum interpreted via arbitrary-reference bound | remove conditioning, sharpened constants, G/Phi optimum comparison and Young inequality |
| `thm:warmstart optional anchor-Lloyd` | approximation | verified preservation under pointwise anchor nonincrease; represented routine linkage open | nonincrease preserves conditional guarantee; actual represented update linkage separate |
| `eq:represented-quantization; app:represented-snap` | approximation | verified actual geometry/finite expectation under geometric grid and residual premises | geometric grid error + rounding residual, mass two; actual rounding routine linkage separate |
| `app:m-warm; eq:m-root` | approximation | verified generic mass-m quantization and m-group cost comparison; asymptotic notation not formalized | m normalized masses, m-group Phi conversion and exact constants |
| `app:kappa-proof upper / eq:merged-root; eq:merged-zero` | approximation | verified conditional transfer from explicit client geometry, ratio bound and MRS inputs | two-weight sandwich, ratio kappa, pure clients, finite expectation sum and transfer |
| `app:kappa-proof lower` | matched-budget | verified finite rational population, sampling law, real optima and lower ratios (matched extension) | finite rational population, ideal categorical model, objective optima and ratio bounds |
| `app:kappa-proof one anchor-Lloyd step` | matched-budget | verified exact centroid and kappa=8 ratios 99/34 and 117/64 | kappa=8 counterexample to refined lower bound constants |
| `app:s2-matched internal calculations` | matched-budget | partial: finite laws/counts/objectives/ratios and ideal fair candidate verified; full represented solver bridge open | all categorical histories, exact objectives/ratios, finite counts, one guarded round optimum |
| `app:certificates radial tightness` | replay/certificates | verified finite scalar cache and actual one-dimensional witnesses (replay) | actual Euclidean witnesses for upper radii, k>=3 exact shifts, k=2 abs bound |
| `app:certificates runner-up` | replay/certificates | verified metric overshoot/non-runner bounds and exact counterexamples (replay) | reverse triangle bound, non-runner bound, strict improvement, counterexample without non-runner |
| `app:certificates top-three` | replay/certificates | partial: identity-aware maximum lookup theorem verified; operation-cost claim unformalized | identity-aware finite maximum excluding two, constant-time operation model |
| `app:certificates outward bounds` | replay/certificates | verified under genuine enclosure hypotheses; enclosure implementation unverified | interval soundness and exact fallback; executable correspondence separate |
| `app:exactness floating subtraction example` | replay/certificates | unstarted: IEEE binary64 arithmetic example not formally evaluated | IEEE binary64 computation 1e16+1-1e16 and deletion discrepancy |
| `app:exactness initializer and round induction` | replay/certificates | verified under deterministic interfaces/authentic cache; integer signed patches instantiated | slice locality, fresh weights/canonical order, exact signed patches, guard/fallback deterministic induction |
| `app:exactness distribution statement` | replay/certificates | verified equal seed-to-output event values; fixed/seed-independent request interpretation required | pushforward equal functions for fixed/seed-independent deletion; adaptive limitation |
| `eq:work; app:startup` | replay/certificates | unstarted: complete operation/bit/packet/cache cost accounting unformalized | operation counts, initialization, sorting, duplicated fallback, cache/packet raw-size arithmetic |
| `app:startup W0 cannot be omitted` | replay/certificates | unstarted: cost-model family not encoded | family requiring linear masks/materialization with bounded touched initializer |
| `app:margin` | replay/certificates | partial: exact margin and ideal count bound verified; observed numerical-only failure accounting not encoded | failure implies gap <=2epsilon, density finite counting, numerical-only failures |
| `app:margin expected touched-slice mass` | approximation | partial: finite union bound and E Ms <= r/n sum ne^2 <= r smax verified from marginals; uniform-subset marginal/hypergeometric identity open | uniform finite subsets, binomial avoidance probability, union bound, E M_s <= r/n sum n_e^2 <= r smax |
| `prop:stable-replay recurrence` | replay/certificates | verified nonnegative recurrence, uniform bound and ideal failure scale (replay) | nonnegative recurrence induction/geometric series and ideal failure sum |
| `app:s2-coupling internal calculations` | coupling | partial: see coupling report; full infinite stream and actual-work linkage open | finite word coupling + rejection tail, explicit dataset geometry, event probabilities and fallback counts |
| `app:multi-group` | fair-update | partial: finite moment quadratic dual/concavity/weak-duality certificate verified; full epigraph/solver correspondence not encoded | epigraph convexity, dual quadratic formula including A=0, concavity, weak-duality eta certificate |
| `app:cache direct reconstruction` | replay/certificates | unstarted: query-count/cost model not formalized | finite query count (n-r)kT and selection work; no universal lower bound |
| `app:client-summary compact invariant` | replay/certificates | partial: one-step model verified; full sequential compact-state invariant not assembled | whole-client step and sequential invariant, persistent IDs/current normalization |
| `app:refined-detail acceptance accounting` | replay/certificates | unstarted: general N-S+J instrumentation identity not encoded (coupling checks its event policy) | point-unit identity N-S+J and zero savings after abandonment |
| `app:implementation rational categorical sampler` | coupling | partial: primitive masses/block uniformity/normalized rejection traces checked; global IID execution refinement open | geometric-series exact uniform accepted integer, almost-sure termination, category interval cardinalities, zero masses |
| `app:implementation saturation/degeneracy` | approximation | partial: covered data cost zero and adding centers preserves zero verified; full identity/order policy instantiation open | zero representation/potential, deterministic completion preserves cost |
| `app:implementation numeric bounds` | replay/certificates | partial: exact integer additive patches verified; overflow/binary64/encoding boundary not encoded | narrow integer overflow bound, exact dyadic representation, signed inversion, domain validation |

## Imported mathematical inputs

| Input | Status | Scope |
|---|---|---|
| Makarychev et al. 2020 exact-k k-means++ alpha=5(log k+2) | imported | Named input hypothesis; its literature proof is outside this task. Weighted rational reduction is our obligation. |
| Ghadiri et al. fair clustering framework and multi-group dual | imported | Any formulas re-proved here can be verified independently; prior attribution remains. |
| Standard Lean/mathlib finite sums, real arithmetic, metric/norm theory | imported | Kernel-checked library dependencies, recorded by pins and axiom audit. |

## Empirical assertions (not kernel proofs)

All measurement tables, timings, RSS/checkpoint/packet observations, seed frequencies, test pass counts, geometry diagnostics and prototype outcomes in `experiment_evidence`, `september26_evidence`, `consolidated_studies_20260926`, `multigroup_study_20260926`, `stage1_protocol`, and their recursively included generated tables are **empirical**. The manifest lists every included file. The compact invariant proposition within these files is separately enumerated above. Mathematical formulas quoted by empirical prose map to the obligations above; numerical agreement does not upgrade their status.

## Coverage limitations

This inventory is a source audit, not a proof of completeness of natural-language extraction. Anonymous statements are anchored by their nearest label and descriptive claim. Mathematical-model verification and formal-to-manuscript correspondence must be distinguished from implementation linkage. No other task is marked passed without inspecting its exact statements and compiler/axiom receipts.

## Inspected evidence and label reconciliation

Current saved source is live commit `733a1a790872f86b647a492ac3d66e6c7c8ef186`; final manifest has 33 recursively included files and 13 theorem environments. Initial manifest (32 files) is retained privately. Main approximation displays moved to the appendix; exact labels and formulas were reread and agree with the formal targets. No manuscript/research file was written by this task.

- Approximation: `REPORT.md`, `SCOPE.md`, `THEOREM_INDEX.json`, final compiler/axiom receipts and `proof/` in this bundle. MRS literature hypotheses are explicit and never added axioms.
- Fair update/moments v2: `FairUpdate_Moments_Lean_ProofBundle_v2_20260926.zip`, SHA-256 `e47733d2e96ebbd5f8dbc1362b7dc37c7fc169023b66f27331620a5c875521bc`. Inspected COVERAGE, exact guard/aggregation statements, source hashes, final trust-zero receipt, and axiom output. The later geometry extension is also inspected: `FairUpdate_Geometry_Lean_Extension_20260926.zip`, SHA-256 `709310d451875fb6ac64a423b79c7874a791367e8ccef9f57ad84b816e36c7c4`; its exact projection/monotonicity/nondyadic statements, source hash, four clean trust-zero receipts and standard-only audit close those three original-mathematics gaps.
- Matched and Merged-1k lower constructions: `lower_constructions_checked_20260926.zip`, SHA-256 `34d309bca7669ce1776455fe26ebf16e59e465a31418c5c42acfb27854c33491`. Inspected REPORT/VERIFIED_THEOREMS and MergedOne report; exact finite_record_ratios and finite_record_lower_bounds/existence statements; separate trust-zero receipts and axiom evidence. Counts of 72+24 are declarations/helpers, not paper-theorem counts.
- Replay/certificates: `Replay_Certificates_Lean_ProofBundle_20260926.zip`, SHA-256 `3c3120a7ce3e5204f0d30cf0ea1d3ee2405a2f5d124bbecd1aad7d719980e9dc`. Inspected COVERAGE, exact seeded/compact/tightness statements, trust-zero CertifiedReplay receipt, and axiom audit. Deterministic algorithm interfaces are genuine model hypotheses, not claims of production refinement.
- Coupling: `Coupling_Lean_ProofBundle_20260926.zip`, SHA-256 `33bcef981dafb5a7bb6b540ec7b9d8ba3075f8501e9e527931c3274a67a27246`. Inspected COVERAGE, STATUS, exact audit and final Obstruction receipt. Both manuscript results deliberately remain partial because full adaptive infinite-word execution refinement is missing.

## Prioritized remaining obligations for all self-contained mathematics

1. Instantiate an exact finite-history D² learner and its zero-potential/completion semantics against the finite-law MRS interface; compose the rational-copy objective/law lemmas into that learner's literature application. Keep the external MRS proof explicitly imported. Connect ideal random-bit execution to its finite selected-center law; finite seeded PRNG frequencies are a different claim.
2. Complete coupling's global infinite IID-word stream/adaptive consumption refinement and identify actual initialization/work variables with the checked trace/event model. Its finite/trace results alone do not prove the whole two labelled claims.
3. Full concrete GFU finite control flow remains distinct from the checked mathematical guard theorem. The projection/lambda/nondyadic extension is now checked. Editorial clarification recommended: the ideal-curve words “decreases” and “increases” mean **nonincreasing** and **nondecreasing**, since equality is possible; no strict version is proved.
4. Encode the uniform fixed-size deletion law to derive marginal r/n and the exact hypergeometric no-hit ratio. The expectation and union-bound consequences are already checked conditionally.
5. Formalize explicit operation-count models for eq:work, prop:cache-upper, top-three O(1), setup lower-family claim, general N-S+J and raw packet/cache size formulas. Asymptotic/log-order statements are not established merely by exact algebraic coefficients.
6. Assemble the sequential compact-state invariant. Separately decide whether to formalize IEEE numeric examples, overflow/encoding bounds, outward enclosure implementations, binary64/grid candidate rounding and production code linkage. The last group is executable correspondence, not required to call the already specified mathematical theorems checked.

Global conclusion: broad mathematical coverage is now available, but **all self-contained manuscript proofs are not yet fully formalized**. Empirical claims remain empirical and are not upgraded by any proof bundle.
