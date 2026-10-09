import FairUpdate
import Mathlib.Data.Fintype.BigOperators

/-! Finite raw-data moments and their connection to guarded fair refinement.
Squared Euclidean distance is represented explicitly as a sum of coordinate squares.
All sums are exact real arithmetic; no executable floating-point claim is made. -/
namespace FairUpdate.Moments
open scoped BigOperators

variable {P D K G C : Type*}

noncomputable def squaredDistance [Fintype D] (x c : D → ℝ) : ℝ :=
  ∑ d, (x d - c d) ^ 2

lemma squaredDistance_nonneg [Fintype D] (x c : D → ℝ) :
    0 ≤ squaredDistance x c := Finset.sum_nonneg (fun d _ => sq_nonneg (x d - c d))

noncomputable def total [Fintype P] (w : P → ℝ) : ℝ := ∑ p, w p
noncomputable def first [Fintype P] (w : P → ℝ) (x : P → D → ℝ) (d : D) : ℝ :=
  ∑ p, w p * x p d
noncomputable def second [Fintype P] [Fintype D] (w : P → ℝ) (x : P → D → ℝ) : ℝ :=
  ∑ p, w p * ∑ d, x p d ^ 2
noncomputable def rawCost [Fintype P] [Fintype D]
    (w : P → ℝ) (x : P → D → ℝ) (c : D → ℝ) : ℝ :=
  ∑ p, w p * squaredDistance (x p) c

lemma total_nonneg [Fintype P] (w : P → ℝ) (hw : ∀ p, 0 ≤ w p) : 0 ≤ total w :=
  Finset.sum_nonneg (fun p _ => hw p)

lemma weights_zero_of_total_zero [Fintype P] (w : P → ℝ) (hw : ∀ p, 0 ≤ w p)
    (hz : total w = 0) (p : P) : w p = 0 := by
  have h : w p ≤ total w := Finset.single_le_sum (fun p _ => hw p) (Finset.mem_univ p)
  exact le_antisymm (by simpa [hz] using h) (hw p)

lemma zero_total_moments [Fintype P] [Fintype D] (w : P → ℝ)
    (hw : ∀ p, 0 ≤ w p) (x : P → D → ℝ) (hz : total w = 0) :
    (∀ d, first w x d = 0) ∧ second w x = 0 := by
  have h := weights_zero_of_total_zero w hw hz
  constructor
  · intro d
    simp [first, h]
  · simp [second, h]

lemma scalar_raw_expansion [Fintype P] (w z : P → ℝ) (c : ℝ) :
    (∑ p, w p * (z p - c) ^ 2) =
      (∑ p, w p * z p ^ 2) + total w * c ^ 2 - 2 * (∑ p, w p * z p) * c := by
  simp only [total, Finset.sum_mul, Finset.mul_sum, ← Finset.sum_add_distrib,
    ← Finset.sum_sub_distrib]
  apply Finset.sum_congr rfl
  intro p _
  ring_nf

/-- Exact coordinate form of SS - 2<S,c> + N ||c||², including empty cells. -/
lemma raw_moment_identity [Fintype P] [Fintype D]
    (w : P → ℝ) (x : P → D → ℝ) (c : D → ℝ) :
    rawCost w x c = second w x +
      ∑ d, (total w * c d ^ 2 - 2 * first w x d * c d) := by
  unfold rawCost squaredDistance
  simp only [Finset.mul_sum]
  rw [Finset.sum_comm]
  simp_rw [scalar_raw_expansion]
  simp only [sub_eq_add_neg, add_assoc, Finset.sum_add_distrib]
  congr 1
  unfold second
  simp only [Finset.mul_sum]
  exact Finset.sum_comm

lemma raw_moment_norm_form [Fintype P] [Fintype D]
    (w : P → ℝ) (x : P → D → ℝ) (c : D → ℝ) :
    rawCost w x c = second w x - 2 * (∑ d, first w x d * c d) +
      total w * ∑ d, c d ^ 2 := by
  rw [raw_moment_identity]
  simp only [Finset.sum_sub_distrib, Finset.mul_sum]
  ring_nf

noncomputable def restricted [DecidableEq K] (w : P → ℝ) (label : P → K)
    (k : K) (p : P) : ℝ := if label p = k then w p else 0

lemma restricted_nonneg [DecidableEq K] (w : P → ℝ) (hw : ∀ p, 0 ≤ w p)
    (label : P → K) (k : K) (p : P) : 0 ≤ restricted w label k p := by
  unfold restricted
  split <;> simp_all

/-- A label assigns each point to exactly one fiber, so summing fibers is exact. -/
lemma sum_restricted [Fintype P] [Fintype K] [DecidableEq K]
    (w : P → ℝ) (label : P → K) (f : P → ℝ) :
    (∑ k, ∑ p, restricted w label k p * f p) = ∑ p, w p * f p := by
  rw [Finset.sum_comm]
  apply Finset.sum_congr rfl
  intro p _
  simp [restricted, ite_mul]

lemma total_restricted_sum [Fintype P] [Fintype K] [DecidableEq K]
    (w : P → ℝ) (label : P → K) : (∑ k, total (restricted w label k)) = total w := by
  simpa [total] using sum_restricted w label (fun _ => 1)

lemma first_restricted_sum [Fintype P] [Fintype K] [DecidableEq K]
    (w : P → ℝ) (label : P → K) (x : P → D → ℝ) (d : D) :
    (∑ k, first (restricted w label k) x d) = first w x d :=
  sum_restricted w label (fun p => x p d)

lemma second_restricted_sum [Fintype P] [Fintype K] [DecidableEq K] [Fintype D]
    (w : P → ℝ) (label : P → K) (x : P → D → ℝ) :
    (∑ k, second (restricted w label k) x) = second w x :=
  sum_restricted w label (fun p => ∑ d, x p d ^ 2)

lemma assigned_cost_by_cells [Fintype P] [Fintype K] [DecidableEq K] [Fintype D]
    (w : P → ℝ) (assignment : P → K) (x : P → D → ℝ) (c : K → D → ℝ) :
    (∑ k, rawCost (restricted w assignment k) x (c k)) =
      ∑ p, w p * squaredDistance (x p) (c (assignment p)) := by
  unfold rawCost
  rw [Finset.sum_comm]
  apply Finset.sum_congr rfl
  intro p _
  simp [restricted, ite_mul]

/-- Coefficients are constructed from raw finite data, including proof of zero-mass consistency. -/
noncomputable def fromData [Fintype P] [Fintype D] [DecidableEq K]
    (w : G → P → ℝ) (hw : ∀ g p, 0 ≤ w g p)
    (assignment : P → K) (x : P → D → ℝ) : Quadratics G (K × D) where
  q g := second (w g) x
  a g i := total (restricted (w g) assignment i.1)
  b g i := first (restricted (w g) assignment i.1) x i.2
  a_nonneg g i := total_nonneg (restricted (w g) assignment i.1) (restricted_nonneg _ (hw g) _ _)
  b_zero g i hz := (zero_total_moments _ (restricted_nonneg _ (hw g) _ _) x hz).1 i.2

noncomputable def flatten (c : K → D → ℝ) (i : K × D) : ℝ := c i.1 i.2

lemma data_groupCost_eq_assignedCost [Fintype P] [Fintype D] [Fintype K] [DecidableEq K]
    (w : G → P → ℝ) (hw : ∀ g p, 0 ≤ w g p)
    (assignment : P → K) (x : P → D → ℝ) (c : K → D → ℝ) (g : G) :
    groupCost (fromData w hw assignment x) (flatten c) g =
      assignedCost w (fun p center => squaredDistance (x p) center) assignment c g := by
  have h := assigned_cost_by_cells (w g) assignment x c
  simp_rw [raw_moment_identity] at h
  rw [Finset.sum_add_distrib, second_restricted_sum] at h
  simpa only [groupCost, fromData, flatten, Fintype.sum_prod_type, assignedCost] using h

lemma data_fixedPhi_eq_assigned_max [Fintype G] [Nonempty G]
    [Fintype P] [Fintype D] [Fintype K] [DecidableEq K]
    (w : G → P → ℝ) (hw : ∀ g p, 0 ≤ w g p)
    (assignment : P → K) (x : P → D → ℝ) (c : K → D → ℝ) :
    fixedPhi (fromData w hw assignment x) (flatten c) =
      groupMax (assignedCost w (fun p center => squaredDistance (x p) center) assignment c) := by
  unfold fixedPhi
  congr 1
  funext g
  exact data_groupCost_eq_assignedCost w hw assignment x c g


noncomputable def membership [DecidableEq G] (group : P → G) (g : G) (p : P) : ℝ :=
  if group p = g then 1 else 0
noncomputable def groupCount [Fintype P] [DecidableEq G] (group : P → G) (g : G) : ℝ :=
  total (membership group g)

lemma membership_nonneg [DecidableEq G] (group : P → G) (g : G) (p : P) :
    0 ≤ membership group g p := by
  unfold membership
  split <;> norm_num

lemma groupCount_eq_card [Fintype P] [DecidableEq G] (group : P → G) (g : G) :
    groupCount group g = ((Finset.univ.filter (fun p => group p = g)).card : ℝ) := by
  simp [groupCount, total, membership]

lemma groupCount_pos [Fintype P] [DecidableEq G] (group : P → G) (g : G)
    (hg : ∃ p, group p = g) : 0 < groupCount group g := by
  obtain ⟨p, hp⟩ := hg
  have h : membership group g p ≤ groupCount group g :=
    Finset.single_le_sum (fun p _ => membership_nonneg group g p) (Finset.mem_univ p)
  have h1 : membership group g p = 1 := by simp [membership, hp]
  rw [h1] at h
  linarith

noncomputable def normalizedWeight [Fintype P] [DecidableEq G]
    (group : P → G) (g : G) (p : P) : ℝ := membership group g p / groupCount group g

lemma normalizedWeight_nonneg [Fintype P] [DecidableEq G] (group : P → G) (g : G) (p : P) :
    0 ≤ normalizedWeight group g p :=
  div_nonneg (membership_nonneg group g p) (total_nonneg _ (membership_nonneg group g))

lemma sum_divide [Fintype P] (z : P → ℝ) (n : ℝ) :
    (∑ p, z p) / n = ∑ p, z p / n := by
  simp only [div_eq_mul_inv, Finset.sum_mul]

lemma normalizedWeight_sum_one [Fintype P] [DecidableEq G] (group : P → G) (g : G)
    (hg : ∃ p, group p = g) : ∑ p, normalizedWeight group g p = 1 := by
  simp only [normalizedWeight, ← sum_divide]
  exact div_self (ne_of_gt (groupCount_pos group g hg))

lemma total_div [Fintype P] (w : P → ℝ) (n : ℝ) :
    total (fun p => w p / n) = total w / n := by
  simp only [total, sum_divide]

lemma first_div [Fintype P] (w : P → ℝ) (x : P → D → ℝ) (n : ℝ) (d : D) :
    first (fun p => w p / n) x d = first w x d / n := by
  simp only [first, div_mul_eq_mul_div, sum_divide]

lemma second_div [Fintype P] [Fintype D] (w : P → ℝ) (x : P → D → ℝ) (n : ℝ) :
    second (fun p => w p / n) x = second w x / n := by
  simp only [second, div_mul_eq_mul_div, sum_divide]

lemma restricted_div [DecidableEq K] (w : P → ℝ) (assignment : P → K) (k : K) (n : ℝ) :
    restricted (fun p => w p / n) assignment k = fun p => restricted w assignment k p / n := by
  funext p
  simp only [restricted]
  split <;> simp_all

/-- The normalized coefficient tuple is precisely N/n, S/n, SS/n from raw cell moments. -/
lemma normalized_coefficients [Fintype P] [Fintype D] [DecidableEq G] [DecidableEq K]
    (group : P → G) (assignment : P → K) (x : P → D → ℝ) (g : G) (k : K) (d : D) :
    (fromData (normalizedWeight group) (normalizedWeight_nonneg group) assignment x).a g (k,d) =
      total (restricted (membership group g) assignment k) / groupCount group g ∧
    (fromData (normalizedWeight group) (normalizedWeight_nonneg group) assignment x).b g (k,d) =
      first (restricted (membership group g) assignment k) x d / groupCount group g ∧
    (fromData (normalizedWeight group) (normalizedWeight_nonneg group) assignment x).q g =
      second (membership group g) x / groupCount group g := by
  dsimp only [fromData]
  have hweight : normalizedWeight group g = fun p => membership group g p / groupCount group g := rfl
  rw [hweight]
  simp only [restricted_div, total_div, first_div, second_div, and_self]

lemma normalized_assignedCost [Fintype P] [Fintype D] [DecidableEq G]
    (group : P → G) (assignment : P → K) (x : P → D → ℝ) (c : K → D → ℝ) (g : G) :
    assignedCost (normalizedWeight group) (fun p center => squaredDistance (x p) center) assignment c g =
      (∑ p ∈ Finset.univ.filter (fun p => group p = g), squaredDistance (x p) (c (assignment p))) /
        groupCount group g := by
  simp only [assignedCost, normalizedWeight, div_mul_eq_mul_div, ← sum_divide]
  congr 1
  simp [membership, ite_mul, Finset.sum_filter]

structure Stats (G K D : Type*) where
  count : G → K → ℝ
  sum : G → K → D → ℝ
  squaredSum : G → K → ℝ

noncomputable def centralStats [Fintype P] [Fintype D] [DecidableEq K]
    (w : G → P → ℝ) (assignment : P → K) (x : P → D → ℝ) : Stats G K D where
  count g k := total (restricted (w g) assignment k)
  sum g k := first (restricted (w g) assignment k) x
  squaredSum g k := second (restricted (w g) assignment k) x

/-- Ownership is a function: fibers are disjoint and cover all records, including empty clients. -/
noncomputable def federatedStats [Fintype P] [Fintype D] [Fintype C]
    [DecidableEq K] [DecidableEq C]
    (owner : P → C) (w : G → P → ℝ) (assignment : P → K) (x : P → D → ℝ) : Stats G K D where
  count g k := ∑ client, total (restricted (restricted (w g) assignment k) owner client)
  sum g k d := ∑ client, first (restricted (restricted (w g) assignment k) owner client) x d
  squaredSum g k := ∑ client, second (restricted (restricted (w g) assignment k) owner client) x

/-- Counts, coordinate sums, and squared-norm sums aggregated over clients equal centralized values. -/
lemma disjoint_client_aggregation [Fintype P] [Fintype D] [Fintype C]
    [DecidableEq K] [DecidableEq C]
    (owner : P → C) (w : G → P → ℝ) (assignment : P → K) (x : P → D → ℝ) :
    federatedStats owner w assignment x = centralStats w assignment x := by
  unfold federatedStats centralStats
  congr 1
  · funext g k
    exact total_restricted_sum _ owner
  · funext g k d
    exact first_restricted_sum _ owner x d
  · funext g k
    exact second_restricted_sum _ owner x

/-- Any one declared deterministic statistic-based solver receives the same tuple and returns the same value. -/
lemma algorithm_relative_centralized_equivalence [Fintype P] [Fintype D] [Fintype C]
    [DecidableEq K] [DecidableEq C] {Result : Type*}
    (owner : P → C) (w : G → P → ℝ) (assignment : P → K) (x : P → D → ℝ)
    (solver : Stats G K D → Result) :
    solver (federatedStats owner w assignment x) = solver (centralStats w assignment x) := by
  rw [disjoint_client_aggregation]

/-- The real raw-data bridge transports the evaluated-dual certificate to raw fixed-partition cost. -/
lemma raw_data_certificate [Fintype G] [Nonempty G] [Fintype P] [Fintype D]
    [Fintype K] [DecidableEq K] {E : Type*} [Fintype E] [Nonempty E]
    (w : G → P → ℝ) (hw : ∀ g p, 0 ≤ w g p)
    (assignment : P → K) (x : P → D → ℝ) (returned : K → D → ℝ)
    (evaluated : E → Simplex G) :
    let p := fromData w hw assignment x
    let raw := groupMax (assignedCost w (fun p center => squaredDistance (x p) center) assignment returned)
    0 ≤ raw - optimum p ∧ raw - optimum p ≤ raw - groupMax (fun e => dual p (evaluated e)) := by
  dsimp only
  rw [← data_fixedPhi_eq_assigned_max w hw assignment x returned]
  exact best_evaluated_certificate _ evaluated (flatten returned)

/-- Guarding the moment score is exactly sufficient for nearest-center monotonicity on raw data. -/
lemma moment_guarded_refinement [Fintype G] [Nonempty G] [Fintype P] [Fintype D]
    [Fintype K] [Nonempty K] [DecidableEq K]
    (w : G → P → ℝ) (hw : ∀ g p, 0 ≤ w g p)
    (assignment : P → K) (x : P → D → ℝ) (incumbent candidate : K → D → ℝ)
    (hnearest : ∀ p k, squaredDistance (x p) (incumbent (assignment p)) ≤
      squaredDistance (x p) (incumbent k)) :
    groupMax (nearestCost w (fun p center => squaredDistance (x p) center)
      (guarded (fun c => fixedPhi (fromData w hw assignment x) (flatten c)) incumbent candidate)) ≤
    groupMax (nearestCost w (fun p center => squaredDistance (x p) center) incumbent) := by
  have hscore : (fun c => fixedPhi (fromData w hw assignment x) (flatten c)) =
      (fun c => groupMax (assignedCost w (fun p center => squaredDistance (x p) center) assignment c)) := by
    funext c
    exact data_fixedPhi_eq_assigned_max w hw assignment x c
  rw [hscore]
  exact guarded_refinement_nonincrease w hw _ assignment incumbent candidate hnearest



/-- Centering at the weighted mean gives the exact variance decomposition; the denominator is nonzero. -/
lemma raw_centered_moment_identity [Fintype P] [Fintype D]
    (w : P → ℝ) (x : P → D → ℝ) (c : D → ℝ) (hn : total w ≠ 0) :
    rawCost w x c = second w x - (∑ d, first w x d ^ 2 / total w) +
      total w * squaredDistance c (fun d => first w x d / total w) := by
  rw [raw_moment_identity]
  have hs : (∑ d, (total w * c d ^ 2 - 2 * first w x d * c d)) =
      ∑ d, (total w * (c d - first w x d / total w) ^ 2 - first w x d ^ 2 / total w) := by
    apply Finset.sum_congr rfl
    intro d _
    have h := scalar_complete_square (total w) (first w x d) (c d) hn
    linarith
  rw [hs]
  simp only [squaredDistance, Finset.sum_sub_distrib, Finset.mul_sum]
  ring

lemma raw_mean_minimizes [Fintype P] [Fintype D]
    (w : P → ℝ) (hw : ∀ p, 0 ≤ w p) (x : P → D → ℝ) (c : D → ℝ) (hn : 0 < total w) :
    rawCost w x (fun d => first w x d / total w) ≤ rawCost w x c := by
  rw [raw_centered_moment_identity w x _ (ne_of_gt hn),
    raw_centered_moment_identity w x c (ne_of_gt hn)]
  have h := mul_nonneg (total_nonneg w hw)
    (squaredDistance_nonneg c (fun d => first w x d / total w))
  simpa only [squaredDistance, sub_self, zero_pow (by decide : 2 ≠ 0), Finset.sum_const_zero,
    mul_zero, add_zero] using le_add_of_nonneg_right h

/-- Flattening a center tuple neither adds nor removes feasible real centers. -/
lemma raw_objective_range [Fintype G] [Nonempty G] [Fintype P] [Fintype D]
    [Fintype K] [DecidableEq K]
    (w : G → P → ℝ) (hw : ∀ g p, 0 ≤ w g p) (assignment : P → K) (x : P → D → ℝ) :
    Set.range (fun c : K → D → ℝ =>
      groupMax (assignedCost w (fun p center => squaredDistance (x p) center) assignment c)) =
    Set.range (fixedPhi (fromData w hw assignment x)) := by
  ext r
  constructor
  · rintro ⟨c, rfl⟩
    exact ⟨flatten c, data_fixedPhi_eq_assigned_max w hw assignment x c⟩
  · rintro ⟨c, rfl⟩
    refine ⟨(fun k d => c (k,d)), ?_⟩
    dsimp only
    rw [← data_fixedPhi_eq_assigned_max w hw assignment x]
    rfl

lemma raw_infimum_eq_optimum [Fintype G] [Nonempty G] [Fintype P] [Fintype D]
    [Fintype K] [DecidableEq K]
    (w : G → P → ℝ) (hw : ∀ g p, 0 ≤ w g p) (assignment : P → K) (x : P → D → ℝ) :
    sInf (Set.range (fun c : K → D → ℝ =>
      groupMax (assignedCost w (fun p center => squaredDistance (x p) center) assignment c))) =
    optimum (fromData w hw assignment x) := by
  rw [raw_objective_range]
  rfl

lemma groupMax_bool (f : Bool → ℝ) : groupMax f = max (f false) (f true) := by
  apply le_antisymm
  · apply groupMax_le
    intro g
    cases g
    · exact le_max_left _ _
    · exact le_max_right _ _
  · exact max_le (le_groupMax f false) (le_groupMax f true)

/-- The manuscript's two-group maximum is the Bool specialization of the moment-guarded theorem. -/
lemma two_group_moment_monotonicity [Fintype P] [Fintype D]
    [Fintype K] [Nonempty K] [DecidableEq K]
    (group : P → Bool) (assignment : P → K) (x : P → D → ℝ)
    (incumbent candidate : K → D → ℝ)
    (hnearest : ∀ p k, squaredDistance (x p) (incumbent (assignment p)) ≤
      squaredDistance (x p) (incumbent k)) :
    let w := normalizedWeight group
    let score := fun c => fixedPhi (fromData w (normalizedWeight_nonneg group) assignment x) (flatten c)
    let updated := guarded score incumbent candidate
    max (nearestCost w (fun p center => squaredDistance (x p) center) updated false)
        (nearestCost w (fun p center => squaredDistance (x p) center) updated true) ≤
    max (nearestCost w (fun p center => squaredDistance (x p) center) incumbent false)
        (nearestCost w (fun p center => squaredDistance (x p) center) incumbent true) := by
  have h := moment_guarded_refinement (normalizedWeight group) (normalizedWeight_nonneg group)
    assignment x incumbent candidate hnearest
  simpa only [groupMax_bool] using h

noncomputable def counterexampleCost (c : ℝ) : ℝ := max (1 + c ^ 2) ((3 - c) ^ 2)

lemma counterexample_values :
    counterexampleCost (4/3) = 25/9 ∧ counterexampleCost (5/4) = 49/16 ∧
    counterexampleCost 0 = 9 ∧ counterexampleCost 3 = 10 ∧ counterexampleCost (3/2) = 13/4 := by
  norm_num [counterexampleCost]

lemma counterexample_global_lower_bound (c : ℝ) : 25/9 ≤ counterexampleCost c := by
  by_cases h : c ≤ 4/3
  · calc
      25/9 ≤ (3-c)^2 := by nlinarith [sq_nonneg (c - 4/3)]
      _ ≤ counterexampleCost c := le_max_right _ _
  · have hc : 4/3 ≤ c := le_of_lt (lt_of_not_ge h)
    calc
      25/9 ≤ 1+c^2 := by nlinarith [sq_nonneg (c - 4/3)]
      _ ≤ counterexampleCost c := le_max_left _ _

lemma counterexample_unique_minimizer (c : ℝ) : counterexampleCost c = 25/9 ↔ c = 4/3 := by
  constructor
  · intro h
    have ha : 1 + c ^ 2 ≤ 25/9 := by rw [← h]; exact le_max_left _ _
    have hb : (3-c)^2 ≤ 25/9 := by rw [← h]; exact le_max_right _ _
    by_cases hc : c ≤ 4/3
    · nlinarith [sq_nonneg (c-4/3)]
    · have hge : 4/3 ≤ c := le_of_lt (lt_of_not_ge hc)
      nlinarith [sq_nonneg (c-4/3)]
  · rintro rfl
    exact counterexample_values.1

/-- Endpoints and one midpoint miss the optimum and all worsen the represented incumbent. -/
lemma finite_search_counterexample :
    counterexampleCost (4/3) < counterexampleCost (3/2) ∧
    counterexampleCost (5/4) < counterexampleCost (3/2) ∧
    counterexampleCost (3/2) < counterexampleCost 0 ∧
    counterexampleCost (3/2) < counterexampleCost 3 ∧
    guarded counterexampleCost (5/4) (3/2) = (5/4 : ℝ) := by
  norm_num [counterexampleCost, guarded]



/-- Unit membership weights recover the manuscript's literal cell cardinality and sums. -/
lemma unweighted_cell_statistics [Fintype P] [Fintype D] [DecidableEq G] [DecidableEq K]
    (group : P → G) (assignment : P → K) (x : P → D → ℝ) (g : G) (k : K) :
    let cell := Finset.univ.filter (fun p => group p = g ∧ assignment p = k)
    total (restricted (membership group g) assignment k) = (cell.card : ℝ) ∧
    (∀ d, first (restricted (membership group g) assignment k) x d = ∑ p ∈ cell, x p d) ∧
    second (restricted (membership group g) assignment k) x = ∑ p ∈ cell, ∑ d, x p d ^ 2 := by
  have hweight : restricted (membership group g) assignment k =
      fun p => if group p = g ∧ assignment p = k then (1 : ℝ) else 0 := by
    funext p
    by_cases hg : group p = g <;> by_cases hk : assignment p = k <;>
      simp [restricted, membership, hg, hk]
  dsimp only
  rw [hweight]
  simp [total, first, second, ite_mul, Finset.sum_filter]

/-- Decoding by a common scale commutes with the first moment in exact real arithmetic. -/
lemma scaled_first [Fintype P] (w : P → ℝ) (z : P → D → ℝ) (scale : ℝ) (d : D) :
    first w (fun p d => z p d / scale) d = first w z d / scale := by
  simp only [first, mul_div_assoc, sum_divide]

lemma scaled_second [Fintype P] [Fintype D] (w : P → ℝ) (z : P → D → ℝ) (scale : ℝ) :
    second w (fun p d => z p d / scale) = second w z / scale ^ 2 := by
  simp only [second, div_pow, sum_divide, mul_div_assoc]

/-- Exact decoded fixed-point moments give S_int/(n scale) and SS_int/(n scale²). -/
lemma normalized_scaled_coefficients [Fintype P] [Fintype D] [DecidableEq G] [DecidableEq K]
    (group : P → G) (assignment : P → K) (z : P → D → ℝ) (scale : ℝ)
    (g : G) (k : K) (d : D) :
    (fromData (normalizedWeight group) (normalizedWeight_nonneg group) assignment
      (fun p d => z p d / scale)).b g (k,d) =
      first (restricted (membership group g) assignment k) z d / (groupCount group g * scale) ∧
    (fromData (normalizedWeight group) (normalizedWeight_nonneg group) assignment
      (fun p d => z p d / scale)).q g = second (membership group g) z / (groupCount group g * scale ^ 2) := by
  have h := normalized_coefficients group assignment (fun p d => z p d / scale) g k d
  constructor
  · rw [h.2.1, scaled_first, div_div]
    rw [mul_comm]
  · rw [h.2.2, scaled_second, div_div]
    rw [mul_comm]



/-- Objective recovered solely from the transmitted count, sum, and squared-norm-sum tuple. -/
noncomputable def statisticsScore [Fintype K] [Fintype D]
    (stats : Stats G K D) (c : K → D → ℝ) (g : G) : ℝ :=
  ∑ k, (stats.squaredSum g k +
    ∑ d, (stats.count g k * c k d ^ 2 - 2 * stats.sum g k d * c k d))

lemma central_statistics_score_eq_raw [Fintype P] [Fintype K] [DecidableEq K] [Fintype D]
    (w : G → P → ℝ) (assignment : P → K) (x : P → D → ℝ) (c : K → D → ℝ) (g : G) :
    statisticsScore (centralStats w assignment x) c g =
      assignedCost w (fun p center => squaredDistance (x p) center) assignment c g := by
  have h := assigned_cost_by_cells (w g) assignment x c
  simp_rw [raw_moment_identity] at h
  exact h

lemma federated_statistics_score_eq_raw [Fintype P] [Fintype K] [DecidableEq K] [Fintype D]
    [Fintype C] [DecidableEq C]
    (owner : P → C) (w : G → P → ℝ) (assignment : P → K) (x : P → D → ℝ)
    (c : K → D → ℝ) (g : G) :
    statisticsScore (federatedStats owner w assignment x) c g =
      assignedCost w (fun p center => squaredDistance (x p) center) assignment c g := by
  rw [disjoint_client_aggregation]
  exact central_statistics_score_eq_raw w assignment x c g

/-- The actual guard can use aggregated statistics; the resulting raw nearest objective is nonincreasing. -/
lemma federated_statistics_guard_nonincrease [Fintype G] [Nonempty G] [Fintype P] [Fintype D]
    [Fintype K] [Nonempty K] [DecidableEq K] [Fintype C] [DecidableEq C]
    (owner : P → C) (w : G → P → ℝ) (hw : ∀ g p, 0 ≤ w g p)
    (assignment : P → K) (x : P → D → ℝ) (incumbent candidate : K → D → ℝ)
    (hnearest : ∀ p k, squaredDistance (x p) (incumbent (assignment p)) ≤
      squaredDistance (x p) (incumbent k)) :
    groupMax (nearestCost w (fun p center => squaredDistance (x p) center)
      (guarded (fun c => groupMax (statisticsScore (federatedStats owner w assignment x) c))
        incumbent candidate)) ≤
    groupMax (nearestCost w (fun p center => squaredDistance (x p) center) incumbent) := by
  have hscore : (fun c => groupMax (statisticsScore (federatedStats owner w assignment x) c)) =
      (fun c => groupMax (assignedCost w (fun p center => squaredDistance (x p) center) assignment c)) := by
    funext c
    congr 1
    funext g
    exact federated_statistics_score_eq_raw owner w assignment x c g
  rw [hscore]
  exact guarded_refinement_nonincrease w hw _ assignment incumbent candidate hnearest

/-- For any fixed partition, the same statistic-based candidate map and guard are centralized-equivalent. -/
lemma federated_guarded_solver_eq_central [Fintype G] [Nonempty G] [Fintype P] [Fintype D]
    [Fintype K] [DecidableEq K] [Fintype C] [DecidableEq C]
    (owner : P → C) (w : G → P → ℝ) (assignment : P → K) (x : P → D → ℝ)
    (incumbent : K → D → ℝ) (candidateMap : Stats G K D → K → D → ℝ) :
    guarded (fun c => groupMax (statisticsScore (federatedStats owner w assignment x) c))
        incumbent (candidateMap (federatedStats owner w assignment x)) =
    guarded (fun c => groupMax (statisticsScore (centralStats w assignment x) c))
        incumbent (candidateMap (centralStats w assignment x)) := by
  rw [disjoint_client_aggregation]

lemma counterexample_raw_group_a (c : ℝ) :
    (((-1-c)^2 + (1-c)^2) / 2) = 1+c^2 := by
  ring

lemma counterexample_curve_values :
    3 * (1 - (0 : ℝ)) = 3 ∧ 3 * (1 - (1 : ℝ)) = 0 ∧
    3 * (1 - (1/2 : ℝ)) = 3/2 ∧ 3 * (1 - (5/9 : ℝ)) = 4/3 := by
  norm_num


end FairUpdate.Moments
