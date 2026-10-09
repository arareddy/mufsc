import Coupling
import Mathlib.Analysis.SpecificLimits.Normed
namespace Coupling
noncomputable section
open scoped BigOperators Topology
open Filter

/-- Weight of one fixed trace with r rejected proposals followed by one accepted proposal.
This is an ideal independent-uniform-proposal model, not a PRNG implementation. -/
def traceWeight (m r : ℕ) : ℝ := (1/(2*(m : ℝ)))^(r+1)
def rejectTail (m n : ℕ) : ℝ := (1/(2*(m : ℝ)))^n

theorem proposal_inverse_bounds (m : ℕ) (hm : 1 ≤ m) :
    0 ≤ 1/(2*(m : ℝ)) ∧ 1/(2*(m : ℝ)) < 1 := by
  have hmR : (1 : ℝ) ≤ m := by exact_mod_cast hm
  constructor
  · positivity
  · apply (div_lt_iff₀ (by positivity)).2
    linarith

/-- Rejection is almost surely finite in the ideal trace model: residual mass tends to zero. -/
theorem rejection_tail_zero (m : ℕ) (hm : 1 ≤ m) :
    Tendsto (rejectTail m) atTop (𝓝 0) := by
  exact tendsto_pow_atTop_nhds_zero_of_lt_one
    (proposal_inverse_bounds m hm).1 (proposal_inverse_bounds m hm).2

/-- Countably many rejecting histories are all included, rather than assigning a fixed fuel. -/
theorem accepted_trace_sum (m : ℕ) (hm : 1 ≤ m) (c : ℝ) :
    HasSum (fun r => c * traceWeight m r) (c/(2*(m : ℝ)-1)) := by
  have hmR : (1 : ℝ) ≤ m := by exact_mod_cast hm
  have hp := hasSum_geometric_of_lt_one
    (proposal_inverse_bounds m hm).1 (proposal_inverse_bounds m hm).2
  have hs := hp.mul_left (c*(1/(2*(m : ℝ))))
  convert hs using 1
  · funext r
    simp only [traceWeight,pow_succ]
    ring
  · have hd : 2*(m : ℝ) ≠ 0 := by linarith
    have he : 1-1/(2*(m : ℝ)) ≠ 0 := by
      have hh := (proposal_inverse_bounds m hm).2
      linarith
    field_simp

/-- Summing all 2m-1 possible accepting proposals over all finite rejection histories gives 1. -/
theorem rejection_terminates_total_mass (m : ℕ) (hm : 1 ≤ m) :
    HasSum (fun r => (2*(m : ℝ)-1)*traceWeight m r) 1 := by
  have hmR : (1 : ℝ) ≤ m := by exact_mod_cast hm
  have hd : 2*(m : ℝ)-1 ≠ 0 := by linarith
  simpa [hd] using accepted_trace_sum m hm (2*(m : ℝ)-1)

/-- Infinite accepted-trace law of a category with c accepting integer proposals. -/
def categoryLaw (m c : ℕ) : ℝ := ∑' r : ℕ, (c : ℝ)*traceWeight m r

theorem category_law (m c : ℕ) (hm : 1 ≤ m) :
    categoryLaw m c = (c : ℝ)/(2*(m : ℝ)-1) :=
  (accepted_trace_sum m hm c).tsum_eq

/-- First accepted-proposal count for category 0 is m. -/
theorem first_category_count (m : ℕ) (hm : 1 ≤ m) :
    (∑ u ∈ Finset.range (2*m-1), if u<m then 1 else 0 : ℕ) = m := by
  have he : 2*m-1 = m+(m-1) := by omega
  rw [he,Finset.sum_range_add]
  have h1 : (∑ u ∈ Finset.range m, if u<m then 1 else 0 : ℕ) = m := by
    have hh : (∑ u ∈ Finset.range m, if u<m then 1 else 0 : ℕ) = ∑ _u ∈ Finset.range m, 1 := by
      apply Finset.sum_congr rfl
      intro u hu
      rw [if_pos (Finset.mem_range.mp hu)]
    simpa using hh
  have h2 : (∑ u ∈ Finset.range (m-1), if m+u<m then 1 else 0 : ℕ) = 0 := by
    apply Finset.sum_eq_zero
    intro u _
    rw [if_neg (by omega)]
  rw [h1,h2,Nat.add_zero]

/-- The accepted-first event and rejection-followed-by-first-category event are disjoint.
The factor 1/(2m) is the mass of the unique rejecting first proposal. -/
def coupledDisagreement (m : ℕ) : ℝ :=
  firstDisagreement m + (1/(2*(m : ℝ)))*categoryLaw m m

theorem exact_coupling_disagreement (t : ℕ) (ht : 0 < t) :
    coupledDisagreement (2*t) = (2*t : ℕ)/(2*(2*t : ℕ)-1 : ℝ) := by
  unfold coupledDisagreement
  rw [first_disagreement_half t ht, category_law _ _ (by omega)]
  have htR : (0 : ℝ) < t := by exact_mod_cast ht
  push_cast
  have ht1 : (1 : ℝ) ≤ t := by exact_mod_cast (Nat.one_le_of_lt ht)
  have hd : 2*(2*(t : ℝ))-1 ≠ 0 := by linarith
  field_simp [hd, ne_of_gt htR]
  ring

def binaryTV (p q : ℝ) : ℝ := (|p-q| + |(1-p)-(1-q)|)/2

theorem binary_total_variation (m : ℕ) (hm : 1 ≤ m) :
    binaryTV (1/2) (categoryLaw m m) = 1/(2*(2*(m : ℝ)-1)) := by
  rw [category_law m m hm]
  have hmR : (1 : ℝ) ≤ m := by exact_mod_cast hm
  have hd : 0 < 2*(m : ℝ)-1 := by linarith
  have hp : (1 : ℝ)/2 ≤ m/(2*(m : ℝ)-1) := by
    apply (le_div_iff₀ hd).2
    linarith
  unfold binaryTV
  rw [abs_of_nonpos (by linarith : (1 : ℝ)/2-m/(2*(m : ℝ)-1) ≤ 0),
    abs_of_nonneg (by linarith : 0 ≤ (1-(1 : ℝ)/2)-(1-m/(2*(m : ℝ)-1)))]
  field_simp
  ring

/-- Closed form isolates the accepted-first half and the rejection contribution. -/
theorem disagreement_decomposition (m : ℝ) (hm : 1 ≤ m) :
    m/(2*m-1) = 1/2+1/(2*(2*m-1)) := by
  have hd : 2*m-1 ≠ 0 := by linarith
  field_simp
  ring

#print axioms rejection_tail_zero
#print axioms accepted_trace_sum
#print axioms rejection_terminates_total_mass
#print axioms first_category_count
#print axioms exact_coupling_disagreement
#print axioms binary_total_variation
end
end Coupling
