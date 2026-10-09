import Mathlib.Algebra.BigOperators.Ring.Finset
import Mathlib.Data.Fintype.BigOperators

/-! Exact finite additive patching. Every identifier denotes one record, so equal
coordinates do not merge distinct records. The additive group may be a product
of integer count, vector-sum, squared-norm-sum and group/cluster cells. -/
namespace Replay
open scoped BigOperators
variable {R L M : Type*} [Fintype R] [AddCommGroup M]

def retainedSum (keep : R → Bool) (f : R → M) : M :=
  ∑ r, if keep r then f r else 0

def deletedSum (keep : R → Bool) (f : R → M) : M :=
  ∑ r, if keep r then 0 else f r

def correction (keep accepted : R → Bool) (old fresh : R → M) : M :=
  ∑ r, if keep r then (if accepted r then 0 else fresh r - old r) else 0

def patched (keep accepted : R → Bool) (old fresh : R → M) : M :=
  (∑ r, old r) - deletedSum keep old + correction keep accepted old fresh

/-- Exact deletion and signed relabel correction, including zero work for a
certified unchanged contribution. No conclusion about the sum is a hypothesis. -/
theorem patch_exact (keep accepted : R → Bool) (old fresh : R → M)
    (sound : ∀ r, keep r = true → accepted r = true → old r = fresh r) :
    patched keep accepted old fresh = retainedSum keep fresh := by
  unfold patched deletedSum correction retainedSum
  rw [← Finset.sum_sub_distrib, ← Finset.sum_add_distrib]
  apply Finset.sum_congr rfl
  intro r _
  cases hk : keep r <;> cases ha : accepted r <;> simp [hk, ha]
  exact sound r hk ha

/-- A label-dependent record contribution, with arbitrary exact cell encoding. -/
theorem label_patch_exact (keep accepted : R → Bool) (oldLabel newLabel : R → L)
    (contribution : R → L → M)
    (sound : ∀ r, keep r = true → accepted r = true → oldLabel r = newLabel r) :
    patched keep accepted (fun r => contribution r (oldLabel r))
      (fun r => contribution r (newLabel r)) =
      retainedSum keep (fun r => contribution r (newLabel r)) := by
  apply patch_exact
  intro r hk ha
  rw [sound r hk ha]

/-- Abandonment discards the entire patch and starts from the fresh reduction.
The Boolean can encode the triggering round or persistent direct mode. -/
def roundStats (abandon : Bool) (keep accepted : R → Bool) (old fresh : R → M) : M :=
  if abandon then retainedSum keep fresh else patched keep accepted old fresh

theorem abandonment_exact (abandon : Bool) (keep accepted : R → Bool)
    (old fresh : R → M)
    (sound : ∀ r, keep r = true → accepted r = true → old r = fresh r) :
    roundStats abandon keep accepted old fresh = retainedSum keep fresh := by
  cases abandon <;> simp [roundStats, patch_exact keep accepted old fresh sound]

/-- Failed passes may be corrected regardless of whether the old label changed. -/
theorem unchanged_correction (v : M) : v - v = 0 := sub_self v

omit [Fintype R] in
/-- Soundness prevents certification of any retained changed label. -/
theorem changed_label_rejects (keep accepted : R → Bool) (oldLabel newLabel : R → L)
    (sound : ∀ r, keep r = true → accepted r = true → oldLabel r = newLabel r)
    (r : R) (hk : keep r = true) (changed : oldLabel r ≠ newLabel r) :
    accepted r = false := by
  cases h : accepted r
  · rfl
  · exact False.elim (changed (sound r hk h))

#print axioms patch_exact
#print axioms label_patch_exact
#print axioms abandonment_exact
#print axioms changed_label_rejects
end Replay
