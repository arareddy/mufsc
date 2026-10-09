import CertificateStrength

/-! One-dimensional geometric witnesses, using |new-old| as exact Euclidean
movement. These are existence statements, independent of executable arithmetic. -/
namespace Replay

/-- Two-center displacement-radius obstruction whenever the basic test fails.
The competitor stops at zero rather than overshooting its allowed radius. -/
theorem radii_obstruction (d₁ d₂ w D : ℝ) (h₁ : 0 ≤ d₁) (h₂ : 0 ≤ d₂)
    (hw : 0 ≤ w) (hD : 0 ≤ D) (fail : d₂ - D ≤ d₁ + w) :
    ∃ winner competitor : ℝ,
      |winner - d₁| ≤ w ∧ |competitor - d₂| ≤ D ∧ |competitor| ≤ |winner| := by
  refine ⟨d₁+w, max 0 (d₂-D), ?_, ?_, ?_⟩
  · have h : d₁ + w - d₁ = w := by ring
    rw [h, abs_of_nonneg hw]
  · by_cases h : d₂ ≤ D
    · rw [max_eq_left (by linarith), zero_sub, abs_neg, abs_of_nonneg h₂]
      exact h
    · rw [max_eq_right (by linarith)]
      have he : d₂ - D - d₂ = -D := by ring
      rw [he, abs_neg, abs_of_nonneg hD]
  · rw [abs_of_nonneg (le_max_left _ _), abs_of_nonneg (by linarith)]
    exact max_le (by linarith) fail

/-- Exact-norm obstruction with a distinct additional runner. This explicitly
constructs every center's old and new real coordinate and realizes every
prescribed displacement norm. It is the k≥3 witness used in prop:cert-tight. -/
theorem exact_norm_obstruction {L : Type*} [DecidableEq L]
    (j q r : L) (hqj : q ≠ j) (hrj : r ≠ j) (hrq : r ≠ q)
    (d₁ d₂ : ℝ) (h₁ : 0 ≤ d₁) (h₁₂ : d₁ < d₂)
    (δ : L → ℝ) (hδ : ∀ m, 0 ≤ δ m)
    (fail : d₂ - δ q ≤ d₁ + δ j) :
    ∃ old new : L → ℝ,
      |old j| = d₁ ∧ |old r| = d₂ ∧
      (∀ m, m ≠ j → d₂ ≤ |old m|) ∧
      (∀ m, m ≠ j → |old j| < |old m|) ∧
      (∀ m, |new m - old m| = δ m) ∧ |new q| ≤ |new j| := by
  let old : L → ℝ := fun m => if m = j then d₁ else if m = q then max d₂ (δ q) else d₂
  let new : L → ℝ := fun m => if m = j then d₁ + δ j
    else if m = q then max d₂ (δ q) - δ q else d₂ + δ m
  have h₂ : 0 ≤ d₂ := le_trans h₁ h₁₂.le
  have holdj : |old j| = d₁ := by simp [old, abs_of_nonneg h₁]
  have holdr : |old r| = d₂ := by simp [old, hrj, hrq, abs_of_nonneg h₂]
  have hlower : ∀ m, m ≠ j → d₂ ≤ |old m| := by
    intro m hm
    by_cases hmq : m = q
    · subst m
      simp only [old, if_neg hqj, if_pos rfl]
      exact (le_max_left _ _).trans (le_abs_self _)
    · simp [old, hm, hmq, abs_of_nonneg h₂]
  refine ⟨old, new, holdj, holdr, hlower, ?_, ?_, ?_⟩
  · intro m hm
    rw [holdj]
    exact lt_of_lt_of_le h₁₂ (hlower m hm)
  · intro m
    by_cases hmj : m = j
    · subst m
      simp only [old, new, if_pos rfl]
      have he : d₁ + δ j - d₁ = δ j := by ring
      rw [he, abs_of_nonneg (hδ j)]
    · by_cases hmq : m = q
      · subst m
        simp only [old, new, if_neg hqj, if_pos rfl]
        change |max d₂ (δ q) - δ q - max d₂ (δ q)| = δ q
        have he : max d₂ (δ q) - δ q - max d₂ (δ q) = -δ q := by ring
        rw [he, abs_neg, abs_of_nonneg (hδ q)]
      · simp only [old, new, if_neg hmj, if_neg hmq]
        have he : d₂ + δ m - d₂ = δ m := by ring
        rw [he, abs_of_nonneg (hδ m)]
  · have hnewj : |new j| = d₁ + δ j := by simp [new, abs_of_nonneg (add_nonneg h₁ (hδ j))]
    have hnewq : |new q| = max d₂ (δ q) - δ q := by
      simp only [new, if_neg hqj, if_pos rfl]
      exact abs_of_nonneg (sub_nonneg.mpr (le_max_right _ _))
    rw [hnewj, hnewq]
    by_cases h : d₂ ≤ δ q
    · rw [max_eq_right h]
      have hw := hδ j
      linarith
    · rw [max_eq_left (le_of_not_ge h)]
      exact fail

/-- For k=2, the exact reverse-triangle lower bound is achievable on a line,
so failure of the stronger scalar test also admits a tie or changed winner. -/
theorem two_center_exact_obstruction (d₁ d₂ w D : ℝ) (h₁ : 0 ≤ d₁)
    (hw : 0 ≤ w) (hD : 0 ≤ D) (fail : |d₂ - D| ≤ d₁ + w) :
    ∃ winner competitor : ℝ,
      |winner - d₁| = w ∧ |competitor - d₂| = D ∧ |competitor| ≤ |winner| := by
  refine ⟨d₁+w, d₂-D, ?_, ?_, ?_⟩
  · have he : d₁+w-d₁=w := by ring
    rw [he, abs_of_nonneg hw]
  · have he : d₂-D-d₂ = -D := by ring
    rw [he, abs_neg, abs_of_nonneg hD]
  · rw [abs_of_nonneg (add_nonneg h₁ hw)]
    exact fail

theorem maxOn_attained {L : Type*} (s : Finset L) (f : L → ℝ) (h : s.Nonempty) :
    ∃ q ∈ s, f q = maxOn s f := by
  obtain ⟨q,hq,hbound⟩ := Finset.exists_max_image s f h
  exact ⟨q,hq,le_antisymm (le_maxOn s f q hq) (maxOn_le s f h (f q) hbound)⟩

theorem exists_third {L : Type*} [Fintype L] [DecidableEq L]
    (j q : L) (hcard : 3 ≤ Fintype.card L) : ∃ r, r ≠ j ∧ r ≠ q := by
  have hsmall : ({j,q} : Finset L).card < (Finset.univ : Finset L).card := by
    have h := Finset.card_le_two (a := j) (b := q)
    rw [Finset.card_univ]
    omega
  obtain ⟨r,_,hr⟩ := Finset.exists_mem_not_mem_of_card_lt_card hsmall
  exact ⟨r, by simpa using hr⟩

theorem competitor_nonempty {L : Type*} [Fintype L] [DecidableEq L]
    (j : L) (hcard : 2 ≤ Fintype.card L) : (competitors j).Nonempty := by
  have hsmall : ({j} : Finset L).card < (Finset.univ : Finset L).card := by
    simp only [Finset.card_singleton, Finset.card_univ]
    omega
  obtain ⟨q,_,hq⟩ := Finset.exists_mem_not_mem_of_card_lt_card hsmall
  exact ⟨q, by simpa [competitors] using hq⟩

/-- Full exact-norm tightness with finite index set of size at least three.
Whenever eq:basic-cert fails, prescribed displacement norms and the scalar
cache permit a configuration where the old unique winner ties or loses. -/
theorem exact_norm_full_tightness {L : Type*} [Fintype L] [DecidableEq L]
    (hcard : 3 ≤ Fintype.card L) (j : L) (d₁ d₂ : ℝ)
    (h₁ : 0 ≤ d₁) (h₁₂ : d₁ < d₂) (δ : L → ℝ) (hδ : ∀ m, 0 ≤ δ m)
    (fail : ¬ (δ j + maxOn (competitors j) δ < d₂ - d₁)) :
    ∃ q r : L, ∃ old new : L → ℝ,
      q ≠ j ∧ r ≠ j ∧ |old j| = d₁ ∧ |old r| = d₂ ∧
      (∀ m, m ≠ j → d₂ ≤ |old m|) ∧
      (∀ m, m ≠ j → |old j| < |old m|) ∧
      (∀ m, |new m - old m| = δ m) ∧ |new q| ≤ |new j| := by
  obtain ⟨q,hq,hmax⟩ := maxOn_attained (competitors j) δ (competitor_nonempty j (by omega))
  have hqj : q ≠ j := (Finset.mem_erase.mp hq).1
  obtain ⟨r,hrj,hrq⟩ := exists_third j q hcard
  have hfail : d₂ - δ q ≤ d₁ + δ j := by rw [hmax]; push_neg at fail; linarith
  obtain ⟨old,new,h⟩ := exact_norm_obstruction j q r hqj hrj hrq d₁ d₂ h₁ h₁₂ δ hδ hfail
  exact ⟨q,r,old,new,hqj,hrj,h⟩

/-- Full radius tightness already holds with two indexed centers. Unused
competitors are left fixed, which always respects nonnegative movement caps. -/
theorem radii_full_tightness {L : Type*} [Fintype L] [DecidableEq L]
    (hcard : 2 ≤ Fintype.card L) (j : L) (d₁ d₂ : ℝ)
    (h₁ : 0 ≤ d₁) (h₁₂ : d₁ < d₂) (δ : L → ℝ) (hδ : ∀ m, 0 ≤ δ m)
    (fail : ¬ (δ j + maxOn (competitors j) δ < d₂ - d₁)) :
    ∃ q : L, ∃ old new : L → ℝ,
      q ≠ j ∧ |old j| = d₁ ∧ |old q| = d₂ ∧
      (∀ m, m ≠ j → |old m| = d₂) ∧
      (∀ m, |new m - old m| ≤ δ m) ∧ |new q| ≤ |new j| := by
  obtain ⟨q,hq,hmax⟩ := maxOn_attained (competitors j) δ (competitor_nonempty j hcard)
  have hqj : q ≠ j := (Finset.mem_erase.mp hq).1
  have h₂ : 0 ≤ d₂ := h₁.trans h₁₂.le
  have hfail : d₂ - δ q ≤ d₁ + δ j := by rw [hmax]; push_neg at fail; linarith
  obtain ⟨w,c,hw,hc,hcw⟩ := radii_obstruction d₁ d₂ (δ j) (δ q) h₁ h₂ (hδ j) (hδ q) hfail
  let old : L → ℝ := fun m => if m = j then d₁ else d₂
  let new : L → ℝ := fun m => if m = j then w else if m = q then c else d₂
  refine ⟨q,old,new,hqj,?_,?_,?_,?_,?_⟩
  · simp [old, abs_of_nonneg h₁]
  · simp [old,hqj,abs_of_nonneg h₂]
  · intro m hm; simp [old,hm,abs_of_nonneg h₂]
  · intro m
    by_cases hmj : m = j
    · subst m; simpa [old,new] using hw
    · by_cases hmq : m = q
      · subst m; simpa [old,new,hqj] using hc
      · simpa [old,new,hmj,hmq] using hδ m
  · simpa [new,hqj] using hcw

#print axioms exact_norm_full_tightness
#print axioms radii_full_tightness
#print axioms radii_obstruction
#print axioms exact_norm_obstruction
#print axioms two_center_exact_obstruction
end Replay
