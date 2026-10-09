import FiniteLaw
import Mathlib.Data.Real.Sqrt

namespace FTF
open scoped BigOperators
variable {I Ω : Type*} [Fintype I] [Fintype Ω]

def energy (w f : I → ℝ) : ℝ := ∑ i, w i * (f i)^2
noncomputable def root (w f : I → ℝ) : ℝ := Real.sqrt (energy w f)

lemma energy_nonneg (w f : I → ℝ) (hw : ∀ i, 0 ≤ w i) : 0 ≤ energy w f :=
  Finset.sum_nonneg fun i _ => mul_nonneg (hw i) (sq_nonneg _)

lemma root_nonneg (w f : I → ℝ) : 0 ≤ root w f := Real.sqrt_nonneg _

lemma root_sq (w f : I → ℝ) (hw : ∀ i, 0 ≤ w i) : (root w f)^2=energy w f :=
  Real.sq_sqrt (energy_nonneg w f hw)

lemma weighted_cauchy (w f g : I → ℝ) (hw : ∀ i, 0 ≤ w i) :
    (∑ i, w i * f i * g i) ≤ root w f * root w g := by
  have h := Real.sum_mul_le_sqrt_mul_sqrt Finset.univ
    (fun i => Real.sqrt (w i) * f i) (fun i => Real.sqrt (w i) * g i)
  have hcross : (∑ i, (Real.sqrt (w i)*f i)*(Real.sqrt (w i)*g i)) =
      ∑ i, w i*f i*g i := by
    apply Finset.sum_congr rfl
    intro i _
    calc
      _ = (Real.sqrt (w i))^2*f i*g i := by ring
      _ = _ := by rw [Real.sq_sqrt (hw i)]
  have hs (f : I → ℝ) : (∑ i, (Real.sqrt (w i)*f i)^2) = energy w f := by
    unfold energy
    apply Finset.sum_congr rfl
    intro i _
    rw [mul_pow, Real.sq_sqrt (hw i)]
  simpa only [hcross, hs, root] using h

/-- Weighted finite Minkowski, derived from Cauchy-Schwarz. -/
lemma root_add (w f g : I → ℝ) (hw : ∀ i, 0 ≤ w i) :
    root w (fun i => f i+g i) ≤ root w f + root w g := by
  have hx := weighted_cauchy w f g hw
  have he : energy w (fun i => f i+g i) = energy w f+energy w g+
      2*(∑ i, w i*f i*g i) := by
    simp only [energy, Finset.mul_sum, ← Finset.sum_add_distrib]
    apply Finset.sum_congr rfl
    intro i _
    ring
  apply (Real.sqrt_le_left (add_nonneg (root_nonneg _ _) (root_nonneg _ _))).2
  rw [he]
  nlinarith [root_sq w f hw, root_sq w g hw]

lemma root_mono (w f g : I → ℝ) (hw : ∀ i, 0 ≤ w i) (hf : ∀ i, 0 ≤ f i)
    (h : ∀ i, f i ≤ g i) : root w f ≤ root w g := by
  apply Real.sqrt_le_sqrt
  apply Finset.sum_le_sum
  intro i _
  apply mul_le_mul_of_nonneg_left _ (hw i)
  nlinarith [h i, hf i]

lemma root_scale (w f : I → ℝ) (a : ℝ) (ha : 0 ≤ a) :
    root w (fun i => a*f i) = a*root w f := by
  have he : energy w (fun i => a*f i) = a^2*energy w f := by
    simp only [energy, Finset.mul_sum]
    apply Finset.sum_congr rfl
    intro i _
    ring
  unfold root
  rw [he, Real.sqrt_mul (sq_nonneg _), Real.sqrt_sq ha]

lemma root_const (p : Law Ω) (c : ℝ) (hc : 0 ≤ c) :
    root p.mass (fun _ => c)=c := by
  simp only [root, energy, ← Finset.sum_mul, p.total, one_mul, Real.sqrt_sq hc]

lemma root_of_sqrt (p : Law Ω) (f : Ω → ℝ) (hf : ∀ o, 0 ≤ f o) :
    root p.mass (fun o => Real.sqrt (f o)) = Real.sqrt (expect p f) := by
  simp [root, energy, expect, Real.sq_sqrt, hf]

/-- Actual finite L2 expectation inequality, not an arbitrary-scalar surrogate. -/
lemma sqrt_expect_affine (p : Law Ω) (f g : Ω → ℝ) (hf : ∀ o, 0 ≤ f o)
    (hg : ∀ o, 0 ≤ g o) (a b : ℝ) (ha : 0 ≤ a) (hb : 0 ≤ b)
    (h : ∀ o, Real.sqrt (f o) ≤ a*Real.sqrt (g o)+b) :
    Real.sqrt (expect p f) ≤ a*Real.sqrt (expect p g)+b := by
  rw [← root_of_sqrt p f hf, ← root_of_sqrt p g hg]
  calc
    root p.mass (fun o => Real.sqrt (f o)) ≤
        root p.mass (fun o => a*Real.sqrt (g o)+b) :=
      root_mono _ _ _ p.nonneg (fun _ => Real.sqrt_nonneg _) h
    _ ≤ root p.mass (fun o => a*Real.sqrt (g o))+root p.mass (fun _ => b) :=
      root_add _ _ _ p.nonneg
    _ = a*root p.mass (fun o => Real.sqrt (g o))+b := by
      rw [root_scale _ _ _ ha, root_const p b hb]

lemma young (a b η : ℝ) (hη : 0 < η) :
    (a+b)^2 ≤ (1+η)*a^2+(1+1/η)*b^2 := by
  have h := sq_nonneg (η*a-b)
  have h' : 0 ≤ η*((1+η)*a^2+(1+1/η)*b^2-(a+b)^2) := by
    field_simp
    nlinarith
  nlinarith

end FTF

namespace FTF
open scoped BigOperators
variable {Ω : Type*} [Fintype Ω]
lemma sqrt_expect_two (p : Law Ω) (f g h : Ω → ℝ)
    (hf : ∀ o, 0 ≤ f o) (hg : ∀ o, 0 ≤ g o) (hh : ∀ o, 0 ≤ h o)
    (hle : ∀ o, Real.sqrt (f o) ≤ Real.sqrt (g o)+Real.sqrt (h o)) :
    Real.sqrt (expect p f) ≤ Real.sqrt (expect p g)+Real.sqrt (expect p h) := by
  rw [← root_of_sqrt p f hf, ← root_of_sqrt p g hg, ← root_of_sqrt p h hh]
  exact (root_mono _ _ _ p.nonneg (fun _ => Real.sqrt_nonneg _) hle).trans
    (root_add _ _ _ p.nonneg)
end FTF
