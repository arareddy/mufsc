# Matched-anchor-budget Lean verification

Status: **checked finite mathematical construction**, frozen 26 September 2026. All 72 exported theorems compile with Lean 4.19.0, warnings treated as errors. The source is an independent formalization of `prop:s2-matched-budget` and `eq:s2-matched-ratios`, not an execution of the existing Python checker. No manuscript or experiment was modified.

The result is more than an arithmetic corollary. It defines distinct finite record identities, locally balanced record weights, normalized weighted-D² sampling, indexed nearest-representative count transfer, four retained server slots, two-stage finite output laws, and actual record-average group costs. The six-pair law and all four ratios are conclusions of those definitions.

## Main results and scope

For every rational κ ≥ 1, `rational_parameter_realizable` constructs natural u,v with 0<v≤u, κ=u/v, and ε=v/(u+v)=1/(κ+1). Records are tagged finite indices. Client 0 has 2u A records at 0 and v B records at each endpoint; client 1 has 2v A and 2u B records at 0. Both clients and both global groups have cardinality 2(u+v). `ownership_parameter` proves that the maximum ownership ratio is κ, and `nonsaturated_budgets` proves the relevant slice sizes and budget minima.

The client-0 local probability law is derived by summing the record weights 1/(2u) on A and 1/(2v) on B. First selection normalizes these masses; second selection multiplies by squared distance and normalizes again. `record_pair_law` proves the six nonzero ordered-pair probabilities 1/4, 1/4, 1/12, 1/12, 1/6, 1/6. Repeated locations have zero probability. `weighted_location_sum` proves the pushforward for an arbitrary function of location, rather than assuming the probability table.

`record_transfer_counts` proves that the integer formulas equal sums of actual record-assignment indicators. The `≤` comparison makes ties go to the first indexed representative. `normalized_count_transfer` divides the group counts by the global group size. Client 1's all-zero geometry is defined separately; its weights are 1 and 0. `four_slots` proves that the ordered table has four distinct slot identities, even when their locations coincide or weights vanish. The server categorical normalization includes all four slots and has total weight two; its zero-weight slot has probability zero.

`record_merged_law` and `record_split_law` connect record-derived sampling and integer server weights to the finite location laws. Endpoint probabilities are (1+ε)/6 and ε/2. Both output laws are normalized and nonnegative over the parameter range. SG's equal-endpoint first draw is separately derived from its finite B slice.

`record_group_costs` derives the group averages from finite records. `real_optimum_at_zero` proves a global minimum at zero for all real centers. `matched_real_ratios` proves the displayed ratios as real expectations. `finite_record_ratios` is the end-to-end rational theorem using the explicitly defined finite-record samplers and costs: ((κ+5)/3, (κ+8)/6, 2, 3/2). Rational/real agreement is kernel checked.

`record_means_zero`, `every_fair_candidate_zero`, and `guarded_fair_candidate_zero` show that both full-data group means vanish and any ideal rational candidate is zero and passes the objective guard. This proves the mathematical reason the separation disappears under a one-cluster fair update.

## Exact remaining bridges

- The model uses exact finite categorical probabilities and their conditional products. It does not implement an infinite random-bit tape, prove rejection-sampler termination, or identify finite PCG64 seed frequencies with those probabilities. No sampling-law premise is an added axiom; this is the explicit probability model being verified.
- Client 1's deterministic smallest-unused-identity completion algorithm is not implemented. All client-1 record locations are proved zero, and its indexed transfer and four retained slots are checked. The identity chosen by completion does not alter these location-level conclusions.
- The complete finite-L bisection program, candidate ordering, encoded tie-breaking and binary64 representation are not encoded. The checked statement is that **every ideal rational candidate** is zero and the guard accepts it, for every incumbent and candidate parameter. Applying that to the production bisection routine still requires its candidates to implement the stated formula and represent zero exactly.
- Fixed preprocessing, clipping, grid representation, serialization, deployed code equivalence, metadata, bytes and runtime are outside this proof. The mathematical model is one-dimensional, k=1, γ=Ta=T=0 for initialization. It makes no post-refinement separation claim.
- The model uses explicit finite sums over the three location constructors, four slot constructors and finite record types, rather than mathlib's PMF abstraction. Normalization/nonnegativity and the substantive finite-record pushforwards are proved.

Accordingly this is a checked finite mathematical construction with explicit implementation bridges, **not a claim that the complete production training map or entire paper is formally verified**.

## Proof integrity

`Axioms.lean` inspects all 72 exported theorem declarations. Its actual output is retained in `evidence/axioms.stdout.log`. The only dependencies reported are Lean's standard `propext`, `Classical.choice`, and `Quot.sound`; several elementary results use no axioms. There are no added domain axioms, `sorry`, `admit`, `native_decide`, unsafe proof escapes, or native oracle proof shortcuts in these proof sources. `ring`, `norm_num`, `linarith`, `nlinarith`, `field_simp`, `omega` and ordinary `decide` construct kernel-checked proofs. Noncomputable real definitions use the standard real-number library.

The trusted environment is the pinned official Lean release and official precompiled mathlib cache, with standard Lean import trust. This run does not rebuild the Lean compiler or independently recheck every imported library object with trust level zero. The local theorem declarations themselves were elaborated and kernel checked. Sources were read after proof generation, and checked milestones were retained.

## Reproduction and evidence

See `BUILD.md`, `requirements.json`, `lean-toolchain`, `VERIFIED_THEOREMS.md`, `PAPER_INPUTS.json` and `MANIFEST.json`. The three final checks exited zero: core 09:34:53 UTC, finite records 09:37:41 UTC, axiom inspection 09:38:24 UTC. Full stdout files and source hashes are in `evidence/`. Successful core and record checks emitted no diagnostic text. Compilation uses one worker under a parent-held shared benchmark flock, released between batches; no network work holds that CPU lock.

## Shared storage and downloads

One shared ARM64 Lean/mathlib environment was installed outside cloud-synced folders. The first complete setup and smoke test took approximately 12 minutes. The pinned toolchain archive is 329,275,227 bytes; the initial matched/fair-update cache has 914 compressed files totaling 37,405,353 bytes. The storage receipt measured 1,555,596,628 logical bytes for the extracted toolchain, 736,160,374 for mathlib sources/dependencies/builds, 40,289,602 for the cache directory, and 329,275,227 for the retained toolchain archive. Allocated disk is separately recorded in the private shared setup receipt. Later module additions for other tasks increase these shared totals; this paragraph describes the initial matched/fair-update snapshot.

Sources were shallow-fetched sequentially, cache transfers serialized, and interrupted toolchain transfer resumed. Git transfer totals and HTTP overhead were not instrumented, so no total network-usage claim is made. No files were moved out of iCloud and no disk savings are claimed. The local files require a separately chosen backup. Private absolute-path inventories and exact local invocations remain in the shared setup folder, outside this shareable proof folder.
