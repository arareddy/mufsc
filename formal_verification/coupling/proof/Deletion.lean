import Coupling
namespace Coupling
noncomputable section
open scoped BigOperators

inductive Location | neg | pos | zero deriving DecidableEq

def coord : Location → ℝ
  | .neg => -1 | .pos => 1 | .zero => 0

/-- Persistent identities distinguish coincident records and clients. -/
abbrev Original (m : ℕ) := Fin m ⊕ (Fin m ⊕ Fin m)
abbrev Retained (m : ℕ) := Fin m ⊕ (Fin (m-1) ⊕ Fin m)

def location {m : ℕ} : Retained m → Location
  | .inl _ => .neg | .inr (.inl _) => .pos | .inr (.inr _) => .zero

def groupA {m : ℕ} (r : Retained m) : Bool :=
  match r with | .inl _ | .inr (.inl _) => true | .inr (.inr _) => false

/-- Keep the identity of every survivor; only client 1's final ID is omitted. -/
def retainID {m : ℕ} : Retained m → Original m
  | .inl i => .inl i
  | .inr (.inl i) => .inr (.inl ⟨i.val, lt_of_lt_of_le i.isLt (Nat.sub_le m 1)⟩)
  | .inr (.inr i) => .inr (.inr i)

theorem retainID_injective (m : ℕ) : Function.Injective (@retainID m) := by
  intro x y h
  cases x with
  | inl x =>
    cases y with
    | inl y => simpa [retainID] using h
    | inr y => cases y <;> simp_all [retainID]
  | inr x =>
    cases x <;> cases y with
    | inl y => simp_all [retainID]
    | inr y => cases y <;> simp_all [retainID, Fin.ext_iff]

def deletedID (m : ℕ) (hm : 0 < m) : Original m :=
  .inr (.inl ⟨m-1, by omega⟩)

theorem retained_exactly_not_deleted (m : ℕ) (hm : 0 < m) (x : Original m) :
    (∃ r : Retained m, retainID r = x) ↔ x ≠ deletedID m hm := by
  cases x with
  | inl i =>
    constructor
    · intro _; simp [deletedID]
    · intro _; exact ⟨.inl i, rfl⟩
  | inr x =>
    cases x with
    | inr i =>
      constructor
      · intro _; simp [deletedID]
      · intro _; exact ⟨.inr (.inr i), rfl⟩
    | inl i =>
      constructor
      · rintro ⟨r,hr⟩ he
        cases r with
        | inl _ => simp [retainID] at hr
        | inr r =>
          cases r with
          | inr _ => simp [retainID] at hr
          | inl j =>
            have hval : j.val = m-1 := by
              have hx := hr.trans he
              simpa [retainID, deletedID, Fin.ext_iff] using hx
            omega
      · intro hn
        have hi : i.val < m-1 := by
          have hh : i.val ≠ m-1 := by
            intro hv
            apply hn
            simp [deletedID, Fin.ext_iff, hv]
          have := i.isLt
          omega
        exact ⟨.inr (.inl ⟨i.val,hi⟩), by simp [retainID]⟩

theorem dataset_sizes (m : ℕ) (hm : 4 ≤ m) :
    Fintype.card (Original m) = 3*m ∧
    Fintype.card (Retained m) = 3*m-1 ∧
    (∑ r : Retained m, if groupA r then 1 else 0 : ℕ) = 2*m-1 ∧
    (∑ r : Retained m, if groupA r then 0 else 1 : ℕ) = m ∧
    3 ≤ m-1 := by
  simp only [Original, Retained, Fintype.card_sum, Fintype.card_fin, Fintype.sum_sum_type]
  simp [groupA]
  omega

/-- Two centers are indexed (0,e); distances decide ties in favor of slot 0. -/
def label (e x : Location) : ℕ := if |coord x| ≤ |coord x-coord e| then 0 else 1

def winnerDistance (e x : Location) : ℝ :=
  if label e x = 0 then |coord x| else |coord x-coord e|
def runnerDistance (e x : Location) : ℝ :=
  if label e x = 0 then |coord x-coord e| else |coord x|

def winnerShift (e x : Location) : ℝ := if label e x = 0 then 0 else 2
def runnerShift (e x : Location) : ℝ := if label e x = 0 then 2 else 0

def basicPass (e x : Location) : Prop :=
  winnerDistance e x + winnerShift e x < runnerDistance e x - runnerShift e x

def runnerPass (e x : Location) : Prop :=
  winnerDistance e x + winnerShift e x < |runnerDistance e x - runnerShift e x|

instance (e x : Location) : Decidable (basicPass e x) := Classical.propDecidable _
instance (e x : Location) : Decidable (runnerPass e x) := Classical.propDecidable _

/-- Every retained A identity changes indexed label under the endpoint flip. -/
theorem endpoint_labels (x : Location) :
    (label .neg x ≠ label .pos x ↔ x ≠ .zero) := by
  cases x <;> norm_num [label, coord] <;> decide

theorem ideal_certificate_decisions (e x : Location) (he : e ≠ .zero) :
    ¬basicPass e x ∧ (runnerPass e x ↔ x = .zero) := by
  cases e <;> cases x <;>
    norm_num [basicPass, runnerPass, winnerDistance, runnerDistance,
      winnerShift, runnerShift, label, coord] at * <;> decide

theorem sound_certificate_rejects_changed_label {R S : Type*}
    (oldLabel : R → ℕ) (assign : S → R → ℕ) (state : S)
    (keep accepted : R → Bool)
    (sound : ∀ r, keep r = true → accepted r = true → oldLabel r = assign state r)
    (r : R) (hk : keep r = true) (hc : oldLabel r ≠ assign state r) :
    accepted r = false := by
  cases ha : accepted r
  · rfl
  · exact False.elim (hc (sound r hk ha))

inductive Variant | basic | runner deriving DecidableEq

def passes (v : Variant) (e x : Location) : Prop :=
  match v with | .basic => basicPass e x | .runner => runnerPass e x
instance (v : Variant) (e x : Location) : Decidable (passes v e x) := Classical.propDecidable _

def failures (m : ℕ) (v : Variant) (e : Location) : ℕ :=
  ∑ r : Retained m, if passes v e (location r) then 0 else 1

theorem failure_counts (m : ℕ) (hm : 1 ≤ m) (e : Location) (he : e ≠ .zero) :
    failures m .basic e = 3*m-1 ∧ failures m .runner e = 2*m-1 := by
  simp only [failures, Retained, Fintype.sum_sum_type]
  simp only [passes, location]
  simp only [(ideal_certificate_decisions e .neg he).1,
    (ideal_certificate_decisions e .pos he).1,
    (ideal_certificate_decisions e .zero he).1, if_false,
    (ideal_certificate_decisions e .neg he).2,
    (ideal_certificate_decisions e .pos he).2,
    (ideal_certificate_decisions e .zero he).2]
  simp
  omega

/-- The policy is evaluated after the attempted round, using a strict majority. -/
def abandons (n f : ℕ) : Bool := decide (n < 2*f)
def saved (n f : ℕ) : ℕ := if abandons n f then 0 else n-f
def duplicated (n f : ℕ) : ℕ := if abandons n f then f else 0

theorem round_zero_policy (m : ℕ) (hm : 4 ≤ m) (e : Location) (he : e ≠ .zero) :
    abandons (3*m-1) (failures m .basic e) = true ∧
    abandons (3*m-1) (failures m .runner e) = true ∧
    saved (3*m-1) (failures m .basic e) = 0 ∧
    saved (3*m-1) (failures m .runner e) = 0 ∧
    duplicated (3*m-1) (failures m .basic e) = 3*m-1 ∧
    duplicated (3*m-1) (failures m .runner e) = 2*m-1 := by
  rw [(failure_counts m (by omega) e he).1, (failure_counts m (by omega) e he).2]
  have hb : 3*m-1 < 2*(3*m-1) := by omega
  have hr : 3*m-1 < 2*(2*m-1) := by omega
  simp [abandons, saved, duplicated, hb, hr]

def indexedCenter (e : Location) (i : Fin 2) : ℝ := if i=0 then 0 else coord e

theorem actual_indexed_shifts (i : Fin 2) :
    |indexedCenter .neg i-indexedCenter .pos i| = if i=0 then 0 else 2 := by
  fin_cases i <;> norm_num [indexedCenter,coord]

theorem unit_cached_margins (e x : Location) (he : e≠.zero) :
    runnerDistance e x-winnerDistance e x = 1 := by
  cases e <;> cases x <;>
    norm_num [runnerDistance,winnerDistance,label,coord] at *

theorem actual_changed_record_count (m : ℕ) (hm : 1≤m) :
    (∑ r : Retained m, if label .neg (location r) ≠ label .pos (location r) then 1 else 0 : ℕ) = 2*m-1 := by
  simp only [Retained,Fintype.sum_sum_type]
  norm_num [location,label,coord]
  omega

#print axioms actual_indexed_shifts
#print axioms unit_cached_margins
#print axioms actual_changed_record_count
#print axioms retainID_injective
#print axioms retained_exactly_not_deleted
#print axioms dataset_sizes
#print axioms endpoint_labels
#print axioms ideal_certificate_decisions
#print axioms sound_certificate_rejects_changed_label
#print axioms failure_counts
#print axioms round_zero_policy
end
end Coupling
