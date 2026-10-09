import WeightedRoot
import Mathlib.Topology.MetricSpace.Basic
import Mathlib.Data.Finset.Lattice.Fold

/-! Finite weighted clustering geometry in any metric space. In particular these
statements apply to every finite-dimensional Euclidean space in the manuscript. -/
namespace FTF
open scoped BigOperators
variable {I K E : Type*} [Fintype I] [Fintype K] [Nonempty K] [MetricSpace E]

noncomputable def near (x : E) (C : K → E) : ℝ :=
  Finset.univ.inf' Finset.univ_nonempty (fun j => dist x (C j))

lemma near_nonneg (x : E) (C : K → E) : 0 ≤ near x C :=
  Finset.le_inf' _ _ (fun _ _ => dist_nonneg)

lemma near_le (x : E) (C : K → E) (j : K) : near x C ≤ dist x (C j) :=
  Finset.inf'_le _ (Finset.mem_univ j)

lemma near_triangle (x y : E) (C : K → E) : near x C ≤ dist x y + near y C := by
  obtain ⟨j, _, hj⟩ := Finset.exists_mem_eq_inf' Finset.univ_nonempty (fun j => dist y (C j))
  change near x C ≤ dist x y + Finset.univ.inf' Finset.univ_nonempty (fun j => dist y (C j))
  rw [hj]
  exact (near_le x C j).trans (dist_triangle x y (C j))

noncomputable def cost (w : I → ℝ) (x : I → E) (C : K → E) : ℝ :=
  energy w (fun i => near (x i) C)

def distortion (w : I → ℝ) (x q : I → E) : ℝ := energy w (fun i => dist (x i) (q i))

lemma cost_nonneg (w : I → ℝ) (hw : ∀ i, 0 ≤ w i) (x : I → E) (C : K → E) :
    0 ≤ cost w x C := energy_nonneg _ _ hw

lemma distortion_nonneg (w : I → ℝ) (hw : ∀ i, 0 ≤ w i) (x q : I → E) :
    0 ≤ distortion w x q := energy_nonneg _ _ hw

lemma distortion_symm (w : I → ℝ) (x q : I → E) : distortion w x q = distortion w q x := by
  simp only [distortion, dist_comm]

/-- Both directions of eq:g-h-minkowski follow by swapping x and q. -/
lemma cost_root_transfer (w : I → ℝ) (hw : ∀ i, 0 ≤ w i) (x q : I → E) (C : K → E) :
    Real.sqrt (cost w x C) ≤ Real.sqrt (distortion w x q)+Real.sqrt (cost w q C) := by
  exact (root_mono w _ _ hw (fun i => near_nonneg (x i) C)
    (fun i => near_triangle (x i) (q i) C)).trans (root_add w _ _ hw)

lemma distortion_root_triangle (w : I → ℝ) (hw : ∀ i, 0 ≤ w i) (x z q : I → E) :
    Real.sqrt (distortion w x q) ≤ Real.sqrt (distortion w x z)+Real.sqrt (distortion w z q) := by
  exact (root_mono w _ _ hw (fun _ => dist_nonneg)
    (fun i => dist_triangle (x i) (z i) (q i))).trans (root_add w _ _ hw)

lemma distortion_bound (w : I → ℝ) (hw : ∀ i, 0 ≤ w i) (x q : I → E) (B : ℝ)
    (h : ∀ i, dist (x i) (q i)^2 ≤ B) :
    distortion w x q ≤ (∑ i, w i)*B := by
  rw [Finset.sum_mul]
  exact Finset.sum_le_sum fun i _ => mul_le_mul_of_nonneg_left (h i) (hw i)

/-- Equal normalization within each nonempty group yields total mass m. -/
lemma normalized_group_mass {G : Type*} [Fintype G] (n : G → ℕ) (hn : ∀ g, 0 < n g) :
    (∑ i : (g : G) × Fin (n g), (1 : ℝ)/(n i.1 : ℝ)) = Fintype.card G := by
  simp only [Fintype.sum_sigma, Finset.sum_const, Finset.card_univ, Fintype.card_fin, nsmul_eq_mul]
  have h (g : G) : (n g : ℝ)*(1/(n g : ℝ)) = 1 := by
    have hne : (n g : ℝ) ≠ 0 := by exact_mod_cast (hn g).ne'
    field_simp
  simp_rw [h]
  simp

/-- Geometric grid + represented residual. Input bounds concern actual points;
no floating-point rounding implementation is assumed verified. -/
lemma represented_snap_bound (w : I → ℝ) (hw : ∀ i, 0 ≤ w i) (z grid q : I → E)
    (B R : ℝ) (hB : ∀ i, dist (z i) (grid i)^2 ≤ B)
    (hR : ∀ i, dist (grid i) (q i)^2 ≤ R) :
    Real.sqrt (distortion w z q) ≤
      Real.sqrt ((∑ i, w i)*B)+Real.sqrt ((∑ i, w i)*R) := by
  exact (distortion_root_triangle w hw z grid q).trans
    (add_le_add (Real.sqrt_le_sqrt (distortion_bound w hw z grid B hB))
      (Real.sqrt_le_sqrt (distortion_bound w hw grid q R hR)))

end FTF

namespace FTF
variable {I K K' E : Type*} [Fintype I] [Fintype K] [Nonempty K]
  [Fintype K'] [Nonempty K'] [MetricSpace E]
lemma near_mono_centers (x : E) (C : K → E) (C' : K' → E)
    (h : ∀ j, ∃ j', C' j'=C j) : near x C' ≤ near x C := by
  obtain ⟨j, _, hj⟩ := Finset.exists_mem_eq_inf' Finset.univ_nonempty (fun j => dist x (C j))
  obtain ⟨j', hj'⟩ := h j
  change near x C' ≤ Finset.univ.inf' Finset.univ_nonempty (fun j => dist x (C j))
  rw [hj, ← hj']
  exact near_le x C' j'

lemma cost_mono_centers (w : I → ℝ) (hw : ∀ i, 0 ≤ w i) (x : I → E)
    (C : K → E) (C' : K' → E) (h : ∀ j, ∃ j', C' j'=C j) : cost w x C' ≤ cost w x C := by
  apply Finset.sum_le_sum
  intro i _
  apply mul_le_mul_of_nonneg_left _ (hw i)
  have hn := near_nonneg (x i) C'
  have hle := near_mono_centers (x i) C C' h
  nlinarith

lemma zero_cost_completion (w : I → ℝ) (hw : ∀ i, 0 ≤ w i) (x : I → E)
    (C : K → E) (C' : K' → E) (h : ∀ j, ∃ j', C' j'=C j) (hz : cost w x C=0) :
    cost w x C'=0 := le_antisymm (by simpa [hz] using cost_mono_centers w hw x C C' h)
      (cost_nonneg w hw x C')

lemma cost_zero_of_covered (w : I → ℝ) (x : I → E) (C : K → E)
    (h : ∀ i, ∃ j, C j=x i) : cost w x C=0 := by
  apply Finset.sum_eq_zero
  intro i _
  obtain ⟨j,hj⟩ := h i
  have hl := near_le (x i) C j
  rw [hj, dist_self] at hl
  have hn : near (x i) C=0 := le_antisymm hl (near_nonneg _ _)
  simp [hn]
end FTF
