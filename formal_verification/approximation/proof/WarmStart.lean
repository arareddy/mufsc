import SplitSlices
import MergedClients
import Quantization
import GroupComparison
import AnchorAggregation
import RationalCopies
import TouchedMass
import Normalization
import Mathlib.Analysis.SpecialFunctions.Log.Basic

namespace FTF
open scoped BigOperators
noncomputable def mrsAlpha (k : ℕ) : ℝ := 5*(Real.log (k : ℝ)+2)
lemma mrsAlpha_nonneg (k : ℕ) (hk : 1 ≤ k) : 0 ≤ mrsAlpha k := by
  have hlog := Real.log_nonneg (show (1 : ℝ) ≤ k by exact_mod_cast hk)
  unfold mrsAlpha
  linarith

variable {A E K L S : Type*} [Fintype A] [MetricSpace E] [Fintype K] [Nonempty K]
  [Fintype L] [Fintype S]

/-- The displayed split root bound with alpha_k=5(log k+2), derived from
explicit finite slices, ideal finite conditional laws and geometric grid error.
The only sampling-approximation premises are the named literature per-call bounds.
For a Euclidean k-center instance take K=Fin k. -/
theorem warm_start_binary_grid (n : A → ℕ) (ω : A → ℝ) (hω : ∀ a, 0 ≤ ω a)
    (x : SliceRecords n → E) (Z : L → A → K → E) (q : L → SliceRecords n → E)
    (ref : K → E) (p : Law L) (r : L → Law S) (C : L → S → K → E)
    (k : ℕ) (hk : 1 ≤ k) (d γ : ℝ)
    (mass : (∑ i : SliceRecords n, ω i.1)=2)
    (makarychev_local : ∀ a, expect p (fun l => cost (fun _ : Fin (n a) => 1)
      (fun j => x ⟨a,j⟩) (Z l a)) ≤ mrsAlpha k*cost (fun _ : Fin (n a) => 1) (fun j => x ⟨a,j⟩) ref)
    (grid : ∀ l i, dist (localRep n x (Z l) i) (q l i)^2 ≤ d*γ^2/4)
    (makarychev_server : ∀ l, expect (r l) (fun s => cost (fun i : SliceRecords n => ω i.1) (q l) (C l s)) ≤
      mrsAlpha k*cost (fun i : SliceRecords n => ω i.1) (q l) ref) :
    Real.sqrt (expect (joint p r) (fun o => cost (fun i : SliceRecords n => ω i.1) x (C o.1 o.2))) ≤
      Real.sqrt (mrsAlpha k)*(Real.sqrt (mrsAlpha k)+2)*Real.sqrt (cost (fun i : SliceRecords n => ω i.1) x ref)+
      (1+Real.sqrt (mrsAlpha k))*Real.sqrt (d*γ^2/2) := by
  exact split_warm_start n ω hω x Z q ref p r C (mrsAlpha k) (d*γ^2/2)
    (mrsAlpha_nonneg k hk) makarychev_local
    (binary_grid_bound (fun i : SliceRecords n => ω i.1) (fun i => hω i.1) mass p
      (fun l => localRep n x (Z l)) q d γ grid) makarychev_server

/-- End-to-end merged upper transfer from finite actual client data, with
κ controlling each mixed client's ratio and pure clients handled explicitly. -/
theorem merged_warm_start (nA nB : A → ℕ) (a b : A → ℝ)
    (ha : ∀ c, 0 ≤ a c) (hb : ∀ c, 0 ≤ b c)
    (emptyA : ∀ c, a c=0 → nA c=0) (emptyB : ∀ c, b c=0 → nB c=0)
    (x : ClientRecords nA nB → E) (Z : L → A → K → E)
    (q : L → ClientRecords nA nB → E) (ref : K → E)
    (p : Law L) (r : L → Law S) (C : L → S → K → E)
    (α κ Q : ℝ) (hα : 0 ≤ α) (hκ : 1 ≤ κ)
    (ratio : ∀ c, 0<a c → 0<b c → max (a c/b c) (b c/a c) ≤ κ)
    (makarychev_local : ∀ c, expect p (fun l => clientA nA nB x c (Z l c)+clientB nA nB x c (Z l c)) ≤
      α*(clientA nA nB x c ref+clientB nA nB x c ref))
    (quantization : expect p (fun l => distortion (globalWeight nA nB a b)
      (mergedRep nA nB x (Z l)) (q l)) ≤ Q)
    (makarychev_server : ∀ l, expect (r l) (fun s => cost (globalWeight nA nB a b) (q l) (C l s)) ≤
      α*cost (globalWeight nA nB a b) (q l) ref) :
    Real.sqrt (expect (joint p r) (fun o => cost (globalWeight nA nB a b) x (C o.1 o.2))) ≤
      Real.sqrt α*((1+Real.sqrt α)*Real.sqrt κ+1)*Real.sqrt (cost (globalWeight nA nB a b) x ref)+
      (1+Real.sqrt α)*Real.sqrt Q := by
  exact merged_root (globalWeight nA nB a b) (globalWeight_nonneg nA nB a b ha hb)
    x (fun l => mergedRep nA nB x (Z l)) q ref p r C α κ Q hα (by linarith)
    (merged_local_geometric_bound nA nB a b ha hb emptyA emptyB x Z ref p α κ hα hκ ratio makarychev_local)
    quantization makarychev_server

end FTF

namespace FTF
open scoped BigOperators
variable {A E K L S : Type*} [Fintype A] [MetricSpace E] [Fintype K] [Nonempty K]
  [Fintype L] [Fintype S]

/-- Exact displayed binary additive Phi bound on the explicit slice model. -/
theorem warm_start_binary_fair (n : A → ℕ) (ω : A → ℝ) (hω : ∀ a, 0 ≤ ω a)
    (group : SliceRecords n → Bool)
    (x : SliceRecords n → E) (Z : L → A → K → E) (q : L → SliceRecords n → E)
    (ref : K → E) (p : Law L) (r : L → Law S) (C : L → S → K → E)
    (k : ℕ) (hk : 1 ≤ k) (d γ η : ℝ) (hd : 0 ≤ d) (hη : 0 < η)
    (mass : (∑ i : SliceRecords n, ω i.1)=2)
    (makarychev_local : ∀ a, expect p (fun l => cost (fun _ : Fin (n a) => 1)
      (fun j => x ⟨a,j⟩) (Z l a)) ≤ mrsAlpha k*cost (fun _ : Fin (n a) => 1) (fun j => x ⟨a,j⟩) ref)
    (grid : ∀ l i, dist (localRep n x (Z l) i) (q l i)^2 ≤ d*γ^2/4)
    (makarychev_server : ∀ l, expect (r l) (fun s => cost (fun i : SliceRecords n => ω i.1) (q l) (C l s)) ≤
      mrsAlpha k*cost (fun i : SliceRecords n => ω i.1) (q l) ref) :
    expect (joint p r) (fun o => fairOn (fun i : SliceRecords n => ω i.1) group x (C o.1 o.2)) ≤
      2*(1+η)*mrsAlpha k*(Real.sqrt (mrsAlpha k)+2)^2*fairOn (fun i : SliceRecords n => ω i.1) group x ref +
      ((1+1/η)*(1+Real.sqrt (mrsAlpha k))^2/2)*d*γ^2 := by
  have hr := warm_start_binary_grid n ω hω x Z q ref p r C k hk d γ mass makarychev_local grid makarychev_server
  have h := fair_additive_from_root (fun i : SliceRecords n => ω i.1) (fun i => hω i.1)
    group x ref (joint p r) (fun o => C o.1 o.2) (mrsAlpha k) (d*γ^2/2) η
    (mrsAlpha_nonneg k hk) (by positivity) hη hr
  simp only [Fintype.card_bool, Nat.cast_ofNat] at h
  convert h using 1
  ring

/-- Exact gamma=0 Phi coefficient, without introducing a Young tradeoff loss. -/
theorem warm_start_binary_fair_zero (n : A → ℕ) (ω : A → ℝ) (hω : ∀ a, 0 ≤ ω a)
    (group : SliceRecords n → Bool)
    (x : SliceRecords n → E) (Z : L → A → K → E) (q : L → SliceRecords n → E)
    (ref : K → E) (p : Law L) (r : L → Law S) (C : L → S → K → E)
    (k : ℕ) (hk : 1 ≤ k)
    (makarychev_local : ∀ a, expect p (fun l => cost (fun _ : Fin (n a) => 1)
      (fun j => x ⟨a,j⟩) (Z l a)) ≤ mrsAlpha k*cost (fun _ : Fin (n a) => 1) (fun j => x ⟨a,j⟩) ref)
    (quantization : expect p (fun l => distortion (fun i : SliceRecords n => ω i.1)
      (localRep n x (Z l)) (q l)) ≤ 0)
    (makarychev_server : ∀ l, expect (r l) (fun s => cost (fun i : SliceRecords n => ω i.1) (q l) (C l s)) ≤
      mrsAlpha k*cost (fun i : SliceRecords n => ω i.1) (q l) ref) :
    expect (joint p r) (fun o => fairOn (fun i : SliceRecords n => ω i.1) group x (C o.1 o.2)) ≤
      2*mrsAlpha k*(Real.sqrt (mrsAlpha k)+2)^2*fairOn (fun i : SliceRecords n => ω i.1) group x ref := by
  have hr := split_warm_start n ω hω x Z q ref p r C (mrsAlpha k) 0 (mrsAlpha_nonneg k hk)
    makarychev_local quantization makarychev_server
  have h := fair_zero_from_root (fun i : SliceRecords n => ω i.1) (fun i => hω i.1)
    group x ref (joint p r) (fun o => C o.1 o.2) (mrsAlpha k) (mrsAlpha_nonneg k hk)
    (by simpa using hr)
  simpa using h
end FTF
