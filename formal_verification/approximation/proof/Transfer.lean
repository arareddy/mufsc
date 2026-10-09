import Geometry

/-! The main transfer result. `makarychev_server` is explicitly the imported
literature guarantee for the conditional finite anchor sampling law; `localBound`
is the localBound replacement guarantee (obtained by local_sum_bound or merged
client bounds). Geometry and both finite L2 conditioning steps are proved. -/
namespace FTF
open scoped BigOperators
variable {I K E L S : Type*} [Fintype I] [Fintype K] [Nonempty K]
  [MetricSpace E] [Fintype L] [Fintype S]

lemma conditional_server_root (w : I → ℝ) (hw : ∀ i, 0 ≤ w i)
    (x q : I → E) (ref : K → E) (p : Law S) (C : S → K → E)
    (α : ℝ) (hα : 0 ≤ α)
    (makarychev_server : expect p (fun s => cost w q (C s)) ≤ α*cost w q ref) :
    Real.sqrt (expect p (fun s => cost w x (C s))) ≤
      (1+Real.sqrt α)*Real.sqrt (distortion w x q)+Real.sqrt α*Real.sqrt (cost w x ref) := by
  have hg := sqrt_expect_affine p (fun s => cost w x (C s)) (fun s => cost w q (C s))
    (fun s => cost_nonneg w hw x (C s)) (fun s => cost_nonneg w hw q (C s))
    1 (Real.sqrt (distortion w x q)) (by norm_num) (Real.sqrt_nonneg _)
    (fun s => by simpa [add_comm] using cost_root_transfer w hw x q (C s))
  have hs := Real.sqrt_le_sqrt makarychev_server
  rw [Real.sqrt_mul hα] at hs
  have hr := cost_root_transfer w hw q x ref
  rw [distortion_symm w q x] at hr
  have hh := mul_le_mul_of_nonneg_left hr (Real.sqrt_nonneg α)
  nlinarith

/-- Substantive two-stage finite probability transfer theorem for actual
nearest-center costs. It holds for any reference center tuple (hence an optimum).
The quantization term is the expectation of the actual represented distortion. -/
theorem finite_geometric_transfer (w : I → ℝ) (hw : ∀ i, 0 ≤ w i)
    (x : I → E) (z q : L → I → E) (ref : K → E)
    (localLaw : Law L) (serverLaw : L → Law S) (C : L → S → K → E)
    (α β : ℝ) (hα : 0 ≤ α) (hβ : 0 ≤ β)
    (localBound : expect localLaw (fun l => distortion w x (z l)) ≤ β*cost w x ref)
    (makarychev_server : ∀ l, expect (serverLaw l) (fun s => cost w (q l) (C l s)) ≤
      α*cost w (q l) ref) :
    Real.sqrt (expect (joint localLaw serverLaw) (fun o => cost w x (C o.1 o.2))) ≤
      ((1+Real.sqrt α)*Real.sqrt β+Real.sqrt α)*Real.sqrt (cost w x ref) +
      (1+Real.sqrt α)*Real.sqrt (expect localLaw (fun l => distortion w (z l) (q l))) := by
  rw [tower localLaw serverLaw (fun l s => cost w x (C l s))]
  have outer := sqrt_expect_affine localLaw
    (fun l => expect (serverLaw l) (fun s => cost w x (C l s)))
    (fun l => distortion w x (q l))
    (fun l => expect_nonneg _ (fun s => cost_nonneg w hw x (C l s)))
    (fun l => distortion_nonneg w hw x (q l))
    (1+Real.sqrt α) (Real.sqrt α*Real.sqrt (cost w x ref))
    (by positivity) (by positivity)
    (fun l => conditional_server_root w hw x (q l) ref (serverLaw l) (C l) α hα
      (makarychev_server l))
  have repl := sqrt_expect_two localLaw
    (fun l => distortion w x (q l)) (fun l => distortion w x (z l))
    (fun l => distortion w (z l) (q l))
    (fun l => distortion_nonneg w hw x (q l))
    (fun l => distortion_nonneg w hw x (z l))
    (fun l => distortion_nonneg w hw (z l) (q l))
    (fun l => distortion_root_triangle w hw x (z l) (q l))
  have hl := Real.sqrt_le_sqrt localBound
  rw [Real.sqrt_mul hβ] at hl
  have hc := mul_le_mul_of_nonneg_left (repl.trans (add_le_add_right hl _))
    (show 0 ≤ 1+Real.sqrt α by positivity)
  nlinarith

/-- Split-group exact root coefficient alpha^(1/2)(alpha^(1/2)+2). -/
theorem split_root (w : I → ℝ) (hw : ∀ i, 0 ≤ w i)
    (x : I → E) (z q : L → I → E) (ref : K → E)
    (p : Law L) (r : L → Law S) (C : L → S → K → E)
    (α Q : ℝ) (hα : 0 ≤ α)
    (localBound : expect p (fun l => distortion w x (z l)) ≤ α*cost w x ref)
    (quantization : expect p (fun l => distortion w (z l) (q l)) ≤ Q)
    (makarychev_server : ∀ l, expect (r l) (fun s => cost w (q l) (C l s)) ≤
      α*cost w (q l) ref) :
    Real.sqrt (expect (joint p r) (fun o => cost w x (C o.1 o.2))) ≤
      Real.sqrt α*(Real.sqrt α+2)*Real.sqrt (cost w x ref) +
      (1+Real.sqrt α)*Real.sqrt Q := by
  have h := finite_geometric_transfer w hw x z q ref p r C α α hα hα localBound makarychev_server
  have hq := mul_le_mul_of_nonneg_left (Real.sqrt_le_sqrt quantization)
    (show 0 ≤ 1+Real.sqrt α by positivity)
  nlinarith

/-- Merged exact root coefficient; beta=alpha*kappa, without squared-triangle loss. -/
theorem merged_root (w : I → ℝ) (hw : ∀ i, 0 ≤ w i)
    (x : I → E) (z q : L → I → E) (ref : K → E)
    (p : Law L) (r : L → Law S) (C : L → S → K → E)
    (α κ Q : ℝ) (hα : 0 ≤ α) (hκ : 0 ≤ κ)
    (localBound : expect p (fun l => distortion w x (z l)) ≤ α*κ*cost w x ref)
    (quantization : expect p (fun l => distortion w (z l) (q l)) ≤ Q)
    (makarychev_server : ∀ l, expect (r l) (fun s => cost w (q l) (C l s)) ≤
      α*cost w (q l) ref) :
    Real.sqrt (expect (joint p r) (fun o => cost w x (C o.1 o.2))) ≤
      Real.sqrt α*((1+Real.sqrt α)*Real.sqrt κ+1)*Real.sqrt (cost w x ref) +
      (1+Real.sqrt α)*Real.sqrt Q := by
  have h := finite_geometric_transfer w hw x z q ref p r C α (α*κ) hα
    (mul_nonneg hα hκ) localBound makarychev_server
  rw [Real.sqrt_mul hα] at h
  have hq := mul_le_mul_of_nonneg_left (Real.sqrt_le_sqrt quantization)
    (show 0 ≤ 1+Real.sqrt α by positivity)
  nlinarith

/-- Any deterministic or stochastic post-processing that lowers the anchor
objective preserves the imported conditional guarantee. -/
lemma server_nonincrease_preserves (w : I → ℝ) (q : I → E) (ref : K → E)
    (p : Law S) (C C' : S → K → E) (α : ℝ)
    (mrs : expect p (fun s => cost w q (C s)) ≤ α*cost w q ref)
    (h : ∀ s, cost w q (C' s) ≤ cost w q (C s)) :
    expect p (fun s => cost w q (C' s)) ≤ α*cost w q ref :=
  (expect_mono p h).trans mrs

end FTF
