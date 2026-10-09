import Coupling
namespace Coupling
noncomputable section
open scoped BigOperators

/-- The exact first-proposal event used by prop:s2-deletion-work. -/
def prefixEvent (m u : ℕ) : Prop := 2*m-1 ≤ u ∧ u < 4*m-2 ∧ 2 ≤ u%4
instance (m u : ℕ) : Decidable (prefixEvent m u) := inferInstanceAs (Decidable (_ ∧ _ ∧ _))

def prefixCount (n : ℕ) : ℕ := ∑ u ∈ Finset.range n, if 2 ≤ u%4 then 1 else 0

theorem four_block_count (t : ℕ) : prefixCount (4*t) = 2*t := by
  induction t with
  | zero => simp [prefixCount]
  | succ t ih =>
    unfold prefixCount at *
    rw [show 4*(t+1) = (((4*t+1)+1)+1)+1 by omega]
    rw [Finset.sum_range_succ, Finset.sum_range_succ,
      Finset.sum_range_succ, Finset.sum_range_succ, ih]
    simp [Nat.add_mod]
    omega

theorem prefix_minus_one (t : ℕ) (ht : 0 < t) : prefixCount (4*t-1) = 2*t-1 := by
  have h := four_block_count t
  have he : 4*t = (4*t-1)+1 := by omega
  rw [he] at h
  unfold prefixCount at h
  rw [Finset.sum_range_succ] at h
  have hp : (4*t-1)%4=3 := by omega
  simp only [hp, show 2 ≤ 3 by omega, if_true] at h
  unfold prefixCount
  omega

theorem prefix_minus_two (t : ℕ) (ht : 0 < t) : prefixCount (4*t-2) = 2*t-2 := by
  have h := prefix_minus_one t ht
  have he : 4*t-1 = (4*t-2)+1 := by omega
  rw [he] at h
  unfold prefixCount at h
  rw [Finset.sum_range_succ] at h
  have hp : (4*t-2)%4=2 := by omega
  simp only [hp, le_refl, if_true] at h
  unfold prefixCount
  omega

theorem sum_cutoff (f : ℕ → ℕ) (k n : ℕ) (hk : k ≤ n) :
    (∑ u ∈ Finset.range n, if u < k then f u else 0) = ∑ u ∈ Finset.range k, f u := by
  obtain ⟨d,rfl⟩ := Nat.exists_eq_add_of_le hk
  rw [Finset.sum_range_add]
  have hfirst : (∑ u ∈ Finset.range k, if u<k then f u else 0) = ∑ u ∈ Finset.range k, f u := by
    apply Finset.sum_congr rfl
    intro u hu
    rw [if_pos (Finset.mem_range.mp hu)]
  have hlast : (∑ u ∈ Finset.range d, if k+u<k then f (k+u) else 0) = 0 := by
    apply Finset.sum_eq_zero
    intro u _
    rw [if_neg (by omega)]
  rw [hfirst,hlast,Nat.add_zero]

/-- Count over the entire actual proposal space, not an assumed event probability. -/
theorem prefix_event_count (t : ℕ) (ht : 0 < t) :
    (∑ u ∈ Finset.range (4*(2*t)), if prefixEvent (2*t) u then 1 else 0 : ℕ) = 2*t-1 := by
  have he :
      (∑ u ∈ Finset.range (8*t), if u < 4*t-1 then (if 2 ≤ u%4 then 1 else 0) else 0 : ℕ) +
      (∑ u ∈ Finset.range (8*t), if prefixEvent (2*t) u then 1 else 0 : ℕ) =
      ∑ u ∈ Finset.range (8*t), if u < 8*t-2 then (if 2 ≤ u%4 then 1 else 0) else 0 := by
    rw [← Finset.sum_add_distrib]
    apply Finset.sum_congr rfl
    intro u _
    unfold prefixEvent
    split_ifs <;> omega
  rw [sum_cutoff _ (4*t-1) (8*t) (by omega),
    sum_cutoff _ (8*t-2) (8*t) (by omega)] at he
  change prefixCount (4*t-1) + _ = prefixCount (8*t-2) at he
  rw [prefix_minus_one t ht] at he
  have hp := prefix_minus_two (2*t) (by omega)
  rw [show 4*(2*t)=8*t by omega] at hp
  rw [hp] at he
  rw [show 4*(2*t)=8*t by omega]
  omega

def oldFirstSlot (u : ℕ) : ℕ := if u%4=0 then 0 else if u%4=1 then 2 else 4

def newFirstSlot (m u : ℕ) : Option ℕ :=
  if u < 4*m-2 then some (if u<m then 0 else if u<2*m-1 then 2 else 4) else none

theorem prefix_common_zero_slot (m u : ℕ) (hm : 2 ≤ m) (he : prefixEvent m u) :
    oldFirstSlot u = 4 ∧ newFirstSlot m u = some 4 := by
  unfold prefixEvent at he
  have h0 : u%4 ≠ 0 := by omega
  have h1 : u%4 ≠ 1 := by omega
  have hm' : ¬u<m := by omega
  have h2 : ¬u<2*m-1 := by omega
  simp [oldFirstSlot,newFirstSlot,h0,h1,he.2.1,hm',h2]

def prefixProbability (m : ℕ) : ℝ :=
  (∑ u ∈ Finset.range (4*m), if prefixEvent m u then 1 else 0 : ℕ) / (4*(m : ℝ))

theorem prefix_probability (t : ℕ) (ht : 0 < t) :
    prefixProbability (2*t) = ((2*t : ℕ)-1 : ℕ)/(4*(2*t : ℕ) : ℝ) := by
  unfold prefixProbability
  rw [prefix_event_count t ht]

/-- Six ordered slots, retaining the three zero masses and using strict cumulative tests. -/
def sixSlotSelect (a b c u : ℕ) : Option ℕ :=
  if u<a then some 0 else if u<a+0 then some 1 else
  if u<a+0+b then some 2 else if u<a+0+b+0 then some 3 else
  if u<a+0+b+0+c then some 4 else if u<a+0+b+0+c+0 then some 5 else none

theorem retained_six_slot_mapping (m u : ℕ) (hm : 1≤m) :
    sixSlotSelect m (m-1) (2*m-1) u = newFirstSlot m u := by
  unfold sixSlotSelect newFirstSlot
  have h1 : m+(m-1)=2*m-1 := by omega
  have h2 : m+(m-1)+(2*m-1)=4*m-2 := by omega
  simp only [Nat.add_zero,h1,h2]
  split_ifs <;> simp_all <;> omega

theorem old_six_slot_mapping (u : ℕ) :
    sixSlotSelect 1 1 2 (u%4) = some (oldFirstSlot u) := by
  have hu := Nat.mod_lt u (by omega : 0<4)
  unfold sixSlotSelect oldFirstSlot
  split_ifs <;> simp_all <;> omega

#print axioms retained_six_slot_mapping
#print axioms old_six_slot_mapping
#print axioms prefix_event_count
#print axioms prefix_common_zero_slot
#print axioms prefix_probability
end
end Coupling
