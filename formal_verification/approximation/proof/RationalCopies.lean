import FiniteLaw
import Mathlib.Data.Rat.Cast.Order
import Mathlib.Algebra.BigOperators.Group.Finset.Piecewise
import Mathlib.Tactic.NormNum

namespace FTF
open scoped BigOperators
variable {I : Type*} [Fintype I]

/-- Coincident copies retain distinct finite identities. -/
abbrev Copies (n : I → ℕ) := (i : I) × Fin (n i)

lemma copies_sum (n : I → ℕ) (f : I → ℝ) :
    (∑ c : Copies n, f c.1) = ∑ i, (n i : ℝ)*f i := by
  simp [Copies, Fintype.sum_sigma]

/-- Finite rational weights admit an actual positive integer copy scale. -/
lemma rational_copy_counts (w : I → ℚ) (hw : ∀ i, 0 ≤ w i) :
    ∃ M : ℕ, 0 < M ∧ ∃ n : I → ℕ, ∀ i, (n i : ℝ) = (M : ℝ)*(w i : ℝ) := by
  classical
  let M := ∏ i, (w i).den
  have hM : 0 < M := Nat.pos_of_ne_zero (Finset.prod_ne_zero_iff.mpr (fun i _ => (w i).den_ne_zero))
  have hd (i : I) : (w i).den ∣ M := Finset.dvd_prod_of_mem _ (Finset.mem_univ i)
  choose d hd using hd
  refine ⟨M, hM, fun i => d i * (w i).num.toNat, ?_⟩
  intro i
  have hn : ((w i).num.toNat : ℝ) = ((w i).num : ℝ) := by
    rw [← Int.cast_natCast, Int.toNat_of_nonneg (Rat.num_nonneg.mpr (hw i))]
  have hden : ((w i).den : ℝ) ≠ 0 := by exact_mod_cast (w i).den_ne_zero
  rw [Nat.cast_mul, hn, Rat.cast_def, hd i, Nat.cast_mul]
  field_simp
  ring

/-- All objectives of the coincident-copy instance scale by M. -/
lemma copies_objective (w : I → ℝ) (M : ℝ) (n : I → ℕ)
    (hscale : ∀ i, (n i : ℝ)=M*w i) (cost : I → ℝ) :
    (∑ c : Copies n, cost c.1) = M * ∑ i, w i*cost i := by
  rw [copies_sum, Finset.mul_sum]
  apply Finset.sum_congr rfl
  intro i _
  rw [hscale i]
  ring

/-- Summing equal-mass copies gives exactly the weighted categorical draw.
Use potential=1 for the first draw, distance² for every later D² draw. -/
lemma copies_category_probability (w potential : I → ℝ) (M : ℝ) (hM : M ≠ 0)
    (n : I → ℕ) (hscale : ∀ i, (n i : ℝ)=M*w i) (i : I) :
    (∑ _j : Fin (n i), potential i / (∑ c : Copies n, potential c.1)) =
      w i * potential i / (∑ j, w j * potential j) := by
  rw [copies_objective w M n hscale]
  simp only [Finset.sum_const, Finset.card_univ, Fintype.card_fin, nsmul_eq_mul]
  rw [hscale i]
  by_cases h : (∑ j, w j*potential j)=0
  · simp [h]
  · field_simp
    ring

/-- Cancel the same positive objective scale in an imported unweighted bound.
The outcome law is explicit; this does not postulate an expected-cost scalar. -/
lemma unweighted_to_weighted_bound {Ω : Type*} [Fintype Ω] (p : Law Ω)
    (w : I → ℝ) (M : ℝ) (hM : 0 < M) (n : I → ℕ)
    (hscale : ∀ i, (n i : ℝ)=M*w i) (cost : Ω → I → ℝ)
    (reference : I → ℝ) (α : ℝ)
    (makarychev_unweighted : expect p (fun o => ∑ c : Copies n, cost o c.1) ≤
      α*(∑ c : Copies n, reference c.1)) :
    expect p (fun o => ∑ i, w i*cost o i) ≤ α*∑ i, w i*reference i := by
  simp_rw [copies_objective w M n hscale] at makarychev_unweighted
  rw [expect_mul] at makarychev_unweighted
  nlinarith

end FTF

namespace FTF
open scoped BigOperators
variable {I T : Type*} [Fintype I]

lemma copies_draw_expectation (w potential f : I → ℝ) (M : ℝ) (hM : M ≠ 0)
    (n : I → ℕ) (hscale : ∀ i, (n i : ℝ)=M*w i) :
    (∑ c : Copies n, (potential c.1 / (∑ d : Copies n, potential d.1))*f c.1) =
      ∑ i, (w i*potential i/(∑ j, w j*potential j))*f i := by
  rw [Fintype.sum_sigma]
  apply Finset.sum_congr rfl
  intro i _
  change (∑ _j : Fin (n i), (potential i / (∑ d : Copies n, potential d.1))*f i) = _
  rw [← Finset.sum_mul, copies_category_probability w potential M hM n hscale i]

/-- Repeated ideal categorical draws on a finite state-dependent potential.
The zero-potential branch uses a common geometric completion operation. -/
noncomputable def weightedRun (w : I → ℝ) (potential : T → I → ℝ)
    (step : T → I → T) (complete : T → T) (test : T → ℝ) : ℕ → T → ℝ
  | 0, state => test state
  | t+1, state =>
      if (∑ i, w i*potential state i)=0 then weightedRun w potential step complete test t (complete state)
      else ∑ i, (w i*potential state i/(∑ j, w j*potential state j))*
        weightedRun w potential step complete test t (step state i)

noncomputable def copiesRun (n : I → ℕ) (potential : T → I → ℝ)
    (step : T → I → T) (complete : T → T) (test : T → ℝ) : ℕ → T → ℝ
  | 0, state => test state
  | t+1, state =>
      if (∑ c : Copies n, potential state c.1)=0 then copiesRun n potential step complete test t (complete state)
      else ∑ c : Copies n, (potential state c.1/(∑ d : Copies n, potential state d.1))*
        copiesRun n potential step complete test t (step state c.1)

/-- Coincident-copy reduction commutes with every finite number of adaptive draws,
for every terminal observable. The potential may be nearest squared distance to
all previously drawn locations, and the state may retain the entire history. -/
theorem copies_run_eq (w : I → ℝ) (M : ℝ) (hM : M ≠ 0) (n : I → ℕ)
    (hscale : ∀ i, (n i : ℝ)=M*w i) (potential : T → I → ℝ)
    (step : T → I → T) (complete : T → T) (test : T → ℝ) (t : ℕ) (state : T) :
    copiesRun n potential step complete test t state = weightedRun w potential step complete test t state := by
  induction t generalizing state with
  | zero => rfl
  | succ t ih =>
    simp only [copiesRun, weightedRun, copies_objective w M n hscale, mul_eq_zero, hM, false_or]
    split_ifs
    · exact ih _
    · simp_rw [ih]
      simpa only [copies_objective w M n hscale] using copies_draw_expectation w (potential state)
        (fun i => weightedRun w potential step complete test t (step state i)) M hM n hscale

end FTF

namespace FTF
open scoped BigOperators
variable {I T J : Type*} [Fintype I]

lemma weightedRun_scale (w : I → ℝ) (potential : T → I → ℝ)
    (step : T → I → T) (complete : T → T) (test : T → ℝ) (a : ℝ) (t : ℕ) (state : T) :
    weightedRun w potential step complete (fun s => a*test s) t state =
      a*weightedRun w potential step complete test t state := by
  induction t generalizing state with
  | zero => rfl
  | succ t ih =>
    simp only [weightedRun]
    split_ifs
    · exact ih _
    · simp_rw [ih]
      rw [Finset.mul_sum]
      apply Finset.sum_congr rfl
      intro i _
      ring

lemma weightedRun_sum [Fintype J] (w : I → ℝ) (potential : T → I → ℝ)
    (step : T → I → T) (complete : T → T) (test : J → T → ℝ) (t : ℕ) (state : T) :
    weightedRun w potential step complete (fun s => ∑ j, test j s) t state =
      ∑ j, weightedRun w potential step complete (test j) t state := by
  induction t generalizing state with
  | zero => rfl
  | succ t ih =>
    simp only [weightedRun]
    split_ifs
    · exact ih _
    · simp_rw [ih, Finset.mul_sum]
      exact Finset.sum_comm

lemma weightedRun_one (w : I → ℝ) (potential : T → I → ℝ)
    (step : T → I → T) (complete : T → T) (t : ℕ) (state : T) :
    weightedRun w potential step complete (fun _ => 1) t state = 1 := by
  induction t generalizing state with
  | zero => rfl
  | succ t ih =>
    simp only [weightedRun]
    split_ifs with hz
    · exact ih _
    · simp_rw [ih, mul_one]
      simp_rw [div_eq_mul_inv]
      rw [← Finset.sum_mul, mul_inv_cancel₀ hz]

lemma weightedRun_nonneg (w : I → ℝ) (hw : ∀ i, 0 ≤ w i) (potential : T → I → ℝ)
    (hp : ∀ s i, 0 ≤ potential s i) (step : T → I → T) (complete : T → T)
    (test : T → ℝ) (ht : ∀ s, 0 ≤ test s) (t : ℕ) (state : T) :
    0 ≤ weightedRun w potential step complete test t state := by
  induction t generalizing state with
  | zero => exact ht state
  | succ t ih =>
    simp only [weightedRun]
    split_ifs
    · exact ih _
    · apply Finset.sum_nonneg
      intro i _
      apply mul_nonneg _ (ih _)
      exact div_nonneg (mul_nonneg (hw i) (hp state i))
        (Finset.sum_nonneg fun j _ => mul_nonneg (hw j) (hp state j))

/-- A genuine finite terminal-state probability law for the adaptive categorical
recursion. D² states can encode the finite history of selected anchor identities. -/
noncomputable def weightedRunLaw [Fintype T] [DecidableEq T]
    (w : I → ℝ) (hw : ∀ i, 0 ≤ w i) (potential : T → I → ℝ)
    (hp : ∀ s i, 0 ≤ potential s i) (step : T → I → T) (complete : T → T)
    (t : ℕ) (state : T) : Law T where
  mass terminal := weightedRun w potential step complete (fun s => if s=terminal then 1 else 0) t state
  nonneg terminal := weightedRun_nonneg w hw potential hp step complete _
    (fun s => by split_ifs <;> norm_num) t state
  total := by
    rw [← weightedRun_sum]
    simpa using weightedRun_one w potential step complete t state

/-- The recursion is exactly expectation with respect to the constructed law. -/
lemma weightedRun_expect [Fintype T] [DecidableEq T]
    (w : I → ℝ) (hw : ∀ i, 0 ≤ w i) (potential : T → I → ℝ)
    (hp : ∀ s i, 0 ≤ potential s i) (step : T → I → T) (complete : T → T)
    (t : ℕ) (state : T) (test : T → ℝ) :
    expect (weightedRunLaw w hw potential hp step complete t state) test =
      weightedRun w potential step complete test t state := by
  unfold expect weightedRunLaw
  simp only
  have he (terminal : T) :
      weightedRun w potential step complete (fun s => if s=terminal then 1 else 0) t state*test terminal =
      weightedRun w potential step complete (fun s => test terminal*(if s=terminal then 1 else 0)) t state := by
    rw [weightedRun_scale]
    ring
  simp_rw [he]
  rw [← weightedRun_sum]
  simp [mul_ite]

end FTF
