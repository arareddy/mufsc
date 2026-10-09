import Obstruction
namespace Coupling
noncomputable section
open scoped BigOperators

def narrowJointCount (m r : ℕ) : ℕ :=
  ∑ u ∈ Finset.range (4*m), ∑ v ∈ Finset.range (2*m-1),
    if prefixEvent m u ∧ traceOldCategory m r v ≠ category m v then 1 else 0

theorem narrow_joint_count (t r : ℕ) (ht : 0<t) :
    narrowJointCount (2*t) r = (2*t-1)*(2*t) := by
  unfold narrowJointCount
  have he :
      (∑ u ∈ Finset.range (4*(2*t)), ∑ v ∈ Finset.range (2*(2*t)-1),
        if prefixEvent (2*t) u ∧ traceOldCategory (2*t) r v ≠ category (2*t) v then 1 else 0 : ℕ) =
      ∑ u ∈ Finset.range (4*(2*t)), (if prefixEvent (2*t) u then 1 else 0)*traceMismatchCount (2*t) r := by
    apply Finset.sum_congr rfl
    intro u _
    by_cases hu : prefixEvent (2*t) u
    · simp only [hu,true_and,if_true,one_mul,traceMismatchCount]
    · simp [hu]
  rw [he,← Finset.sum_mul,prefix_event_count t ht,trace_mismatch_count t r ht]

/-- The narrow event law is the sum of actual finite first-block / successful-tail pairs. -/
theorem narrow_joint_trace_mass (t : ℕ) (ht : 0<t) :
    HasSum (fun r => ((narrowJointCount (2*t) r : ℝ)/(4*(2*t : ℕ)))*traceWeight (2*t) r)
      (narrowEventProbability (2*t)) := by
  simp_rw [narrow_joint_count t _ ht]
  have hm : 1≤2*t := by omega
  have hs := accepted_trace_sum (2*t) hm (((2*t-1)*(2*t) : ℕ)/(4*(2*t : ℕ)) : ℝ)
  convert hs using 1
  unfold narrowEventProbability
  rw [prefix_probability_real t ht,exact_coupling_disagreement t ht]
  simp only [Nat.cast_mul,Nat.cast_sub hm,Nat.cast_one,Nat.cast_ofNat]
  ring

/-- Count of accepted proposals in the second category. -/
theorem second_category_count (m : ℕ) (hm : 1≤m) :
    (∑ u ∈ Finset.range (2*m-1), if u<m then 0 else 1 : ℕ) = m-1 := by
  have he :
      (∑ u ∈ Finset.range (2*m-1), if u<m then 1 else 0 : ℕ) +
      (∑ u ∈ Finset.range (2*m-1), if u<m then 0 else 1 : ℕ) = 2*m-1 := by
    rw [← Finset.sum_add_distrib]
    have hz : (∑ u ∈ Finset.range (2*m-1), ((if u<m then 1 else 0)+(if u<m then 0 else 1)) : ℕ) =
        ∑ _u ∈ Finset.range (2*m-1), 1 := by
      apply Finset.sum_congr rfl
      intro u _
      split_ifs <;> omega
    simpa using hz
  rw [first_category_count m hm] at he
  omega

def wideOppositeCount (m bit : ℕ) : ℕ :=
  ∑ v ∈ Finset.range (2*m-1), if (if bit=0 then 0 else 1) ≠ category m v then 1 else 0

theorem wide_opposite_count (m bit : ℕ) (hm : 1≤m) :
    wideOppositeCount m bit = if bit=0 then m-1 else m := by
  unfold wideOppositeCount
  by_cases hb : bit=0
  · simp only [hb,if_true,category]
    have he : (∑ v ∈ Finset.range (2*m-1), if 0 ≠ (if v<m then 0 else 1) then 1 else 0 : ℕ) =
        ∑ v ∈ Finset.range (2*m-1), if v<m then 0 else 1 := by
      apply Finset.sum_congr rfl
      intro v _
      split_ifs <;> norm_num at *
    rw [he,second_category_count m hm]
  · simp only [hb,if_false,category]
    have he : (∑ v ∈ Finset.range (2*m-1), if 1 ≠ (if v<m then 0 else 1) then 1 else 0 : ℕ) =
        ∑ v ∈ Finset.range (2*m-1), if v<m then 1 else 0 := by
      apply Finset.sum_congr rfl
      intro v _
      split_ifs <;> norm_num at *
    rw [he,first_category_count m hm]

theorem wide_opposite_trace_mass (m bit : ℕ) (hm : 1≤m) :
    HasSum (fun r => (wideOppositeCount m bit : ℝ)*traceWeight m r) (oppositeProbability m bit) := by
  rw [wide_opposite_count m bit hm]
  unfold oppositeProbability
  split_ifs <;> rw [category_law m _ hm] <;> exact accepted_trace_sum m hm _

/-- Normalization of the local first-block / accepted-tail product law.
This law contains all finite successful tail traces, with unbounded rejection count. -/
theorem local_product_trace_normalized (m : ℕ) (hm : 1≤m) :
    HasSum (fun r => ((4*(m : ℝ)*(2*m-1))/(4*m))*traceWeight m r) 1 := by
  have hmR : (1 : ℝ) ≤ m := by exact_mod_cast hm
  have hm0 : (m : ℝ) ≠ 0 := by linarith
  have he : 4*(m : ℝ)*(2*m-1)/(4*m) = 2*m-1 := by field_simp
  simp only [he]
  exact rejection_terminates_total_mass m hm

def wideJointCount (m : ℕ) (oldBit : ℕ→ℕ) : ℕ :=
  ∑ u ∈ Finset.range (4*m), if prefixEvent m u then wideOppositeCount m (oldBit u) else 0

/-- Wide-width event law, with all first-block values and all tail rejection counts included. -/
theorem wide_joint_trace_mass (m : ℕ) (hm : 1≤m) (oldBit : ℕ→ℕ) :
    HasSum (fun r => ((wideJointCount m oldBit : ℝ)/(4*m))*traceWeight m r)
      (wideEventProbability m oldBit) := by
  have hs : ∀ u∈Finset.range (4*m),
      HasSum (fun r => if prefixEvent m u then (wideOppositeCount m (oldBit u) : ℝ)*traceWeight m r else 0)
        (if prefixEvent m u then oppositeProbability m (oldBit u) else 0) := by
    intro u _
    by_cases he : prefixEvent m u
    · simp only [if_pos he];exact wide_opposite_trace_mass m (oldBit u) hm
    · simp only [if_neg he];exact hasSum_zero
  have hh := (hasSum_sum hs).div_const (4*(m : ℝ))
  convert hh using 1
  funext r
  simp only [wideJointCount,Nat.cast_sum,Nat.cast_ite,Nat.cast_zero]
  have he : ∀ u, (if prefixEvent m u then (wideOppositeCount m (oldBit u) : ℝ)*traceWeight m r else 0) =
      (if prefixEvent m u then (wideOppositeCount m (oldBit u) : ℝ) else 0)*traceWeight m r := by
    intro u
    split_ifs <;> simp
  simp_rw [he]
  rw [← Finset.sum_mul]
  ring

#print axioms wide_joint_trace_mass
#print axioms narrow_joint_count
#print axioms narrow_joint_trace_mass
#print axioms wide_opposite_count
#print axioms wide_opposite_trace_mass
#print axioms local_product_trace_normalized
end
end Coupling
