import Mathlib.Data.Rat.Cast.Order
import Mathlib.Data.Fintype.BigOperators

/-! A pure keyed initializer interface. Local sampling and the server algorithm
are explicit deterministic function parameters, not imported sampling theorems.
Inputs are ordered lists; keys are the fixed canonical order. -/
namespace Replay
open scoped BigOperators
inductive StreamKey (Slice : Type*) where
  | local : Slice → StreamKey Slice
  | server : StreamKey Slice
  deriving DecidableEq

structure Anchor (Point : Type*) where
  point : Point
  mass : ℕ
  deriving DecidableEq

structure WeightedAnchor (Slice Point : Type*) where
  slice : Slice
  anchorIndex : ℕ
  point : Point
  mass : ℕ
  weight : ℚ
  deriving DecidableEq

variable {Slice Record Point Seed Tape State Group : Type*}

/-- The canonical list includes slice identity and local anchor index. -/
def canonicalAnchors (keys : List Slice) (active : Slice → Bool)
    (group : Slice → Group) (counts : Group → ℕ)
    (summaries : Slice → List (Anchor Point)) : List (WeightedAnchor Slice Point) :=
  keys.flatMap fun e => if active e then
    ((summaries e).zipIdx).map (fun ai =>
      ⟨e, ai.2, ai.1.point, ai.1.mass, (ai.1.mass : ℚ) / (counts (group e) : ℚ)⟩)
  else []

/-- Group counts are recomputed on retained ordered inputs. -/
def groupCounts [DecidableEq Group] (keys : List Slice) (active : Slice → Bool)
    (group : Slice → Group) (input : Slice → List Record) (g : Group) : ℕ :=
  (keys.map fun e => if active e && decide (group e = g) then (input e).length else 0).sum

def freshSummaries (localMap : Slice → Tape → List Record → List (Anchor Point))
    (streams : Seed → StreamKey Slice → Tape) (seed : Seed)
    (input : Slice → List Record) : Slice → List (Anchor Point) :=
  fun e => localMap e (streams seed (.local e)) (input e)

def replaySummaries (localMap : Slice → Tape → List Record → List (Anchor Point))
    (streams : Seed → StreamKey Slice → Tape) (seed : Seed)
    (oldInput retainedInput : Slice → List Record) (touched : Slice → Bool) :
    Slice → List (Anchor Point) :=
  fun e => if touched e then localMap e (streams seed (.local e)) (retainedInput e)
    else localMap e (streams seed (.local e)) (oldInput e)

/-- Untouched reuse is justified by equal slice inputs and the same keyed tape.
Touched slices are actually recomputed, not assumed to have equal output. -/
theorem summaries_equal
    (localMap : Slice → Tape → List Record → List (Anchor Point))
    (streams : Seed → StreamKey Slice → Tape) (seed : Seed)
    (oldInput retainedInput : Slice → List Record) (touched : Slice → Bool)
    (untouched : ∀ e, touched e = false → oldInput e = retainedInput e) :
    replaySummaries localMap streams seed oldInput retainedInput touched =
      freshSummaries localMap streams seed retainedInput := by
  funext e
  cases h : touched e
  · simp [replaySummaries, freshSummaries, h, untouched e h]
  · simp [replaySummaries, freshSummaries, h]

/-- The server receives exactly the same canonical anchors, rational weights,
counts and server-keyed stream. Its deterministic completion/refinement rules
are part of serverMap. -/
theorem initialized_state_equal [DecidableEq Group]
    (localMap : Slice → Tape → List Record → List (Anchor Point))
    (serverMap : Tape → (Group → ℕ) → List (WeightedAnchor Slice Point) → State)
    (streams : Seed → StreamKey Slice → Tape) (seed : Seed)
    (keys : List Slice) (active : Slice → Bool) (group : Slice → Group)
    (oldInput retainedInput : Slice → List Record) (touched : Slice → Bool)
    (untouched : ∀ e, touched e = false → oldInput e = retainedInput e) :
    serverMap (streams seed .server) (groupCounts keys active group retainedInput)
      (canonicalAnchors keys active group (groupCounts keys active group retainedInput)
        (replaySummaries localMap streams seed oldInput retainedInput touched)) =
    serverMap (streams seed .server) (groupCounts keys active group retainedInput)
      (canonicalAnchors keys active group (groupCounts keys active group retainedInput)
        (freshSummaries localMap streams seed retainedInput)) := by
  rw [summaries_equal localMap streams seed oldInput retainedInput touched untouched]

/-- Whole-client T=0 specialization: surviving slices have unchanged ordered
records; deleted slices are omitted. Cached summaries may differ on omitted
slices without affecting the canonical server list. -/
theorem canonical_active_congr (keys : List Slice) (active : Slice → Bool)
    (group : Slice → Group) (counts : Group → ℕ)
    (old fresh : Slice → List (Anchor Point))
    (h : ∀ e, active e = true → old e = fresh e) :
    canonicalAnchors keys active group counts old =
      canonicalAnchors keys active group counts fresh := by
  unfold canonicalAnchors
  congr 1
  funext e
  cases he : active e
  · simp [he]
  · simp [he, h e he]

theorem whole_client_initializer [DecidableEq Group]
    (localMap : Slice → Tape → List Record → List (Anchor Point))
    (serverMap : Tape → (Group → ℕ) → List (WeightedAnchor Slice Point) → State)
    (streams : Seed → StreamKey Slice → Tape) (seed : Seed)
    (keys : List Slice) (active : Slice → Bool) (group : Slice → Group)
    (oldInput retainedInput : Slice → List Record)
    (survives : ∀ e, active e = true → oldInput e = retainedInput e) :
    serverMap (streams seed .server) (groupCounts keys active group retainedInput)
      (canonicalAnchors keys active group (groupCounts keys active group retainedInput)
        (freshSummaries localMap streams seed oldInput)) =
    serverMap (streams seed .server) (groupCounts keys active group retainedInput)
      (canonicalAnchors keys active group (groupCounts keys active group retainedInput)
        (freshSummaries localMap streams seed retainedInput)) := by
  congr 1
  apply canonical_active_congr
  intro e he
  simp [freshSummaries, survives e he]

/-- Counts available to a compact summary-only API. -/
def summaryGroupCounts [DecidableEq Group] (keys : List Slice) (active : Slice → Bool)
    (group : Slice → Group) (summaries : Slice → List (Anchor Point)) (g : Group) : ℕ :=
  (keys.map fun e => if active e && decide (group e = g) then
    ((summaries e).map Anchor.mass).sum else 0).sum

/-- The local mass-conservation contract is stated explicitly. It is the sum of
anchor multiplicities, not an assumed equality of final group counts. -/
theorem summary_counts_exact [DecidableEq Group] (keys : List Slice) (active : Slice → Bool)
    (group : Slice → Group) (summaries : Slice → List (Anchor Point))
    (input : Slice → List Record)
    (massConservation : ∀ e, active e = true →
      ((summaries e).map Anchor.mass).sum = (input e).length) :
    summaryGroupCounts keys active group summaries = groupCounts keys active group input := by
  funext g
  unfold summaryGroupCounts groupCounts
  congr 1
  apply List.map_congr_left
  intro e _
  cases he : active e
  · simp [he]
  · simp [he, massConservation e he]

/-- prop:client-summary with retained counts obtained only from cached summary
multiplicities. Surviving slices have unchanged ordered records. -/
theorem whole_client_compact [DecidableEq Group]
    (localMap : Slice → Tape → List Record → List (Anchor Point))
    (serverMap : Tape → (Group → ℕ) → List (WeightedAnchor Slice Point) → State)
    (streams : Seed → StreamKey Slice → Tape) (seed : Seed)
    (keys : List Slice) (active : Slice → Bool) (group : Slice → Group)
    (oldInput retainedInput : Slice → List Record)
    (survives : ∀ e, active e = true → oldInput e = retainedInput e)
    (massConservation : ∀ e, active e = true →
      ((freshSummaries localMap streams seed oldInput e).map Anchor.mass).sum =
        (oldInput e).length) :
    let cached := freshSummaries localMap streams seed oldInput
    let counts := summaryGroupCounts keys active group cached
    serverMap (streams seed .server) counts (canonicalAnchors keys active group counts cached) =
    serverMap (streams seed .server) (groupCounts keys active group retainedInput)
      (canonicalAnchors keys active group (groupCounts keys active group retainedInput)
        (freshSummaries localMap streams seed retainedInput)) := by
  dsimp only
  have hc := summary_counts_exact keys active group
    (freshSummaries localMap streams seed oldInput) retainedInput (fun e he => by
      rw [massConservation e he, survives e he])
  rw [hc]
  exact whole_client_initializer localMap serverMap streams seed keys active group
    oldInput retainedInput survives

#print axioms summary_counts_exact
#print axioms whole_client_compact
#print axioms summaries_equal
#print axioms initialized_state_equal
#print axioms canonical_active_congr
#print axioms whole_client_initializer
end Replay
