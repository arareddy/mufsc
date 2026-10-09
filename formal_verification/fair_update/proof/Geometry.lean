import Moments

namespace FairUpdate.Geometry
open scoped BigOperators
open FairUpdate.Moments

/-- Two optimality comparisons imply the direction of change of each objective. -/
lemma two_weight_comparison (t u a₀ b₀ a₁ b₁ : ℝ)
    (ht : 0 ≤ t) (hu : u ≤ 1) (htu : t < u)
    (h₀ : t*a₀ + (1-t)*b₀ ≤ t*a₁ + (1-t)*b₁)
    (h₁ : u*a₁ + (1-u)*b₁ ≤ u*a₀ + (1-u)*b₀) :
    a₁ ≤ a₀ ∧ b₀ ≤ b₁ := by
  have ht1 : 0 ≤ 1-t := by linarith
  have hu0 : 0 ≤ u := by linarith
  have hA₀ := mul_le_mul_of_nonneg_left h₀ (sub_nonneg.mpr hu)
  have hA₁ := mul_le_mul_of_nonneg_left h₁ ht1
  have hB₀ := mul_le_mul_of_nonneg_left h₀ hu0
  have hB₁ := mul_le_mul_of_nonneg_left h₁ ht
  constructor
  · by_contra h
    have hp := mul_pos (sub_pos.mpr htu) (sub_pos.mpr (lt_of_not_ge h))
    nlinarith
  · by_contra h
    have hp := mul_pos (sub_pos.mpr htu) (sub_pos.mpr (lt_of_not_ge h))
    nlinarith

/-- A selected minimizer at each lambda has nonincreasing A cost and nondecreasing B cost. -/
lemma selected_minimizers_monotone {X : Type*} (fA fB : X → ℝ) (curve : ℝ → X)
    (hmin : ∀ t, 0 ≤ t → t ≤ 1 → ∀ x,
      t * fA (curve t) + (1-t) * fB (curve t) ≤ t * fA x + (1-t) * fB x)
    (t u : ℝ) (ht : 0 ≤ t) (htu : t ≤ u) (hu : u ≤ 1) :
    fA (curve u) ≤ fA (curve t) ∧ fB (curve t) ≤ fB (curve u) := by
  rcases eq_or_lt_of_le htu with h | h
  · subst u
    exact ⟨le_rfl, le_rfl⟩
  · exact two_weight_comparison t u _ _ _ _ ht hu h
      (hmin t ht (htu.trans hu) (curve u))
      (hmin u (ht.trans htu) hu (curve t))

noncomputable def binarySimplex (t : ℝ) (ht : 0 ≤ t) (ht1 : t ≤ 1) : Simplex Bool where
  weight g := if g then 1-t else t
  nonneg g := by cases g <;> simp [ht, sub_nonneg.mpr ht1]
  sum_one := by simp

lemma weighted_binary (t : ℝ) (ht : 0 ≤ t) (ht1 : t ≤ 1) (f : Bool → ℝ) :
    weighted (binarySimplex t ht ht1) f = t*f false + (1-t)*f true := by
  simp [weighted, binarySimplex, add_comm]

/-- Concrete quadratic minimizers from the existing proved formula, including boundary fallbacks. -/
lemma quadratic_lambda_monotonicity {I : Type*} [Fintype I] (p : Quadratics Bool I)
    (fallback : ℝ → I → ℝ) (t u : ℝ) (ht : 0 ≤ t) (htu : t ≤ u) (hu : u ≤ 1) :
    let ct := minimizer p (binarySimplex t ht (htu.trans hu)) (fallback t)
    let cu := minimizer p (binarySimplex u (ht.trans htu) hu) (fallback u)
    groupCost p cu false ≤ groupCost p ct false ∧ groupCost p ct true ≤ groupCost p cu true := by
  dsimp only
  rcases eq_or_lt_of_le htu with h | h
  · subst u
    exact ⟨le_rfl, le_rfl⟩
  · have h₀ := dual_le_weighted p (binarySimplex t ht (htu.trans hu))
      (minimizer p (binarySimplex u (ht.trans htu) hu) (fallback u))
    rw [← weighted_minimizer_eq_dual p (binarySimplex t ht (htu.trans hu)) (fallback t)] at h₀
    have h₁ := dual_le_weighted p (binarySimplex u (ht.trans htu) hu)
      (minimizer p (binarySimplex t ht (htu.trans hu)) (fallback t))
    rw [← weighted_minimizer_eq_dual p (binarySimplex u (ht.trans htu) hu) (fallback u)] at h₁
    simp only [weighted_binary] at h₀ h₁
    exact two_weight_comparison t u _ _ _ _ ht hu h h₀ h₁

/-- When the denominator is nonzero this is exactly the manuscript's two-mean formula. -/
lemma binary_minimizer_formula {I : Type*} [Fintype I] (p : Quadratics Bool I)
    (t : ℝ) (ht : 0 ≤ t) (ht1 : t ≤ 1) (fallback : I → ℝ) (i : I)
    (hden : t*p.a false i + (1-t)*p.a true i ≠ 0) :
    minimizer p (binarySimplex t ht ht1) fallback i =
      (t*p.b false i + (1-t)*p.b true i) / (t*p.a false i + (1-t)*p.a true i) := by
  have hm : mass p (binarySimplex t ht ht1) i = t*p.a false i + (1-t)*p.a true i := by
    simp [mass, binarySimplex, add_comm]
  have hb : linear p (binarySimplex t ht ht1) i = t*p.b false i + (1-t)*p.b true i := by
    simp [linear, binarySimplex, add_comm]
  simp [minimizer, hm, hb, hden]

variable {D : Type*} [Fintype D]
noncomputable def along (a b : D → ℝ) (t : ℝ) (d : D) : ℝ := a d + t*(b d-a d)
noncomputable def directionSquare (a b : D → ℝ) : ℝ := ∑ d, (b d-a d)^2
noncomputable def directionDot (x a b : D → ℝ) : ℝ := ∑ d, (x d-a d)*(b d-a d)

lemma projection_expansion_a (x a b : D → ℝ) (t : ℝ) :
    squaredDistance x a = squaredDistance x (along a b t) + squaredDistance (along a b t) a +
      2*t*(directionDot x a b - t*directionSquare a b) := by
  simp only [squaredDistance, along, directionDot, directionSquare, Finset.mul_sum,
    mul_sub, ← Finset.sum_sub_distrib, ← Finset.sum_add_distrib]
  apply Finset.sum_congr rfl
  intro d _
  ring

lemma projection_expansion_b (x a b : D → ℝ) (t : ℝ) :
    squaredDistance x b = squaredDistance x (along a b t) + squaredDistance (along a b t) b +
      2*(t-1)*(directionDot x a b - t*directionSquare a b) := by
  simp only [squaredDistance, along, directionDot, directionSquare, Finset.mul_sum,
    mul_sub, ← Finset.sum_sub_distrib, ← Finset.sum_add_distrib]
  apply Finset.sum_congr rfl
  intro d _
  ring

noncomputable def clampParameter (h v : ℝ) : ℝ :=
  if h ≤ 0 then 0 else if v ≤ h then 1 else h/v

lemma clamp_properties (h v : ℝ) (hv : 0 < v) :
    let t := clampParameter h v
    0 ≤ t ∧ t ≤ 1 ∧ 0 ≤ t*(h-t*v) ∧ 0 ≤ (t-1)*(h-t*v) := by
  unfold clampParameter
  by_cases hh : h ≤ 0
  · simp [hh, neg_nonneg.mpr hh]
  · by_cases hhigh : v ≤ h
    · simp [hh, hhigh, sub_nonneg.mpr hhigh]
    · have hlo : 0 ≤ h/v := div_nonneg (le_of_lt (lt_of_not_ge hh)) (le_of_lt hv)
      have hhi : h/v ≤ 1 := (div_le_one hv).mpr (le_of_lt (lt_of_not_ge hhigh))
      have hz : h - h/v*v = 0 := by field_simp
      simp [hh, hhigh, hlo, hhi, hz]

lemma coincident_of_direction_zero (a b : D → ℝ) (hz : directionSquare a b = 0) : a = b := by
  funext d
  have h : (b d-a d)^2 ≤ directionSquare a b :=
    Finset.single_le_sum (fun e _ => sq_nonneg (b e-a e)) (Finset.mem_univ d)
  have hs : (b d-a d)^2 = 0 := le_antisymm (by simpa [hz] using h) (sq_nonneg _)
  nlinarith

/-- Constructive clamped orthogonal projection simultaneously decreases distances to both endpoints. -/
lemma segment_projection_nonincrease (x a b : D → ℝ) :
    ∃ t : ℝ, 0 ≤ t ∧ t ≤ 1 ∧
      squaredDistance (along a b t) a ≤ squaredDistance x a ∧
      squaredDistance (along a b t) b ≤ squaredDistance x b := by
  have hv : 0 ≤ directionSquare a b := Finset.sum_nonneg (fun d _ => sq_nonneg (b d-a d))
  by_cases hz : directionSquare a b = 0
  · have hab := coincident_of_direction_zero a b hz
    subst b
    refine ⟨0, le_rfl, zero_le_one, ?_, ?_⟩ <;>
      simpa [along, squaredDistance] using squaredDistance_nonneg x a
  · have hp := clamp_properties (directionDot x a b) (directionSquare a b) (lt_of_le_of_ne hv (Ne.symm hz))
    dsimp only at hp
    refine ⟨clampParameter (directionDot x a b) (directionSquare a b), hp.1, hp.2.1, ?_, ?_⟩
    · have he := projection_expansion_a x a b (clampParameter (directionDot x a b) (directionSquare a b))
      have hn := squaredDistance_nonneg x (along a b (clampParameter (directionDot x a b) (directionSquare a b)))
      nlinarith [hp.2.2.1]
    · have he := projection_expansion_b x a b (clampParameter (directionDot x a b) (directionSquare a b))
      have hn := squaredDistance_nonneg x (along a b (clampParameter (directionDot x a b) (directionSquare a b)))
      nlinarith [hp.2.2.2]


lemma projection_expansion_segment (x a b : D → ℝ) (s t : ℝ) :
    squaredDistance x (along a b s) = squaredDistance x (along a b t) +
      (s-t)^2 * directionSquare a b - 2*(s-t)*(directionDot x a b-t*directionSquare a b) := by
  simp only [squaredDistance, along, directionDot, directionSquare, Finset.mul_sum,
    mul_sub, ← Finset.sum_sub_distrib, ← Finset.sum_add_distrib]
  apply Finset.sum_congr rfl
  intro d _
  ring

lemma clamp_variational (h v s : ℝ) (hv : 0 < v) (hs : 0 ≤ s) (hs1 : s ≤ 1) :
    (s-clampParameter h v)*(h-clampParameter h v*v) ≤ 0 := by
  have hp := clamp_properties h v hv
  dsimp only at hp
  have h₀ := mul_nonneg (sub_nonneg.mpr hs1) hp.2.2.1
  have h₁ := mul_nonneg hs hp.2.2.2
  nlinarith

/-- The clamped parameter really minimizes distance to the entire segment, not only its endpoints. -/
lemma clamped_projection_is_nearest (x a b : D → ℝ) (hv : 0 < directionSquare a b)
    (s : ℝ) (hs : 0 ≤ s) (hs1 : s ≤ 1) :
    squaredDistance x (along a b (clampParameter (directionDot x a b) (directionSquare a b))) ≤
      squaredDistance x (along a b s) := by
  have he := projection_expansion_segment x a b s
    (clampParameter (directionDot x a b) (directionSquare a b))
  have hn := mul_nonneg (sq_nonneg (s-clampParameter (directionDot x a b) (directionSquare a b)))
    (le_of_lt hv)
  have hc := clamp_variational (directionDot x a b) (directionSquare a b) s hv hs hs1
  nlinarith

/-- Nonnegative group masses preserve both inequalities supplied by one segment projection. -/
lemma weighted_segment_projection (x a b : D → ℝ) (α β : ℝ) (hα : 0 ≤ α) (hβ : 0 ≤ β) :
    ∃ t : ℝ, 0 ≤ t ∧ t ≤ 1 ∧
      α*squaredDistance (along a b t) a ≤ α*squaredDistance x a ∧
      β*squaredDistance (along a b t) b ≤ β*squaredDistance x b := by
  obtain ⟨t, ht, ht1, ha, hb⟩ := segment_projection_nonincrease x a b
  exact ⟨t, ht, ht1, mul_le_mul_of_nonneg_left ha hα, mul_le_mul_of_nonneg_left hb hβ⟩

lemma two_pow_mod_three (n : ℕ) : (2 : ℤ)^n % 3 = 1 ∨ (2 : ℤ)^n % 3 = 2 := by
  induction n with
  | zero => norm_num
  | succ n ih =>
    rw [pow_succ, Int.mul_emod]
    rcases ih with h | h <;> norm_num [h]

/-- No integer divided by a finite power of two equals 5/9, in exact real arithmetic. -/
lemma five_ninths_not_dyadic (m : ℤ) (n : ℕ) : (5/9 : ℝ) ≠ (m : ℝ)/(2:ℝ)^n := by
  intro h
  have hc : (5 : ℝ)*2^n = 9*(m:ℝ) := by
    field_simp at h
    nlinarith [h]
  have hi : (5 : ℤ)*2^n = 9*m := by exact_mod_cast hc
  have hm := congrArg (fun z : ℤ => z % 3) hi
  rcases two_pow_mod_three n with hn | hn <;> norm_num [Int.mul_emod, hn] at hm



noncomputable def meanCost {I : Type*} [Fintype I] (δ : ℝ) (α μ c : I → ℝ) : ℝ :=
  δ + ∑ i, α i * (c i-μ i)^2

noncomputable def meanQuadratics {I : Type*} [Fintype I]
    (α β μ ν : I → ℝ) (hα : ∀ i, 0 ≤ α i) (hβ : ∀ i, 0 ≤ β i) (δA δB : ℝ) :
    Quadratics Bool I where
  q g := if g then δB + ∑ i, β i * ν i^2 else δA + ∑ i, α i * μ i^2
  a g i := if g then β i else α i
  b g i := if g then β i*ν i else α i*μ i
  a_nonneg g i := by cases g <;> simp [hα, hβ]
  b_zero g i hz := by cases g <;> simp_all

lemma mean_cost_expansion {I : Type*} [Fintype I] (δ : ℝ) (α μ c : I → ℝ) :
    δ + (∑ i, α i*μ i^2) + (∑ i, (α i*c i^2-2*(α i*μ i)*c i)) = meanCost δ α μ c := by
  unfold meanCost
  rw [add_assoc, ← Finset.sum_add_distrib]
  congr 1
  apply Finset.sum_congr rfl
  intro i _
  ring

lemma mean_group_costs {I : Type*} [Fintype I]
    (α β μ ν : I → ℝ) (hα : ∀ i, 0 ≤ α i) (hβ : ∀ i, 0 ≤ β i)
    (δA δB : ℝ) (c : I → ℝ) :
    groupCost (meanQuadratics α β μ ν hα hβ δA δB) c false = meanCost δA α μ c ∧
    groupCost (meanQuadratics α β μ ν hα hβ δA δB) c true = meanCost δB β ν c := by
  constructor <;> simp only [groupCost, meanQuadratics, Bool.false_eq_true, if_false, if_true]
  · exact mean_cost_expansion δA α μ c
  · exact mean_cost_expansion δB β ν c

lemma positive_mean_denominator (α β t : ℝ) (hα : 0 < α) (hβ : 0 < β)
    (ht : 0 ≤ t) (ht1 : t ≤ 1) : 0 < t*α+(1-t)*β := by
  by_cases hz : t = 0
  · simpa [hz] using hβ
  · have hp := mul_pos (lt_of_le_of_ne ht (Ne.symm hz)) hα
    have hn := mul_nonneg (sub_nonneg.mpr ht1) (le_of_lt hβ)
    linarith

noncomputable def meanCurve {I : Type*} (α β μ ν : I → ℝ) (t : ℝ) (i : I) : ℝ :=
  (t*α i*μ i+(1-t)*β i*ν i)/(t*α i+(1-t)*β i)

/-- Explicit formula from eq:lambda-center for occupied two-group cells, any finite dimension. -/
lemma ideal_mean_curve_monotonicity {I : Type*} [Fintype I]
    (α β μ ν : I → ℝ) (hα : ∀ i, 0 < α i) (hβ : ∀ i, 0 < β i)
    (δA δB t u : ℝ) (ht : 0 ≤ t) (htu : t ≤ u) (hu : u ≤ 1) :
    meanCost δA α μ (meanCurve α β μ ν u) ≤ meanCost δA α μ (meanCurve α β μ ν t) ∧
    meanCost δB β ν (meanCurve α β μ ν t) ≤ meanCost δB β ν (meanCurve α β μ ν u) := by
  let p := meanQuadratics α β μ ν (fun i => le_of_lt (hα i)) (fun i => le_of_lt (hβ i)) δA δB
  have hcurve : ∀ s (hs : 0 ≤ s) (hs1 : s ≤ 1),
      minimizer p (binarySimplex s hs hs1) (fun _ => 0) = meanCurve α β μ ν s := by
    intro s hs hs1
    funext i
    have hd : s*p.a false i + (1-s)*p.a true i ≠ 0 := by
      exact ne_of_gt (positive_mean_denominator (α i) (β i) s (hα i) (hβ i) hs hs1)
    rw [binary_minimizer_formula p s hs hs1 _ i hd]
    simp only [p, meanQuadratics, Bool.false_eq_true, if_false, if_true, meanCurve]
    ring
  have h := quadratic_lambda_monotonicity p (fun _ _ => 0) t u ht htu hu
  dsimp only at h
  rw [hcurve t ht (htu.trans hu), hcurve u (ht.trans htu) hu] at h
  have hct := mean_group_costs α β μ ν (fun i => le_of_lt (hα i)) (fun i => le_of_lt (hβ i))
    δA δB (meanCurve α β μ ν t)
  have hcu := mean_group_costs α β μ ν (fun i => le_of_lt (hα i)) (fun i => le_of_lt (hβ i))
    δA δB (meanCurve α β μ ν u)
  change groupCost p _ false ≤ groupCost p _ false ∧ groupCost p _ true ≤ groupCost p _ true at h
  rw [hct.1, hct.2, hcu.1, hcu.2] at h
  exact h


end FairUpdate.Geometry
