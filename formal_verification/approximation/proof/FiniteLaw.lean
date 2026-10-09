import Mathlib.Algebra.BigOperators.Ring.Finset
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Data.Real.Basic
import Mathlib.Data.Fintype.BigOperators
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.Ring
import Mathlib.Tactic.FieldSimp
import Mathlib.Tactic.Positivity

/-! Finite outcome laws. Conditional server laws may depend on the local outcome;
this is stronger than requiring one independent server stream. No expectation is
represented by a free scalar. -/
namespace FTF
open scoped BigOperators

structure Law (Ω : Type*) [Fintype Ω] where
  mass : Ω → ℝ
  nonneg : ∀ o, 0 ≤ mass o
  total : ∑ o, mass o = 1

variable {Ω I : Type*} [Fintype Ω] [Fintype I]

def expect (p : Law Ω) (f : Ω → ℝ) : ℝ := ∑ o, p.mass o * f o

lemma expect_nonneg (p : Law Ω) {f : Ω → ℝ} (h : ∀ o, 0 ≤ f o) :
    0 ≤ expect p f := Finset.sum_nonneg fun o _ => mul_nonneg (p.nonneg o) (h o)

lemma expect_mono (p : Law Ω) {f g : Ω → ℝ} (h : ∀ o, f o ≤ g o) :
    expect p f ≤ expect p g := Finset.sum_le_sum fun o _ => mul_le_mul_of_nonneg_left (h o) (p.nonneg o)

@[simp] lemma expect_const (p : Law Ω) (a : ℝ) : expect p (fun _ => a) = a := by
  simp [expect, ← Finset.sum_mul, p.total]

lemma expect_add (p : Law Ω) (f g : Ω → ℝ) :
    expect p (fun o => f o + g o) = expect p f + expect p g := by
  simp [expect, mul_add, Finset.sum_add_distrib]

lemma expect_mul (p : Law Ω) (a : ℝ) (f : Ω → ℝ) :
    expect p (fun o => a * f o) = a * expect p f := by
  simp [expect, ← Finset.mul_sum, mul_left_comm]

lemma expect_sum (p : Law Ω) (f : I → Ω → ℝ) :
    expect p (fun o => ∑ i, f i o) = ∑ i, expect p (f i) := by
  simp only [expect, Finset.mul_sum]
  exact Finset.sum_comm

/-- Finite conditional probability construction. -/
def joint {S : Type*} [Fintype S] (p : Law Ω) (q : Ω → Law S) : Law (Ω × S) where
  mass o := p.mass o.1 * (q o.1).mass o.2
  nonneg o := mul_nonneg (p.nonneg _) ((q _).nonneg _)
  total := by
    simp only [Fintype.sum_prod_type, ← Finset.mul_sum]
    simp [Law.total, p.total]

lemma tower {S : Type*} [Fintype S] (p : Law Ω) (q : Ω → Law S) (f : Ω → S → ℝ) :
    expect (joint p q) (fun o => f o.1 o.2) = expect p (fun o => expect (q o) (f o)) := by
  simp [expect, joint, Fintype.sum_prod_type, Finset.mul_sum, mul_assoc]

/-- Summing genuine per-slice literature bounds preserves the global factor. -/
lemma local_sum_bound (p : Law Ω) (weight : I → ℝ) (cost : I → Ω → ℝ)
    (reference : I → ℝ) (α : ℝ) (hw : ∀ i, 0 ≤ weight i)
    (mrs : ∀ i, expect p (cost i) ≤ α * reference i) :
    expect p (fun o => ∑ i, weight i * cost i o) ≤ α * ∑ i, weight i * reference i := by
  rw [expect_sum, Finset.mul_sum]
  apply Finset.sum_le_sum
  intro i _
  rw [expect_mul]
  nlinarith [mul_le_mul_of_nonneg_left (mrs i) (hw i)]

/-- The two local/global objective sandwiches are proved from nonnegative costs. -/
lemma weight_sandwich (a b A B : ℝ) (hA : 0 ≤ A) (hB : 0 ≤ B) :
    min a b * (A + B) ≤ a*A+b*B ∧ a*A+b*B ≤ max a b * (A+B) := by
  constructor
  · nlinarith [mul_le_mul_of_nonneg_right (min_le_left a b) hA,
      mul_le_mul_of_nonneg_right (min_le_right a b) hB]
  · nlinarith [mul_le_mul_of_nonneg_right (le_max_left a b) hA,
      mul_le_mul_of_nonneg_right (le_max_right a b) hB]

lemma max_weight_le_kappa (a b : ℝ) (ha : 0 < a) (hb : 0 < b) :
    max a b ≤ max (a/b) (b/a) * min a b := by
  by_cases hab : a ≤ b
  · rw [max_eq_right hab, min_eq_left hab]
    have h := mul_le_mul_of_nonneg_right (le_max_right (a/b) (b/a)) ha.le
    have e : b/a*a=b := by field_simp
    linarith
  · have hba : b ≤ a := le_of_not_ge hab
    rw [max_eq_left hba, min_eq_right hba]
    have h := mul_le_mul_of_nonneg_right (le_max_left (a/b) (b/a)) hb.le
    have e : a/b*b=a := by field_simp
    linarith

/-- Merged-client mismatch bound, using an actual finite sampling law. -/
lemma merged_client_bound (p : Law Ω) (a b α : ℝ) (ha : 0 < a) (hb : 0 < b)
    (hα : 0 ≤ α) (A B : Ω → ℝ) (hA : ∀ o, 0 ≤ A o) (hB : ∀ o, 0 ≤ B o)
    (A₀ B₀ : ℝ) (hA₀ : 0 ≤ A₀) (hB₀ : 0 ≤ B₀)
    (mrs : expect p (fun o => A o + B o) ≤ α * (A₀+B₀)) :
    expect p (fun o => a*A o+b*B o) ≤ α * max (a/b) (b/a) * (a*A₀+b*B₀) := by
  have hm : 0 ≤ max a b := le_trans ha.le (le_max_left _ _)
  have hk : 0 ≤ max (a/b) (b/a) := le_trans (div_nonneg ha.le hb.le) (le_max_left _ _)
  have h1 := expect_mono p (fun o => (weight_sandwich a b (A o) (B o) (hA o) (hB o)).2)
  rw [expect_mul] at h1
  have h2 := mul_le_mul_of_nonneg_left mrs hm
  have h3 := mul_le_mul_of_nonneg_right (max_weight_le_kappa a b ha hb) (mul_nonneg hα (add_nonneg hA₀ hB₀))
  have h4 := mul_le_mul_of_nonneg_left (weight_sandwich a b A₀ B₀ hA₀ hB₀).1 (mul_nonneg hα hk)
  nlinarith

end FTF
