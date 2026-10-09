import AnchorAggregation
import SplitSlices

namespace FTF
open scoped BigOperators
variable {A G : Type*} [Fintype A] [Fintype G]

/-- Exact normalized mass across a client-by-group partition, including empty
slices; only each global group's total must be positive. -/
lemma client_group_normalized_mass (n : A → G → ℕ)
    (hn : ∀ g, 0 < ∑ a, (n a g : ℝ)) :
    (∑ i : (ag : A × G) × Fin (n ag.1 ag.2),
      (1 : ℝ)/(∑ a, (n a i.1.2 : ℝ))) = (Fintype.card G : ℝ) := by
  simp only [Fintype.sum_sigma, Finset.sum_const, Finset.card_univ,
    Fintype.card_fin, nsmul_eq_mul, Fintype.sum_prod_type]
  rw [Finset.sum_comm]
  have he (g : G) : (∑ a, (n a g : ℝ)*(1/(∑ c, (n c g : ℝ))))=1 := by
    rw [← Finset.sum_mul, one_div, mul_inv_cancel₀ (ne_of_gt (hn g))]
  simp_rw [he]
  simp

/-- The exact rational anchor multiplicity formula h/n_g, with no dense
synthetic expansion in the represented algorithm. -/
lemma anchor_count_divisor {I J : Type*} [Fintype I] [DecidableEq J]
    (bucket : I → J) (N : J → ℝ) :
    ∀ j, anchorWeight (fun i => 1/N (bucket i)) bucket j =
      ((Finset.univ.filter (fun i => bucket i=j)).card : ℝ)/N j := by
  intro j
  rw [anchor_count_weight _ bucket (fun j => 1/N j) (fun _ => rfl)]
  ring

end FTF
