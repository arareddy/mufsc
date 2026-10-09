import Corollaries

namespace FTF
open scoped BigOperators
variable {I G K E Ω : Type*} [Fintype I] [Fintype G] [Nonempty G] [DecidableEq G]
  [Fintype K] [Nonempty K] [MetricSpace E] [Fintype Ω]

noncomputable def groupPart (w : I → ℝ) (group : I → G) (x : I → E) (C : K → E) (g : G) : ℝ :=
  cost (fun i => if group i=g then w i else 0) x C
noncomputable def fairOn (w : I → ℝ) (group : I → G) (x : I → E) (C : K → E) : ℝ :=
  Finset.univ.sup' Finset.univ_nonempty (groupPart w group x C)

omit [Fintype G] [Nonempty G] in
lemma groupPart_nonneg (w : I → ℝ) (hw : ∀ i, 0 ≤ w i) (group : I → G)
    (x : I → E) (C : K → E) (g : G) : 0 ≤ groupPart w group x C g := by
  apply cost_nonneg
  intro i
  split_ifs
  · exact hw i
  · rfl

omit [Nonempty G] in
lemma groupPart_sum (w : I → ℝ) (group : I → G) (x : I → E) (C : K → E) :
    (∑ g, groupPart w group x C g)=cost w x C := by
  simp only [groupPart, cost, energy]
  rw [Finset.sum_comm]
  apply Finset.sum_congr rfl
  intro i _
  simp [ite_mul]

lemma fairOn_le_cost (w : I → ℝ) (hw : ∀ i, 0 ≤ w i) (group : I → G)
    (x : I → E) (C : K → E) : fairOn w group x C ≤ cost w x C := by
  rw [← groupPart_sum w group x C]
  apply Finset.sup'_le
  intro g _
  exact Finset.single_le_sum (fun g _ => groupPart_nonneg w hw group x C g) (Finset.mem_univ g)

lemma cost_le_card_fairOn (w : I → ℝ) (group : I → G) (x : I → E) (C : K → E) :
    cost w x C ≤ (Fintype.card G : ℝ)*fairOn w group x C := by
  rw [← groupPart_sum w group x C]
  calc
    (∑ g, groupPart w group x C g) ≤ ∑ _g : G, fairOn w group x C :=
      Finset.sum_le_sum fun g _ => Finset.le_sup' (groupPart w group x C) (Finset.mem_univ g)
    _ = _ := by simp

/-- Converts the sharp split root bound to the full additive fairness bound for
any finite number of groups and any reference tuple. -/
theorem fair_additive_from_root (w : I → ℝ) (hw : ∀ i, 0 ≤ w i) (group : I → G)
    (x : I → E) (ref : K → E) (p : Law Ω) (C : Ω → K → E)
    (α Q η : ℝ) (hα : 0 ≤ α) (hQ : 0 ≤ Q) (hη : 0 < η)
    (hroot : Real.sqrt (expect p (fun o => cost w x (C o))) ≤
      Real.sqrt α*(Real.sqrt α+2)*Real.sqrt (cost w x ref)+(1+Real.sqrt α)*Real.sqrt Q) :
    expect p (fun o => fairOn w group x (C o)) ≤
      (Fintype.card G : ℝ)*(1+η)*α*(Real.sqrt α+2)^2*fairOn w group x ref +
      (1+1/η)*(1+Real.sqrt α)^2*Q := by
  have hE := expect_mono p (fun o => fairOn_le_cost w hw group x (C o))
  have hs := split_additive_constant _ α (cost w x ref) Q η hα (cost_nonneg w hw x ref) hQ hη hroot
  have hg := mul_le_mul_of_nonneg_left (cost_le_card_fairOn w group x ref)
    (show 0 ≤ (1+η)*α*(Real.sqrt α+2)^2 by positivity)
  nlinarith

lemma fair_zero_from_root (w : I → ℝ) (hw : ∀ i, 0 ≤ w i) (group : I → G)
    (x : I → E) (ref : K → E) (p : Law Ω) (C : Ω → K → E) (α : ℝ) (hα : 0 ≤ α)
    (hroot : Real.sqrt (expect p (fun o => cost w x (C o))) ≤
      Real.sqrt α*(Real.sqrt α+2)*Real.sqrt (cost w x ref)) :
    expect p (fun o => fairOn w group x (C o)) ≤
      (Fintype.card G : ℝ)*α*(Real.sqrt α+2)^2*fairOn w group x ref := by
  have hE := expect_mono p (fun o => fairOn_le_cost w hw group x (C o))
  have hs := split_zero_constant _ α (cost w x ref) hα (cost_nonneg w hw x ref) hroot
  have hg := mul_le_mul_of_nonneg_left (cost_le_card_fairOn w group x ref)
    (show 0 ≤ α*(Real.sqrt α+2)^2 by positivity)
  nlinarith

end FTF
