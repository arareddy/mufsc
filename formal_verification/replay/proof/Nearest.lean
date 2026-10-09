import Mathlib.Data.Real.Basic
import Mathlib.Data.Finset.Max
import Mathlib.Data.Fintype.Basic

/-! A finite exact nearest-label map with the smallest-label tie rule. This is a
mathematical, noncomputable specification; no executable comparison linkage is
claimed. Strict certificates bypass the tie rule safely. -/
namespace Replay
variable {L : Type*} [Fintype L] [LinearOrder L] [Nonempty L]

noncomputable def minimizers (score : L → ℝ) : Finset L :=
  Finset.univ.filter (fun j => ∀ m, score j ≤ score m)

omit [LinearOrder L] in
theorem minimizers_nonempty (score : L → ℝ) : (minimizers score).Nonempty := by
  classical
  obtain ⟨j, _, hj⟩ := Finset.exists_min_image Finset.univ score Finset.univ_nonempty
  exact ⟨j, Finset.mem_filter.mpr ⟨Finset.mem_univ _, fun m => hj m (Finset.mem_univ _)⟩⟩

noncomputable def nearest (score : L → ℝ) : L :=
  (minimizers score).min' (minimizers_nonempty score)

theorem nearest_le (score : L → ℝ) (m : L) : score (nearest score) ≤ score m := by
  have hm := Finset.min'_mem (minimizers score) (minimizers_nonempty score)
  exact (Finset.mem_filter.mp hm).2 m

theorem nearest_tie_smallest (score : L → ℝ) (m : L)
    (hm : score m = score (nearest score)) : nearest score ≤ m := by
  apply Finset.min'_le
  apply Finset.mem_filter.mpr
  exact ⟨Finset.mem_univ _, fun j => hm.trans_le (nearest_le score j)⟩

theorem strict_winner_nearest (score : L → ℝ) (j : L)
    (strict : ∀ m, m ≠ j → score j < score m) : nearest score = j := by
  by_contra hn
  exact (not_lt_of_ge (nearest_le score j)) (strict (nearest score) hn)

/-- Exact Euclidean and exact squared-distance comparison have the same full
minimizer set and therefore the same smallest-index tie result. -/
theorem nearest_square (score : L → ℝ) (nonneg : ∀ j, 0 ≤ score j) :
    nearest (fun j => score j ^ 2) = nearest score := by
  have hm : minimizers (fun j => score j ^ 2) = minimizers score := by
    ext j
    simp only [minimizers, Finset.mem_filter, Finset.mem_univ, true_and]
    constructor
    · intro h m
      exact (sq_le_sq₀ (nonneg j) (nonneg m)).mp (h m)
    · intro h m
      exact (sq_le_sq₀ (nonneg j) (nonneg m)).mpr (h m)
  unfold nearest
  congr 1

#print axioms nearest_square
#print axioms nearest_le
#print axioms nearest_tie_smallest
#print axioms strict_winner_nearest
end Replay
