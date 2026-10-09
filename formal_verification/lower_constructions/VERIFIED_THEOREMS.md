# Verified theorem map — matched slots

Manuscript labels: `prop:s2-matched-budget`, `eq:s2-matched-ratios`; definitions of Φg, Φ and G in the main text; candidate equation `eq:lambda-center` and guard in `alg:guarded-update` only to the scope stated below.

All listed declarations were compiled and inspected with `#print axioms`. Definitions and hypotheses are the Lean statements in the linked source; the table is a paper-to-Lean guide, not a replacement statement.

| Paper step | Checked declarations | Hypotheses and exact scope |
|---|---|---|
| Finite witness for each rational κ≥1 | `rational_parameter_realizable`, `client_cardinalities`, `group_cardinalities`, `ownership_parameter`, `ownership_fractions` | κ rational ≥1, or natural u≥v>0; tagged finite records; equal group/client sizes; maximum ownership ratio |
| Weighted D² six-pair law | `weighted_location_sum`, `record_first_law`, `record_second_law`, `record_pair_law`, `pair_law`, `local_categorical_valid` | Positive natural u,v; exact normalized record masses and squared distances; no final probability law assumed |
| Integer transfer and indexed ties | `record_transfer_counts`, `indexed_endpoint_counts`, `normalized_count_transfer`, `record_slot_weights` | Explicit ≤ distance comparison; positive v for normalization; group counts are actual record-indicator sums |
| Client-1 zero-weight row and matched slots | `client_one_location`, `client_one_weights`, `unused_slot_probability`, `four_slots`, `nonsaturated_budgets` | All-zero client-1 locations, retained four slot identities, no deduplication; deterministic identity-completion routine not encoded |
| Complete finite server laws | `record_merged_law`, `record_split_law`, `record_split_weights`, `merged_law`, `split_law`, `endpoint_probabilities` | Derived record sampling and normalized integer slot weights; ideal finite conditional product law |
| Probability validity | `pair_nonneg`, `pair_normalized`, `merged_nonneg`, `merged_normalized`, `split_nonneg`, `split_normalized`, `slot_weights_nonnegative` | 0≤ε≤1 where needed; intended range 0<ε≤1/2 derived from κ≥1 |
| Group objectives and global optimum | `record_group_costs`, `record_objectives`, `group_costs`, `real_group_costs`, `real_optimum_at_zero`, `rational_real_agreement` | Finite record averages in ℚ; algebra and optimum certificate for all real c and real ε≥0; no assumed optimum |
| Four displayed expected ratios | `finite_record_ratios`, `matched_ratios`, `matched_real_ratios`, `expected_g_cast`, `expected_phi_cast` | End-to-end finite-record expectation theorem for u≥v>0; arbitrary rational κ≥1 realizability; real expectations via proven cast bridge |
| Refinement limitation | `record_means_zero`, `every_fair_candidate_zero`, `guarded_fair_candidate_zero`, `finite_matched_witness` | Every ideal rational candidate λ and incumbent c; no full represented finite-L bisection program or binary64 semantics |

The production random-bit interface, finite PRNG seed frequencies, represented-grid implementation and full bisection program remain outside scope. These are implementation bridges; none are concealed as axioms or theorem hypotheses asserting the desired conclusion. See `REPORT.md`.

## Complete exported declaration index


### MatchedBudget.lean

- `MatchedBudget.zero_ne_neg` — `MatchedBudget.lean:19`
- `MatchedBudget.zero_ne_pos` — `MatchedBudget.lean:20`
- `MatchedBudget.neg_ne_zero` — `MatchedBudget.lean:21`
- `MatchedBudget.pos_ne_zero` — `MatchedBudget.lean:22`
- `MatchedBudget.neg_ne_pos` — `MatchedBudget.lean:23`
- `MatchedBudget.pos_ne_neg` — `MatchedBudget.lean:24`
- `MatchedBudget.pair_law` — `MatchedBudget.lean:52`
- `MatchedBudget.pair_nonneg` — `MatchedBudget.lean:57`
- `MatchedBudget.pair_normalized` — `MatchedBudget.lean:60`
- `MatchedBudget.no_repeated_location` — `MatchedBudget.lean:63`
- `MatchedBudget.transfer_conservation` — `MatchedBudget.lean:80`
- `MatchedBudget.endpoints_indexed_tie` — `MatchedBudget.lean:85`
- `MatchedBudget.client_one_weights` — `MatchedBudget.lean:115`
- `MatchedBudget.server_total` — `MatchedBudget.lean:119`
- `MatchedBudget.merged_law` — `MatchedBudget.lean:135`
- `MatchedBudget.split_server_total` — `MatchedBudget.lean:162`
- `MatchedBudget.split_law` — `MatchedBudget.lean:165`
- `MatchedBudget.endpoint_probabilities` — `MatchedBudget.lean:173`
- `MatchedBudget.merged_normalized` — `MatchedBudget.lean:179`
- `MatchedBudget.split_normalized` — `MatchedBudget.lean:182`
- `MatchedBudget.merged_nonneg` — `MatchedBudget.lean:185`
- `MatchedBudget.split_nonneg` — `MatchedBudget.lean:189`
- `MatchedBudget.group_costs` — `MatchedBudget.lean:201`
- `MatchedBudget.g_cost` — `MatchedBudget.lean:205`
- `MatchedBudget.phi_cost` — `MatchedBudget.lean:208`
- `MatchedBudget.optimum_at_zero` — `MatchedBudget.lean:213`
- `MatchedBudget.expected_merged_g` — `MatchedBudget.lean:227`
- `MatchedBudget.expected_split_g` — `MatchedBudget.lean:232`
- `MatchedBudget.expected_merged_phi` — `MatchedBudget.lean:237`
- `MatchedBudget.expected_split_phi` — `MatchedBudget.lean:242`
- `MatchedBudget.epsilon_bounds` — `MatchedBudget.lean:249`
- `MatchedBudget.matched_ratios` — `MatchedBudget.lean:259`
- `MatchedBudget.real_group_costs` — `MatchedBudget.lean:285`
- `MatchedBudget.real_g` — `MatchedBudget.lean:289`
- `MatchedBudget.real_phi` — `MatchedBudget.lean:292`
- `MatchedBudget.real_optimum_at_zero` — `MatchedBudget.lean:297`
- `MatchedBudget.rational_real_agreement` — `MatchedBudget.lean:308`
- `MatchedBudget.local_categorical_valid` — `MatchedBudget.lean:316`
- `MatchedBudget.slot_weights_nonnegative` — `MatchedBudget.lean:329`
- `MatchedBudget.unused_slot_probability` — `MatchedBudget.lean:335`
- `MatchedBudget.expected_g_cast` — `MatchedBudget.lean:344`
- `MatchedBudget.expected_phi_cast` — `MatchedBudget.lean:350`
- `MatchedBudget.matched_real_ratios` — `MatchedBudget.lean:358`

### FiniteRecords.lean

- `MatchedBudget.client_cardinalities` — `FiniteRecords.lean:36`
- `MatchedBudget.group_cardinalities` — `FiniteRecords.lean:46`
- `MatchedBudget.weighted_location_sum` — `FiniteRecords.lean:54`
- `MatchedBudget.record_first_law` — `FiniteRecords.lean:74`
- `MatchedBudget.record_second_law` — `FiniteRecords.lean:81`
- `MatchedBudget.record_pair_law` — `FiniteRecords.lean:88`
- `MatchedBudget.global_location_sum` — `FiniteRecords.lean:94`
- `MatchedBudget.indexed_endpoint_counts` — `FiniteRecords.lean:118`
- `MatchedBudget.normalized_count_transfer` — `FiniteRecords.lean:123`
- `MatchedBudget.count_parameters` — `FiniteRecords.lean:138`
- `MatchedBudget.rational_parameter_realizable` — `FiniteRecords.lean:155`
- `MatchedBudget.record_group_costs` — `FiniteRecords.lean:186`
- `MatchedBudget.record_means_zero` — `FiniteRecords.lean:204`
- `MatchedBudget.every_fair_candidate_zero` — `FiniteRecords.lean:213`
- `MatchedBudget.guarded_fair_candidate_zero` — `FiniteRecords.lean:223`
- `MatchedBudget.split_record_first_law` — `FiniteRecords.lean:244`
- `MatchedBudget.nonsaturated_budgets` — `FiniteRecords.lean:251`
- `MatchedBudget.four_slots` — `FiniteRecords.lean:261`
- `MatchedBudget.finite_matched_witness` — `FiniteRecords.lean:270`
- `MatchedBudget.record_transfer_counts` — `FiniteRecords.lean:290`
- `MatchedBudget.client_one_location` — `FiniteRecords.lean:305`
- `MatchedBudget.ownership_parameter` — `FiniteRecords.lean:310`
- `MatchedBudget.ownership_fractions` — `FiniteRecords.lean:326`
- `MatchedBudget.record_slot_weights` — `FiniteRecords.lean:342`
- `MatchedBudget.record_merged_law` — `FiniteRecords.lean:362`
- `MatchedBudget.record_split_weights` — `FiniteRecords.lean:372`
- `MatchedBudget.record_split_law` — `FiniteRecords.lean:382`
- `MatchedBudget.record_objectives` — `FiniteRecords.lean:390`
- `MatchedBudget.finite_record_ratios` — `FiniteRecords.lean:398`
