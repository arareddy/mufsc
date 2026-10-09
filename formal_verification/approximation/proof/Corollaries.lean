import Transfer

namespace FTF
open scoped BigOperators

/-- Squaring the sharp root bound with the manuscript's exact coefficients. -/
lemma split_zero_constant (E α g : ℝ) (hα : 0 ≤ α) (hg : 0 ≤ g)
    (h : Real.sqrt E ≤ Real.sqrt α*(Real.sqrt α+2)*Real.sqrt g) :
    E ≤ α*(Real.sqrt α+2)^2*g := by
  have hr : 0 ≤ Real.sqrt α*(Real.sqrt α+2)*Real.sqrt g := by positivity
  have hs : (Real.sqrt α*(Real.sqrt α+2)*Real.sqrt g)^2 = α*(Real.sqrt α+2)^2*g := by
    rw [mul_pow, mul_pow, Real.sq_sqrt hα, Real.sq_sqrt hg]
  exact ((Real.sqrt_le_left hr).mp h).trans_eq hs

lemma split_additive_constant (E α g Q η : ℝ) (hα : 0 ≤ α)
    (hg : 0 ≤ g) (hQ : 0 ≤ Q) (hη : 0 < η)
    (h : Real.sqrt E ≤ Real.sqrt α*(Real.sqrt α+2)*Real.sqrt g +
      (1+Real.sqrt α)*Real.sqrt Q) :
    E ≤ (1+η)*α*(Real.sqrt α+2)^2*g + (1+1/η)*(1+Real.sqrt α)^2*Q := by
  let a := Real.sqrt α*(Real.sqrt α+2)*Real.sqrt g
  let b := (1+Real.sqrt α)*Real.sqrt Q
  have ha : 0 ≤ a := by dsimp [a]; positivity
  have hb : 0 ≤ b := by dsimp [b]; positivity
  have hsq : E ≤ (a+b)^2 := (Real.sqrt_le_left (add_nonneg ha hb)).mp h
  have hasq : a^2=α*(Real.sqrt α+2)^2*g := by
    dsimp [a]
    rw [mul_pow, mul_pow, Real.sq_sqrt hα, Real.sq_sqrt hg]
  have hbsq : b^2=(1+Real.sqrt α)^2*Q := by
    dsimp [b]
    rw [mul_pow, Real.sq_sqrt hQ]
  have hy := young a b η hη
  rw [hasq,hbsq] at hy
  nlinarith

lemma merged_zero_constant (E α κ g : ℝ) (hα : 0 ≤ α) (hg : 0 ≤ g)
    (h : Real.sqrt E ≤ Real.sqrt α*((1+Real.sqrt α)*Real.sqrt κ+1)*Real.sqrt g) :
    E ≤ α*((1+Real.sqrt α)*Real.sqrt κ+1)^2*g := by
  have hr : 0 ≤ Real.sqrt α*((1+Real.sqrt α)*Real.sqrt κ+1)*Real.sqrt g := by positivity
  have hs : (Real.sqrt α*((1+Real.sqrt α)*Real.sqrt κ+1)*Real.sqrt g)^2 =
      α*((1+Real.sqrt α)*Real.sqrt κ+1)^2*g := by
    rw [mul_pow, mul_pow, Real.sq_sqrt hα, Real.sq_sqrt hg]
  exact ((Real.sqrt_le_left hr).mp h).trans_eq hs

variable {G K E : Type*} [Fintype G] [Nonempty G] [Fintype K] [Nonempty K] [MetricSpace E]

abbrev GroupRecords (n : G → ℕ) := (g : G) × Fin (n g)

noncomputable def groupCost (n : G → ℕ) (x : GroupRecords n → E) (g : G) (C : K → E) : ℝ :=
  ∑ j : Fin (n g), (1/(n g : ℝ)) * (near (x ⟨g,j⟩) C)^2

noncomputable def fairCost (n : G → ℕ) (x : GroupRecords n → E) (C : K → E) : ℝ :=
  Finset.univ.sup' Finset.univ_nonempty (fun g => groupCost n x g C)

omit [Fintype G] [Nonempty G] in
lemma groupCost_nonneg (n : G → ℕ) (x : GroupRecords n → E) (g : G) (C : K → E) :
    0 ≤ groupCost n x g C := by
  exact Finset.sum_nonneg fun _ _ => mul_nonneg (by positivity) (sq_nonneg _)

omit [Nonempty G] in
lemma group_cost_sum (n : G → ℕ) (x : GroupRecords n → E) (C : K → E) :
    cost (fun i : GroupRecords n => 1/(n i.1 : ℝ)) x C = ∑ g, groupCost n x g C := by
  simp only [cost, energy, Fintype.sum_sigma, groupCost]

lemma fair_le_total (n : G → ℕ) (x : GroupRecords n → E) (C : K → E) :
    fairCost n x C ≤ cost (fun i : GroupRecords n => 1/(n i.1 : ℝ)) x C := by
  rw [group_cost_sum]
  apply Finset.sup'_le
  intro g _
  exact Finset.single_le_sum (fun g _ => groupCost_nonneg n x g C) (Finset.mem_univ g)

lemma total_le_card_fair (n : G → ℕ) (x : GroupRecords n → E) (C : K → E) :
    cost (fun i : GroupRecords n => 1/(n i.1 : ℝ)) x C ≤ (Fintype.card G : ℝ)*fairCost n x C := by
  rw [group_cost_sum]
  calc
    (∑ g, groupCost n x g C) ≤ ∑ _g : G, fairCost n x C :=
      Finset.sum_le_sum fun g _ => (show groupCost n x g C ≤
        Finset.univ.sup' Finset.univ_nonempty (fun g => groupCost n x g C) from
          Finset.le_sup' (fun g => groupCost n x g C) (Finset.mem_univ g))
    _ = _ := by simp

/-- This is the actual G-optimum to Phi-comparator conversion, with optimality
stated as a genuine assumption rather than assuming its conclusion. -/
lemma optimal_total_le_card_fair (n : G → ℕ) (x : GroupRecords n → E) (CG CP : K → E)
    (hmin : ∀ C : K → E, cost (fun i : GroupRecords n => 1/(n i.1 : ℝ)) x CG ≤
      cost (fun i : GroupRecords n => 1/(n i.1 : ℝ)) x C) :
    cost (fun i : GroupRecords n => 1/(n i.1 : ℝ)) x CG ≤ (Fintype.card G : ℝ)*fairCost n x CP :=
  (hmin CP).trans (total_le_card_fair n x CP)

/-- Finite expectation respects Phi <= G pointwise, for arbitrary finite laws. -/
lemma expect_fair_le_total {Ω : Type*} [Fintype Ω] (p : Law Ω) (n : G → ℕ)
    (x : GroupRecords n → E) (C : Ω → K → E) :
    expect p (fun o => fairCost n x (C o)) ≤
      expect p (fun o => cost (fun i : GroupRecords n => 1/(n i.1 : ℝ)) x (C o)) :=
  expect_mono p (fun o => fair_le_total n x (C o))

end FTF
