import ExactPatch
import Initialization

/-! Fresh and replay recurrences. Replay actually computes deletion/relabel
patches from the original all-record cache, rebuilds on strict-majority failure,
and keeps direct mode thereafter. Equality is derived from patch algebra. -/
namespace Replay
open scoped BigOperators
variable {R L M S : Type*} [Fintype R] [AddCommGroup M]

structure RoundModel (R L M S : Type*) where
  keep : R → Bool
  assign : S → R → L
  contribution : R → L → M
  cachedLabel : ℕ → R → L
  accepted : ℕ → S → R → Bool
  update : ℕ → S → M → S

variable (model : RoundModel R L M S)

def freshStats (s : S) : M :=
  retainedSum model.keep (fun r => model.contribution r (model.assign s r))

def failedCount (t : ℕ) (s : S) : ℕ :=
  ∑ r, if model.keep r && !(model.accepted t s r) then 1 else 0

def survivorCount : ℕ := ∑ r, if model.keep r then 1 else 0

def goDirect (t : ℕ) (s : S) (wasDirect : Bool) : Bool :=
  wasDirect || decide (survivorCount model < 2 * failedCount model t s)

def freshStep (t : ℕ) (s : S) : S := model.update t s (freshStats model s)

def replayStep (t : ℕ) (st : S × Bool) : S × Bool :=
  let direct := goDirect model t st.1 st.2
  (model.update t st.1
    (roundStats direct model.keep (model.accepted t st.1)
      (fun r => model.contribution r (model.cachedLabel t r))
      (fun r => model.contribution r (model.assign st.1 r))), direct)

/-- The persistent direct flag never resets. -/
theorem direct_stays_direct (t : ℕ) (s : S) : (replayStep model t (s, true)).2 = true := by
  simp [replayStep, goDirect]

/-- Sound certificates are the sole label-level premise; patched aggregate
identity and equality of the next state are conclusions, not assumptions. -/
theorem replayStep_equal (t : ℕ) (st : S × Bool)
    (sound : ∀ r, model.keep r = true → model.accepted t st.1 r = true →
      model.cachedLabel t r = model.assign st.1 r) :
    (replayStep model t st).1 = freshStep model t st.1 := by
  dsimp only [replayStep, freshStep, freshStats]
  congr 1
  apply abandonment_exact
  intro r hk ha
  rw [sound r hk ha]

def freshRun (initial : S) : ℕ → S
  | 0 => initial
  | t+1 => freshStep model t (freshRun initial t)

def replayRun (initial : S) (initialDirect : Bool) : ℕ → S × Bool
  | 0 => (initial, initialDirect)
  | t+1 => replayStep model t (replayRun initial initialDirect t)

/-- Natural-number induction covers every indexed round, with arbitrary
original cached labels and arbitrary valid abandonment events. -/
theorem trajectory_equal (initialReplay initialFresh : S) (initialDirect : Bool)
    (initialEq : initialReplay = initialFresh)
    (sound : ∀ t s r, model.keep r = true → model.accepted t s r = true →
      model.cachedLabel t r = model.assign s r) :
    ∀ t, (replayRun model initialReplay initialDirect t).1 = freshRun model initialFresh t := by
  intro t
  induction t with
  | zero => exact initialEq
  | succ t ih =>
    change (replayStep model t (replayRun model initialReplay initialDirect t)).1 =
      freshStep model t (freshRun model initialFresh t)
    rw [replayStep_equal model t _ (sound t _), ih]

/-- Full finite indexed trajectory equality, retaining labels/order, not merely
permutation equivalence or equality of the final unordered center set. -/
theorem finite_trajectory_equal (initialReplay initialFresh : S) (initialDirect : Bool)
    (initialEq : initialReplay = initialFresh)
    (sound : ∀ t s r, model.keep r = true → model.accepted t s r = true →
      model.cachedLabel t r = model.assign s r) (T : ℕ) :
    (fun t : Fin (T+1) => (replayRun model initialReplay initialDirect t.val).1) =
      (fun t : Fin (T+1) => freshRun model initialFresh t.val) := by
  funext t
  exact trajectory_equal model initialReplay initialFresh initialDirect initialEq sound t.val

/-- T=0 releases exactly the initialization, even when replay would use direct
mode for positive budgets. -/
theorem zero_round (initial : S) (initialDirect : Bool) :
    (replayRun model initial initialDirect 0).1 = initial ∧ freshRun model initial 0 = initial :=
  ⟨rfl, rfl⟩

#print axioms direct_stays_direct
#print axioms replayStep_equal
#print axioms trajectory_equal
#print axioms finite_trajectory_equal
#print axioms zero_round
end Replay
