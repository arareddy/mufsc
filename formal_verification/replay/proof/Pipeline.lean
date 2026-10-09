import CertifiedReplay
import IntegerStats

/-! Composition of keyed initialization and exact replay. This layer does not
assume initialized-state equality; it invokes the proved initializer theorem.
The maps localMap, serverMap and update are deterministic mathematical interfaces.
No PRNG, executable sampler, floating arithmetic or Python linkage is asserted. -/
namespace Replay

structure Initializer (Slice Record Point Seed Tape Group State : Type*) where
  keys : List Slice
  active : Slice → Bool
  group : Slice → Group
  oldInput : Slice → List Record
  retainedInput : Slice → List Record
  touched : Slice → Bool
  localMap : Slice → Tape → List Record → List (Anchor Point)
  serverMap : Tape → (Group → ℕ) → List (WeightedAnchor Slice Point) → State
  streams : Seed → StreamKey Slice → Tape

variable {Slice Record Point Seed Tape Group State : Type*} [DecidableEq Group]

namespace Initializer
variable (cfg : Initializer Slice Record Point Seed Tape Group State)

def fresh (seed : Seed) : State :=
  let counts := groupCounts cfg.keys cfg.active cfg.group cfg.retainedInput
  cfg.serverMap (cfg.streams seed .server) counts
    (canonicalAnchors cfg.keys cfg.active cfg.group counts
      (freshSummaries cfg.localMap cfg.streams seed cfg.retainedInput))

def replay (seed : Seed) : State :=
  let counts := groupCounts cfg.keys cfg.active cfg.group cfg.retainedInput
  cfg.serverMap (cfg.streams seed .server) counts
    (canonicalAnchors cfg.keys cfg.active cfg.group counts
      (replaySummaries cfg.localMap cfg.streams seed cfg.oldInput cfg.retainedInput cfg.touched))

theorem same_seed (untouched : ∀ e, cfg.touched e = false → cfg.oldInput e = cfg.retainedInput e)
    (seed : Seed) : cfg.replay seed = cfg.fresh seed :=
  initialized_state_equal cfg.localMap cfg.serverMap cfg.streams seed cfg.keys cfg.active
    cfg.group cfg.oldInput cfg.retainedInput cfg.touched untouched
end Initializer

variable {R L M : Type*} [Fintype R] [AddCommGroup M]

/-- thm:exactness at the deterministic map interface. The initializer is proved
from untouched input reuse; every round is proved from exact signed patches.
The remaining soundness premise is discharged by basic/runner models below. -/
theorem seeded_full_trajectory (cfg : Initializer Slice Record Point Seed Tape Group State)
    (untouched : ∀ e, cfg.touched e = false → cfg.oldInput e = cfg.retainedInput e)
    (model : Seed → RoundModel R L M State)
    (sound : ∀ seed t state r, (model seed).keep r = true →
      (model seed).accepted t state r = true →
      (model seed).cachedLabel t r = (model seed).assign state r)
    (seed : Seed) (initialDirect : Bool) (T : ℕ) :
    (fun t : Fin (T+1) => (replayRun (model seed) (cfg.replay seed) initialDirect t.val).1) =
      (fun t : Fin (T+1) => freshRun (model seed) (cfg.fresh seed) t.val) :=
  finite_trajectory_equal (model seed) _ _ _ (cfg.same_seed untouched seed) (sound seed) T

section MetricPipeline
variable {P : Type*} [PseudoMetricSpace P] [Fintype L] [LinearOrder L] [Nonempty L]

/-- Complete basic-certificate model composition. There is no assumed equality
of initialized outputs, no assumed round equality and no assumed certificate
soundness: the hypotheses concern unchanged slice inputs and authentic cache
distance lower bounds only. -/
theorem seeded_basic_exactness
    (cfg : Initializer Slice Record Point Seed Tape Group (L → P))
    (untouched : ∀ e, cfg.touched e = false → cfg.oldInput e = cfg.retainedInput e)
    (keep : R → Bool) (point : R → P) (contribution : R → L → M)
    (cachedCenters : Seed → ℕ → L → P) (cachedLabel : Seed → ℕ → R → L)
    (second : Seed → ℕ → R → ℝ)
    (update : ℕ → (L → P) → M → (L → P))
    (cacheLower : ∀ seed t r m, m ≠ cachedLabel seed t r →
      second seed t r ≤ dist (point r) (cachedCenters seed t m))
    (seed : Seed) (initialDirect : Bool) (T : ℕ) :
    let model := basicModel keep point contribution (cachedCenters seed)
      (cachedLabel seed) (second seed) update
    (fun t : Fin (T+1) => (replayRun model (cfg.replay seed) initialDirect t.val).1) =
      (fun t : Fin (T+1) => freshRun model (cfg.fresh seed) t.val) := by
  exact basic_full_trajectory keep point contribution (cachedCenters seed) (cachedLabel seed)
    (second seed) update (cacheLower seed) _ _ initialDirect (cfg.same_seed untouched seed) T

/-- Complete runner-up model composition, also using the authentic cached
runner-up distance. The empty non-runner case is already proved sound. -/
theorem seeded_runner_exactness
    (cfg : Initializer Slice Record Point Seed Tape Group (L → P))
    (untouched : ∀ e, cfg.touched e = false → cfg.oldInput e = cfg.retainedInput e)
    (keep : R → Bool) (point : R → P) (contribution : R → L → M)
    (cachedCenters : Seed → ℕ → L → P) (cachedLabel runner : Seed → ℕ → R → L)
    (second : Seed → ℕ → R → ℝ)
    (update : ℕ → (L → P) → M → (L → P))
    (cacheLower : ∀ seed t r m, m ≠ cachedLabel seed t r →
      second seed t r ≤ dist (point r) (cachedCenters seed t m))
    (runnerDistance : ∀ seed t r,
      dist (point r) (cachedCenters seed t (runner seed t r)) = second seed t r)
    (seed : Seed) (initialDirect : Bool) (T : ℕ) :
    let model := runnerModel keep point contribution (cachedCenters seed)
      (cachedLabel seed) (runner seed) (second seed) update
    (fun t : Fin (T+1) => (replayRun model (cfg.replay seed) initialDirect t.val).1) =
      (fun t : Fin (T+1) => freshRun model (cfg.fresh seed) t.val) := by
  exact runner_full_trajectory keep point contribution (cachedCenters seed) (cachedLabel seed)
    (runner seed) (second seed) update (cacheLower seed) (runnerDistance seed)
    _ _ initialDirect (cfg.same_seed untouched seed) T
end MetricPipeline

/-- Equality of all pushed-forward events under an arbitrary seed law. A law is
represented by its value on seed events; measure-theoretic well-formedness is
irrelevant to this equality. Fixed deletion parameters are outside the seed
argument. This does not introduce a fresh independent seed after adaptive
checkpoint-dependent deletion. -/
theorem same_seed_event_law {Seed Output Value : Type*}
    (law : Set Seed → Value) (fresh replay : Seed → Output)
    (same : ∀ seed, replay seed = fresh seed) (event : Set Output) :
    law (replay ⁻¹' event) = law (fresh ⁻¹' event) := by
  have h : replay = fresh := funext same
  rw [h]

#print axioms Initializer.same_seed
#print axioms seeded_full_trajectory
#print axioms seeded_basic_exactness
#print axioms seeded_runner_exactness
#print axioms same_seed_event_law
end Replay
