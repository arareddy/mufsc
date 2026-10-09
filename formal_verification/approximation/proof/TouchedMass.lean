import FiniteLaw
import Mathlib.Tactic.NormNum

namespace FTF
open scoped BigOperators
variable {I Ω C : Type*} [Fintype Ω] [Fintype C]

lemma expect_sum_on (p : Law Ω) (s : Finset I) (f : I → Ω → ℝ) :
    expect p (fun o => ∑ i ∈ s, f i o) = ∑ i ∈ s, expect p (f i) := by
  simp only [expect, Finset.mul_sum]
  exact Finset.sum_comm

noncomputable def deletedIndicator (d : Ω → I → Prop) (o : Ω) (i : I) : ℝ := by
  classical
  exact if d o i then 1 else 0

noncomputable def touchedIndicator (d : Ω → I → Prop) (s : Finset I) (o : Ω) : ℝ := by
  classical
  exact if ∃ i ∈ s, d o i then 1 else 0

omit [Fintype Ω] in
lemma deletedIndicator_nonneg (d : Ω → I → Prop) (o : Ω) (i : I) :
    0 ≤ deletedIndicator d o i := by
  classical
  unfold deletedIndicator
  split_ifs <;> norm_num

omit [Fintype Ω] in
lemma touch_le_indicators (d : Ω → I → Prop) (s : Finset I) (o : Ω) :
    touchedIndicator d s o ≤ ∑ i ∈ s, deletedIndicator d o i := by
  classical
  by_cases h : ∃ i ∈ s, d o i
  · obtain ⟨i,hi,hd⟩ := h
    have hh := Finset.single_le_sum (fun j _ => deletedIndicator_nonneg d o j) hi
    simpa [touchedIndicator, deletedIndicator, hd, show ∃ i ∈ s, d o i from ⟨i,hi,hd⟩] using hh
  · simp only [touchedIndicator, if_neg h]
    exact Finset.sum_nonneg fun i _ => deletedIndicator_nonneg d o i

/-- Union bound for an arbitrary finite deletion law with bounded marginals.
For a uniform r-subset, h=r/n; establishing that marginal is a separate bridge. -/
lemma touch_probability_bound (p : Law Ω) (d : Ω → I → Prop) (s : Finset I) (h : ℝ)
    (marginal : ∀ i ∈ s, expect p (fun o => deletedIndicator d o i) ≤ h) :
    expect p (touchedIndicator d s) ≤ (s.card : ℝ)*h := by
  calc
    expect p (touchedIndicator d s) ≤ expect p (fun o => ∑ i ∈ s, deletedIndicator d o i) :=
      expect_mono p (fun o => touch_le_indicators d s o)
    _ = ∑ i ∈ s, expect p (fun o => deletedIndicator d o i) := expect_sum_on p s _
    _ ≤ ∑ _i ∈ s, h := Finset.sum_le_sum marginal
    _ = _ := by simp

/-- Expected total touched population, retaining the finite probability model. -/
theorem expected_touched_mass (p : Law Ω) (d : Ω → I → Prop) (s : C → Finset I)
    (h : ℝ) (marginal : ∀ i, expect p (fun o => deletedIndicator d o i) ≤ h) :
    expect p (fun o => ∑ c, ((s c).card : ℝ)*touchedIndicator d (s c) o) ≤
      h*∑ c, ((s c).card : ℝ)^2 := by
  rw [expect_sum, Finset.mul_sum]
  apply Finset.sum_le_sum
  intro c _
  rw [expect_mul]
  have hc := mul_le_mul_of_nonneg_left (touch_probability_bound p d (s c) h (fun i _ => marginal i))
    (show 0 ≤ ((s c).card : ℝ) by positivity)
  nlinarith

lemma slice_square_bound (s : C → Finset I) (smax : ℝ) (h : ∀ c, ((s c).card : ℝ) ≤ smax) :
    (∑ c, ((s c).card : ℝ)^2) ≤ smax*∑ c, ((s c).card : ℝ) := by
  rw [Finset.mul_sum]
  apply Finset.sum_le_sum
  intro c _
  have hc := mul_le_mul_of_nonneg_left (h c) (show 0 ≤ ((s c).card : ℝ) by positivity)
  nlinarith

/-- The displayed r*smax consequence, conditional only on actual record marginals
and the slice partition's total cardinality. No hypergeometric identity assumed. -/
theorem expected_touched_mass_max (p : Law Ω) (d : Ω → I → Prop) (s : C → Finset I)
    (n r smax : ℝ) (hn : 0 < n) (hr : 0 ≤ r)
    (sizes : (∑ c, ((s c).card : ℝ))=n) (hs : ∀ c, ((s c).card : ℝ) ≤ smax)
    (marginal : ∀ i, expect p (fun o => deletedIndicator d o i) ≤ r/n) :
    expect p (fun o => ∑ c, ((s c).card : ℝ)*touchedIndicator d (s c) o) ≤ r*smax := by
  have h1 := expected_touched_mass p d s (r/n) marginal
  have h2 := mul_le_mul_of_nonneg_left (slice_square_bound s smax hs) (div_nonneg hr hn.le)
  rw [sizes] at h2
  have he : r/n*(smax*n)=r*smax := by field_simp; ring
  rw [he] at h2
  exact h1.trans h2
end FTF
