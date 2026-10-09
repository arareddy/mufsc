import Certificates
import Mathlib.Tactic.NormNum
import Mathlib.Tactic.FinCases

namespace Replay

theorem maxOn_le {L : Type*} (s : Finset L) (f : L → ℝ) (h : s.Nonempty)
    (B : ℝ) (bound : ∀ m ∈ s, f m ≤ B) : maxOn s f ≤ B := by
  simp only [maxOn, dif_pos h]
  exact (Finset.sup'_le_iff h f).mpr bound

/-- The exact runner-up test accepts every basic-test pass. -/
theorem basic_implies_runner {P L : Type*} [PseudoMetricSpace P] [Fintype L]
    [DecidableEq L] (x : P) (old new : L → P) (j r : L) (d₂ : ℝ)
    (hr : r ≠ j)
    (test : shift old new j + maxOn (competitors j) (shift old new) <
      d₂ - dist x (old j)) : runnerTest x old new j r d₂ := by
  constructor
  · have hm := le_maxOn (competitors j) (shift old new) r (by simp [competitors, hr])
    have hab := le_abs_self (d₂ - shift old new r)
    linarith
  · intro hn
    have hmax : maxOn (nonRunners j r) (shift old new) ≤
        maxOn (competitors j) (shift old new) := by
      apply maxOn_le _ _ hn
      intro m hm
      exact le_maxOn _ _ m (Finset.mem_of_mem_erase hm)
    have hb := le_max_right 0 (d₂ - maxOn (nonRunners j r) (shift old new))
    linarith

/-- Three distinct candidates cannot all be excluded by two identities. -/
theorem three_leave_one {L : Type*} [DecidableEq L] (a b c j r : L)
    (hab : a ≠ b) (hac : a ≠ c) (hbc : b ≠ c) :
    ∃ m ∈ ({a, b, c} : Finset L), m ≠ j ∧ m ≠ r := by
  by_contra hn
  push_neg at hn
  have ha : a = j ∨ a = r := by
    by_cases h : a = j
    · exact Or.inl h
    · exact Or.inr (hn a (by simp) h)
  have hb : b = j ∨ b = r := by
    by_cases h : b = j
    · exact Or.inl h
    · exact Or.inr (hn b (by simp) h)
  have hc : c = j ∨ c = r := by
    by_cases h : c = j
    · exact Or.inl h
    · exact Or.inr (hn c (by simp) h)
  rcases ha with ha | ha <;> rcases hb with hb | hb <;> rcases hc with hc | hc
  all_goals first | exact hab (ha.trans hb.symm) | exact hac (ha.trans hc.symm) | exact hbc (hb.trans hc.symm)

/-- A maximum after excluding at most two identities lies among the top three.
This is a finite correctness statement, not a machine runtime theorem. -/
theorem top_three_suffice {L : Type*} [Fintype L] [DecidableEq L]
    (f : L → ℝ) (a b c j r : L)
    (hab : a ≠ b) (hac : a ≠ c) (hbc : b ≠ c)
    (hba : f b ≤ f a) (hcb : f c ≤ f b)
    (rest : ∀ m, m ≠ a → m ≠ b → m ≠ c → f m ≤ f c) :
    maxOn (nonRunners j r) f =
      maxOn (({a,b,c} : Finset L).filter (fun m => m ≠ j ∧ m ≠ r)) f := by
  let top := ({a,b,c} : Finset L).filter (fun m => m ≠ j ∧ m ≠ r)
  obtain ⟨q, hq, hqj, hqr⟩ := three_leave_one a b c j r hab hac hbc
  have hqtop : q ∈ top := by simp only [top, Finset.mem_filter]; exact ⟨hq,hqj,hqr⟩
  have htop : top.Nonempty := ⟨q,hqtop⟩
  have hqall : q ∈ nonRunners j r := by simp [nonRunners, competitors, hqj, hqr]
  have hall : (nonRunners j r).Nonempty := ⟨q,hqall⟩
  have hqbig : f c ≤ f q := by
    simp only [Finset.mem_insert, Finset.mem_singleton] at hq
    rcases hq with hq | hq | hq
    · subst q; exact hcb.trans hba
    · subst q; exact hcb
    · subst q; exact le_rfl
  change maxOn (nonRunners j r) f = maxOn top f
  apply le_antisymm
  · apply maxOn_le _ _ hall
    intro m hm
    by_cases ht : m ∈ ({a,b,c} : Finset L)
    · apply le_maxOn _ _ m
      have hjr : m ≠ j ∧ m ≠ r := by
        simpa [nonRunners, competitors, and_comm] using hm
      exact Finset.mem_filter.mpr ⟨ht, hjr⟩
    · have hma : m ≠ a := by intro h; subst m; exact ht (by simp)
      have hmb : m ≠ b := by intro h; subst m; exact ht (by simp)
      have hmc : m ≠ c := by intro h; subst m; exact ht (by simp)
      exact (rest m hma hmb hmc).trans (hqbig.trans (le_maxOn _ _ q hqtop))
  · apply maxOn_le _ _ htop
    intro m hm
    have hh := (Finset.mem_filter.mp hm).2
    exact le_maxOn _ _ m (by simp [nonRunners, competitors, hh.1, hh.2])

/-- Strict improvement is already visible with two centers and overshoot. -/
theorem overshoot_strict_improvement :
    ¬ ((0 : ℝ) + 100 < 1 - 0) ∧ (0 : ℝ) + 0 < |1 - 100| := by norm_num

/-- Appendix's runner-only counterexample: the third center beats the shifted
winner despite a large retained margin against the old runner. -/
theorem runner_only_counterexample :
    (0 : ℝ) < 10 ∧ (10 : ℝ) < 11 ∧
    |(1 : ℝ)/2| < |10 - 0| ∧ |(1 : ℝ)/10| < |(1 : ℝ)/2| := by
  norm_num [abs_of_nonneg (by norm_num : (0 : ℝ) ≤ 1/2),
    abs_of_nonneg (by norm_num : (0 : ℝ) ≤ 1/10)]

#print axioms basic_implies_runner
#print axioms three_leave_one
#print axioms top_three_suffice
#print axioms overshoot_strict_improvement
#print axioms runner_only_counterexample
end Replay
