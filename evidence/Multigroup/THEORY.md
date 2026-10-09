# Scoped functional and optimization arguments

This is a proof argument for a separate deterministic prototype, conditional on its stated primitives and trusted inputs. Executed tests are listed separately in CORRECTNESS.json and VERIFICATION.json. Neither this document nor those checks are an independent sign-off.

## Prior work and existing manuscript

Ghadiri, Samadi and Vempala, *Socially Fair k-Means Clustering*, Section 3, already treats m groups, gives the convex fixed-partition epigraph program, explains why the objective composed with simplex weights need not be convex or even quasiconvex, and discusses finite heuristics and optimality bounds. The local author-fulltext copy was read (source hash in SOURCE_INPUTS.json); citation: https://doi.org/10.1145/3442188.3445906. The live manuscript's app:m-warm and app:multi-group already state the m-group initialization extension and the concave dual/exact-guard formulation. This task implements those ideas; it does not invent multi-group socially fair clustering or a new initialization approximation theorem.

Pan et al., *Machine Unlearning of Federated Clusters*, Section 5.3 and Algorithm 4, already covers whole-client deletion by dropping client contributions and recomputing the server: https://openreview.net/forum?id=VzwfoFyYDga. Its local initialization distribution/complexity statements are not substituted for the prototype's pointwise same-seed statement. The prior independent binary T0 review is input context only and does not approve this new code or pilot.

## Exact whole-client replay for categorical groups

Fix a represented ordered dataset, persistent client IDs, disjoint group labels 0..m-1, and a configuration and seed. All declared global n_g must be positive before and after deletion. Preprocessing, label definition, encoding, quantization, local/server iteration budgets, representation, PRNG implementation and tie rules are fixed. State is produced by this implementation and not externally mutated.

For each nonempty surviving slice (c,g), whole-client deletion leaves its ordered represented rows and keyed tape [seed,1,c,g] unchanged. Its ordinary local seeding, unsnapped assignment multiplicities, snapped anchors, selected indices and slot identities therefore equal a fresh execution. Locally absent slices are omitted by both executions. No local stage depends on global n_g. Exact count subtraction yields the new global n'_g, so sorting (c,g,slot) and assigning the rational weights h/n'_g reproduces the fresh compact server input. The server restarts the same [seed,2] stream and inherits the canonical exact mass, rejection, saturation, zero-potential completion and indexed tie conventions. Optional fixed guarded anchor Lloyd sees the same inputs. Thus C0 is identical as an indexed represented tuple.

At each positive round assume indexed centers agree. Exact nearest assignment on the identical retained represented rows agrees, including ties. Exact integer N/S/SS aggregation agrees, without floating sum-order dependence. The deterministic bounded multi-group solver receives identical values and incumbent bytes and therefore takes identical rational branches, rounding and guard decisions. The next centers agree. Induction proves pointwise same-seed equality for every fixed finite supported T; the actual bounded pilot validates T=0,1,2. DIRECT reuses the local summaries; it still performs all surviving raw-coordinate assignment and moment work in positive rounds.

At T0 the returned compact state satisfies the same active-client/count/summary invariant after every valid whole-client request. Induction gives model equality along a valid sequence. It does not preserve an original per-point certificate cache, physically erase earlier state, or authorize mutation of trusted nested dictionaries. The positive-round API releases a model; it is not a maintained sequential deletion checkpoint service.

For a fixed or seed-independent deletion request, pointwise equality implies the corresponding equality in distribution under the same seed law. It does not imply an independent fresh seed distribution conditional on a model-adaptively selected deletion. Finite PCG64 streams do not establish ideal independent random tapes for approximation proofs.

## Exact optimization certificate and monotonicity

For a fixed partition let a_gj=N_gj/n_g, b_gj=S_gj/(n_g scale), Q_g=sum_j SS_gj/(n_g scale^2). Then

f_g(C) = Q_g + sum_j [a_gj ||c_j||^2 - 2 b_gj dot c_j].

The maximum over g is convex in the center coordinates. Its epigraph problem has simplex dual

D(lambda) = sum_g lambda_g Q_g - sum_{j:A_j>0} ||B_j||^2/A_j,

where A_j=sum_g lambda_g a_gj and B_j=sum_g lambda_g b_gj. This is the infimum of affine functions of lambda and hence concave. The prototype does not optimize under a false convexity assumption on max_g f_g(C(lambda)).

If A_j>0, B_j/A_j minimizes that cluster's weighted quadratic. If A_j=0, nonnegativity implies every positively weighted group's cell count and sum at that cluster are zero, so B_j=0 and that weighted quadratic is identically zero. Selecting the sole occupied group's mean or retaining the incumbent if multiple/no groups occupy it remains a weighted minimizer. No empty mean is formed. Costs at the exact minimizer are a dual supergradient, including the declared degenerate selection. On each search segment, positive-denominator interior derivatives are exact; the finite line search is only a bounded optimization method, not a claim of convergence to an exact optimum.

Each rational lambda on the simplex provides D(lambda) <= Phi_partition^*, by weak duality. The code evaluates D exactly. The returned center coordinates are represented binary64 values, converted back to exact dyadic rationals for objective evaluation. Thus

0 <= Phi_partition(C_returned) - Phi_partition^* <= Phi_partition(C_returned) - max_evaluated D.

The saved nonnegative difference is a valid absolute certificate for the fixed partition, even if the finite search is poor, stalls, rejects every candidate, or some optimum groups are inactive. It is not a bound on the global nonconvex clustering optimum. The relative number gap/Phi_returned is descriptive normalization of this certified absolute gap, not a stronger global guarantee.

The exact guard admits a represented candidate only if its fixed-partition maximum cost is no larger than the incumbent's. After acceptance or rejection, reassignment to the nearest indexed centers weakly lowers each group's cost compared with that fixed partition. Hence actual nearest-center Phi cannot increase in a refinement round. This depends on checking the represented centers actually returned, not the unrounded rational minimizer. Guard rejection is exercised explicitly by the small test suite.

## Resource scope

At most C*m nonempty slices and sum min(k,n_cg) <= C*m*k local slots occur. Compact state needs O(C*m*k*d + C*m) numeric/metadata entries; exact Fraction/int bit lengths are additional. DIRECT also retains O(n*d+n) represented/encoded/group data. Per-round statistics occupy m*k*(d+2) integers. The pilot has 9*10*18=1620 such integers per round.

At the frozen solver settings, at most m+1+12*6 distinct lambda evaluations occur per update; each uses O(m*k*d) exact arithmetic operations. This includes m vertices, so it is not a claim of linear total solver time in m. Rational numerator/denominator growth, native array work, allocation, server sampling, input/output costs and host load affect wall time. The inherited zero-quantization O(m log^2 k) warm-start approximation result has the manuscript's ideal-tape assumptions; the finite real pilot neither re-proves it nor improves known centralized approximation dependence.
