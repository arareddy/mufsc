import Certificates
import Trajectory

/-! End-to-end assignment/patch/trajectory bridge. Certificate soundness here is
proved from exact metric tests, rather than assumed as a round-output premise. -/
namespace Replay
variable {R L M P : Type*} [Fintype R] [AddCommGroup M]
  [Fintype L] [LinearOrder L] [Nonempty L] [PseudoMetricSpace P]

noncomputable def basicModel (keep : R → Bool) (point : R → P)
    (contribution : R → L → M) (cachedCenters : ℕ → L → P)
    (cachedLabel : ℕ → R → L) (second : ℕ → R → ℝ)
    (update : ℕ → (L → P) → M → (L → P)) : RoundModel R L M (L → P) := by
  classical
  exact {
    keep := keep
    assign := fun centers r => nearest (fun j => dist (point r) (centers j))
    contribution := contribution
    cachedLabel := cachedLabel
    accepted := fun t centers r => decide
      (shift (cachedCenters t) centers (cachedLabel t r) +
        maxOn (competitors (cachedLabel t r)) (shift (cachedCenters t) centers) <
        second t r - dist (point r) (cachedCenters t (cachedLabel t r)))
    update := update }

omit [Fintype R] [AddCommGroup M] in
theorem basicModel_sound (keep : R → Bool) (point : R → P)
    (contribution : R → L → M) (cachedCenters : ℕ → L → P)
    (cachedLabel : ℕ → R → L) (second : ℕ → R → ℝ)
    (update : ℕ → (L → P) → M → (L → P))
    (cacheLower : ∀ t r m, m ≠ cachedLabel t r → second t r ≤ dist (point r) (cachedCenters t m))
    (t : ℕ) (centers : L → P) (r : R)
    (accepted : (basicModel keep point contribution cachedCenters cachedLabel second update).accepted t centers r = true) :
    cachedLabel t r = nearest (fun j => dist (point r) (centers j)) := by
  classical
  have htest := of_decide_eq_true accepted
  exact (basic_certified_label (point r) (cachedCenters t) centers (cachedLabel t r)
    (second t r) (cacheLower t r) htest).symm

/-- thm:exactness, refinement part for the basic certificate. Only cache facts,
exact additive operations and deterministic maps are premises. -/
theorem basic_full_trajectory (keep : R → Bool) (point : R → P)
    (contribution : R → L → M) (cachedCenters : ℕ → L → P)
    (cachedLabel : ℕ → R → L) (second : ℕ → R → ℝ)
    (update : ℕ → (L → P) → M → (L → P))
    (cacheLower : ∀ t r m, m ≠ cachedLabel t r → second t r ≤ dist (point r) (cachedCenters t m))
    (initialReplay initialFresh : L → P) (initialDirect : Bool)
    (initialEq : initialReplay = initialFresh) (T : ℕ) :
    let model := basicModel keep point contribution cachedCenters cachedLabel second update
    (fun t : Fin (T+1) => (replayRun model initialReplay initialDirect t.val).1) =
      (fun t : Fin (T+1) => freshRun model initialFresh t.val) := by
  dsimp only
  apply finite_trajectory_equal _ _ _ _ initialEq
  intro t centers r _ ha
  exact basicModel_sound keep point contribution cachedCenters cachedLabel second update cacheLower t centers r ha

noncomputable def runnerModel (keep : R → Bool) (point : R → P)
    (contribution : R → L → M) (cachedCenters : ℕ → L → P)
    (cachedLabel runner : ℕ → R → L) (second : ℕ → R → ℝ)
    (update : ℕ → (L → P) → M → (L → P)) : RoundModel R L M (L → P) := by
  classical
  exact {
    keep := keep
    assign := fun centers r => nearest (fun j => dist (point r) (centers j))
    contribution := contribution
    cachedLabel := cachedLabel
    accepted := fun t centers r => decide
      (runnerTest (point r) (cachedCenters t) centers (cachedLabel t r) (runner t r) (second t r))
    update := update }

omit [Fintype R] [AddCommGroup M] in
theorem runnerModel_sound (keep : R → Bool) (point : R → P)
    (contribution : R → L → M) (cachedCenters : ℕ → L → P)
    (cachedLabel runner : ℕ → R → L) (second : ℕ → R → ℝ)
    (update : ℕ → (L → P) → M → (L → P))
    (cacheLower : ∀ t r m, m ≠ cachedLabel t r → second t r ≤ dist (point r) (cachedCenters t m))
    (runnerDistance : ∀ t r, dist (point r) (cachedCenters t (runner t r)) = second t r)
    (t : ℕ) (centers : L → P) (r : R)
    (accepted : (runnerModel keep point contribution cachedCenters cachedLabel runner second update).accepted t centers r = true) :
    cachedLabel t r = nearest (fun j => dist (point r) (centers j)) := by
  classical
  have htest := of_decide_eq_true accepted
  exact (runner_certified_label (point r) (cachedCenters t) centers (cachedLabel t r)
    (runner t r) (second t r) (runnerDistance t r) (cacheLower t r) htest).symm

/-- thm:exactness, refinement part for the stronger runner-up certificate. -/
theorem runner_full_trajectory (keep : R → Bool) (point : R → P)
    (contribution : R → L → M) (cachedCenters : ℕ → L → P)
    (cachedLabel runner : ℕ → R → L) (second : ℕ → R → ℝ)
    (update : ℕ → (L → P) → M → (L → P))
    (cacheLower : ∀ t r m, m ≠ cachedLabel t r → second t r ≤ dist (point r) (cachedCenters t m))
    (runnerDistance : ∀ t r, dist (point r) (cachedCenters t (runner t r)) = second t r)
    (initialReplay initialFresh : L → P) (initialDirect : Bool)
    (initialEq : initialReplay = initialFresh) (T : ℕ) :
    let model := runnerModel keep point contribution cachedCenters cachedLabel runner second update
    (fun t : Fin (T+1) => (replayRun model initialReplay initialDirect t.val).1) =
      (fun t : Fin (T+1) => freshRun model initialFresh t.val) := by
  dsimp only
  apply finite_trajectory_equal _ _ _ _ initialEq
  intro t centers r _ ha
  exact runnerModel_sound keep point contribution cachedCenters cachedLabel runner second update
    cacheLower runnerDistance t centers r ha

#print axioms basicModel_sound
#print axioms basic_full_trajectory
#print axioms runnerModel_sound
#print axioms runner_full_trajectory
end Replay
