import SplitSlices

namespace FTF
open scoped BigOperators
variable {Ω A : Type*} [Fintype Ω] [Fintype A]

/-- Pure clients incur factor one; mixed clients incur their weight ratio.
Zero global share entails an absent reference-group contribution. -/
lemma merged_client_uniform (p : Law Ω) (a b α κ : ℝ) (ha : 0 ≤ a) (hb : 0 ≤ b)
    (hα : 0 ≤ α) (hκ : 1 ≤ κ) (A B : Ω → ℝ) (hA : ∀ o, 0 ≤ A o) (hB : ∀ o, 0 ≤ B o)
    (A₀ B₀ : ℝ) (hA₀ : 0 ≤ A₀) (hB₀ : 0 ≤ B₀)
    (zeroA : a=0 → A₀=0) (zeroB : b=0 → B₀=0)
    (ratio : 0<a → 0<b → max (a/b) (b/a) ≤ κ)
    (mrs : expect p (fun o => A o+B o) ≤ α*(A₀+B₀)) :
    expect p (fun o => a*A o+b*B o) ≤ α*κ*(a*A₀+b*B₀) := by
  have hJ : 0 ≤ a*A₀+b*B₀ := by positivity
  by_cases ha0 : a=0
  · have hz := zeroA ha0
    simp only [ha0, zero_mul, zero_add, hz, zero_add] at *
    have hs := expect_add p A B
    have hnon := expect_nonneg p hA
    have hm : expect p B ≤ α*B₀ := by linarith
    rw [expect_mul]
    have h1 := mul_le_mul_of_nonneg_left hm hb
    have h2 := mul_le_mul_of_nonneg_left hκ (mul_nonneg hα (mul_nonneg hb hB₀))
    nlinarith
  · by_cases hb0 : b=0
    · have hz := zeroB hb0
      simp only [hb0, mul_zero, zero_mul, add_zero, hz, add_zero] at *
      have hs := expect_add p A B
      have hnon := expect_nonneg p hB
      have hm : expect p A ≤ α*A₀ := by linarith
      rw [expect_mul]
      have h1 := mul_le_mul_of_nonneg_left hm ha
      have h2 := mul_le_mul_of_nonneg_left hκ (mul_nonneg hα (mul_nonneg ha hA₀))
      nlinarith
    · have h := merged_client_bound p a b α (lt_of_le_of_ne ha (Ne.symm ha0))
        (lt_of_le_of_ne hb (Ne.symm hb0)) hα A B hA hB A₀ B₀ hA₀ hB₀ mrs
      have hrat := mul_le_mul_of_nonneg_right (ratio (lt_of_le_of_ne ha (Ne.symm ha0))
        (lt_of_le_of_ne hb (Ne.symm hb0))) (mul_nonneg hα hJ)
      nlinarith

/-- Summation over all actual clients, including pure clients. -/
lemma merged_sum_bound (p : Law Ω) (a b : A → ℝ) (α κ : ℝ)
    (ha : ∀ c, 0 ≤ a c) (hb : ∀ c, 0 ≤ b c) (hα : 0 ≤ α) (hκ : 1 ≤ κ)
    (Ac Bc : A → Ω → ℝ) (hA : ∀ c o, 0 ≤ Ac c o) (hB : ∀ c o, 0 ≤ Bc c o)
    (A₀ B₀ : A → ℝ) (hA₀ : ∀ c, 0 ≤ A₀ c) (hB₀ : ∀ c, 0 ≤ B₀ c)
    (zeroA : ∀ c, a c=0 → A₀ c=0) (zeroB : ∀ c, b c=0 → B₀ c=0)
    (ratio : ∀ c, 0<a c → 0<b c → max (a c/b c) (b c/a c) ≤ κ)
    (mrs : ∀ c, expect p (fun o => Ac c o+Bc c o) ≤ α*(A₀ c+B₀ c)) :
    expect p (fun o => ∑ c, (a c*Ac c o+b c*Bc c o)) ≤ α*κ*∑ c, (a c*A₀ c+b c*B₀ c) := by
  rw [expect_sum, Finset.mul_sum]
  exact Finset.sum_le_sum fun c _ => merged_client_uniform p (a c) (b c) α κ (ha c) (hb c)
    hα hκ (Ac c) (Bc c) (hA c) (hB c) (A₀ c) (B₀ c) (hA₀ c) (hB₀ c)
    (zeroA c) (zeroB c) (ratio c) (mrs c)

end FTF

namespace FTF
open scoped BigOperators
variable {A E K L S : Type*} [Fintype A] [MetricSpace E] [Fintype K] [Nonempty K]
  [Fintype L] [Fintype S]

abbrev ClientRecords (nA nB : A → ℕ) := (c : A) × (Fin (nA c) ⊕ Fin (nB c))

noncomputable def globalWeight (nA nB : A → ℕ) (a b : A → ℝ) (i : ClientRecords nA nB) : ℝ :=
  Sum.elim (fun _ => a i.1/(nA i.1 : ℝ)) (fun _ => b i.1/(nB i.1 : ℝ)) i.2

noncomputable def clientA (nA nB : A → ℕ) (x : ClientRecords nA nB → E) (c : A) (C : K → E) : ℝ :=
  cost (fun _ : Fin (nA c) => 1/(nA c : ℝ)) (fun j => x ⟨c,Sum.inl j⟩) C
noncomputable def clientB (nA nB : A → ℕ) (x : ClientRecords nA nB → E) (c : A) (C : K → E) : ℝ :=
  cost (fun _ : Fin (nB c) => 1/(nB c : ℝ)) (fun j => x ⟨c,Sum.inr j⟩) C
noncomputable def mergedRep (nA nB : A → ℕ) (x : ClientRecords nA nB → E)
    (Z : A → K → E) (i : ClientRecords nA nB) : E := Z i.1 (nearestIndex (x i) (Z i.1))

omit [Fintype A] in
lemma globalWeight_nonneg (nA nB : A → ℕ) (a b : A → ℝ)
    (ha : ∀ c, 0 ≤ a c) (hb : ∀ c, 0 ≤ b c) (i : ClientRecords nA nB) :
    0 ≤ globalWeight nA nB a b i := by
  rcases i with ⟨c,j | j⟩
  · exact div_nonneg (ha c) (Nat.cast_nonneg _)
  · exact div_nonneg (hb c) (Nat.cast_nonneg _)

lemma merged_cost_decomposition (nA nB : A → ℕ) (a b : A → ℝ)
    (x : ClientRecords nA nB → E) (C : K → E) :
    cost (globalWeight nA nB a b) x C =
      ∑ c, (a c*clientA nA nB x c C+b c*clientB nA nB x c C) := by
  simp only [cost, energy, Fintype.sum_sigma, Fintype.sum_sum_type,
    globalWeight, Sum.elim_inl, Sum.elim_inr, clientA, clientB, Finset.mul_sum]
  apply Finset.sum_congr rfl
  intro c _
  congr 1 <;> apply Finset.sum_congr rfl <;> intro j _ <;> simp [div_eq_mul_inv, mul_assoc]

lemma merged_rep_decomposition (nA nB : A → ℕ) (a b : A → ℝ)
    (x : ClientRecords nA nB → E) (Z : A → K → E) :
    distortion (globalWeight nA nB a b) x (mergedRep nA nB x Z) =
      ∑ c, (a c*clientA nA nB x c (Z c)+b c*clientB nA nB x c (Z c)) := by
  simp only [distortion, energy, mergedRep, nearestIndex_spec, Fintype.sum_sigma, Fintype.sum_sum_type,
    globalWeight, Sum.elim_inl, Sum.elim_inr, clientA, clientB, cost, energy, Finset.mul_sum]
  apply Finset.sum_congr rfl
  intro c _
  congr 1 <;> apply Finset.sum_congr rfl <;> intro j _ <;> simp [div_eq_mul_inv, mul_assoc]

/-- Actual finite weighted geometry establishes the merged local premise. -/
theorem merged_local_geometric_bound (nA nB : A → ℕ) (a b : A → ℝ)
    (ha : ∀ c, 0 ≤ a c) (hb : ∀ c, 0 ≤ b c)
    (emptyA : ∀ c, a c=0 → nA c=0) (emptyB : ∀ c, b c=0 → nB c=0)
    (x : ClientRecords nA nB → E) (Z : L → A → K → E) (ref : K → E)
    (p : Law L) (α κ : ℝ) (hα : 0 ≤ α) (hκ : 1 ≤ κ)
    (ratio : ∀ c, 0<a c → 0<b c → max (a c/b c) (b c/a c) ≤ κ)
    (makarychev_local : ∀ c, expect p (fun l => clientA nA nB x c (Z l c)+clientB nA nB x c (Z l c)) ≤
      α*(clientA nA nB x c ref+clientB nA nB x c ref)) :
    expect p (fun l => distortion (globalWeight nA nB a b) x (mergedRep nA nB x (Z l))) ≤
      α*κ*cost (globalWeight nA nB a b) x ref := by
  simp_rw [merged_rep_decomposition, merged_cost_decomposition]
  apply merged_sum_bound p a b α κ ha hb hα hκ
  · intro c l; exact cost_nonneg _ (fun _ => by positivity) _ _
  · intro c l; exact cost_nonneg _ (fun _ => by positivity) _ _
  · intro c; exact cost_nonneg _ (fun _ => by positivity) _ _
  · intro c; exact cost_nonneg _ (fun _ => by positivity) _ _
  · intro c hc
    simp [clientA, cost, energy, emptyA c hc]
  · intro c hc
    simp [clientB, cost, energy, emptyB c hc]
  · exact ratio
  · exact makarychev_local

/-- The zero-share/empty-client bridge for actual globally normalized counts. -/
lemma share_zero_implies_empty (n : ℕ) (N : ℝ) (hN : N ≠ 0) (h : (n : ℝ)/N=0) : n=0 := by
  have hn : (n : ℝ)=0 := (div_eq_zero_iff.mp h).resolve_right hN
  exact_mod_cast hn

end FTF
