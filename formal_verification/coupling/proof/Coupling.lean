import Mathlib.Data.Real.Archimedean
import Mathlib.Data.Fintype.BigOperators
import Mathlib.Algebra.BigOperators.Ring.Finset
import Mathlib.Tactic.Ring
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.FieldSimp
import Mathlib.Tactic.NormNum
import Mathlib.Tactic.Positivity
import Mathlib.Tactic.FinCases

open scoped BigOperators
namespace Coupling
noncomputable section

/-- Exact integer low-bit proposal; category 0 is the first category. -/
def oldCategory (u : ℕ) : ℕ := u % 2
def newProposal (m u : ℕ) : Option ℕ :=
  if u < 2*m-1 then some (if u < m then 0 else 1) else none

def acceptedMismatch (m u : ℕ) : ℕ :=
  if (u % 2 = 1 ∧ u < m) ∨ (u % 2 = 0 ∧ m ≤ u ∧ u < 2*m-1) then 1 else 0

theorem primitive_old (m : ℕ) (hm : 0 < m) :
    m / Nat.gcd m m = 1 := by simp [Nat.div_self hm]

theorem primitive_new (m : ℕ) (hm : 1 ≤ m) :
    Nat.gcd m (m-1) = 1 := by
  obtain ⟨k,rfl⟩ := Nat.exists_eq_add_of_le hm
  simp [Nat.add_comm, Nat.gcd_add_self_left]

theorem count_odd (t : ℕ) :
    (∑ u ∈ Finset.range (2*t), if u % 2 = 1 then 1 else 0 : ℕ) = t := by
  induction t with
  | zero => simp
  | succ t ih =>
    rw [show 2*(t+1) = (2*t+1)+1 by omega]
    rw [Finset.sum_range_succ, Finset.sum_range_succ, ih]
    simp [Nat.add_mod]

theorem count_even (t : ℕ) :
    (∑ u ∈ Finset.range (2*t), if u % 2 = 0 then 1 else 0 : ℕ) = t := by
  induction t with
  | zero => simp
  | succ t ih =>
    rw [show 2*(t+1) = (2*t+1)+1 by omega]
    rw [Finset.sum_range_succ, Finset.sum_range_succ, ih]
    simp [Nat.add_mod]

theorem accepted_mismatch_bridge (m u : ℕ) (hu : u < 2*m) :
    acceptedMismatch m u = 1 ↔
      ∃ c, newProposal m u = some c ∧ oldCategory u ≠ c := by
  have hp : u%2 < 2 := Nat.mod_lt u (by omega)
  simp only [acceptedMismatch, newProposal, oldCategory]
  split_ifs <;> simp_all <;> omega

/-- Exactly m of the 2m finite uniform proposals disagree and are accepted. -/
theorem accepted_mismatch_count (t : ℕ) :
    (∑ u ∈ Finset.range (2*(2*t)), acceptedMismatch (2*t) u) = 2*t := by
  rw [show 2*(2*t) = 2*t+2*t by omega, Finset.sum_range_add]
  have hlo : (∑ u ∈ Finset.range (2*t), acceptedMismatch (2*t) u) = t := by
    conv_rhs => rw [← count_odd t]
    apply Finset.sum_congr rfl
    intro u hu
    have hu' := Finset.mem_range.mp hu
    simp [acceptedMismatch, hu', show ¬2*t ≤ u by omega]
  have hhi : (∑ u ∈ Finset.range (2*t), acceptedMismatch (2*t) (2*t+u)) = t := by
    conv_rhs => rw [← count_even t]
    apply Finset.sum_congr rfl
    intro u hu
    have hu' := Finset.mem_range.mp hu
    have hp : u%2 < 2 := Nat.mod_lt u (by omega)
    have he : (2*t+u)%2 = u%2 := by omega
    by_cases h : u%2=0
    · have hb : 2*t+u < 2*(2*t)-1 := by omega
      simp [acceptedMismatch, he, h, hb, show 2*t ≤ 2*t+u by omega]
    · simp [acceptedMismatch, he, h, show ¬2*t+u < 2*t by omega]
  rw [hlo,hhi]; omega

/-- A finite uniform proposal probability, defined by actual counts. -/
def firstDisagreement (m : ℕ) : ℝ :=
  (∑ u ∈ Finset.range (2*m), acceptedMismatch m u : ℕ) / (2*(m : ℝ))

theorem first_disagreement_half (t : ℕ) (ht : 0 < t) :
    firstDisagreement (2*t) = 1/2 := by
  unfold firstDisagreement
  rw [accepted_mismatch_count]
  have htR : (t : ℝ) ≠ 0 := by exact_mod_cast (Nat.ne_of_gt ht)
  push_cast
  field_simp
  ring

/-- Only the final proposal rejects; its low bit is 1. -/
theorem rejection_shape (m u : ℕ) (hm : 0 < m) (hu : u < 2*m) :
    (newProposal m u = none ↔ u = 2*m-1) ∧
    (u = 2*m-1 → oldCategory u = 1) := by
  simp only [newProposal, oldCategory]
  constructor
  · split_ifs <;> simp_all <;> omega
  · intro h; omega

/-- Width h+1 covers precisely 2m proposals when m=2^h. -/
theorem proposal_width (h : ℕ) : 2*(2^h) = 2^(h+1) := by ring

theorem power_is_even (h : ℕ) (hh : 1 ≤ h) :
    ∃ t : ℕ, 0 < t ∧ 2^h = 2*t := by
  obtain ⟨j,rfl⟩ := Nat.exists_eq_add_of_le hh
  refine ⟨2^j, by positivity, ?_⟩
  simp [pow_add]

/-- Low bits of a least-significant-first assembled word agree with its first word. -/
theorem assembled_low_bit (first high : ℕ) :
    (first + 2^64*high)%2 = first%2 := by omega

/-- Uniform low-bit counts for any whole number of equally likely blocks. -/
theorem low_bits_count (b q c : ℕ) (hc : c < b) :
    (∑ u ∈ Finset.range (b*q), if u%b=c then 1 else 0 : ℕ) = q := by
  induction q with
  | zero => simp
  | succ q ih =>
    rw [Nat.mul_succ, Finset.sum_range_add, ih]
    have he : (∑ u ∈ Finset.range b, if (b*q+u)%b=c then 1 else 0 : ℕ) = 1 := by
      have hs : (∑ u ∈ Finset.range b, if (b*q+u)%b=c then 1 else 0 : ℕ) =
          ∑ u ∈ Finset.range b, if u=c then 1 else 0 := by
        apply Finset.sum_congr rfl
        intro u hu
        have hu' := Finset.mem_range.mp hu
        simp [Nat.add_mod, Nat.mod_eq_of_lt hu']
      rw [hs]
      simp [hc]
    rw [he]

theorem uniform_low_bits (b q c : ℕ) (hb : 0 < b) (hq : 0 < q) (hc : c < b) :
    ((∑ u ∈ Finset.range (b*q), if u%b=c then 1 else 0 : ℕ) : ℝ) /
      (b*q : ℕ) = 1/(b : ℝ) := by
  rw [low_bits_count b q c hc]
  have hbR : (b : ℝ) ≠ 0 := by exact_mod_cast (Nat.ne_of_gt hb)
  have hqR : (q : ℝ) ≠ 0 := by exact_mod_cast (Nat.ne_of_gt hq)
  push_cast
  field_simp
  ring

/-- Finite 64-bit words have exactly uniform low w bits, including w=0. -/
theorem word_low_bits_uniform (w c : ℕ) (hw : w ≤ 64) (hc : c < 2^w) :
    ((∑ u ∈ Finset.range (2^64), if u%(2^w)=c then 1 else 0 : ℕ) : ℝ) /
      (2^64 : ℕ) = 1/(2^w : ℕ) := by
  have he : 2^w*2^(64-w) = (2^64 : ℕ) := by rw [← pow_add, Nat.add_sub_of_le hw]
  rw [← he]
  exact uniform_low_bits _ _ _ (by positivity) (by positivity) hc

/-- Clearing a positive rational common multiplier produces a common positive integer scale.
Gcd reduction cancels every such integer scale. -/
theorem primitive_scaled_new (scale m : ℕ) (hs : 0<scale) (hm : 1≤m) :
    (scale*m)/Nat.gcd (scale*m) (scale*(m-1)) = m ∧
    (scale*(m-1))/Nat.gcd (scale*m) (scale*(m-1)) = m-1 := by
  rw [Nat.gcd_mul_left,primitive_new m hm,Nat.mul_one]
  exact ⟨Nat.mul_div_cancel_left m hs,Nat.mul_div_cancel_left (m-1) hs⟩

theorem primitive_scaled_old (scale m : ℕ) (hs : 0<scale) (hm : 0<m) :
    (scale*m)/Nat.gcd (scale*m) (scale*m) = 1 := by
  exact primitive_old _ (Nat.mul_pos hs hm)

#print axioms primitive_scaled_new
#print axioms primitive_scaled_old
#print axioms low_bits_count
#print axioms uniform_low_bits
#print axioms word_low_bits_uniform
#print axioms primitive_old
#print axioms primitive_new
#print axioms accepted_mismatch_count
#print axioms first_disagreement_half
#print axioms rejection_shape
#print axioms assembled_low_bit
end
end Coupling
