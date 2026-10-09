# Verified geometry extension

**20 new lemmas; 100 audited including 80 unchanged prerequisites.** Counts include supporting lemmas, not counts of paper theorems. All four final commands used `--trust=0 -j1` and returned zero. All three compiler logs are empty. Every audited lemma depends exactly on propext, Classical.choice, Quot.sound.

| New declaration | Source line |
| --- | ---: |
| `FairUpdate.Geometry.two_weight_comparison` | 8 |
| `FairUpdate.Geometry.selected_minimizers_monotone` | 28 |
| `FairUpdate.Geometry.weighted_binary` | 45 |
| `FairUpdate.Geometry.quadratic_lambda_monotonicity` | 50 |
| `FairUpdate.Geometry.binary_minimizer_formula` | 69 |
| `FairUpdate.Geometry.projection_expansion_a` | 85 |
| `FairUpdate.Geometry.projection_expansion_b` | 94 |
| `FairUpdate.Geometry.clamp_properties` | 106 |
| `FairUpdate.Geometry.coincident_of_direction_zero` | 119 |
| `FairUpdate.Geometry.segment_projection_nonincrease` | 127 |
| `FairUpdate.Geometry.projection_expansion_segment` | 148 |
| `FairUpdate.Geometry.clamp_variational` | 157 |
| `FairUpdate.Geometry.clamped_projection_is_nearest` | 166 |
| `FairUpdate.Geometry.weighted_segment_projection` | 178 |
| `FairUpdate.Geometry.two_pow_mod_three` | 185 |
| `FairUpdate.Geometry.five_ninths_not_dyadic` | 193 |
| `FairUpdate.Geometry.mean_cost_expansion` | 216 |
| `FairUpdate.Geometry.mean_group_costs` | 225 |
| `FairUpdate.Geometry.positive_mean_denominator` | 234 |
| `FairUpdate.Geometry.ideal_mean_curve_monotonicity` | 246 |

## Exact compiler-printed new statements

```lean
FairUpdate.Geometry.two_weight_comparison : ∀ (t u a₀ b₀ a₁ b₁ : ℝ),
  0 ≤ t →
    u ≤ 1 →
      t < u →
        t * a₀ + (1 - t) * b₀ ≤ t * a₁ + (1 - t) * b₁ →
          u * a₁ + (1 - u) * b₁ ≤ u * a₀ + (1 - u) * b₀ → a₁ ≤ a₀ ∧ b₀ ≤ b₁

@FairUpdate.Geometry.selected_minimizers_monotone : ∀ {X : Type u_1} (fA fB : X → ℝ) (curve : ℝ → X),
  (∀ (t : ℝ), 0 ≤ t → t ≤ 1 → ∀ (x : X), t * fA (curve t) + (1 - t) * fB (curve t) ≤ t * fA x + (1 - t) * fB x) →
    ∀ (t u : ℝ), 0 ≤ t → t ≤ u → u ≤ 1 → fA (curve u) ≤ fA (curve t) ∧ fB (curve t) ≤ fB (curve u)

FairUpdate.Geometry.weighted_binary : ∀ (t : ℝ) (ht : 0 ≤ t) (ht1 : t ≤ 1) (f : Bool → ℝ),
  FairUpdate.weighted (FairUpdate.Geometry.binarySimplex t ht ht1) f = t * f false + (1 - t) * f true

@FairUpdate.Geometry.quadratic_lambda_monotonicity : ∀ {I : Type u_1} [inst : Fintype I]
  (p : FairUpdate.Quadratics Bool I) (fallback : ℝ → I → ℝ) (t u : ℝ) (ht : 0 ≤ t) (htu : t ≤ u) (hu : u ≤ 1),
  let ct := FairUpdate.minimizer p (FairUpdate.Geometry.binarySimplex t ht ⋯) (fallback t);
  let cu := FairUpdate.minimizer p (FairUpdate.Geometry.binarySimplex u ⋯ hu) (fallback u);
  FairUpdate.groupCost p cu false ≤ FairUpdate.groupCost p ct false ∧
    FairUpdate.groupCost p ct true ≤ FairUpdate.groupCost p cu true

@FairUpdate.Geometry.binary_minimizer_formula : ∀ {I : Type u_1} [inst : Fintype I] (p : FairUpdate.Quadratics Bool I)
  (t : ℝ) (ht : 0 ≤ t) (ht1 : t ≤ 1) (fallback : I → ℝ) (i : I),
  t * p.a false i + (1 - t) * p.a true i ≠ 0 →
    FairUpdate.minimizer p (FairUpdate.Geometry.binarySimplex t ht ht1) fallback i =
      (t * p.b false i + (1 - t) * p.b true i) / (t * p.a false i + (1 - t) * p.a true i)

@FairUpdate.Geometry.projection_expansion_a : ∀ {D : Type u_1} [inst : Fintype D] (x a b : D → ℝ) (t : ℝ),
  FairUpdate.Moments.squaredDistance x a =
    FairUpdate.Moments.squaredDistance x (FairUpdate.Geometry.along a b t) +
        FairUpdate.Moments.squaredDistance (FairUpdate.Geometry.along a b t) a +
      2 * t * (FairUpdate.Geometry.directionDot x a b - t * FairUpdate.Geometry.directionSquare a b)

@FairUpdate.Geometry.projection_expansion_b : ∀ {D : Type u_1} [inst : Fintype D] (x a b : D → ℝ) (t : ℝ),
  FairUpdate.Moments.squaredDistance x b =
    FairUpdate.Moments.squaredDistance x (FairUpdate.Geometry.along a b t) +
        FairUpdate.Moments.squaredDistance (FairUpdate.Geometry.along a b t) b +
      2 * (t - 1) * (FairUpdate.Geometry.directionDot x a b - t * FairUpdate.Geometry.directionSquare a b)

FairUpdate.Geometry.clamp_properties : ∀ (h v : ℝ),
  0 < v →
    let t := FairUpdate.Geometry.clampParameter h v;
    0 ≤ t ∧ t ≤ 1 ∧ 0 ≤ t * (h - t * v) ∧ 0 ≤ (t - 1) * (h - t * v)

@FairUpdate.Geometry.coincident_of_direction_zero : ∀ {D : Type u_1} [inst : Fintype D] (a b : D → ℝ),
  FairUpdate.Geometry.directionSquare a b = 0 → a = b

@FairUpdate.Geometry.segment_projection_nonincrease : ∀ {D : Type u_1} [inst : Fintype D] (x a b : D → ℝ),
  ∃ t,
    0 ≤ t ∧
      t ≤ 1 ∧
        FairUpdate.Moments.squaredDistance (FairUpdate.Geometry.along a b t) a ≤
            FairUpdate.Moments.squaredDistance x a ∧
          FairUpdate.Moments.squaredDistance (FairUpdate.Geometry.along a b t) b ≤
            FairUpdate.Moments.squaredDistance x b

@FairUpdate.Geometry.projection_expansion_segment : ∀ {D : Type u_1} [inst : Fintype D] (x a b : D → ℝ) (s t : ℝ),
  FairUpdate.Moments.squaredDistance x (FairUpdate.Geometry.along a b s) =
    FairUpdate.Moments.squaredDistance x (FairUpdate.Geometry.along a b t) +
        (s - t) ^ 2 * FairUpdate.Geometry.directionSquare a b -
      2 * (s - t) * (FairUpdate.Geometry.directionDot x a b - t * FairUpdate.Geometry.directionSquare a b)

FairUpdate.Geometry.clamp_variational : ∀ (h v s : ℝ),
  0 < v →
    0 ≤ s → s ≤ 1 → (s - FairUpdate.Geometry.clampParameter h v) * (h - FairUpdate.Geometry.clampParameter h v * v) ≤ 0

@FairUpdate.Geometry.clamped_projection_is_nearest : ∀ {D : Type u_1} [inst : Fintype D] (x a b : D → ℝ),
  0 < FairUpdate.Geometry.directionSquare a b →
    ∀ (s : ℝ),
      0 ≤ s →
        s ≤ 1 →
          FairUpdate.Moments.squaredDistance x
              (FairUpdate.Geometry.along a b
                (FairUpdate.Geometry.clampParameter (FairUpdate.Geometry.directionDot x a b)
                  (FairUpdate.Geometry.directionSquare a b))) ≤
            FairUpdate.Moments.squaredDistance x (FairUpdate.Geometry.along a b s)

@FairUpdate.Geometry.weighted_segment_projection : ∀ {D : Type u_1} [inst : Fintype D] (x a b : D → ℝ) (α β : ℝ),
  0 ≤ α →
    0 ≤ β →
      ∃ t,
        0 ≤ t ∧
          t ≤ 1 ∧
            α * FairUpdate.Moments.squaredDistance (FairUpdate.Geometry.along a b t) a ≤
                α * FairUpdate.Moments.squaredDistance x a ∧
              β * FairUpdate.Moments.squaredDistance (FairUpdate.Geometry.along a b t) b ≤
                β * FairUpdate.Moments.squaredDistance x b

FairUpdate.Geometry.two_pow_mod_three : ∀ (n : ℕ), 2 ^ n % 3 = 1 ∨ 2 ^ n % 3 = 2

FairUpdate.Geometry.five_ninths_not_dyadic : ∀ (m : ℤ) (n : ℕ), 5 / 9 ≠ ↑m / 2 ^ n

@FairUpdate.Geometry.mean_cost_expansion : ∀ {I : Type u_1} [inst : Fintype I] (δ : ℝ) (α μ c : I → ℝ),
  δ + ∑ i, α i * μ i ^ 2 + ∑ i, (α i * c i ^ 2 - 2 * (α i * μ i) * c i) = FairUpdate.Geometry.meanCost δ α μ c

@FairUpdate.Geometry.mean_group_costs : ∀ {I : Type u_1} [inst : Fintype I] (α β μ ν : I → ℝ) (hα : ∀ (i : I), 0 ≤ α i)
  (hβ : ∀ (i : I), 0 ≤ β i) (δA δB : ℝ) (c : I → ℝ),
  FairUpdate.groupCost (FairUpdate.Geometry.meanQuadratics α β μ ν hα hβ δA δB) c false =
      FairUpdate.Geometry.meanCost δA α μ c ∧
    FairUpdate.groupCost (FairUpdate.Geometry.meanQuadratics α β μ ν hα hβ δA δB) c true =
      FairUpdate.Geometry.meanCost δB β ν c

FairUpdate.Geometry.positive_mean_denominator : ∀ (α β t : ℝ), 0 < α → 0 < β → 0 ≤ t → t ≤ 1 → 0 < t * α + (1 - t) * β

@FairUpdate.Geometry.ideal_mean_curve_monotonicity : ∀ {I : Type u_1} [inst : Fintype I] (α β μ ν : I → ℝ),
  (∀ (i : I), 0 < α i) →
    (∀ (i : I), 0 < β i) →
      ∀ (δA δB t u : ℝ),
        0 ≤ t →
          t ≤ u →
            u ≤ 1 →
              FairUpdate.Geometry.meanCost δA α μ (FairUpdate.Geometry.meanCurve α β μ ν u) ≤
                  FairUpdate.Geometry.meanCost δA α μ (FairUpdate.Geometry.meanCurve α β μ ν t) ∧
                FairUpdate.Geometry.meanCost δB β ν (FairUpdate.Geometry.meanCurve α β μ ν t) ≤
                  FairUpdate.Geometry.meanCost δB β ν (FairUpdate.Geometry.meanCurve α β μ ν u)
```

The unmodified complete output, including all prerequisite lemmas, is logs/final_axioms.log. Definitions and proof arguments are in proof/Geometry.lean.
