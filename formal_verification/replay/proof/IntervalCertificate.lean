import Certificates

/-! Exact real-arithmetic justification of outward interval certificate logic.
The interval enclosure of actual floating point routines remains an executable
linkage obligation; this file does not infer enclosure from display floats. -/
namespace Replay

def intervalGap (aLo aHi bLo bHi : ℝ) : ℝ :=
  max 0 (max (aLo - bHi) (bLo - aHi))

theorem intervalGap_lower (a b aLo aHi bLo bHi : ℝ)
    (haLo : aLo ≤ a) (haHi : a ≤ aHi) (hbLo : bLo ≤ b) (hbHi : b ≤ bHi) :
    intervalGap aLo aHi bLo bHi ≤ |a - b| := by
  unfold intervalGap
  apply max_le (abs_nonneg _)
  apply max_le
  · have hab := le_abs_self (a - b)
    linarith
  · have hab := neg_le_abs (a - b)
    linarith

variable {P L : Type*} [PseudoMetricSpace P] [Fintype L] [DecidableEq L]

/-- Outward runner certificate, including interval overshoot and all other
competitors. Empty non-runner families have no additional test obligation. -/
theorem outward_runner_certificate
    (x : P) (old new : L → P) (j r : L) (d₂ : ℝ)
    (winnerHi secondLo secondHi runnerShiftLo : ℝ) (shiftHi : L → ℝ)
    (winnerBound : dist x (old j) ≤ winnerHi)
    (secondBounds : secondLo ≤ d₂ ∧ d₂ ≤ secondHi)
    (shiftBound : ∀ m, shift old new m ≤ shiftHi m)
    (runnerShiftBound : runnerShiftLo ≤ shift old new r)
    (runnerDistance : dist x (old r) = d₂)
    (cachedLower : ∀ m, m ≠ j → d₂ ≤ dist x (old m))
    (runnerPass : winnerHi + shiftHi j < intervalGap secondLo secondHi runnerShiftLo (shiftHi r))
    (otherPass : (nonRunners j r).Nonempty → winnerHi + shiftHi j <
      max 0 (secondLo - maxOn (nonRunners j r) shiftHi)) :
    ∀ m, m ≠ j → dist x (new j) < dist x (new m) := by
  intro m hm
  have hj : dist x (new j) ≤ winnerHi + shiftHi j := by
    have htri := dist_triangle x (old j) (new j)
    have hshift := shiftBound j
    unfold shift at hshift
    linarith
  by_cases hr : m = r
  · subst m
    have hg := intervalGap_lower d₂ (shift old new r) secondLo secondHi
      runnerShiftLo (shiftHi r) secondBounds.1 secondBounds.2 runnerShiftBound (shiftBound r)
    have hrev := reverse_triangle_shift x (old r) (new r)
    rw [runnerDistance] at hrev
    exact lt_of_le_of_lt hj (lt_of_lt_of_le runnerPass (hg.trans hrev))
  · have hmem : m ∈ nonRunners j r := by simp [nonRunners, competitors, hm, hr]
    have hmax := le_maxOn (nonRunners j r) shiftHi m hmem
    have hmtri := dist_triangle x (new m) (old m)
    rw [dist_comm (new m) (old m)] at hmtri
    have hc := cachedLower m hm
    have hs := shiftBound m
    unfold shift at hs
    have hl : max 0 (secondLo - maxOn (nonRunners j r) shiftHi) ≤ dist x (new m) := by
      apply max_le dist_nonneg
      have hd := secondBounds.1
      linarith
    exact lt_of_le_of_lt hj (lt_of_lt_of_le (otherPass ⟨m, hmem⟩) hl)

/-- The implemented basic test uses the nonnegative clipped lower bound. -/
theorem outward_basic_certificate (x : P) (old new : L → P) (j : L)
    (winnerHi secondLo : ℝ) (shiftHi : L → ℝ)
    (winnerBound : dist x (old j) ≤ winnerHi)
    (cachedLower : ∀ m, m ≠ j → secondLo ≤ dist x (old m))
    (shiftBound : ∀ m, shift old new m ≤ shiftHi m)
    (test : winnerHi + shiftHi j < max 0 (secondLo - maxOn (competitors j) shiftHi)) :
    ∀ m, m ≠ j → dist x (new j) < dist x (new m) := by
  intro m hm
  have hj : dist x (new j) ≤ winnerHi + shiftHi j := by
    have htri := dist_triangle x (old j) (new j)
    have hs := shiftBound j
    unfold shift at hs
    linarith
  have hmax := le_maxOn (competitors j) shiftHi m (by simp [competitors, hm])
  have hmtri := dist_triangle x (new m) (old m)
  rw [dist_comm (new m) (old m)] at hmtri
  have hc := cachedLower m hm
  have hs := shiftBound m
  unfold shift at hs
  have hl : max 0 (secondLo - maxOn (competitors j) shiftHi) ≤ dist x (new m) := by
    apply max_le dist_nonneg
    linarith
  exact lt_of_le_of_lt hj (lt_of_lt_of_le test hl)

#print axioms intervalGap_lower
#print axioms outward_runner_certificate
#print axioms outward_basic_certificate
end Replay
