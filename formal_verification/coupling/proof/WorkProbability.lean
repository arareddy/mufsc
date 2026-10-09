import Deletion
import PrefixEvent
import Rejection
namespace Coupling
noncomputable section
open scoped BigOperators

def beta (m : ℝ) : ℝ := (m-1)^2/(4*m*(2*m-1))

def oppositeProbability (m : ℕ) (bit : ℕ) : ℝ :=
  if bit=0 then categoryLaw m (m-1) else categoryLaw m m

theorem opposite_probability_lower (m : ℕ) (hm : 1 ≤ m) (bit : ℕ) :
    ((m : ℝ)-1)/(2*(m : ℝ)-1) ≤ oppositeProbability m bit := by
  have hmR : (1 : ℝ) ≤ m := by exact_mod_cast hm
  have hd : 0 < 2*(m : ℝ)-1 := by linarith
  unfold oppositeProbability
  split_ifs <;> rw [category_law _ _ hm]
  · simp [Nat.cast_sub hm]
  · apply (div_le_div_iff_of_pos_right hd).2
    linarith

/-- A wide first proposal fixes the old second low bit; the retained continuation is fresh.
The supplied bit function is arbitrary: the lower bound needs no uniformity of that bit. -/
def wideEventProbability (m : ℕ) (oldBit : ℕ → ℕ) : ℝ :=
  (∑ u ∈ Finset.range (4*m), if prefixEvent m u then oppositeProbability m (oldBit u) else 0) /
    (4*(m : ℝ))

def narrowEventProbability (m : ℕ) : ℝ := prefixProbability m * coupledDisagreement m

theorem prefix_probability_real (t : ℕ) (ht : 0 < t) :
    prefixProbability (2*t) = (((2*t : ℕ) : ℝ)-1)/(4*((2*t : ℕ) : ℝ)) := by
  rw [prefix_probability t ht]
  rw [Nat.cast_sub (by omega : 1 ≤ 2*t)]
  norm_num

theorem wide_event_lower (t : ℕ) (ht : 0 < t) (oldBit : ℕ → ℕ) :
    beta (2*t : ℕ) ≤ wideEventProbability (2*t) oldBit := by
  have hm : 1 ≤ 2*t := by omega
  have hmR : (1 : ℝ) ≤ (2*t : ℕ) := by exact_mod_cast hm
  have hd : 0 < 4*((2*t : ℕ) : ℝ) := by positivity
  let b : ℝ := (((2*t : ℕ) : ℝ)-1)/(2*((2*t : ℕ) : ℝ)-1)
  have hsum :
      (∑ u ∈ Finset.range (4*(2*t)), if prefixEvent (2*t) u then b else 0) ≤
      ∑ u ∈ Finset.range (4*(2*t)), if prefixEvent (2*t) u then oppositeProbability (2*t) (oldBit u) else 0 := by
    apply Finset.sum_le_sum
    intro u _
    split_ifs
    · exact opposite_probability_lower (2*t) hm (oldBit u)
    · rfl
  have he : (∑ u ∈ Finset.range (4*(2*t)), if prefixEvent (2*t) u then b else 0) =
      (((2*t : ℕ) : ℝ)-1)*b := by
    calc
      _ = (∑ u ∈ Finset.range (4*(2*t)), ((if prefixEvent (2*t) u then 1 else 0 : ℕ) : ℝ))*b := by
        rw [Finset.sum_mul]
        apply Finset.sum_congr rfl
        intro u _
        split_ifs <;> norm_num
      _ = _ := by
        rw [← Nat.cast_sum, prefix_event_count t ht, Nat.cast_sub hm]
        norm_num
  unfold wideEventProbability
  apply le_trans _ ((div_le_div_iff_of_pos_right hd).2 hsum)
  rw [he]
  unfold beta b
  have hn : 2*((2*t : ℕ) : ℝ)-1 ≠ 0 := by linarith
  apply le_of_eq
  field_simp
  ring

theorem narrow_event_lower (t : ℕ) (ht : 0 < t) :
    beta (2*t : ℕ) ≤ narrowEventProbability (2*t) := by
  have hmR : (1 : ℝ) ≤ (2*t : ℕ) := by exact_mod_cast (show 1 ≤ 2*t by omega)
  have hdp : 0 < 2*((2*t : ℕ) : ℝ)-1 := by linarith
  have hd : 0 < 4*((2*t : ℕ) : ℝ)*(2*((2*t : ℕ) : ℝ)-1) := by positivity
  unfold narrowEventProbability beta
  rw [prefix_probability_real t ht, exact_coupling_disagreement t ht]
  rw [div_mul_div_comm]
  apply (div_le_div_iff_of_pos_right hd).2
  nlinarith

theorem beta_gt_sixteenth (m : ℝ) (hm : 4 ≤ m) : 1/16 < beta m := by
  have hmp : 0 < m := by linarith
  have hdp : 0 < 2*m-1 := by linarith
  have hd : 0 < 4*m*(2*m-1) := by positivity
  unfold beta
  apply (lt_div_iff₀ hd).2
  nlinarith [sq_nonneg (m-4)]

theorem beta_times_failed (m : ℝ) (hm : 4 ≤ m) :
    beta m*(2*m-1) = (m-1)^2/(4*m) := by
  have h1 : m ≠ 0 := by linarith
  have h2 : 2*m-1 ≠ 0 := by linarith
  unfold beta
  field_simp
  ring

/-- A uniform linear constant valid for all m≥4 and n=3m. -/
theorem linear_work_constant (m : ℝ) (hm : 4 ≤ m) :
    (3*m)/32 ≤ (m-1)^2/(4*m) := by
  apply (le_div_iff₀ (by positivity : 0<4*m)).2
  nlinarith [sq_nonneg (m-4)]

/-- General finite weighted expectation bridge; no event-size assumption is hidden in the proof. -/
theorem expectation_event_lower {Ω : Type*} [Fintype Ω]
    (weight work : Ω → ℝ) (event : Ω → Prop) [DecidablePred event]
    (hw : ∀ x, 0 ≤ weight x) (hf : ∀ x, 0 ≤ work x)
    (c p : ℝ) (hc : 0 ≤ c)
    (he : ∀ x, event x → c ≤ work x)
    (hp : p ≤ ∑ x, if event x then weight x else 0) :
    p*c ≤ ∑ x, weight x*work x := by
  calc
    p*c ≤ (∑ x, if event x then weight x else 0)*c := mul_le_mul_of_nonneg_right hp hc
    _ = ∑ x, (if event x then weight x else 0)*c := Finset.sum_mul _ _ _
    _ ≤ _ := by
      apply Finset.sum_le_sum
      intro x _
      by_cases hx : event x
      · simp only [if_pos hx]
        exact mul_le_mul_of_nonneg_left (he x hx) (hw x)
      · simp only [if_neg hx,zero_mul]
        exact mul_nonneg (hw x) (hf x)

/-- Probabilistic bridge for any finite model with the established endpoint-flip event mass.
Its assumptions are the actual event mass and nonnegative point-work, not the expectation conclusion. -/
theorem obstruction_expectation {Ω : Type*} [Fintype Ω]
    (m : ℕ) (hm : 4 ≤ m) (weight F J : Ω → ℝ) (event : Ω → Prop) [DecidablePred event]
    (hw : ∀ x, 0 ≤ weight x) (hF : ∀ x, 0 ≤ F x) (hJ : ∀ x, 0 ≤ J x)
    (mass : beta m ≤ ∑ x, if event x then weight x else 0)
    (fail : ∀ x, event x → (2*(m : ℝ)-1) ≤ F x)
    (dup : ∀ x, event x → (2*(m : ℝ)-1) ≤ J x) :
    ((m : ℝ)-1)^2/(4*m) ≤ ∑ x, weight x*F x ∧
    ((m : ℝ)-1)^2/(4*m) ≤ ∑ x, weight x*J x := by
  have hmR : (4 : ℝ) ≤ m := by exact_mod_cast hm
  rw [← beta_times_failed m hmR]
  constructor
  · exact expectation_event_lower weight F event hw hF _ _ (by linarith) fail mass
  · exact expectation_event_lower weight J event hw hJ _ _ (by linarith) dup mass

#print axioms wide_event_lower
#print axioms narrow_event_lower
#print axioms beta_gt_sixteenth
#print axioms linear_work_constant
#print axioms obstruction_expectation
end
end Coupling
