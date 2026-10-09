import FiniteRecords

/-! The Merged-1k lower construction of thm:kappa. This has one local
representative per client and must not be confused with Merged-2k. -/
namespace MergedOne
open scoped BigOperators
open MatchedBudget

/-- False is zero, true is the positive location L. -/
def siteCoord (L : ℝ) (s : Bool) : ℝ := if s then L else 0

def localSite {u v : ℕ} : ClientZeroRecord u v → Bool
  | .inl _ => false | .inr _ => true

def recordCoord {u v : ℕ} (L : ℝ) : Record u v → ℝ
  | .inl r => siteCoord L (localSite r)
  | .inr _ => 0

def sumSite (f : Bool → ℚ) : ℚ := f false + f true

/-- The single locally balanced draw, summed over persistent record identities. -/
def firstProb (u v : ℕ) (s : Bool) : ℚ :=
  (∑ r : ClientZeroRecord u v, balancedWeight r * if localSite r = s then 1 else 0) /
    (∑ r : ClientZeroRecord u v, balancedWeight r)

theorem local_first_law (u v : ℕ) (hu : 0 < u) (hv : 0 < v) (s : Bool) :
    firstProb u v s = 1/2 := by
  have huq : (u : ℚ) ≠ 0 := by exact_mod_cast (Nat.ne_of_gt hu)
  have hvq : (v : ℚ) ≠ 0 := by exact_mod_cast (Nat.ne_of_gt hv)
  unfold firstProb
  simp only [ClientZeroRecord, Fintype.sum_sum_type]
  cases s <;> simp [balancedWeight, localSite, nsmul_eq_mul]
  <;> field_simp <;> ring

/-- Each single representative receives its client's entire globally normalized count. -/
def anchorWeight (u v : ℕ) (client : Bool) : ℚ :=
  if client then (2*(v : ℚ)+2*(u : ℚ))/groupSize u v
  else (2*(u : ℚ)+2*(v : ℚ))/groupSize u v

theorem anchor_weight_one (u v : ℕ) (hv : 0 < v) (client : Bool) :
    anchorWeight u v client = 1 := by
  have hvq : (0 : ℚ) < v := by exact_mod_cast hv
  have huq : (0 : ℚ) ≤ u := Nat.cast_nonneg u
  have hd : (u : ℚ)+v ≠ 0 := by linarith
  cases client <;> norm_num [anchorWeight, groupSize] <;> field_simp <;> ring

def anchorSite (a client : Bool) : Bool := if client then false else a

def serverProb (u v : ℕ) (a s : Bool) : ℚ :=
  sumSite (fun client => if anchorSite a client = s then anchorWeight u v client else 0) /
    sumSite (anchorWeight u v)

def outputLaw (u v : ℕ) (s : Bool) : ℚ :=
  sumSite (fun a => firstProb u v a * serverProb u v a s)

theorem output_law (u v : ℕ) (hu : 0 < u) (hv : 0 < v) (s : Bool) :
    outputLaw u v s = if s then 1/4 else 3/4 := by
  unfold outputLaw serverProb
  simp only [sumSite, local_first_law u v hu hv, anchor_weight_one u v hv]
  cases s <;> norm_num [anchorSite]

theorem output_probability_valid (u v : ℕ) (hu : 0 < u) (hv : 0 < v) :
    sumSite (outputLaw u v) = 1 ∧ (∀ s, 0 ≤ outputLaw u v s) := by
  constructor
  · norm_num [sumSite, output_law u v hu hv]
  · intro s; rw [output_law u v hu hv]; cases s <;> norm_num

noncomputable section

def costA (eps _L c : ℝ) : ℝ := (1-eps)*(0-c)^2 + eps*(0-c)^2
def costB (eps L c : ℝ) : ℝ := eps*(L-c)^2 + (1-eps)*(0-c)^2

def G (eps L c : ℝ) : ℝ := costA eps L c + costB eps L c
def Phi (eps L c : ℝ) : ℝ := max (costA eps L c) (costB eps L c)

def gOpt (eps L : ℝ) : ℝ := eps*(1-eps/2)*L^2
def phiOpt (eps L : ℝ) : ℝ := eps*(1-eps)*L^2

theorem group_costs (eps L c : ℝ) :
    costA eps L c = c^2 ∧ costB eps L c = c^2-2*eps*L*c+eps*L^2 := by
  constructor <;> dsimp [costA, costB] <;> ring

theorem g_completed_square (eps L c : ℝ) :
    G eps L c = 2*(c-eps*L/2)^2 + gOpt eps L := by
  dsimp [G, costA, costB, gOpt]; ring

theorem b_completed_square (eps L c : ℝ) :
    costB eps L c = (c-eps*L)^2 + phiOpt eps L := by
  dsimp [costB, phiOpt]; ring

theorem g_optimum (eps L : ℝ) :
    G eps L (eps*L/2) = gOpt eps L ∧ (∀ c, gOpt eps L ≤ G eps L c) := by
  constructor
  · rw [g_completed_square]; ring
  · intro c; rw [g_completed_square]; nlinarith [sq_nonneg (c-eps*L/2)]

theorem phi_optimum (eps L : ℝ) (h0 : 0 ≤ eps) (h1 : eps ≤ 1/2) :
    Phi eps L (eps*L) = phiOpt eps L ∧ (∀ c, phiOpt eps L ≤ Phi eps L c) := by
  constructor
  · unfold Phi
    rw [(group_costs eps L (eps*L)).1, b_completed_square]
    have h : (eps*L)^2 ≤ phiOpt eps L := by
      unfold phiOpt
      have : 0 ≤ eps*(1-2*eps)*L^2 := mul_nonneg (mul_nonneg h0 (by linarith)) (sq_nonneg L)
      nlinarith
    norm_num
    exact h
  · intro c
    calc
      phiOpt eps L ≤ costB eps L c := by
        rw [b_completed_square]
        nlinarith [sq_nonneg (c-eps*L)]
      _ ≤ Phi eps L c := le_max_right _ _

theorem positive_optima (eps L : ℝ) (h0 : 0 < eps) (h1 : eps ≤ 1/2) (hL : 0 < L) :
    0 < gOpt eps L ∧ 0 < phiOpt eps L := by
  have hLs : 0 < L^2 := sq_pos_of_pos hL
  have hd1 : 0 < 1-eps/2 := by linarith
  have hd2 : 0 < 1-eps := by linarith
  constructor <;> dsimp [gOpt, phiOpt] <;> positivity

def expectation (u v : ℕ) (L : ℝ) (cost : ℝ → ℝ) : ℝ :=
  (outputLaw u v false : ℝ)*cost 0 + (outputLaw u v true : ℝ)*cost L

theorem expected_g (u v : ℕ) (hu : 0 < u) (hv : 0 < v) (eps L : ℝ) :
    expectation u v L (G eps L) = (1+eps)*L^2/2 := by
  simp only [expectation, output_law u v hu hv]
  norm_num [G, costA, costB]
  ring

theorem phi_endpoints (eps L : ℝ) (h0 : 0 ≤ eps) (_h1 : eps ≤ 1) :
    Phi eps L 0 = eps*L^2 ∧ Phi eps L L = L^2 := by
  have hs := sq_nonneg L
  constructor
  · unfold Phi
    rw [(group_costs eps L 0).1, (group_costs eps L 0).2]
    norm_num
    exact mul_nonneg h0 hs
  · unfold Phi
    rw [(group_costs eps L L).1, (group_costs eps L L).2]
    apply max_eq_left
    nlinarith [mul_nonneg h0 hs]

theorem expected_phi (u v : ℕ) (hu : 0 < u) (hv : 0 < v)
    (eps L : ℝ) (h0 : 0 ≤ eps) (h1 : eps ≤ 1) :
    expectation u v L (Phi eps L) = (1+3*eps)*L^2/4 := by
  simp only [expectation, output_law u v hu hv, (phi_endpoints eps L h0 h1).1,
    (phi_endpoints eps L h0 h1).2]
  norm_num
  ring

theorem exact_ratios (u v : ℕ) (hu : 0 < u) (hv : 0 < v)
    (eps L : ℝ) (h0 : 0 < eps) (h1 : eps ≤ 1/2) (hL : 0 < L) :
    expectation u v L (G eps L) / gOpt eps L = (1+eps)/(2*eps*(1-eps/2)) ∧
    expectation u v L (Phi eps L) / phiOpt eps L = (1+3*eps)/(4*eps*(1-eps)) := by
  have hp := positive_optima eps L h0 h1 hL
  have hd1 : 0 < 1-eps/2 := by linarith
  have hd2 : 0 < 1-eps := by linarith
  rw [expected_g u v hu hv, expected_phi u v hu hv eps L (le_of_lt h0) (by linarith)]
  constructor
  · apply (div_eq_div_iff (ne_of_gt hp.1) (by positivity : 2*eps*(1-eps/2) ≠ 0)).2
    dsimp [gOpt]
    ring
  · apply (div_eq_div_iff (ne_of_gt hp.2) (by positivity : 4*eps*(1-eps) ≠ 0)).2
    dsimp [phiOpt]
    ring

theorem lower_ratios (eps : ℝ) (h0 : 0 < eps) (h1 : eps ≤ 1/2) :
    (1-eps)/eps/2 ≤ (1+eps)/(2*eps*(1-eps/2)) ∧
    (1-eps)/eps/4 ≤ (1+3*eps)/(4*eps*(1-eps)) := by
  have hd1 : 0 < 1-eps/2 := by linarith
  have hd2 : 0 < 1-eps := by linarith
  constructor
  · apply (le_div_iff₀ (by positivity : 0 < 2*eps*(1-eps/2))).2
    have he : eps ≠ 0 := ne_of_gt h0
    have hc : (1-eps)/eps/2 * (2*eps*(1-eps/2)) = (1-eps)*(1-eps/2) := by
      field_simp
      ring
    rw [hc]
    nlinarith [mul_nonneg (le_of_lt h0) (le_of_lt hd2)]
  · apply (le_div_iff₀ (by positivity : 0 < 4*eps*(1-eps))).2
    have he : eps ≠ 0 := ne_of_gt h0
    have hc : (1-eps)/eps/4 * (4*eps*(1-eps)) = (1-eps)^2 := by
      field_simp
      ring
    rw [hc]
    nlinarith [mul_nonneg (le_of_lt h0) (le_of_lt hd2)]

end
noncomputable section

/-- Full-record group averages on the two-location construction. -/
def recordCostA (u v : ℕ) (L c : ℝ) : ℝ :=
  (∑ r : Record u v, if groupA r then (recordCoord L r-c)^2 else 0) / groupSize u v

def recordCostB (u v : ℕ) (L c : ℝ) : ℝ :=
  (∑ r : Record u v, if groupA r then 0 else (recordCoord L r-c)^2) / groupSize u v

def recordG (u v : ℕ) (L c : ℝ) : ℝ := recordCostA u v L c + recordCostB u v L c
def recordPhi (u v : ℕ) (L c : ℝ) : ℝ := max (recordCostA u v L c) (recordCostB u v L c)

theorem record_group_costs (u v : ℕ) (hv : 0 < v) (L c : ℝ) :
    recordCostA u v L c = costA (countEpsilon u v) L c ∧
    recordCostB u v L c = costB (countEpsilon u v) L c := by
  have hvq : (0 : ℝ) < v := by exact_mod_cast hv
  have huq : (0 : ℝ) ≤ u := Nat.cast_nonneg u
  have hd : (u : ℝ)+v ≠ 0 := by linarith
  simp only [recordCostA, recordCostB, Record, ClientZeroRecord, ClientOneRecord,
    Fintype.sum_sum_type]
  simp [recordCoord, siteCoord, localSite, groupA, groupSize, countEpsilon,
    costA, costB, nsmul_eq_mul]
  constructor <;> field_simp <;> ring

theorem record_objectives (u v : ℕ) (hv : 0 < v) (L : ℝ) :
    recordG u v L = G (countEpsilon u v) L ∧
    recordPhi u v L = Phi (countEpsilon u v) L := by
  constructor <;> funext c <;>
    simp only [recordG, recordPhi, G, Phi,
      (record_group_costs u v hv L c).1, (record_group_costs u v hv L c).2]

theorem real_epsilon_bounds (u v : ℕ) (huv : v ≤ u) (hv : 0 < v) :
    0 < (countEpsilon u v : ℝ) ∧ (countEpsilon u v : ℝ) ≤ 1/2 := by
  have hp := count_parameters u v huv hv
  have h := epsilon_bounds _ hp.1
  rw [← hp.2.1] at h
  constructor
  · exact_mod_cast h.1
  · have hh := (Rat.cast_le (K := ℝ)).2 h.2
    norm_num at hh
    exact hh

/-- The actual finite-record objectives have these global real optima. -/
theorem record_optima (u v : ℕ) (huv : v ≤ u) (hv : 0 < v) (L : ℝ) :
    recordG u v L ((countEpsilon u v : ℝ)*L/2) = gOpt (countEpsilon u v) L ∧
    (∀ c : ℝ, gOpt (countEpsilon u v) L ≤ recordG u v L c) ∧
    recordPhi u v L ((countEpsilon u v : ℝ)*L) = phiOpt (countEpsilon u v) L ∧
    (∀ c : ℝ, phiOpt (countEpsilon u v) L ≤ recordPhi u v L c) := by
  rw [(record_objectives u v hv L).1, (record_objectives u v hv L).2]
  have he := real_epsilon_bounds u v huv hv
  exact ⟨(g_optimum _ _).1, (g_optimum _ _).2,
    (phi_optimum _ _ (le_of_lt he.1) he.2).1,
    (phi_optimum _ _ (le_of_lt he.1) he.2).2⟩

/-- The lower bounds involve finite-record sampling and finite-record objective sums. -/
theorem finite_record_lower_bounds (u v : ℕ) (huv : v ≤ u) (hv : 0 < v)
    (L : ℝ) (hL : 0 < L) :
    (countKappa u v : ℝ)/2 ≤
      expectation u v L (recordG u v L) / gOpt (countEpsilon u v) L ∧
    (countKappa u v : ℝ)/4 ≤
      expectation u v L (recordPhi u v L) / phiOpt (countEpsilon u v) L := by
  have hu := lt_of_lt_of_le hv huv
  have he := real_epsilon_bounds u v huv hv
  have hr := exact_ratios u v hu hv (countEpsilon u v) L he.1 he.2 hL
  have hbound := lower_ratios (countEpsilon u v) he.1 he.2
  have hk : (1-(countEpsilon u v : ℝ))/(countEpsilon u v : ℝ) = (countKappa u v : ℝ) := by
    exact_mod_cast (count_parameters u v huv hv).2.2
  rw [hk] at hbound
  rw [(record_objectives u v hv L).1, (record_objectives u v hv L).2, hr.1, hr.2]
  exact hbound

/-- Existence part of thm:kappa (lower half), with explicit finite identities. -/
theorem rational_kappa_lower_construction (kappa : ℚ) (hk : 1 ≤ kappa)
    (L : ℝ) (hL : 0 < L) :
    ∃ u v : ℕ, 0 < v ∧ v ≤ u ∧ countKappa u v = kappa ∧
      ownershipParameter (countEpsilon u v) = kappa ∧
      Fintype.card (ClientZeroRecord u v) = groupSize u v ∧
      Fintype.card (ClientOneRecord u v) = groupSize u v ∧
      (kappa : ℝ)/2 ≤ expectation u v L (recordG u v L) / gOpt (countEpsilon u v) L ∧
      (kappa : ℝ)/4 ≤ expectation u v L (recordPhi u v L) / phiOpt (countEpsilon u v) L := by
  obtain ⟨u,v,hv,huv,hkap,_⟩ := rational_parameter_realizable kappa hk
  have hb := finite_record_lower_bounds u v huv hv L hL
  rw [hkap] at hb
  exact ⟨u,v,hv,huv,hkap,by rw [ownership_parameter u v huv hv,hkap],
    (client_cardinalities u v).1,(client_cardinalities u v).2.1,hb.1,hb.2⟩

end

noncomputable section

/-- One exact k=1 anchor-Lloyd step on the two retained anchors. -/
def lloydCenter (u v : ℕ) (L : ℝ) (a : Bool) : ℝ :=
  ((anchorWeight u v false : ℝ)*siteCoord L a + (anchorWeight u v true : ℝ)*0) /
    ((anchorWeight u v false : ℝ)+(anchorWeight u v true : ℝ))

theorem lloyd_center (u v : ℕ) (hv : 0 < v) (L : ℝ) (a : Bool) :
    lloydCenter u v L a = siteCoord L a / 2 := by
  norm_num [lloydCenter, anchor_weight_one u v hv]

def lloydExpectation (u v : ℕ) (L : ℝ) (cost : ℝ → ℝ) : ℝ :=
  (firstProb u v false : ℝ)*cost (lloydCenter u v L false) +
    (firstProb u v true : ℝ)*cost (lloydCenter u v L true)

/-- The concrete anchor-refinement caveat in app:kappa-proof, with L=1. -/
theorem lloyd_caveat_kappa_eight :
    lloydExpectation 8 1 1 (recordG 8 1 1) / gOpt (countEpsilon 8 1) 1 = 99/34 ∧
    lloydExpectation 8 1 1 (recordPhi 8 1 1) / phiOpt (countEpsilon 8 1) 1 = 117/64 ∧
    (99/34 : ℝ) < 8/2 ∧ (117/64 : ℝ) < 8/4 := by
  rw [(record_objectives 8 1 (by decide) 1).1,
    (record_objectives 8 1 (by decide) 1).2]
  norm_num [lloydExpectation, lloyd_center 8 1 (by decide),
    local_first_law 8 1 (by decide) (by decide), siteCoord, countEpsilon,
    G, Phi, costA, costB, gOpt, phiOpt]

theorem declared_ownership_parameter (u v : ℕ) (huv : v ≤ u) (hv : 0 < v) :
    max 1 (ownershipParameter (countEpsilon u v)) = countKappa u v := by
  rw [ownership_parameter u v huv hv]
  exact max_eq_right (count_parameters u v huv hv).1

end

end MergedOne
