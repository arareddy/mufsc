import Mathlib.Data.Real.Archimedean
import Mathlib.Algebra.BigOperators.Ring.Finset
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Data.Finset.Lattice.Fold
import Mathlib.Order.ConditionallyCompleteLattice.Basic
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.Ring
import Mathlib.Tactic.FieldSimp
import Mathlib.Tactic.Positivity

/-!
Finite-dimensional, real-valued fixed-partition certificates and guarded refinement.
This file does not model binary64, Fraction, PRNGs, or the production executable.
Coordinates may be indexed by a product of cluster and feature types.
-/

namespace FairUpdate
open scoped BigOperators

variable {G I : Type*} [Fintype G] [Nonempty G] [Fintype I]

structure Simplex (G : Type*) [Fintype G] where
  weight : G → ℝ
  nonneg : ∀ g, 0 ≤ weight g
  sum_one : ∑ g, weight g = 1

noncomputable def groupMax (f : G → ℝ) : ℝ :=
  Finset.univ.sup' Finset.univ_nonempty f

lemma le_groupMax (f : G → ℝ) (g : G) : f g ≤ groupMax f := by
  exact Finset.le_sup' f (Finset.mem_univ g)

lemma groupMax_le (f : G → ℝ) (r : ℝ) (h : ∀ g, f g ≤ r) :
    groupMax f ≤ r := by
  exact Finset.sup'_le _ _ (fun g _ => h g)

lemma groupMax_mono (f h : G → ℝ) (hle : ∀ g, f g ≤ h g) :
    groupMax f ≤ groupMax h := by
  apply groupMax_le
  intro g
  exact (hle g).trans (le_groupMax h g)

noncomputable def weighted (w : Simplex G) (f : G → ℝ) : ℝ :=
  ∑ g, w.weight g * f g

lemma weighted_le_groupMax (w : Simplex G) (f : G → ℝ) :
    weighted w f ≤ groupMax f := by
  calc
    weighted w f ≤ ∑ g, w.weight g * groupMax f := by
      exact Finset.sum_le_sum (fun g _ => mul_le_mul_of_nonneg_left
        (le_groupMax f g) (w.nonneg g))
    _ = (∑ g, w.weight g) * groupMax f := by rw [Finset.sum_mul]
    _ = groupMax f := by rw [w.sum_one, one_mul]

/-- `a=0 → b=0` is a domain hypothesis about valid cell moments, not an axiom. -/
structure Quadratics (G I : Type*) where
  q : G → ℝ
  a : G → I → ℝ
  b : G → I → ℝ
  a_nonneg : ∀ g i, 0 ≤ a g i
  b_zero : ∀ g i, a g i = 0 → b g i = 0

noncomputable def groupCost (p : Quadratics G I) (c : I → ℝ) (g : G) : ℝ :=
  p.q g + ∑ i, (p.a g i * c i ^ 2 - 2 * p.b g i * c i)

noncomputable def fixedPhi (p : Quadratics G I) (c : I → ℝ) : ℝ :=
  groupMax (groupCost p c)

noncomputable def mass (p : Quadratics G I) (w : Simplex G) (i : I) : ℝ :=
  ∑ g, w.weight g * p.a g i

noncomputable def linear (p : Quadratics G I) (w : Simplex G) (i : I) : ℝ :=
  ∑ g, w.weight g * p.b g i

omit [Nonempty G] [Fintype I] in
lemma mass_nonneg (p : Quadratics G I) (w : Simplex G) (i : I) :
    0 ≤ mass p w i := by
  exact Finset.sum_nonneg (fun g _ => mul_nonneg (w.nonneg g) (p.a_nonneg g i))

omit [Nonempty G] [Fintype I] in
lemma linear_zero_of_mass_zero (p : Quadratics G I) (w : Simplex G) (i : I)
    (h : mass p w i = 0) : linear p w i = 0 := by
  apply Finset.sum_eq_zero
  intro g _
  have ht : w.weight g * p.a g i ≤ mass p w i :=
    Finset.single_le_sum (fun g _ => mul_nonneg (w.nonneg g) (p.a_nonneg g i))
      (Finset.mem_univ g)
  have hz : w.weight g * p.a g i = 0 :=
    le_antisymm (by simpa [h] using ht) (mul_nonneg (w.nonneg g) (p.a_nonneg g i))
  rcases mul_eq_zero.mp hz with hw | ha
  · rw [hw, zero_mul]
  · rw [p.b_zero g i ha, mul_zero]

/-- Total real division makes the zero-mass summand zero; its numerator is also zero. -/
noncomputable def dual (p : Quadratics G I) (w : Simplex G) : ℝ :=
  weighted w p.q - ∑ i, (linear p w i) ^ 2 / mass p w i

/-- Any fallback is a minimizer in a coordinate with zero weighted mass. -/
noncomputable def minimizer (p : Quadratics G I) (w : Simplex G)
    (fallback : I → ℝ) (i : I) : ℝ :=
  if mass p w i = 0 then fallback i else linear p w i / mass p w i

lemma scalar_complete_square (a b x : ℝ) (ha : a ≠ 0) :
    a * x ^ 2 - 2 * b * x + b ^ 2 / a = a * (x - b / a) ^ 2 := by
  field_simp [ha]
  ring

lemma scalar_lower_bound (a b x : ℝ) (ha : 0 ≤ a) (hz : a = 0 → b = 0) :
    -(b ^ 2 / a) ≤ a * x ^ 2 - 2 * b * x := by
  by_cases h : a = 0
  · simp [h, hz h]
  · have hs := scalar_complete_square a b x h
    have hn := mul_nonneg ha (sq_nonneg (x - b / a))
    linarith

lemma scalar_value_at_candidate (a b z : ℝ) (hz : a = 0 → b = 0) :
    a * (if a = 0 then z else b / a) ^ 2 -
      2 * b * (if a = 0 then z else b / a) = -(b ^ 2 / a) := by
  by_cases h : a = 0
  · simp [h, hz h]
  · simp only [if_neg h]
    have hs := scalar_complete_square a b (b / a) h
    simp only [sub_self, zero_pow (by decide : 2 ≠ 0), mul_zero] at hs
    linarith

omit [Nonempty G] in
lemma weighted_expansion (p : Quadratics G I) (w : Simplex G) (c : I → ℝ) :
    weighted w (groupCost p c) = weighted w p.q +
      ∑ i, (mass p w i * c i ^ 2 - 2 * linear p w i * c i) := by
  classical
  simp only [weighted, groupCost, mul_add, Finset.sum_add_distrib, Finset.mul_sum]
  congr 1
  rw [Finset.sum_comm]
  apply Finset.sum_congr rfl
  intro i _
  simp only [mass, linear, Finset.sum_mul, Finset.mul_sum, mul_sub,
    Finset.sum_sub_distrib]
  congr 1 <;> apply Finset.sum_congr rfl <;> intros <;> ring

omit [Nonempty G] in
lemma dual_le_weighted (p : Quadratics G I) (w : Simplex G) (c : I → ℝ) :
    dual p w ≤ weighted w (groupCost p c) := by
  rw [weighted_expansion]
  unfold dual
  have h := Finset.sum_le_sum (s := (Finset.univ : Finset I))
    (fun i _ => scalar_lower_bound (mass p w i) (linear p w i) (c i)
      (mass_nonneg p w i) (linear_zero_of_mass_zero p w i))
  rw [Finset.sum_neg_distrib] at h
  linarith

omit [Nonempty G] in
lemma weighted_minimizer_eq_dual (p : Quadratics G I) (w : Simplex G)
    (fallback : I → ℝ) :
    weighted w (groupCost p (minimizer p w fallback)) = dual p w := by
  rw [weighted_expansion]
  unfold dual
  have h : (∑ i, (mass p w i * minimizer p w fallback i ^ 2 -
      2 * linear p w i * minimizer p w fallback i)) =
      -(∑ i, (linear p w i) ^ 2 / mass p w i) := by
    rw [← Finset.sum_neg_distrib]
    apply Finset.sum_congr rfl
    intro i _
    exact scalar_value_at_candidate _ _ _ (linear_zero_of_mass_zero p w i)
  rw [h, sub_eq_add_neg]

lemma weak_duality (p : Quadratics G I) (w : Simplex G) (c : I → ℝ) :
    dual p w ≤ fixedPhi p c := by
  exact (dual_le_weighted p w c).trans (weighted_le_groupMax w (groupCost p c))

noncomputable def optimum (p : Quadratics G I) : ℝ := sInf (Set.range (fixedPhi p))

lemma objective_bddBelow (p : Quadratics G I) (w : Simplex G) :
    BddBelow (Set.range (fixedPhi p)) := by
  refine ⟨dual p w, ?_⟩
  rintro _ ⟨c, rfl⟩
  exact weak_duality p w c

lemma dual_le_optimum (p : Quadratics G I) (w : Simplex G) :
    dual p w ≤ optimum p := by
  apply le_csInf
  · exact ⟨fixedPhi p (fun _ => 0), Set.mem_range_self _⟩
  · rintro _ ⟨c, rfl⟩
    exact weak_duality p w c

lemma optimum_le_returned (p : Quadratics G I) (w : Simplex G) (returned : I → ℝ) :
    optimum p ≤ fixedPhi p returned := by
  exact csInf_le (objective_bddBelow p w) (Set.mem_range_self returned)

/-- No primal attainment, successful search, or strong duality is assumed. -/
lemma returned_gap_certificate (p : Quadratics G I) (w : Simplex G) (returned : I → ℝ) :
    0 ≤ fixedPhi p returned - optimum p ∧
    fixedPhi p returned - optimum p ≤ fixedPhi p returned - dual p w := by
  constructor
  · exact sub_nonneg.mpr (optimum_le_returned p w returned)
  · exact sub_le_sub_left (dual_le_optimum p w) _

lemma best_evaluated_certificate {E : Type*} [Fintype E] [Nonempty E]
    (p : Quadratics G I) (evaluated : E → Simplex G) (returned : I → ℝ) :
    0 ≤ fixedPhi p returned - optimum p ∧
    fixedPhi p returned - optimum p ≤
      fixedPhi p returned - groupMax (fun e => dual p (evaluated e)) := by
  have hlow : groupMax (fun e => dual p (evaluated e)) ≤ optimum p := by
    apply groupMax_le
    exact fun e => dual_le_optimum p (evaluated e)
  constructor
  · exact sub_nonneg.mpr (optimum_le_returned p (evaluated (Classical.choice inferInstance)) returned)
  · exact sub_le_sub_left hlow _

/-- The score is evaluated on exactly the candidate that would be returned. -/
noncomputable def guarded {X : Type*} (score : X → ℝ) (incumbent candidate : X) : X :=
  if score candidate ≤ score incumbent then candidate else incumbent

lemma guarded_nonincrease {X : Type*} (score : X → ℝ) (incumbent candidate : X) :
    score (guarded score incumbent candidate) ≤ score incumbent := by
  by_cases h : score candidate ≤ score incumbent
  · simpa only [guarded, if_pos h] using h
  · simp only [guarded, if_neg h, le_refl]

section Reassignment
variable {P K X : Type*} [Fintype P] [Fintype K] [Nonempty K]

noncomputable def nearestDistance (distance : P → X → ℝ) (c : K → X) (p : P) : ℝ :=
  Finset.univ.inf' Finset.univ_nonempty (fun k => distance p (c k))

omit [Fintype P] in
lemma nearestDistance_le (distance : P → X → ℝ) (c : K → X) (p : P) (k : K) :
    nearestDistance distance c p ≤ distance p (c k) := by
  exact Finset.inf'_le _ (Finset.mem_univ k)

noncomputable def assignedCost (weight : G → P → ℝ) (distance : P → X → ℝ)
    (assignment : P → K) (c : K → X) (g : G) : ℝ :=
  ∑ p, weight g p * distance p (c (assignment p))

noncomputable def nearestCost (weight : G → P → ℝ) (distance : P → X → ℝ)
    (c : K → X) (g : G) : ℝ :=
  ∑ p, weight g p * nearestDistance distance c p

omit [Fintype G] [Nonempty G] in
lemma nearestCost_le_assignedCost (weight : G → P → ℝ)
    (hnonneg : ∀ g p, 0 ≤ weight g p) (distance : P → X → ℝ)
    (assignment : P → K) (c : K → X) (g : G) :
    nearestCost weight distance c g ≤ assignedCost weight distance assignment c g := by
  apply Finset.sum_le_sum
  intro p _
  exact mul_le_mul_of_nonneg_left (nearestDistance_le distance c p (assignment p)) (hnonneg g p)

lemma nearest_max_le_assigned_max (weight : G → P → ℝ)
    (hnonneg : ∀ g p, 0 ≤ weight g p) (distance : P → X → ℝ)
    (assignment : P → K) (c : K → X) :
    groupMax (nearestCost weight distance c) ≤
      groupMax (assignedCost weight distance assignment c) := by
  apply groupMax_mono
  exact fun g => nearestCost_le_assignedCost weight hnonneg distance assignment c g

omit [Fintype G] [Nonempty G] in
lemma assigned_eq_nearest_of_minimizing (weight : G → P → ℝ)
    (distance : P → X → ℝ) (assignment : P → K) (c : K → X)
    (hnearest : ∀ p k, distance p (c (assignment p)) ≤ distance p (c k)) :
    assignedCost weight distance assignment c = nearestCost weight distance c := by
  funext g
  apply Finset.sum_congr rfl
  intro p _
  congr 1
  apply le_antisymm
  · exact Finset.le_inf' _ _ (fun k _ => hnearest p k)
  · exact nearestDistance_le distance c p (assignment p)

/-- Fixed partition is the incumbent's nearest partition; the output is reassessed by minima. -/
lemma guarded_refinement_nonincrease (weight : G → P → ℝ)
    (hnonneg : ∀ g p, 0 ≤ weight g p) (distance : P → X → ℝ)
    (assignment : P → K) (incumbent candidate : K → X)
    (hnearest : ∀ p k, distance p (incumbent (assignment p)) ≤ distance p (incumbent k)) :
    groupMax (nearestCost weight distance
      (guarded (fun c => groupMax (assignedCost weight distance assignment c)) incumbent candidate)) ≤
    groupMax (nearestCost weight distance incumbent) := by
  let score := fun c => groupMax (assignedCost weight distance assignment c)
  calc
    groupMax (nearestCost weight distance (guarded score incumbent candidate)) ≤
        score (guarded score incumbent candidate) :=
      nearest_max_le_assigned_max weight hnonneg distance assignment _
    _ ≤ score incumbent := guarded_nonincrease score incumbent candidate
    _ = groupMax (nearestCost weight distance incumbent) := by
      dsimp only [score]
      rw [assigned_eq_nearest_of_minimizing weight distance assignment incumbent hnearest]
end Reassignment

/-- Convex mixing preserves the simplex, including its boundary. -/
noncomputable def mix (u v : Simplex G) (t : ℝ) (ht : 0 ≤ t) (ht1 : t ≤ 1) : Simplex G where
  weight g := t * u.weight g + (1 - t) * v.weight g
  nonneg g := add_nonneg (mul_nonneg ht (u.nonneg g))
    (mul_nonneg (sub_nonneg.mpr ht1) (v.nonneg g))
  sum_one := by
    simp only [Finset.sum_add_distrib, ← Finset.mul_sum, u.sum_one, v.sum_one]
    ring

omit [Nonempty G] in
lemma weighted_mix (u v : Simplex G) (t : ℝ) (ht : 0 ≤ t) (ht1 : t ≤ 1) (f : G → ℝ) :
    weighted (mix u v t ht ht1) f = t * weighted u f + (1 - t) * weighted v f := by
  simp only [weighted, mix, add_mul, mul_assoc, Finset.sum_add_distrib, Finset.mul_sum]

omit [Nonempty G] in
/-- The closed-form dual equals the infimum; the displayed minimizer proves attainment. -/
lemma dual_eq_infimum (p : Quadratics G I) (w : Simplex G) :
    dual p w = sInf (Set.range (fun c => weighted w (groupCost p c))) := by
  apply le_antisymm
  · apply le_csInf
    · exact ⟨weighted w (groupCost p (fun _ => 0)), Set.mem_range_self _⟩
    · rintro _ ⟨c, rfl⟩
      exact dual_le_weighted p w c
  · have hb : BddBelow (Set.range (fun c => weighted w (groupCost p c))) := by
      refine ⟨dual p w, ?_⟩
      rintro _ ⟨c, rfl⟩
      exact dual_le_weighted p w c
    have h := csInf_le hb (Set.mem_range_self (minimizer p w (fun _ => 0)))
    simpa only [weighted_minimizer_eq_dual] using h

omit [Nonempty G] in
/-- Jensen's concavity inequality on the whole simplex. No interior assumption. -/
lemma dual_concave (p : Quadratics G I) (u v : Simplex G)
    (t : ℝ) (ht : 0 ≤ t) (ht1 : t ≤ 1) :
    t * dual p u + (1 - t) * dual p v ≤ dual p (mix u v t ht ht1) := by
  let w := mix u v t ht ht1
  let c := minimizer p w (fun _ => 0)
  have hu := mul_le_mul_of_nonneg_left (dual_le_weighted p u c) ht
  have hv := mul_le_mul_of_nonneg_left (dual_le_weighted p v c) (sub_nonneg.mpr ht1)
  calc
    t * dual p u + (1 - t) * dual p v ≤
      t * weighted u (groupCost p c) + (1 - t) * weighted v (groupCost p c) := add_le_add hu hv
    _ = weighted w (groupCost p c) := (weighted_mix u v t ht ht1 _).symm
    _ = dual p w := weighted_minimizer_eq_dual p w _

omit [Nonempty G] in
lemma weighted_difference (u v : Simplex G) (f : G → ℝ) :
    weighted v f = weighted u f + ∑ g, (v.weight g - u.weight g) * f g := by
  simp only [sub_mul, Finset.sum_sub_distrib, weighted]
  ring

omit [Nonempty G] in
/-- Costs at the explicitly constructed minimizer are a supergradient, even at the boundary. -/
lemma dual_supergradient (p : Quadratics G I) (u v : Simplex G) (fallback : I → ℝ) :
    dual p v ≤ dual p u + ∑ g, (v.weight g - u.weight g) *
      groupCost p (minimizer p u fallback) g := by
  have h := dual_le_weighted p v (minimizer p u fallback)
  rw [weighted_difference u v, weighted_minimizer_eq_dual] at h
  exact h

end FairUpdate
