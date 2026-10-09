# Merged-1k theorem mapping

Scope: lower half of `thm:kappa`, `app:kappa-proof`, ownership in `eq:kappa`, and exact κ=8 anchor-Lloyd caveat. Not the approximation upper bound.

| Paper step | Lean declarations |
|---|---|
| Integer existence, cardinalities, ownership | Imported `MatchedBudget.rational_parameter_realizable`, `client_cardinalities`, `group_cardinalities`; `MergedOne.rational_kappa_lower_construction`, `declared_ownership_parameter` |
| Locally balanced draw from finite identities | `local_first_law` |
| Integer-normalized server anchors and 1/4 far law | `anchor_weight_one`, `output_law`, `output_probability_valid` |
| Full-record real group objectives | `record_group_costs`, `record_objectives`, `group_costs` |
| Attained global real optima and positive denominators | `g_optimum`, `phi_optimum`, `positive_optima`, `record_optima` |
| Exact expectations and κ/2,κ/4 inequalities | `expected_g`, `expected_phi`, `exact_ratios`, `lower_ratios`, `finite_record_lower_bounds` |
| One exact anchor-Lloyd caveat | `lloyd_center`, `lloyd_caveat_kappa_eight` |

Every hypothesis and definition is stated in `MergedOne.lean`. See `MERGED_ONE_REPORT.md` for exact implementation bridges.

## Exported declaration index

- `MergedOne.local_first_law` — `MergedOne.lean:26`
- `MergedOne.anchor_weight_one` — `MergedOne.lean:40`
- `MergedOne.output_law` — `MergedOne.lean:56`
- `MergedOne.output_probability_valid` — `MergedOne.lean:62`
- `MergedOne.group_costs` — `MergedOne.lean:79`
- `MergedOne.g_completed_square` — `MergedOne.lean:83`
- `MergedOne.b_completed_square` — `MergedOne.lean:87`
- `MergedOne.g_optimum` — `MergedOne.lean:91`
- `MergedOne.phi_optimum` — `MergedOne.lean:97`
- `MergedOne.positive_optima` — `MergedOne.lean:115`
- `MergedOne.expected_g` — `MergedOne.lean:125`
- `MergedOne.phi_endpoints` — `MergedOne.lean:131`
- `MergedOne.expected_phi` — `MergedOne.lean:144`
- `MergedOne.exact_ratios` — `MergedOne.lean:152`
- `MergedOne.lower_ratios` — `MergedOne.lean:168`
- `MergedOne.record_group_costs` — `MergedOne.lean:202`
- `MergedOne.record_objectives` — `MergedOne.lean:214`
- `MergedOne.real_epsilon_bounds` — `MergedOne.lean:221`
- `MergedOne.record_optima` — `MergedOne.lean:233`
- `MergedOne.finite_record_lower_bounds` — `MergedOne.lean:245`
- `MergedOne.rational_kappa_lower_construction` — `MergedOne.lean:262`
- `MergedOne.lloyd_center` — `MergedOne.lean:285`
- `MergedOne.lloyd_caveat_kappa_eight` — `MergedOne.lean:294`
- `MergedOne.declared_ownership_parameter` — `MergedOne.lean:304`
