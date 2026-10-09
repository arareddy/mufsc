import Nearest
import Mathlib.Topology.MetricSpace.Basic
import Mathlib.Data.Finset.Lattice.Fold
import Mathlib.Tactic.Linarith

/-! Assignment certificates for a finite indexed family in any pseudometric
space. The Euclidean specialization is immediate. All distances below are exact;
implemented outward-rounded intervals require a separate implementation audit. -/
namespace Replay

noncomputable def maxOn {L : Type*} (s : Finset L) (f : L → ℝ) : ℝ :=
  if h : s.Nonempty then s.sup' h f else 0

theorem le_maxOn {L : Type*} (s : Finset L) (f : L → ℝ) (m : L) (hm : m ∈ s) :
    f m ≤ maxOn s f := by
  simp only [maxOn, dif_pos (show s.Nonempty from ⟨m, hm⟩)]
  exact Finset.le_sup' f hm

variable {P L : Type*} [PseudoMetricSpace P]

def shift (old new : L → P) (m : L) : ℝ := dist (old m) (new m)

/-- The exact-norm overshoot bound follows from two triangle inequalities. -/
theorem reverse_triangle_shift (x a b : P) : |dist x a - dist a b| ≤ dist x b := by
  apply abs_le.mpr
  constructor
  · have h := dist_triangle a x b
    rw [dist_comm a x] at h
    linarith
  · have h := dist_triangle x b a
    rw [dist_comm b a] at h
    linarith

section Finite
variable [Fintype L] [DecidableEq L]

def competitors (j : L) : Finset L := Finset.univ.erase j

def nonRunners (j r : L) : Finset L := (competitors j).erase r

/-- Manuscript lem:basic-cert, eq:basic-cert. Empty competitor sets are harmless:
the strict unique-winner conclusion is then vacuous. -/
theorem basic_certificate (x : P) (old new : L → P) (j : L) (d₂ : ℝ)
    (cachedLower : ∀ m, m ≠ j → d₂ ≤ dist x (old m))
    (test : shift old new j + maxOn (competitors j) (shift old new) <
      d₂ - dist x (old j)) :
    ∀ m, m ≠ j → dist x (new j) < dist x (new m) := by
  intro m hm
  have hmax := le_maxOn (competitors j) (shift old new) m
    (by simp [competitors, hm])
  have hj := dist_triangle x (old j) (new j)
  have hmtri := dist_triangle x (new m) (old m)
  rw [dist_comm (new m) (old m)] at hmtri
  have hc := cachedLower m hm
  unfold shift at test hmax
  linarith

/-- Runner-up certificate with the infinity convention encoded by a conditional
obligation: when no non-runner exists, only the runner comparison is required. -/
def runnerTest (x : P) (old new : L → P) (j r : L) (d₂ : ℝ) : Prop :=
  dist x (old j) + shift old new j < |d₂ - shift old new r| ∧
  ((nonRunners j r).Nonempty →
    dist x (old j) + shift old new j <
      max 0 (d₂ - maxOn (nonRunners j r) (shift old new)))

/-- Manuscript eq:runner-cert: full soundness, including exact-norm overshoot. -/
theorem runner_certificate (x : P) (old new : L → P) (j r : L) (d₂ : ℝ)
    (runnerDistance : dist x (old r) = d₂)
    (cachedLower : ∀ m, m ≠ j → d₂ ≤ dist x (old m))
    (test : runnerTest x old new j r d₂) :
    ∀ m, m ≠ j → dist x (new j) < dist x (new m) := by
  intro m hm
  have hj := dist_triangle x (old j) (new j)
  change dist x (new j) ≤ dist x (old j) + shift old new j at hj
  by_cases hr : m = r
  · subst m
    have hrev := reverse_triangle_shift x (old r) (new r)
    rw [runnerDistance] at hrev
    exact lt_of_le_of_lt hj (lt_of_lt_of_le test.1 hrev)
  · have hmem : m ∈ nonRunners j r := by simp [nonRunners, competitors, hm, hr]
    have hmax := le_maxOn (nonRunners j r) (shift old new) m hmem
    have hmtri := dist_triangle x (new m) (old m)
    rw [dist_comm (new m) (old m)] at hmtri
    have hc := cachedLower m hm
    have hlo : max 0 (d₂ - maxOn (nonRunners j r) (shift old new)) ≤
        dist x (new m) := by
      apply max_le (dist_nonneg)
      unfold shift at hmax ⊢
      linarith
    exact lt_of_le_of_lt hj (lt_of_lt_of_le (test.2 ⟨m, hmem⟩) hlo)

omit [Fintype L] [DecidableEq L] in
/-- Any outward-bound implementation is sound if it produces genuinely enclosing
bounds. Ambiguous bounds cannot satisfy this strict test. -/
theorem outward_bounds_sound (x : P) (new : L → P) (j : L)
    (upper : ℝ) (lower : L → ℝ)
    (hu : dist x (new j) ≤ upper)
    (hl : ∀ m, m ≠ j → lower m ≤ dist x (new m))
    (test : ∀ m, m ≠ j → upper < lower m) :
    ∀ m, m ≠ j → dist x (new j) < dist x (new m) := by
  intro m hm
  exact lt_of_le_of_lt hu (lt_of_lt_of_le (test m hm) (hl m hm))
end Finite

section Labels
variable [Fintype L] [LinearOrder L] [Nonempty L]

theorem basic_certified_label (x : P) (old new : L → P) (j : L) (d₂ : ℝ)
    (cachedLower : ∀ m, m ≠ j → d₂ ≤ dist x (old m))
    (test : shift old new j + maxOn (competitors j) (shift old new) <
      d₂ - dist x (old j)) : nearest (fun m => dist x (new m)) = j := by
  apply strict_winner_nearest
  exact basic_certificate x old new j d₂ cachedLower test

theorem runner_certified_label (x : P) (old new : L → P) (j r : L) (d₂ : ℝ)
    (runnerDistance : dist x (old r) = d₂)
    (cachedLower : ∀ m, m ≠ j → d₂ ≤ dist x (old m))
    (test : runnerTest x old new j r d₂) : nearest (fun m => dist x (new m)) = j := by
  apply strict_winner_nearest
  exact runner_certificate x old new j r d₂ runnerDistance cachedLower test
end Labels

#print axioms reverse_triangle_shift
#print axioms basic_certificate
#print axioms runner_certificate
#print axioms outward_bounds_sound
#print axioms basic_certified_label
#print axioms runner_certified_label
end Replay
