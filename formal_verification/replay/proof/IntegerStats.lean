import ExactPatch

/-! Concrete fixed-point represented integer statistics. Coordinates are integer
numerators at a common fixed scale. Scaling back to reals is a separate map. -/
namespace Replay
open scoped BigOperators

abbrev CellStats (d : ℕ) := ℤ × (Fin d → ℤ) × ℤ
abbrev IntegerStats (G L : Type*) (d : ℕ) := G → L → CellStats d

def integerContribution {R G L : Type*} [DecidableEq G] [DecidableEq L]
    {d : ℕ} (group : R → G) (coord : R → Fin d → ℤ)
    (r : R) (label : L) : IntegerStats G L d :=
  fun g j => if group r = g ∧ label = j then
    (1, coord r, ∑ i, coord r i * coord r i) else 0

/-- Simultaneously covers all group/cluster count, coordinate-sum and
squared-norm-sum cells, with exact signed deletion and relabel corrections. -/
theorem integer_stats_patch {R G L : Type*} [Fintype R] [DecidableEq G] [DecidableEq L]
    {d : ℕ} (group : R → G) (coord : R → Fin d → ℤ)
    (keep accepted : R → Bool) (oldLabel freshLabel : R → L)
    (sound : ∀ r, keep r = true → accepted r = true → oldLabel r = freshLabel r) :
    patched keep accepted
      (fun r => integerContribution group coord r (oldLabel r))
      (fun r => integerContribution group coord r (freshLabel r)) =
    retainedSum keep (fun r => integerContribution group coord r (freshLabel r)) :=
  label_patch_exact keep accepted oldLabel freshLabel (integerContribution group coord) sound

/-- The same concrete statistics are reconstructed when patches are abandoned. -/
theorem integer_stats_abandonment {R G L : Type*} [Fintype R] [DecidableEq G] [DecidableEq L]
    {d : ℕ} (group : R → G) (coord : R → Fin d → ℤ)
    (abandon : Bool) (keep accepted : R → Bool) (oldLabel freshLabel : R → L)
    (sound : ∀ r, keep r = true → accepted r = true → oldLabel r = freshLabel r) :
    roundStats abandon keep accepted
      (fun r => integerContribution group coord r (oldLabel r))
      (fun r => integerContribution group coord r (freshLabel r)) =
    retainedSum keep (fun r => integerContribution group coord r (freshLabel r)) := by
  apply abandonment_exact
  intro r hk ha
  rw [sound r hk ha]

/-- Exact aggregation over a finite ownership partition equals centralized
aggregation. This proves the additive part of prop:central-equivalence. -/
theorem owner_partition_sum {R C M : Type*} [Fintype R] [Fintype C]
    [DecidableEq C] [AddCommMonoid M] (owner : R → C) (f : R → M) :
    (∑ c, ∑ r, if owner r = c then f r else 0) = ∑ r, f r := by
  rw [Finset.sum_comm]
  apply Finset.sum_congr rfl
  intro r _
  simp

/-- Assigning every slice record to exactly one anchor preserves total
multiplicity, including repeated coordinates and empty anchor cells. -/
theorem local_multiplicity_conservation {R L : Type*} [Fintype R] [Fintype L]
    [DecidableEq L] (label : R → L) :
    (∑ j, ∑ r, if label r = j then 1 else 0 : ℕ) = Fintype.card R := by
  rw [owner_partition_sum label (fun _ => (1 : ℕ))]
  simp

#print axioms local_multiplicity_conservation
#print axioms integer_stats_patch
#print axioms integer_stats_abandonment
#print axioms owner_partition_sum
end Replay
