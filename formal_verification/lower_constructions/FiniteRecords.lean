import MatchedBudget
import Mathlib.Data.Fintype.BigOperators
import Mathlib.Algebra.BigOperators.Ring.Finset

/-! Explicit persistent identities: every record is a tagged finite index.
The tags distinguish groups, clients, and the two endpoint locations. -/
namespace MatchedBudget
open Loc
open scoped BigOperators

abbrev ClientZeroRecord (u v : ℕ) := Fin (2*u) ⊕ (Fin v ⊕ Fin v)
abbrev ClientOneRecord (u v : ℕ) := Fin (2*v) ⊕ Fin (2*u)
abbrev Record (u v : ℕ) := ClientZeroRecord u v ⊕ ClientOneRecord u v

def recordLoc {u v : ℕ} : ClientZeroRecord u v → Loc
  | .inl _ => zero
  | .inr (.inl _) => neg
  | .inr (.inr _) => pos

def balancedWeight {u v : ℕ} : ClientZeroRecord u v → ℚ
  | .inl _ => 1/(2*(u : ℚ))
  | .inr _ => 1/(2*(v : ℚ))

def groupA {u v : ℕ} : Record u v → Bool
  | .inl (.inl _) | .inr (.inl _) => true
  | _ => false

def allRecordLoc {u v : ℕ} : Record u v → Loc
  | .inl r => recordLoc r
  | .inr _ => zero

def groupSize (u v : ℕ) : ℕ := 2*(u+v)
def countEpsilon (u v : ℕ) : ℚ := (v : ℚ)/((u : ℚ)+v)
def countKappa (u v : ℕ) : ℚ := (u : ℚ)/v

theorem client_cardinalities (u v : ℕ) :
    Fintype.card (ClientZeroRecord u v) = groupSize u v ∧
    Fintype.card (ClientOneRecord u v) = groupSize u v ∧
    Fintype.card (Record u v) = 2*groupSize u v := by
  simp only [ClientZeroRecord, ClientOneRecord, Record, Fintype.card_sum,
    Fintype.card_fin, groupSize]
  constructor
  · omega
  constructor <;> omega

theorem group_cardinalities (u v : ℕ) :
    (∑ r : Record u v, if groupA r then 1 else 0 : ℕ) = groupSize u v ∧
    (∑ r : Record u v, if groupA r then 0 else 1 : ℕ) = groupSize u v := by
  simp only [Record, ClientZeroRecord, ClientOneRecord, Fintype.sum_sum_type]
  simp [groupA, groupSize]
  omega

/-- An exact pushforward identity valid for any function of a record's location. -/
theorem weighted_location_sum (u v : ℕ) (hu : 0 < u) (hv : 0 < v) (f : Loc → ℚ) :
    (∑ r : ClientZeroRecord u v, balancedWeight r * f (recordLoc r)) =
      sumLoc (fun x => localMass x * f x) := by
  have huq : (u : ℚ) ≠ 0 := by exact_mod_cast (Nat.ne_of_gt hu)
  have hvq : (v : ℚ) ≠ 0 := by exact_mod_cast (Nat.ne_of_gt hv)
  simp [ClientZeroRecord, Fintype.sum_sum_type, balancedWeight, recordLoc,
    sumLoc, localMass, nsmul_eq_mul]
  field_simp
  ring

/-- Location probability obtained by summing record masses and normalizing. -/
def recordFirst (u v : ℕ) (a : Loc) : ℚ :=
  (∑ r : ClientZeroRecord u v, balancedWeight r * (if recordLoc r = a then 1 else 0)) /
  (∑ r : ClientZeroRecord u v, balancedWeight r * 1)

def recordSecond (u v : ℕ) (a b : Loc) : ℚ :=
  (∑ r : ClientZeroRecord u v, balancedWeight r *
    (distSq (recordLoc r) a * if recordLoc r = b then 1 else 0)) /
  (∑ r : ClientZeroRecord u v, balancedWeight r * distSq (recordLoc r) a)

theorem record_first_law (u v : ℕ) (hu : 0 < u) (hv : 0 < v) (a : Loc) :
    recordFirst u v a = firstProb a := by
  unfold recordFirst
  rw [weighted_location_sum u v hu hv (fun x => if x = a then 1 else 0),
    weighted_location_sum u v hu hv (fun _ => 1)]
  cases a <;> norm_num [firstProb, sumLoc, localMass]

theorem record_second_law (u v : ℕ) (hu : 0 < u) (hv : 0 < v) (a b : Loc) :
    recordSecond u v a b = secondProb a b := by
  unfold recordSecond
  rw [weighted_location_sum u v hu hv (fun x => distSq x a * if x = b then 1 else 0),
    weighted_location_sum u v hu hv (fun x => distSq x a)]
  cases a <;> cases b <;> norm_num [secondProb, d2Mass, sumLoc, localMass, distSq, coord]

theorem record_pair_law (u v : ℕ) (hu : 0 < u) (hv : 0 < v) (a b : Loc) :
    recordFirst u v a * recordSecond u v a b = pairTable a b := by
  rw [record_first_law u v hu hv, record_second_law u v hu hv]
  exact pair_law a b

/-- The normalized full-record mass pushforward, independently of local sampling weights. -/
theorem global_location_sum (u v : ℕ) (hv : 0 < v) (f : Loc → ℚ) :
    (∑ r : ClientZeroRecord u v, f (recordLoc r)) / (groupSize u v : ℚ) =
      sumLoc (fun x => globalMass (countEpsilon u v) x * f x) := by
  have hvq : (0 : ℚ) < v := by exact_mod_cast hv
  have huq : (0 : ℚ) ≤ u := Nat.cast_nonneg u
  have hd : (u : ℚ)+v ≠ 0 := by linarith
  simp [ClientZeroRecord, Fintype.sum_sum_type, recordLoc, sumLoc, globalMass,
    countEpsilon, groupSize, nsmul_eq_mul]
  field_simp
  ring

/-- Integer record counts assigned to each indexed representative, by group. -/
def firstCountA (u : ℕ) (a b : Loc) : ℕ :=
  if firstWins a b zero then 2*u else 0

def firstCountB (v : ℕ) (a b : Loc) : ℕ :=
  (if firstWins a b neg then v else 0) + (if firstWins a b pos then v else 0)

def secondCountA (u : ℕ) (a b : Loc) : ℕ :=
  if firstWins a b zero then 0 else 2*u

def secondCountB (v : ℕ) (a b : Loc) : ℕ :=
  (if firstWins a b neg then 0 else v) + (if firstWins a b pos then 0 else v)

theorem indexed_endpoint_counts (u v : ℕ) :
    firstCountA u neg pos = 2*u ∧ firstCountB v neg pos = v ∧
    secondCountA u neg pos = 0 ∧ secondCountB v neg pos = v := by
  norm_num [firstCountA, firstCountB, secondCountA, secondCountB, firstWins, distSq, coord]

theorem normalized_count_transfer (u v : ℕ) (hv : 0 < v) (a b : Loc) :
    ((firstCountA u a b : ℚ) + firstCountB v a b) / groupSize u v =
      transferFirst (countEpsilon u v) a b ∧
    ((secondCountA u a b : ℚ) + secondCountB v a b) / groupSize u v =
      transferSecond (countEpsilon u v) a b := by
  have hvq : (0 : ℚ) < v := by exact_mod_cast hv
  have huq : (0 : ℚ) ≤ u := Nat.cast_nonneg u
  have hd : (u : ℚ)+v ≠ 0 := by linarith
  cases a <;> cases b <;>
    norm_num [firstCountA, firstCountB, secondCountA, secondCountB,
      transferFirst, transferSecond, firstWins, distSq, coord, sumLoc, globalMass,
      groupSize, countEpsilon] <;>
    field_simp <;> ring_nf <;> simp

/-- Ownership fractions give the parameter in the paper. -/
theorem count_parameters (u v : ℕ) (huv : v ≤ u) (hv : 0 < v) :
    1 ≤ countKappa u v ∧ countEpsilon u v = epsilon (countKappa u v) ∧
    (1-countEpsilon u v)/countEpsilon u v = countKappa u v := by
  have hvq : (0 : ℚ) < v := by exact_mod_cast hv
  have huvq : (v : ℚ) ≤ u := by exact_mod_cast huv
  have hd : (u : ℚ)+v ≠ 0 := by linarith
  constructor
  · unfold countKappa
    apply (le_div_iff₀ hvq).2
    simpa using huvq
  constructor
  · unfold countEpsilon epsilon countKappa
    field_simp
  · unfold countEpsilon countKappa
    field_simp

/-- Every rational parameter in the proposition has positive integer counts. -/
theorem rational_parameter_realizable (kappa : ℚ) (hk : 1 ≤ kappa) :
    ∃ u v : ℕ, 0 < v ∧ v ≤ u ∧ countKappa u v = kappa ∧
      countEpsilon u v = epsilon kappa := by
  have hn : 0 ≤ kappa.num := Rat.num_nonneg.mpr (by linarith)
  have hncast : (kappa.num.natAbs : ℚ) = (kappa.num : ℚ) := by
    have hi : (kappa.num.natAbs : ℤ) = kappa.num := Int.natAbs_of_nonneg hn
    have hh := congrArg (fun z : ℤ => (z : ℚ)) hi
    simpa only [Int.cast_natCast] using hh
  have heq : countKappa kappa.num.natAbs kappa.den = kappa := by
    unfold countKappa
    rw [hncast, Rat.num_div_den]
  have hd : (0 : ℚ) < kappa.den := by exact_mod_cast kappa.den_pos
  have hle : kappa.den ≤ kappa.num.natAbs := by
    have h := hk
    rw [← heq] at h
    unfold countKappa at h
    have h' := (le_div_iff₀ hd).mp h
    norm_num at h'
    exact_mod_cast h'
  exact ⟨kappa.num.natAbs, kappa.den, kappa.den_pos, hle, heq,
    by rw [(count_parameters _ _ hle kappa.den_pos).2.1, heq]⟩

def recordCostA (u v : ℕ) (c : ℚ) : ℚ :=
  (∑ r : Record u v, if groupA r then (coord (allRecordLoc r)-c)^2 else 0) /
    groupSize u v

def recordCostB (u v : ℕ) (c : ℚ) : ℚ :=
  (∑ r : Record u v, if groupA r then 0 else (coord (allRecordLoc r)-c)^2) /
    groupSize u v

/-- The location objectives really are the finite record group averages. -/
theorem record_group_costs (u v : ℕ) (hv : 0 < v) (c : ℚ) :
    recordCostA u v c = costA (countEpsilon u v) c ∧
    recordCostB u v c = costB (countEpsilon u v) c := by
  have hvq : (0 : ℚ) < v := by exact_mod_cast hv
  have huq : (0 : ℚ) ≤ u := Nat.cast_nonneg u
  have hd : (u : ℚ)+v ≠ 0 := by linarith
  simp only [recordCostA, recordCostB, Record, ClientZeroRecord, ClientOneRecord,
    Fintype.sum_sum_type]
  simp [groupA, allRecordLoc, recordLoc, coord, groupSize, countEpsilon,
    costA, costB, nsmul_eq_mul]
  constructor <;> field_simp <;> ring

def recordMeanA (u v : ℕ) : ℚ :=
  (∑ r : Record u v, if groupA r then coord (allRecordLoc r) else 0) / groupSize u v

def recordMeanB (u v : ℕ) : ℚ :=
  (∑ r : Record u v, if groupA r then 0 else coord (allRecordLoc r)) / groupSize u v

theorem record_means_zero (u v : ℕ) : recordMeanA u v = 0 ∧ recordMeanB u v = 0 := by
  simp only [recordMeanA, recordMeanB, Record, ClientZeroRecord, ClientOneRecord,
    Fintype.sum_sum_type]
  simp [groupA, allRecordLoc, recordLoc, coord, nsmul_eq_mul]

/-- On the sole cluster both normalized group masses are one. -/
def fairCandidate (u v : ℕ) (lam : ℚ) : ℚ :=
  (lam*recordMeanA u v + (1-lam)*recordMeanB u v) / (lam+(1-lam))

theorem every_fair_candidate_zero (u v : ℕ) (lam : ℚ) : fairCandidate u v lam = 0 := by
  simp [fairCandidate, (record_means_zero u v).1, (record_means_zero u v).2]

def guardedCandidate (u v : ℕ) (c lam : ℚ) : ℚ :=
  let candidate := fairCandidate u v lam
  if costPhi (countEpsilon u v) candidate ≤ costPhi (countEpsilon u v) c then
    candidate else c

/-- Any selected ideal candidate is zero and passes the objective guard.
The bisection implementation itself is not encoded here. -/
theorem guarded_fair_candidate_zero (u v : ℕ) (huv : v ≤ u) (hv : 0 < v)
    (c lam : ℚ) : guardedCandidate u v c lam = 0 := by
  have hp := count_parameters u v huv hv
  have he : 0 ≤ countEpsilon u v := by
    rw [hp.2.1]
    exact le_of_lt (epsilon_bounds _ hp.1).1
  unfold guardedCandidate
  rw [every_fair_candidate_zero]
  dsimp only
  have hopt := optimum_at_zero (countEpsilon u v) he
  rw [hopt.2.1, if_pos (hopt.2.2.2 c)]

/-- One uniformly sampled client-0 B record has the equal-endpoint law. -/
abbrev BRecord (v : ℕ) := Fin v ⊕ Fin v

def bRecordLoc {v : ℕ} : BRecord v → Loc
  | .inl _ => neg | .inr _ => pos

def splitRecordFirst (v : ℕ) (x : Loc) : ℚ :=
  (∑ r : BRecord v, if bRecordLoc r = x then (1 : ℚ) else 0) / (2*(v : ℚ))

theorem split_record_first_law (v : ℕ) (hv : 0 < v) (x : Loc) :
    splitRecordFirst v x = splitFirstMass x := by
  have hvq : (v : ℚ) ≠ 0 := by exact_mod_cast (Nat.ne_of_gt hv)
  unfold splitRecordFirst
  simp only [BRecord, Fintype.sum_sum_type]
  cases x <;> simp [bRecordLoc, splitFirstMass, nsmul_eq_mul] <;> field_simp <;> ring

theorem nonsaturated_budgets (u v : ℕ) (huv : v ≤ u) (hv : 0 < v) :
    2 ≤ 2*u ∧ 2 ≤ 2*v ∧ 2 < groupSize u v ∧
    min 2 (groupSize u v) = 2 ∧ min 1 (2*u) = 1 ∧ min 1 (2*v) = 1 := by
  dsimp [groupSize]
  omega

/-- The ordered tables have four slots, including coincident or zero-weight slots. -/
def orderedSlots : List Slot :=
  [Slot.c0first, Slot.c0second, Slot.c1first, Slot.c1second]

theorem four_slots : orderedSlots.length = 4 ∧ orderedSlots.Nodup ∧
    (∀ s : Slot, s ∈ orderedSlots) := by
  constructor
  · rfl
  constructor
  · decide
  · intro s; cases s <;> simp [orderedSlots]

/-- The paper's parameter range is realized without adding a domain axiom. -/
theorem finite_matched_witness (kappa : ℚ) (hk : 1 ≤ kappa) :
    ∃ u v : ℕ, 0 < v ∧ v ≤ u ∧ countKappa u v = kappa ∧
      countEpsilon u v = epsilon kappa ∧
      Fintype.card (ClientZeroRecord u v) = groupSize u v ∧
      Fintype.card (ClientOneRecord u v) = groupSize u v ∧
      (∀ a b, recordFirst u v a * recordSecond u v a b = pairTable a b) ∧
      (∀ c, recordCostA u v c = costA (epsilon kappa) c ∧
        recordCostB u v c = costB (epsilon kappa) c) ∧
      (∀ c lam, guardedCandidate u v c lam = 0) := by
  obtain ⟨u,v,hv,huv,hkappa,heps⟩ := rational_parameter_realizable kappa hk
  have hu : 0 < u := lt_of_lt_of_le hv huv
  refine ⟨u,v,hv,huv,hkappa,heps,(client_cardinalities u v).1,
    (client_cardinalities u v).2.1,?_,?_,?_⟩
  · exact record_pair_law u v hu hv
  · intro c
    rw [← heps]
    exact record_group_costs u v hv c
  · exact guarded_fair_candidate_zero u v huv hv

/-- The closed integer transfer formulas equal actual sums over distinct records. -/
theorem record_transfer_counts (u v : ℕ) (a b : Loc) :
    firstCountA u a b = (∑ r : ClientZeroRecord u v,
      if groupA (Sum.inl r) ∧ firstWins a b (recordLoc r) then 1 else 0 : ℕ) ∧
    firstCountB v a b = (∑ r : ClientZeroRecord u v,
      if ¬groupA (Sum.inl r) ∧ firstWins a b (recordLoc r) then 1 else 0 : ℕ) ∧
    secondCountA u a b = (∑ r : ClientZeroRecord u v,
      if groupA (Sum.inl r) ∧ ¬firstWins a b (recordLoc r) then 1 else 0 : ℕ) ∧
    secondCountB v a b = (∑ r : ClientZeroRecord u v,
      if ¬groupA (Sum.inl r) ∧ ¬firstWins a b (recordLoc r) then 1 else 0 : ℕ) := by
  simp only [ClientZeroRecord, Fintype.sum_sum_type]
  cases a <;> cases b <;>
    norm_num [groupA, recordLoc, firstCountA, firstCountB, secondCountA,
      secondCountB, firstWins, distSq, coord]

/-- Any deterministic identity completion on client 1 still sends zero locations. -/
theorem client_one_location (u v : ℕ) (r : ClientOneRecord u v) :
    allRecordLoc (Sum.inr r) = zero := rfl

def ownershipParameter (eps : ℚ) : ℚ := max ((1-eps)/eps) (eps/(1-eps))

theorem ownership_parameter (u v : ℕ) (huv : v ≤ u) (hv : 0 < v) :
    ownershipParameter (countEpsilon u v) = countKappa u v := by
  have hvq : (0 : ℚ) < v := by exact_mod_cast hv
  have huvq : (v : ℚ) ≤ u := by exact_mod_cast huv
  have huq : (0 : ℚ) < u := lt_of_lt_of_le hvq huvq
  have hd : (u : ℚ)+v ≠ 0 := by linarith
  have hr : countEpsilon u v / (1-countEpsilon u v) = (v : ℚ)/u := by
    unfold countEpsilon
    field_simp
  unfold ownershipParameter
  rw [(count_parameters u v huv hv).2.2, hr]
  apply max_eq_left
  unfold countKappa
  apply (div_le_div_iff₀ huq hvq).2
  nlinarith

theorem ownership_fractions (u v : ℕ) (hv : 0 < v) :
    (2*(u : ℚ))/groupSize u v = 1-countEpsilon u v ∧
    (2*(v : ℚ))/groupSize u v = countEpsilon u v := by
  have hvq : (0 : ℚ) < v := by exact_mod_cast hv
  have huq : (0 : ℚ) ≤ u := Nat.cast_nonneg u
  have hd : (u : ℚ)+v ≠ 0 := by linarith
  norm_num [groupSize, countEpsilon]
  constructor <;> field_simp <;> ring

/-- Server weights calculated directly from transferred integer group counts. -/
def recordSlotWeight (u v : ℕ) (a b : Loc) : Slot → ℚ
  | Slot.c0first => ((firstCountA u a b : ℚ)+firstCountB v a b)/groupSize u v
  | Slot.c0second => ((secondCountA u a b : ℚ)+secondCountB v a b)/groupSize u v
  | Slot.c1first => (2*(v : ℚ)+2*(u : ℚ))/groupSize u v
  | Slot.c1second => 0

theorem record_slot_weights (u v : ℕ) (hv : 0 < v) (a b : Loc) (s : Slot) :
    recordSlotWeight u v a b s = slotWeight (countEpsilon u v) a b s := by
  cases s with
  | c0first => exact (normalized_count_transfer u v hv a b).1
  | c0second => exact (normalized_count_transfer u v hv a b).2
  | c1first =>
    have hvq : (0 : ℚ) < v := by exact_mod_cast hv
    have huq : (0 : ℚ) ≤ u := Nat.cast_nonneg u
    have hd : (u : ℚ)+v ≠ 0 := by linarith
    simp only [recordSlotWeight, slotWeight, (client_one_weights (countEpsilon u v)).1]
    norm_num [groupSize]
    field_simp
    ring
  | c1second => simp [recordSlotWeight, slotWeight, (client_one_weights (countEpsilon u v)).2]

def recordMergedLaw (u v : ℕ) (x : Loc) : ℚ :=
  sumLoc (fun a => sumLoc (fun b => recordFirst u v a * recordSecond u v a b *
    (sumSlot (fun s => if slotLoc a b s = x then recordSlotWeight u v a b s else 0) /
      sumSlot (recordSlotWeight u v a b))))

theorem record_merged_law (u v : ℕ) (hu : 0 < u) (hv : 0 < v) (x : Loc) :
    recordMergedLaw u v x = mergedLaw (countEpsilon u v) x := by
  unfold recordMergedLaw mergedLaw serverProb pairLaw
  simp only [record_first_law u v hu hv, record_second_law u v hu hv,
    sumSlot, record_slot_weights u v hv]

def recordSplitWeight (u v : ℕ) : Slot → ℚ
  | Slot.c0first | Slot.c1second => 2*(u : ℚ)/groupSize u v
  | Slot.c0second | Slot.c1first => 2*(v : ℚ)/groupSize u v

theorem record_split_weights (u v : ℕ) (hv : 0 < v) (s : Slot) :
    recordSplitWeight u v s = splitSlotWeight (countEpsilon u v) s := by
  cases s <;> simp only [recordSplitWeight, splitSlotWeight,
    (ownership_fractions u v hv).1, (ownership_fractions u v hv).2]

def recordSplitLaw (u v : ℕ) (x : Loc) : ℚ :=
  sumLoc (fun b => splitRecordFirst v b *
    (sumSlot (fun s => if splitSlotLoc b s = x then recordSplitWeight u v s else 0) /
      sumSlot (recordSplitWeight u v)))

theorem record_split_law (u v : ℕ) (hv : 0 < v) (x : Loc) :
    recordSplitLaw u v x = splitLaw (countEpsilon u v) x := by
  unfold recordSplitLaw splitLaw splitServerProb
  simp only [split_record_first_law v hv, sumSlot, record_split_weights u v hv]

def recordG (u v : ℕ) (c : ℚ) : ℚ := recordCostA u v c + recordCostB u v c
def recordPhi (u v : ℕ) (c : ℚ) : ℚ := max (recordCostA u v c) (recordCostB u v c)

theorem record_objectives (u v : ℕ) (hv : 0 < v) :
    recordG u v = costG (countEpsilon u v) ∧
    recordPhi u v = costPhi (countEpsilon u v) := by
  constructor <;> funext c <;>
    simp only [recordG, recordPhi, costG, costPhi,
      (record_group_costs u v hv c).1, (record_group_costs u v hv c).2]

/-- End-to-end rational expectations use the explicit finite-record sampler and costs. -/
theorem finite_record_ratios (u v : ℕ) (huv : v ≤ u) (hv : 0 < v) :
    expected (recordMergedLaw u v) (recordG u v) / recordG u v 0 = (countKappa u v+5)/3 ∧
    expected (recordMergedLaw u v) (recordPhi u v) / recordPhi u v 0 = (countKappa u v+8)/6 ∧
    expected (recordSplitLaw u v) (recordG u v) / recordG u v 0 = 2 ∧
    expected (recordSplitLaw u v) (recordPhi u v) / recordPhi u v 0 = 3/2 := by
  have hp := count_parameters u v huv hv
  have hu := lt_of_lt_of_le hv huv
  have hm : recordMergedLaw u v = mergedLaw (countEpsilon u v) :=
    funext (record_merged_law u v hu hv)
  have hs : recordSplitLaw u v = splitLaw (countEpsilon u v) :=
    funext (record_split_law u v hv)
  rw [hm, hs, (record_objectives u v hv).1, (record_objectives u v hv).2, hp.2.1]
  exact matched_ratios _ hp.1

end MatchedBudget
