import Obstruction
namespace Coupling
noncomputable section
open scoped BigOperators

/-- The expectation bridge also applies to countably supported ideal trace laws.
Summability of bounded work follows from summability of the nonnegative probability weights. -/
theorem countable_expectation_event_lower {Ω : Type*}
    (weight work : Ω→ℝ) (event : Ω→Prop) [DecidablePred event]
    (hw : ∀ x,0≤weight x) (hs : Summable weight)
    (M : ℝ) (hf : ∀ x,0≤work x ∧ work x≤M)
    (c p : ℝ) (hc : 0≤c)
    (he : ∀ x,event x→c≤work x)
    (hp : p≤∑' x,if event x then weight x else 0) :
    p*c≤∑' x,weight x*work x := by
  have se : Summable (fun x => if event x then weight x else 0) := by
    apply Summable.of_nonneg_of_le _ _ hs
    · intro x;split_ifs <;> simp [hw]
    · intro x;split_ifs <;> simp [hw]
  have sf : Summable (fun x => weight x*work x) := by
    apply Summable.of_nonneg_of_le _ _ (hs.mul_right M)
    · intro x;exact mul_nonneg (hw x) (hf x).1
    · intro x;exact mul_le_mul_of_nonneg_left (hf x).2 (hw x)
  calc
    p*c ≤ (∑' x,if event x then weight x else 0)*c := mul_le_mul_of_nonneg_right hp hc
    _ = ∑' x,(if event x then weight x else 0)*c := (se.tsum_mul_right c).symm
    _ ≤ _ := by
      apply Summable.tsum_le_tsum _ (se.mul_right c) sf
      intro x
      by_cases hx : event x
      · simp only [if_pos hx]
        exact mul_le_mul_of_nonneg_left (he x hx) (hw x)
      · simp only [if_neg hx,zero_mul]
        exact mul_nonneg (hw x) (hf x).1

/-- Conditional expectation bound for the same event on an infinite trace space.
This does not assume the expected-work conclusion, but does require the joint event law. -/
theorem countable_law_expected_work {Ω : Type*}
    (h : ℕ) (hh : 2≤h) (v : Variant) (weight : Ω→ℝ)
    (event : Ω→Prop) [DecidablePred event] (work : Ω→ℝ)
    (hw : ∀ x,0≤weight x) (hs : Summable weight)
    (M : ℝ) (hf : ∀ x,0≤work x ∧ work x≤M)
    (mass : deletionEventProbability h ≤ ∑' x,if event x then weight x else 0)
    (on_event : ∀ x,event x→work x=(failures (2^h) v .neg : ℝ)) :
    (((2^h : ℕ) : ℝ)-1)^2/(4*(2^h : ℕ)) ≤ ∑' x,weight x*work x := by
  have hm := (power_parameter h hh).1
  have hmR : (4 : ℝ) ≤ (2^h : ℕ) := by exact_mod_cast hm
  have hc := (each_variant_event_counts (2^h) hm v).1
  have hn : 1≤2*(2^h) := by omega
  have hcr : 2*((2^h : ℕ) : ℝ)-1 ≤ (failures (2^h) v .neg : ℝ) := by exact_mod_cast hc
  rw [← beta_times_failed _ hmR]
  apply countable_expectation_event_lower weight work event hw hs M hf _ _ (by linarith)
  · intro x hx;rw [on_event x hx];exact hcr
  · exact le_trans (event_probability_lower h hh).1 mass

#print axioms countable_expectation_event_lower
#print axioms countable_law_expected_work
end
end Coupling
