# Claim disposition for the frozen multi-group handoff

**SCOPED PASS — no blocking correctness defect found.** This applies only to `FTF-MG-FW12-B6-v1`, manifest SHA-256 `98a51b5391fff46dae2ab37a5fe7a0870e61a2a2417034c10048186ca9705917`. Preserve the distinctions below when integrating the new variant. No source repair is requested; any stronger claim should be omitted rather than inferred from this audit.

| Claim | Disposition | Scope / minimum wording |
| --- | --- | --- |
| Concave simplex dual | Verified mathematically and in independent exact checks | Dual is the infimum of weighted fixed-partition quadratics; weighted minimizer costs are supergradients, including zero-denominator choices. |
| Returned-center certificate | Verified | Exact weak-duality upper bound on fixed-partition suboptimality: returned represented Phi minus best evaluated exact dual lower bound. |
| Refinement nonincrease | Verified conditionally; independently tested | Exact guard evaluates actual binary64 returned centers, then nearest reassignment cannot raise any group cost against the fixed partition. |
| Exact/global optimizer | Unsupported; omit | Finite 12-step/six-bisection search. All ten distinct real updates reach the iteration bound; no global clustering-optimum certificate or convergence rate. |
| Same-seed whole-client replay for arbitrary finite supported T | Conditional proof supported; bounded execution verified | Fixed representation, configuration, PRNG and tie rules; stable IDs/order; all declared groups remain nonempty; trusted original state. Executed independently at T=0,1,2. |
| T0 compact sequential replay without raw arrays | Verified by code and independent bounded tests | Trusted counts/summaries, whole-client requests, returned next compact state. 18 independent sequence steps. |
| Positive-T compact replay / maintained sequential checkpoint | Unsupported; omit | DIRECT uses retained represented/encoded/group arrays and recomputes all positive-round assignments/moments; it releases a model, not a next checkpoint. |
| Deep immutability, hostile-state validation, erasure, privacy | Unsupported; omit | Nested dictionaries remain mutable/shared; selected representatives can be original rows; previous states/data remain. |
| RAC1P recovery and alignment | Verified for frozen processed data | All 100,000 exact forward labels, native IDs/offsets/source-row alignment and 1,600,000 encoded coordinates checked. Original raw Census bytes and category-name semantics were not newly externally verified. |
| Nine-group real pilot | Supported, narrowly | One selected 100,000-row/10-client population, one 6,799-row deletion, 93,201 survivors, five training seeds, T=0,1,2. All 16 features retained, including RAC1P; no survey weighting; smallest retained group has seven rows. |
| 35 + 105 exact models | Rephrase to prevent inflated sample count | 20 configured replay-versus-fresh gate comparisons across 35 gate files; 105 timed outputs are 45 fresh + 60 replay repetitions. One population/request, 15 seed/budget cases. |
| 1,164 certificate evaluations | Supported with distinctness disclosed | 15 saved update records repeat round 0 across T1/T2; ten distinct seed/round partitions contain 778 candidate evaluations independently rederived. |
| T0 speed | Supported only at matched resident boundary | Ratio of total request times 138.70x DIRECT / 139.14x compact; no demonstrated extra compact runtime advantage. |
| Positive-T speed | Supported only at matched resident boundary | DIRECT request ratios 1.60x at T1 and 1.30x at T2. Validation, complete solver/guard/certificate and identical model-witness output write included; loading/setup/state persistence/network/erasure excluded. No universal factor. |
| Utility improvement | Saved evidence and aggregates verified | Mean Phi 16.3740 → 9.9941 → 9.4454, mean paired T0-to-T2 decrease 42.0241%; no utility adequacy or population fairness inference. Independent full real-row reassignment for every model was not performed. |
| Resource growth with m | Structural bound reviewed; empirical probe remains author measurement | At most C*m*k local slots and m*k*(d+2) integer moments per round; exact-number bit lengths matter, and the solver evaluates m vertices. No independent runtime scaling theorem or RAM/disk-savings claim. |
| Binary implementation identity or prior approval transfer | Unsupported for positive rounds; omit | Separate numerical map. The prior binary review is context, not approval of this candidate. |
| Fresh-independent adaptive deletion law / ideal tapes | Unsupported; omit | Pointwise fixed-seed replay is distinct from a fresh independent seed conditional on model-adaptive deletion; finite PCG64 does not establish ideal independence. |
| New multi-group fair clustering or centralized approximation novelty | Not established by this audit | Keep existing attribution and additive prototype framing; this audit did not conduct a new literature/novelty review. |

No new benchmark is needed to use the supported bounded-pilot claims. If time is too short to preserve the essential certificate, timing, rare-group and count qualifications, omit the corresponding stronger claim rather than promoting it to a general result.

Independent evidence and exact code locators are in [AUDIT_REPORT.md](study://Multigroup_Audit/AUDIT_REPORT.md). Machine status is [AUDIT_STATUS.json](study://Multigroup_Audit/AUDIT_STATUS.json). Latest writer: `[coordination-id-omitted]`. No manuscript file was edited by this audit.
