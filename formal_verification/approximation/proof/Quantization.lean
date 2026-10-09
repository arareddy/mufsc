import Transfer

namespace FTF
open scoped BigOperators
variable {I L E : Type*} [Fintype I] [Fintype L] [MetricSpace E]

lemma quantization_expectation_bound (w : I → ℝ) (hw : ∀ i, 0 ≤ w i)
    (p : Law L) (z q : L → I → E) (B : ℝ)
    (grid : ∀ l i, dist (z l i) (q l i)^2 ≤ B) :
    expect p (fun l => distortion w (z l) (q l)) ≤ (∑ i, w i)*B := by
  exact (expect_mono p (fun l => distortion_bound w hw (z l) (q l) B (grid l))).trans_eq
    (expect_const _ _)

/-- The binary normalized mass gives exactly d*gamma²/2. -/
lemma binary_grid_bound (w : I → ℝ) (hw : ∀ i, 0 ≤ w i) (mass : ∑ i, w i=2)
    (p : Law L) (z q : L → I → E) (d γ : ℝ)
    (grid : ∀ l i, dist (z l i) (q l i)^2 ≤ d*γ^2/4) :
    expect p (fun l => distortion w (z l) (q l)) ≤ d*γ^2/2 := by
  have h := quantization_expectation_bound w hw p z q (d*γ^2/4) grid
  rw [mass] at h
  linarith

/-- This same formula yields m*d*gamma²/4 with m nonempty groups. -/
lemma multigroup_grid_bound (w : I → ℝ) (hw : ∀ i, 0 ≤ w i) (m : ℝ)
    (mass : ∑ i, w i=m) (p : Law L) (z q : L → I → E) (d γ : ℝ)
    (grid : ∀ l i, dist (z l i) (q l i)^2 ≤ d*γ^2/4) :
    expect p (fun l => distortion w (z l) (q l)) ≤ m*d*γ^2/4 := by
  have h := quantization_expectation_bound w hw p z q (d*γ^2/4) grid
  rw [mass] at h
  nlinarith

/-- Represented-anchor snap term, including its expected-cost form.
Grid and actual rounding residual bounds are geometric premises. -/
theorem represented_quantization (w : I → ℝ) (hw : ∀ i, 0 ≤ w i) (mass : ∑ i, w i=2)
    (p : Law L) (z grid q : L → I → E) (d γ ρ : ℝ) (hρ : 0 ≤ ρ)
    (hgrid : ∀ l i, dist (z l i) (grid l i)^2 ≤ d*γ^2/4)
    (hround : ∀ l i, dist (grid l i) (q l i) ≤ ρ) :
    expect p (fun l => distortion w (z l) (q l)) ≤
      (Real.sqrt (d*γ^2/2)+Real.sqrt 2*ρ)^2 := by
  have hroot (l : L) : Real.sqrt (distortion w (z l) (q l)) ≤
      Real.sqrt (d*γ^2/2)+Real.sqrt 2*ρ := by
    have h := represented_snap_bound w hw (z l) (grid l) (q l) (d*γ^2/4) (ρ^2)
      (hgrid l) (fun i => by nlinarith [hround l i, dist_nonneg (x := grid l i) (y := q l i)])
    have he : 2*(d*γ^2/4)=d*γ^2/2 := by ring
    rw [mass, he, Real.sqrt_mul (by norm_num : (0 : ℝ) ≤ 2) (ρ^2), Real.sqrt_sq hρ] at h
    exact h
  have hbound (l : L) : distortion w (z l) (q l) ≤
      (Real.sqrt (d*γ^2/2)+Real.sqrt 2*ρ)^2 :=
    (Real.sqrt_le_left (by positivity)).mp (hroot l)
  exact (expect_mono p hbound).trans_eq (expect_const _ _)
end FTF
