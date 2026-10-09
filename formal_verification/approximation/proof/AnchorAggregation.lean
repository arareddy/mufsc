import Geometry

namespace FTF
open scoped BigOperators
variable {I J K E : Type*} [Fintype I] [Fintype J] [DecidableEq J]
  [Fintype K] [Nonempty K] [MetricSpace E]

noncomputable def anchorWeight (w : I → ℝ) (bucket : I → J) (j : J) : ℝ :=
  ∑ i, if bucket i=j then w i else 0

omit [Fintype J] in
lemma anchorWeight_nonneg (w : I → ℝ) (hw : ∀ i, 0 ≤ w i) (bucket : I → J) (j : J) :
    0 ≤ anchorWeight w bucket j := by
  apply Finset.sum_nonneg
  intro i _
  split_ifs
  · exact hw i
  · rfl

lemma aggregate_weighted_sum (w : I → ℝ) (bucket : I → J) (f : J → ℝ) :
    (∑ j, anchorWeight w bucket j*f j) = ∑ i, w i*f (bucket i) := by
  simp only [anchorWeight, Finset.sum_mul]
  rw [Finset.sum_comm]
  apply Finset.sum_congr rfl
  intro i _
  simp [ite_mul]

lemma anchor_total_mass (w : I → ℝ) (bucket : I → J) :
    (∑ j, anchorWeight w bucket j) = ∑ i, w i := by
  simpa using aggregate_weighted_sum w bucket (fun _ => 1)

/-- The compressed anchor objective is exactly the expanded record objective,
including empty slots, coincident locations and arbitrary bucket multiplicities. -/
lemma anchor_cost_identity (w : I → ℝ) (bucket : I → J) (q : J → E) (C : K → E) :
    cost (anchorWeight w bucket) q C = cost w (fun i => q (bucket i)) C :=
  aggregate_weighted_sum w bucket (fun j => (near (q j) C)^2)

/- If record weights are constant within an anchor's ownership-group bucket,
its weight is precisely the integer multiplicity times that group weight. -/
omit [Fintype J] in
lemma anchor_count_weight (w : I → ℝ) (bucket : I → J) (v : J → ℝ)
    (h : ∀ i, w i=v (bucket i)) (j : J) :
    anchorWeight w bucket j = ((Finset.univ.filter (fun i => bucket i=j)).card : ℝ)*v j := by
  classical
  unfold anchorWeight
  have he (i : I) : (if bucket i=j then w i else 0) = if bucket i=j then v j else 0 := by
    split_ifs with hi
    · rw [h i,hi]
    · rfl
  simp_rw [he]
  rw [← Finset.sum_filter]
  simp

end FTF
