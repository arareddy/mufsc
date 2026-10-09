import Transfer

set_option maxHeartbeats 800000

namespace FTF
open scoped BigOperators
variable {E K A L S : Type*} [MetricSpace E] [Fintype K] [Nonempty K]
  [Fintype A] [Fintype L] [Fintype S]

noncomputable def nearestIndex (x : E) (C : K → E) : K :=
  Classical.choose (Finset.exists_mem_eq_inf' Finset.univ_nonempty (fun j => dist x (C j)))

lemma nearestIndex_spec (x : E) (C : K → E) : dist x (C (nearestIndex x C)) = near x C :=
  (Classical.choose_spec (Finset.exists_mem_eq_inf' Finset.univ_nonempty (fun j => dist x (C j)))).2.symm

abbrev SliceRecords (n : A → ℕ) := (a : A) × Fin (n a)

noncomputable def localRep (n : A → ℕ) (x : SliceRecords n → E)
    (Z : A → K → E) (i : SliceRecords n) : E :=
  Z i.1 (nearestIndex (x i) (Z i.1))

lemma slice_cost_decomposition (n : A → ℕ) (ω : A → ℝ) (x : SliceRecords n → E) (C : K → E) :
    cost (fun i : SliceRecords n => ω i.1) x C =
      ∑ a, ω a * cost (fun _ : Fin (n a) => 1) (fun j => x ⟨a,j⟩) C := by
  simp only [cost, energy, Fintype.sum_sigma, Finset.mul_sum, one_mul]

lemma local_rep_decomposition (n : A → ℕ) (ω : A → ℝ) (x : SliceRecords n → E) (Z : A → K → E) :
    distortion (fun i : SliceRecords n => ω i.1) x (localRep n x Z) =
      ∑ a, ω a * cost (fun _ : Fin (n a) => 1) (fun j => x ⟨a,j⟩) (Z a) := by
  simp only [distortion, energy, localRep, nearestIndex_spec, Fintype.sum_sigma,
    cost, Finset.mul_sum, one_mul]

/-- eq:dz-mrs from slice-constant weights and per-slice literature guarantees.
All record identities, locations, selected centers and nearest representatives are
explicit. Empty finite slices contribute zero automatically. -/
theorem split_local_bound (n : A → ℕ) (ω : A → ℝ) (hω : ∀ a, 0 ≤ ω a)
    (x : SliceRecords n → E) (Z : L → A → K → E) (ref : K → E) (p : Law L) (α : ℝ)
    (makarychev_local : ∀ a, expect p (fun l => cost (fun _ : Fin (n a) => 1)
      (fun j => x ⟨a,j⟩) (Z l a)) ≤ α*cost (fun _ : Fin (n a) => 1) (fun j => x ⟨a,j⟩) ref) :
    expect p (fun l => distortion (fun i : SliceRecords n => ω i.1) x (localRep n x (Z l))) ≤
      α*cost (fun i : SliceRecords n => ω i.1) x ref := by
  simp_rw [local_rep_decomposition, slice_cost_decomposition]
  exact local_sum_bound p ω _ _ α hω makarychev_local

/-- Mathematical-model warm start conditional only on per-call k-means++
literature guarantees and a quantization bound. It quantifies over genuine
finite local/server laws and actual selected local/server center tuples. -/
theorem split_warm_start (n : A → ℕ) (ω : A → ℝ) (hω : ∀ a, 0 ≤ ω a)
    (x : SliceRecords n → E) (Z : L → A → K → E) (q : L → SliceRecords n → E)
    (ref : K → E) (p : Law L) (r : L → Law S) (C : L → S → K → E)
    (α Q : ℝ) (hα : 0 ≤ α)
    (makarychev_local : ∀ a, expect p (fun l => cost (fun _ : Fin (n a) => 1)
      (fun j => x ⟨a,j⟩) (Z l a)) ≤ α*cost (fun _ : Fin (n a) => 1) (fun j => x ⟨a,j⟩) ref)
    (quantization : expect p (fun l => distortion (fun i : SliceRecords n => ω i.1)
      (localRep n x (Z l)) (q l)) ≤ Q)
    (makarychev_server : ∀ l, expect (r l) (fun s => cost (fun i : SliceRecords n => ω i.1) (q l) (C l s)) ≤
      α*cost (fun i : SliceRecords n => ω i.1) (q l) ref) :
    Real.sqrt (expect (joint p r) (fun o => cost (fun i : SliceRecords n => ω i.1) x (C o.1 o.2))) ≤
      Real.sqrt α*(Real.sqrt α+2)*Real.sqrt (cost (fun i : SliceRecords n => ω i.1) x ref)+
      (1+Real.sqrt α)*Real.sqrt Q := by
  exact split_root (fun i : SliceRecords n => ω i.1) (fun i => hω i.1) x (fun l => localRep n x (Z l)) q ref p r C α Q hα
    (split_local_bound n ω hω x Z ref p α makarychev_local) quantization makarychev_server

end FTF
