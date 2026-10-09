import CertificateStrength
import Mathlib.Tactic.FieldSimp

/-! Conditional local-stability algebra and finite failure counting. Contractive
recurrence and empirical margin-density bounds are genuine hypotheses of the
paper's conditional result, not claimed consequences of the learner. No runtime
or bit-complexity theorem is asserted here. -/
namespace Replay
open scoped BigOperators

/-- prop:stable-replay perturbation bound, proved directly by an invariant.
The deletion fraction h can be r/n with n>0. -/
theorem stable_recurrence (δ : ℕ → ℝ) (q a₀ a h : ℝ)
    (hq₀ : 0 ≤ q) (hq₁ : q < 1) (ha₀ : 0 ≤ a₀) (ha : 0 ≤ a) (hh : 0 ≤ h)
    (initial : δ 0 ≤ a₀*h) (step : ∀ t, δ (t+1) ≤ q*δ t+a*h) :
    ∀ t, δ t ≤ (a₀+a/(1-q))*h := by
  have hd : 0 < 1-q := by linarith
  have hid : q*(a/(1-q))+a = a/(1-q) := by
    field_simp
    ring
  have hbound : q*(a₀+a/(1-q))+a ≤ a₀+a/(1-q) := by
    have hp := mul_nonneg ha₀ hd.le
    nlinarith [hid]
  intro t
  induction t with
  | zero =>
    have hx : 0 ≤ a/(1-q) := div_nonneg ha hd.le
    nlinarith [mul_nonneg hx hh]
  | succ t ih =>
    calc
      δ (t+1) ≤ q*δ t+a*h := step t
      _ ≤ q*((a₀+a/(1-q))*h)+a*h := add_le_add_right (mul_le_mul_of_nonneg_left ih hq₀) _
      _ = (q*(a₀+a/(1-q))+a)*h := by ring
      _ ≤ (a₀+a/(1-q))*h := mul_le_mul_of_nonneg_right hbound hh

theorem maxOn_bounded {L : Type*} (s : Finset L) (f : L → ℝ) (ε : ℝ)
    (hε : 0 ≤ ε) (bound : ∀ m ∈ s, f m ≤ ε) : maxOn s f ≤ ε := by
  by_cases hs : s.Nonempty
  · exact maxOn_le s f hs ε bound
  · simp [maxOn, hs, hε]

/-- Failure of the exact basic certificate implies a margin at most 2ε. -/
theorem basic_failure_margin {L : Type*} [Fintype L] [DecidableEq L]
    (j : L) (δ : L → ℝ) (d₁ d₂ ε : ℝ) (hε : 0 ≤ ε)
    (bound : ∀ m, δ m ≤ ε)
    (failure : ¬ (δ j + maxOn (competitors j) δ < d₂-d₁)) : d₂-d₁ ≤ 2*ε := by
  have hm := maxOn_bounded (competitors j) δ ε hε (fun m _ => bound m)
  have hj := bound j
  push_neg at failure
  linarith

/-- Finite margin-count consequence. n is the number of indexed records in R;
F may be any active survivor failure set, so deleted records need not be counted.
The density assumption is evaluated at the actual h=2ε. -/
theorem margin_failure_count {R : Type*} [Fintype R] [DecidableEq R]
    (F : Finset R) (gap : R → ℝ) (μ ε : ℝ)
    (failureGap : ∀ r ∈ F, gap r ≤ 2*ε)
    (density : ((Finset.univ.filter (fun r => gap r ≤ 2*ε)).card : ℝ) ≤
      μ * (Fintype.card R : ℝ) * (2*ε)) :
    (F.card : ℝ) ≤ min (Fintype.card R : ℝ) (2*μ*ε*(Fintype.card R : ℝ)) := by
  have hs : F ⊆ Finset.univ.filter (fun r => gap r ≤ 2*ε) := by
    intro r hr
    exact Finset.mem_filter.mpr ⟨Finset.mem_univ _, failureGap r hr⟩
  have hcard : (F.card : ℝ) ≤ ((Finset.univ.filter (fun r => gap r ≤ 2*ε)).card : ℝ) := by
    exact_mod_cast Finset.card_le_card hs
  have hn : (F.card : ℝ) ≤ (Fintype.card R : ℝ) := by
    exact_mod_cast Finset.card_le_univ F
  apply le_min hn
  nlinarith

/-- Explicit cancellation used by the local-stability failure bound. -/
theorem stable_failure_scale (n r μ B : ℝ) (hn : 0 < n) (hμ : 0 ≤ μ)
    (δ : ℝ) (bound : δ ≤ B*(r/n)) : 2*μ*δ*n ≤ 2*μ*B*r := by
  have h := mul_le_mul_of_nonneg_right (mul_le_mul_of_nonneg_left bound (by positivity : 0 ≤ 2*μ)) hn.le
  have he : 2*μ*(B*(r/n))*n = 2*μ*B*r := by
    field_simp
    ring
  rwa [he] at h

#print axioms stable_recurrence
#print axioms basic_failure_margin
#print axioms margin_failure_count
#print axioms stable_failure_scale
end Replay
