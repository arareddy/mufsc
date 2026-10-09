import Coupling
import WordBlocks
import Rejection
import Traces
import PrefixEvent
import Deletion
import Initialization
import WorkProbability
import Obstruction
import InfiniteExpectation
import JointTrace

#check @Coupling.primitive_old
#print axioms Coupling.primitive_old
#check @Coupling.primitive_new
#print axioms Coupling.primitive_new
#check @Coupling.count_odd
#print axioms Coupling.count_odd
#check @Coupling.count_even
#print axioms Coupling.count_even
#check @Coupling.accepted_mismatch_bridge
#print axioms Coupling.accepted_mismatch_bridge
#check @Coupling.accepted_mismatch_count
#print axioms Coupling.accepted_mismatch_count
#check @Coupling.first_disagreement_half
#print axioms Coupling.first_disagreement_half
#check @Coupling.rejection_shape
#print axioms Coupling.rejection_shape
#check @Coupling.proposal_width
#print axioms Coupling.proposal_width
#check @Coupling.power_is_even
#print axioms Coupling.power_is_even
#check @Coupling.assembled_low_bit
#print axioms Coupling.assembled_low_bit
#check @Coupling.low_bits_count
#print axioms Coupling.low_bits_count
#check @Coupling.uniform_low_bits
#print axioms Coupling.uniform_low_bits
#check @Coupling.word_low_bits_uniform
#print axioms Coupling.word_low_bits_uniform
#check @Coupling.primitive_scaled_new
#print axioms Coupling.primitive_scaled_new
#check @Coupling.primitive_scaled_old
#print axioms Coupling.primitive_scaled_old
#check @Coupling.assembly_formula
#print axioms Coupling.assembly_formula
#check @Coupling.assembly_bijective
#print axioms Coupling.assembly_bijective
#check @Coupling.block_low_bits_count
#print axioms Coupling.block_low_bits_count
#check @Coupling.block_low_bits_uniform
#print axioms Coupling.block_low_bits_uniform
#check @Coupling.block_first_low_bit
#print axioms Coupling.block_first_low_bit
#check @Coupling.word_consumption
#print axioms Coupling.word_consumption
#check @Coupling.proposal_inverse_bounds
#print axioms Coupling.proposal_inverse_bounds
#check @Coupling.rejection_tail_zero
#print axioms Coupling.rejection_tail_zero
#check @Coupling.accepted_trace_sum
#print axioms Coupling.accepted_trace_sum
#check @Coupling.rejection_terminates_total_mass
#print axioms Coupling.rejection_terminates_total_mass
#check @Coupling.category_law
#print axioms Coupling.category_law
#check @Coupling.first_category_count
#print axioms Coupling.first_category_count
#check @Coupling.exact_coupling_disagreement
#print axioms Coupling.exact_coupling_disagreement
#check @Coupling.binary_total_variation
#print axioms Coupling.binary_total_variation
#check @Coupling.disagreement_decomposition
#print axioms Coupling.disagreement_decomposition
#check @Coupling.trace_runs
#print axioms Coupling.trace_runs
#check @Coupling.trace_length
#print axioms Coupling.trace_length
#check @Coupling.trace_weight_from_cylinder
#print axioms Coupling.trace_weight_from_cylinder
#check @Coupling.old_trace_zero
#print axioms Coupling.old_trace_zero
#check @Coupling.old_trace_after_reject
#print axioms Coupling.old_trace_after_reject
#check @Coupling.accepted_count_without_reject
#print axioms Coupling.accepted_count_without_reject
#check @Coupling.trace_mismatch_count
#print axioms Coupling.trace_mismatch_count
#check @Coupling.trace_disagreement_exact
#print axioms Coupling.trace_disagreement_exact
#check @Coupling.trace_and_decomposition_agree
#print axioms Coupling.trace_and_decomposition_agree
#check @Coupling.successful_prefix_classification
#print axioms Coupling.successful_prefix_classification
#check @Coupling.old_first_trace_count
#print axioms Coupling.old_first_trace_count
#check @Coupling.old_trace_marginal_half
#print axioms Coupling.old_trace_marginal_half
#check @Coupling.trace_binary_total_variation
#print axioms Coupling.trace_binary_total_variation
#check @Coupling.four_block_count
#print axioms Coupling.four_block_count
#check @Coupling.prefix_minus_one
#print axioms Coupling.prefix_minus_one
#check @Coupling.prefix_minus_two
#print axioms Coupling.prefix_minus_two
#check @Coupling.sum_cutoff
#print axioms Coupling.sum_cutoff
#check @Coupling.prefix_event_count
#print axioms Coupling.prefix_event_count
#check @Coupling.prefix_common_zero_slot
#print axioms Coupling.prefix_common_zero_slot
#check @Coupling.prefix_probability
#print axioms Coupling.prefix_probability
#check @Coupling.retained_six_slot_mapping
#print axioms Coupling.retained_six_slot_mapping
#check @Coupling.old_six_slot_mapping
#print axioms Coupling.old_six_slot_mapping
#check @Coupling.retainID_injective
#print axioms Coupling.retainID_injective
#check @Coupling.retained_exactly_not_deleted
#print axioms Coupling.retained_exactly_not_deleted
#check @Coupling.dataset_sizes
#print axioms Coupling.dataset_sizes
#check @Coupling.endpoint_labels
#print axioms Coupling.endpoint_labels
#check @Coupling.ideal_certificate_decisions
#print axioms Coupling.ideal_certificate_decisions
#check @Coupling.sound_certificate_rejects_changed_label
#print axioms Coupling.sound_certificate_rejects_changed_label
#check @Coupling.failure_counts
#print axioms Coupling.failure_counts
#check @Coupling.round_zero_policy
#print axioms Coupling.round_zero_policy
#check @Coupling.actual_indexed_shifts
#print axioms Coupling.actual_indexed_shifts
#check @Coupling.unit_cached_margins
#print axioms Coupling.unit_cached_margins
#check @Coupling.actual_changed_record_count
#print axioms Coupling.actual_changed_record_count
#check @Coupling.table_is_d2_sampling
#print axioms Coupling.table_is_d2_sampling
#check @Coupling.diagonal_zero
#print axioms Coupling.diagonal_zero
#check @Coupling.local_representatives_fixed
#print axioms Coupling.local_representatives_fixed
#check @Coupling.record_location_counts
#print axioms Coupling.record_location_counts
#check @Coupling.transferred_weights
#print axioms Coupling.transferred_weights
#check @Coupling.old_transferred_weights
#print axioms Coupling.old_transferred_weights
#check @Coupling.table_probability_sum
#print axioms Coupling.table_probability_sum
#check @Coupling.table_nonnegative
#print axioms Coupling.table_nonnegative
#check @Coupling.six_table_signs
#print axioms Coupling.six_table_signs
#check @Coupling.initialization_tuple_TV
#print axioms Coupling.initialization_tuple_TV
#check @Coupling.retained_parameter_range
#print axioms Coupling.retained_parameter_range
#check @Coupling.retained_tuple_TV
#print axioms Coupling.retained_tuple_TV
#check @Coupling.opposite_probability_lower
#print axioms Coupling.opposite_probability_lower
#check @Coupling.prefix_probability_real
#print axioms Coupling.prefix_probability_real
#check @Coupling.wide_event_lower
#print axioms Coupling.wide_event_lower
#check @Coupling.narrow_event_lower
#print axioms Coupling.narrow_event_lower
#check @Coupling.beta_gt_sixteenth
#print axioms Coupling.beta_gt_sixteenth
#check @Coupling.beta_times_failed
#print axioms Coupling.beta_times_failed
#check @Coupling.linear_work_constant
#print axioms Coupling.linear_work_constant
#check @Coupling.expectation_event_lower
#print axioms Coupling.expectation_event_lower
#check @Coupling.obstruction_expectation
#print axioms Coupling.obstruction_expectation
#check @Coupling.power_parameter
#print axioms Coupling.power_parameter
#check @Coupling.event_probability_lower
#print axioms Coupling.event_probability_lower
#check @Coupling.initialization_word_offsets
#print axioms Coupling.initialization_word_offsets
#check @Coupling.each_variant_event_counts
#print axioms Coupling.each_variant_event_counts
#check @Coupling.event_work_contribution
#print axioms Coupling.event_work_contribution
#check @Coupling.finite_law_expected_work
#print axioms Coupling.finite_law_expected_work
#check @Coupling.deletion_witness_summary
#print axioms Coupling.deletion_witness_summary
#check @Coupling.countable_expectation_event_lower
#print axioms Coupling.countable_expectation_event_lower
#check @Coupling.countable_law_expected_work
#print axioms Coupling.countable_law_expected_work
#check @Coupling.narrow_joint_count
#print axioms Coupling.narrow_joint_count
#check @Coupling.narrow_joint_trace_mass
#print axioms Coupling.narrow_joint_trace_mass
#check @Coupling.second_category_count
#print axioms Coupling.second_category_count
#check @Coupling.wide_opposite_count
#print axioms Coupling.wide_opposite_count
#check @Coupling.wide_opposite_trace_mass
#print axioms Coupling.wide_opposite_trace_mass
#check @Coupling.local_product_trace_normalized
#print axioms Coupling.local_product_trace_normalized
#check @Coupling.wide_joint_trace_mass
#print axioms Coupling.wide_joint_trace_mass
