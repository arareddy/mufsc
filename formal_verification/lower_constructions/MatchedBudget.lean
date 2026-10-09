import Mathlib.Data.Real.Basic
import Mathlib.Data.Rat.Cast.Order
import Mathlib.Tactic.Ring
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.FieldSimp
import Mathlib.Tactic.NormNum
import Mathlib.Tactic.Positivity

/-! A finite location-level model of the matched-slot witness. All sampling laws
are defined by normalization of masses, not by the desired final probabilities.
Persistent record identities and the implementation's random-bit interface are
outside this module. -/
namespace MatchedBudget

inductive Loc where
  | zero | neg | pos
  deriving DecidableEq, Repr
open Loc
@[simp] theorem zero_ne_neg : (zero : Loc) ≠ neg := by decide
@[simp] theorem zero_ne_pos : (zero : Loc) ≠ pos := by decide
@[simp] theorem neg_ne_zero : (neg : Loc) ≠ zero := by decide
@[simp] theorem pos_ne_zero : (pos : Loc) ≠ zero := by decide
@[simp] theorem neg_ne_pos : (neg : Loc) ≠ pos := by decide
@[simp] theorem pos_ne_neg : (pos : Loc) ≠ neg := by decide

def coord : Loc → ℚ
  | zero => 0 | neg => -1 | pos => 1

def sumLoc (f : Loc → ℚ) : ℚ := f zero + f neg + f pos

def distSq (x y : Loc) : ℚ := (coord x - coord y)^2

/-- Client 0's aggregate locally group-balanced masses. -/
def localMass : Loc → ℚ
  | zero => 1 | neg => 1/2 | pos => 1/2

def firstProb (a : Loc) : ℚ := localMass a / sumLoc localMass

def d2Mass (a b : Loc) : ℚ := localMass b * distSq b a

def secondProb (a b : Loc) : ℚ := d2Mass a b / sumLoc (d2Mass a)

def pairLaw (a b : Loc) : ℚ := firstProb a * secondProb a b

def pairTable : Loc → Loc → ℚ
  | zero, neg | zero, pos => 1/4
  | neg, zero | pos, zero => 1/12
  | neg, pos | pos, neg => 1/6
  | _, _ => 0

/-- The six probabilities are derived from the weighted squared-distance rule. -/
theorem pair_law (a b : Loc) : pairLaw a b = pairTable a b := by
  cases a <;> cases b <;>
    norm_num [pairLaw, firstProb, secondProb, d2Mass, sumLoc, localMass, distSq, coord,
      pairTable]

theorem pair_nonneg (a b : Loc) : 0 ≤ pairLaw a b := by
  rw [pair_law]; cases a <;> cases b <;> norm_num [pairTable]

theorem pair_normalized : sumLoc (fun a => sumLoc (pairLaw a)) = 1 := by
  norm_num [sumLoc, pair_law, pairTable]

theorem no_repeated_location (a : Loc) : pairLaw a a = 0 := by
  rw [pair_law]; cases a <;> rfl

/-- Client 0's globally normalized mass: group A at zero, B at the endpoints. -/
def globalMass (eps : ℚ) : Loc → ℚ
  | zero => 1-eps | neg => eps/2 | pos => eps/2

/-- True means the first indexed representative wins, including distance ties. -/
def firstWins (a b x : Loc) : Prop := distSq x a ≤ distSq x b
instance (a b x : Loc) : Decidable (firstWins a b x) := inferInstanceAs
  (Decidable (distSq x a ≤ distSq x b))

def transferFirst (eps : ℚ) (a b : Loc) : ℚ :=
  sumLoc (fun x => if firstWins a b x then globalMass eps x else 0)
def transferSecond (eps : ℚ) (a b : Loc) : ℚ :=
  sumLoc (fun x => if firstWins a b x then 0 else globalMass eps x)

theorem transfer_conservation (eps : ℚ) (a b : Loc) :
    transferFirst eps a b + transferSecond eps a b = 1 := by
  cases a <;> cases b <;>
    norm_num [transferFirst, transferSecond, sumLoc, firstWins, distSq, coord, globalMass] <;> ring

theorem endpoints_indexed_tie (eps : ℚ) :
    transferFirst eps neg pos = 1-eps/2 ∧ transferSecond eps neg pos = eps/2 ∧
    transferFirst eps pos neg = 1-eps/2 ∧ transferSecond eps pos neg = eps/2 := by
  norm_num [transferFirst, transferSecond, sumLoc, firstWins, distSq, coord, globalMass]
  ring

/-- Four ordered slots remain present, including the client-1 zero-weight slot. -/
inductive Slot where
  | c0first | c0second | c1first | c1second
  deriving DecidableEq, Repr
open Slot

def sumSlot (f : Slot → ℚ) : ℚ := f c0first + f c0second + f c1first + f c1second

def slotLoc (a b : Loc) : Slot → Loc
  | c0first => a | c0second => b | c1first => zero | c1second => zero

/-- Client 1 has normalized group masses eps and 1-eps, both located at zero. -/
def clientOneFirst (eps : ℚ) : ℚ :=
  if firstWins zero zero zero then eps + (1-eps) else 0
def clientOneSecond (eps : ℚ) : ℚ :=
  if firstWins zero zero zero then 0 else eps + (1-eps)

/-- Client 1 is entirely at zero; ties transfer all normalized mass to its first slot. -/
def slotWeight (eps : ℚ) (a b : Loc) : Slot → ℚ
  | c0first => transferFirst eps a b
  | c0second => transferSecond eps a b
  | c1first => clientOneFirst eps
  | c1second => clientOneSecond eps

theorem client_one_weights (eps : ℚ) :
    clientOneFirst eps = 1 ∧ clientOneSecond eps = 0 := by
  simp [clientOneFirst, clientOneSecond, firstWins, distSq]

theorem server_total (eps : ℚ) (a b : Loc) : sumSlot (slotWeight eps a b) = 2 := by
  unfold sumSlot slotWeight
  rw [transfer_conservation, (client_one_weights eps).1, (client_one_weights eps).2]
  norm_num

/-- Exact categorical server selection on all four ordered slots. -/
def serverProb (eps : ℚ) (a b x : Loc) : ℚ :=
  sumSlot (fun s => if slotLoc a b s = x then slotWeight eps a b s else 0) /
    sumSlot (slotWeight eps a b)

def mergedLaw (eps : ℚ) (x : Loc) : ℚ :=
  sumLoc (fun a => sumLoc (fun b => pairLaw a b * serverProb eps a b x))

def mergedTable (eps : ℚ) : Loc → ℚ
  | zero => (5-eps)/6 | neg => (1+eps)/12 | pos => (1+eps)/12

theorem merged_law (eps : ℚ) (x : Loc) : mergedLaw eps x = mergedTable eps x := by
  unfold mergedLaw serverProb
  simp only [server_total]
  cases x <;>
    norm_num [sumLoc, pair_law, pairTable, sumSlot, slotLoc, slotWeight, clientOneFirst, clientOneSecond,
      transferFirst, transferSecond, firstWins, distSq, coord, globalMass, mergedTable] <;> ring

/-- SG chooses one B endpoint on client 0, equally likely, and keeps four slots. -/
def splitSlotLoc (b : Loc) : Slot → Loc
  | c0first => zero | c0second => b | c1first => zero | c1second => zero

def splitSlotWeight (eps : ℚ) : Slot → ℚ
  | c0first => 1-eps | c0second => eps | c1first => eps | c1second => 1-eps

def splitFirstMass : Loc → ℚ
  | zero => 0 | neg => 1/2 | pos => 1/2

def splitServerProb (eps : ℚ) (b x : Loc) : ℚ :=
  sumSlot (fun s => if splitSlotLoc b s = x then splitSlotWeight eps s else 0) /
    sumSlot (splitSlotWeight eps)

def splitLaw (eps : ℚ) (x : Loc) : ℚ :=
  sumLoc (fun b => splitFirstMass b * splitServerProb eps b x)

def splitTable (eps : ℚ) : Loc → ℚ
  | zero => 1-eps/2 | neg => eps/4 | pos => eps/4

theorem split_server_total (eps : ℚ) : sumSlot (splitSlotWeight eps) = 2 := by
  simp only [sumSlot, splitSlotWeight]; ring

theorem split_law (eps : ℚ) (x : Loc) : splitLaw eps x = splitTable eps x := by
  unfold splitLaw splitServerProb
  simp only [split_server_total]
  cases x <;> norm_num [sumLoc, splitFirstMass, sumSlot, splitSlotLoc,
    splitSlotWeight, splitTable] <;> ring

def endpointProb (law : Loc → ℚ) : ℚ := law neg + law pos

theorem endpoint_probabilities (eps : ℚ) :
    endpointProb (mergedLaw eps) = (1+eps)/6 ∧
    endpointProb (splitLaw eps) = eps/2 := by
  norm_num [endpointProb, merged_law, split_law, mergedTable, splitTable]
  constructor <;> ring

theorem merged_normalized (eps : ℚ) : sumLoc (mergedLaw eps) = 1 := by
  simp only [sumLoc, merged_law, mergedTable]; ring

theorem split_normalized (eps : ℚ) : sumLoc (splitLaw eps) = 1 := by
  simp only [sumLoc, split_law, splitTable]; ring

theorem merged_nonneg (eps : ℚ) (h0 : 0 ≤ eps) (h1 : eps ≤ 1) (x : Loc) :
    0 ≤ mergedLaw eps x := by
  rw [merged_law]; cases x <;> dsimp [mergedTable] <;> linarith

theorem split_nonneg (eps : ℚ) (h0 : 0 ≤ eps) (h1 : eps ≤ 1) (x : Loc) :
    0 ≤ splitLaw eps x := by
  rw [split_law]; cases x <;> dsimp [splitTable] <;> linarith

/-! Group objectives are defined by their mass-weighted squared distances. -/
def costA (eps c : ℚ) : ℚ := (1-eps)*(0-c)^2 + eps*(0-c)^2
def costB (eps c : ℚ) : ℚ :=
  (eps/2)*(-1-c)^2 + (eps/2)*(1-c)^2 + (1-eps)*(0-c)^2

def costG (eps c : ℚ) : ℚ := costA eps c + costB eps c
def costPhi (eps c : ℚ) : ℚ := max (costA eps c) (costB eps c)

theorem group_costs (eps c : ℚ) :
    costA eps c = c^2 ∧ costB eps c = c^2+eps := by
  constructor <;> dsimp [costA, costB] <;> ring

theorem g_cost (eps c : ℚ) : costG eps c = 2*c^2+eps := by
  simp only [costG, (group_costs eps c).1, (group_costs eps c).2]; ring

theorem phi_cost (eps c : ℚ) (h : 0 ≤ eps) : costPhi eps c = c^2+eps := by
  unfold costPhi
  rw [(group_costs eps c).1, (group_costs eps c).2]
  exact max_eq_right (by linarith)

theorem optimum_at_zero (eps : ℚ) (h : 0 ≤ eps) :
    costG eps 0 = eps ∧ costPhi eps 0 = eps ∧
    (∀ c, eps ≤ costG eps c) ∧ (∀ c, eps ≤ costPhi eps c) := by
  constructor
  · norm_num [g_cost]
  constructor
  · rw [phi_cost eps 0 h]; norm_num
  constructor
  · intro c; rw [g_cost]; nlinarith [sq_nonneg c]
  · intro c; rw [phi_cost eps c h]; nlinarith [sq_nonneg c]

def expected (law : Loc → ℚ) (cost : ℚ → ℚ) : ℚ :=
  sumLoc (fun x => law x * cost (coord x))

theorem expected_merged_g (eps : ℚ) :
    expected (mergedLaw eps) (costG eps) = (1+4*eps)/3 := by
  simp only [expected, sumLoc, merged_law, mergedTable, coord, g_cost]
  ring

theorem expected_split_g (eps : ℚ) :
    expected (splitLaw eps) (costG eps) = 2*eps := by
  simp only [expected, sumLoc, split_law, splitTable, coord, g_cost]
  ring

theorem expected_merged_phi (eps : ℚ) (h : 0 ≤ eps) :
    expected (mergedLaw eps) (costPhi eps) = (1+7*eps)/6 := by
  simp only [expected, sumLoc, merged_law, mergedTable, coord, phi_cost eps _ h]
  ring

theorem expected_split_phi (eps : ℚ) (h : 0 ≤ eps) :
    expected (splitLaw eps) (costPhi eps) = 3*eps/2 := by
  simp only [expected, sumLoc, split_law, splitTable, coord, phi_cost eps _ h]
  ring

def epsilon (kappa : ℚ) : ℚ := 1/(kappa+1)

theorem epsilon_bounds (kappa : ℚ) (hk : 1 ≤ kappa) :
    0 < epsilon kappa ∧ epsilon kappa ≤ 1/2 := by
  have hd : 0 < kappa+1 := by linarith
  constructor
  · exact one_div_pos.mpr hd
  · unfold epsilon
    apply (div_le_iff₀ hd).2
    linarith

/-- The four paper ratios, with expectations computed from the finite samplers. -/
theorem matched_ratios (kappa : ℚ) (hk : 1 ≤ kappa) :
    let eps := epsilon kappa
    expected (mergedLaw eps) (costG eps) / costG eps 0 = (kappa+5)/3 ∧
    expected (mergedLaw eps) (costPhi eps) / costPhi eps 0 = (kappa+8)/6 ∧
    expected (splitLaw eps) (costG eps) / costG eps 0 = 2 ∧
    expected (splitLaw eps) (costPhi eps) / costPhi eps 0 = 3/2 := by
  dsimp only
  have he : 0 ≤ epsilon kappa := le_of_lt (epsilon_bounds kappa hk).1
  have hd : kappa+1 ≠ 0 := by linarith
  rw [expected_merged_g, expected_merged_phi _ he, expected_split_g,
    expected_split_phi _ he, (optimum_at_zero _ he).1, (optimum_at_zero _ he).2.1]
  dsimp [epsilon]
  field_simp
  ring_nf
  simp

noncomputable section

/-! The optimum certificate also holds for all real centers, not only rational ones. -/
def realCostA (eps c : ℝ) : ℝ := (1-eps)*(0-c)^2 + eps*(0-c)^2
def realCostB (eps c : ℝ) : ℝ :=
  (eps/2)*(-1-c)^2 + (eps/2)*(1-c)^2 + (1-eps)*(0-c)^2

def realG (eps c : ℝ) : ℝ := realCostA eps c + realCostB eps c
def realPhi (eps c : ℝ) : ℝ := max (realCostA eps c) (realCostB eps c)

theorem real_group_costs (eps c : ℝ) :
    realCostA eps c = c^2 ∧ realCostB eps c = c^2+eps := by
  constructor <;> dsimp [realCostA, realCostB] <;> ring

theorem real_g (eps c : ℝ) : realG eps c = 2*c^2+eps := by
  simp only [realG, (real_group_costs eps c).1, (real_group_costs eps c).2]; ring

theorem real_phi (eps c : ℝ) (h : 0 ≤ eps) : realPhi eps c = c^2+eps := by
  unfold realPhi
  rw [(real_group_costs eps c).1, (real_group_costs eps c).2]
  exact max_eq_right (by linarith)

theorem real_optimum_at_zero (eps : ℝ) (h : 0 ≤ eps) :
    realG eps 0 = eps ∧ realPhi eps 0 = eps ∧
    (∀ c : ℝ, eps ≤ realG eps c) ∧ (∀ c : ℝ, eps ≤ realPhi eps c) := by
  constructor
  · norm_num [real_g]
  constructor
  · rw [real_phi eps 0 h]; norm_num
  constructor
  · intro c; rw [real_g]; nlinarith [sq_nonneg c]
  · intro c; rw [real_phi eps c h]; nlinarith [sq_nonneg c]

theorem rational_real_agreement (eps c : ℚ) (h : 0 ≤ eps) :
    (costG eps c : ℝ) = realG eps c ∧
    (costPhi eps c : ℝ) = realPhi eps c := by
  have hr : (0 : ℝ) ≤ (eps : ℝ) := by exact_mod_cast h
  rw [g_cost, phi_cost eps c h, real_g, real_phi (eps : ℝ) c hr]
  constructor <;> push_cast <;> ring

/-- First and second categorical calls are probability laws with positive denominators. -/
theorem local_categorical_valid :
    sumLoc localMass = 2 ∧
    (∀ a, 0 < sumLoc (d2Mass a)) ∧
    sumLoc firstProb = 1 ∧
    (∀ a, sumLoc (secondProb a) = 1) := by
  constructor
  · norm_num [sumLoc, localMass]
  constructor
  · intro a; cases a <;> norm_num [sumLoc, d2Mass, localMass, distSq, coord]
  constructor
  · norm_num [sumLoc, firstProb, localMass]
  · intro a; cases a <;> norm_num [sumLoc, secondProb, d2Mass, localMass, distSq, coord]

theorem slot_weights_nonnegative (eps : ℚ) (h0 : 0 ≤ eps) (h1 : eps ≤ 1)
    (a b : Loc) (s : Slot) : 0 ≤ slotWeight eps a b s := by
  cases a <;> cases b <;> cases s <;>
    norm_num [slotWeight, clientOneFirst, clientOneSecond, transferFirst, transferSecond, sumLoc, firstWins,
      distSq, coord, globalMass] <;> linarith

theorem unused_slot_probability (eps : ℚ) (a b : Loc) :
    slotWeight eps a b Slot.c1second / sumSlot (slotWeight eps a b) = 0 := by
  rw [server_total]
  simp only [slotWeight, (client_one_weights eps).2, zero_div]

noncomputable def realExpected (law : Loc → ℚ) (cost : ℝ → ℝ) : ℝ :=
  (law zero : ℝ)*cost (coord zero) + (law neg : ℝ)*cost (coord neg) +
    (law pos : ℝ)*cost (coord pos)

theorem expected_g_cast (law : Loc → ℚ) (eps : ℚ) :
    (expected law (costG eps) : ℝ) = realExpected law (realG eps) := by
  simp only [expected, sumLoc, realExpected, g_cost, real_g]
  push_cast
  ring

theorem expected_phi_cast (law : Loc → ℚ) (eps : ℚ) (h : 0 ≤ eps) :
    (expected law (costPhi eps) : ℝ) = realExpected law (realPhi eps) := by
  have hr : (0 : ℝ) ≤ (eps : ℝ) := by exact_mod_cast h
  simp only [expected, sumLoc, realExpected, phi_cost eps _ h, real_phi (eps : ℝ) _ hr]
  push_cast
  ring

/-- The same ratios interpreted as real expectations of the paper's real objectives. -/
theorem matched_real_ratios (kappa : ℚ) (hk : 1 ≤ kappa) :
    let eps := epsilon kappa
    realExpected (mergedLaw eps) (realG eps) / realG eps 0 = ((kappa : ℝ)+5)/3 ∧
    realExpected (mergedLaw eps) (realPhi eps) / realPhi eps 0 = ((kappa : ℝ)+8)/6 ∧
    realExpected (splitLaw eps) (realG eps) / realG eps 0 = 2 ∧
    realExpected (splitLaw eps) (realPhi eps) / realPhi eps 0 = 3/2 := by
  dsimp only
  have he := le_of_lt (epsilon_bounds kappa hk).1
  have hg := (rational_real_agreement (epsilon kappa) 0 he).1
  have hp := (rational_real_agreement (epsilon kappa) 0 he).2
  norm_num only [Rat.cast_zero] at hg hp
  rw [← expected_g_cast, ← expected_phi_cast _ _ he, ← expected_g_cast,
    ← expected_phi_cast _ _ he, ← hg, ← hp]
  obtain ⟨h1, h2, h3, h4⟩ := matched_ratios kappa hk
  refine ⟨?_, ?_, ?_, ?_⟩
  · exact_mod_cast h1
  · exact_mod_cast h2
  · exact_mod_cast h3
  · have hh := congrArg (fun q : ℚ => (q : ℝ)) h4
    push_cast at hh
    exact hh

end
end MatchedBudget
