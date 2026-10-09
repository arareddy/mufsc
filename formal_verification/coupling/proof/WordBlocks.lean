import Coupling
import Mathlib.Algebra.BigOperators.Fin
namespace Coupling
noncomputable section
open scoped BigOperators

abbrev Word := Fin (2^64)

/-- Least-significant word first, precisely the finite base-2^64 positional encoding. -/
def assemble {ell : ℕ} (words : Fin ell → Word) : Fin ((2^64)^ell) := finFunctionFinEquiv words

theorem assembly_formula {ell : ℕ} (words : Fin ell → Word) :
    (assemble words).val = ∑ i, (words i).val*(2^64)^i.val := rfl

theorem assembly_bijective (ell : ℕ) : Function.Bijective (@assemble ell) :=
  finFunctionFinEquiv.bijective

/-- IID uniform words give a uniform integer block because positional assembly is a bijection. -/
theorem block_low_bits_count (ell w c : ℕ) (hw : w ≤ 64*ell) (hc : c < 2^w) :
    (∑ words : Fin ell → Word, if (assemble words).val%(2^w)=c then 1 else 0 : ℕ) =
      2^(64*ell-w) := by
  have he : (∑ words : Fin ell → Word, if (assemble words).val%(2^w)=c then 1 else 0 : ℕ) =
      ∑ u : Fin ((2^64)^ell), if u.val%(2^w)=c then 1 else 0 := by
    exact Equiv.sum_comp finFunctionFinEquiv (fun u => if u.val%(2^w)=c then 1 else 0)
  rw [he]
  change (∑ u : Fin ((2^64)^ell), (fun v : ℕ => if v%(2^w)=c then 1 else 0) u.val) = _
  rw [Fin.sum_univ_eq_sum_range (fun v : ℕ => if v%(2^w)=c then (1 : ℕ) else 0) ((2^64)^ell)]
  have hp : (2^64)^ell = 2^w*2^(64*ell-w) := by
    rw [← pow_mul,← pow_add,Nat.add_sub_of_le hw]
  rw [hp]
  exact low_bits_count _ _ _ hc

theorem block_low_bits_uniform (ell w c : ℕ) (hw : w ≤ 64*ell) (hc : c < 2^w) :
    ((∑ words : Fin ell → Word, if (assemble words).val%(2^w)=c then 1 else 0 : ℕ) : ℝ) /
      (Fintype.card (Fin ell → Word) : ℝ) = 1/(2^w : ℕ) := by
  rw [block_low_bits_count ell w c hw hc]
  simp only [Fintype.card_fun,Fintype.card_fin,Word]
  have hp : (2^64)^ell = 2^w*2^(64*ell-w) := by
    rw [← pow_mul,← pow_add,Nat.add_sub_of_le hw]
  rw [hp]
  push_cast
  have hn : (2 : ℝ)^w ≠ 0 := by positivity
  have hn' : (2 : ℝ)^(64*ell-w) ≠ 0 := by positivity
  field_simp
  ring

/-- The first word's low bit survives wide assembly. -/
theorem block_first_low_bit (ell : ℕ) (words : Fin (ell+1) → Word) :
    (assemble words).val%2 = (words 0).val%2 := by
  rw [assembly_formula,Fin.sum_univ_succ]
  simp only [Fin.val_zero, Fin.val_succ, pow_zero, Nat.mul_one]
  simp only [pow_succ (2^64 : ℕ)]
  have he : (∑ i : Fin ell, (words i.succ).val*((2^64)^i.val*2^64)) =
      (2^64)*(∑ i : Fin ell, (words i.succ).val*(2^64)^i.val) := by
    rw [Finset.mul_sum]
    apply Finset.sum_congr rfl
    intro i _
    ring
  rw [he]
  exact assembled_low_bit _ _

def wordsNeeded (w : ℕ) : ℕ := (w+63)/64

theorem word_consumption (w : ℕ) :
    (wordsNeeded w = 0 ↔ w=0) ∧
    (wordsNeeded w = 1 ↔ 0<w ∧ w≤64) ∧
    w ≤ 64*wordsNeeded w ∧
    (64<w → 2 ≤ wordsNeeded w) := by unfold wordsNeeded; omega

#print axioms assembly_bijective
#print axioms block_low_bits_count
#print axioms block_low_bits_uniform
#print axioms block_first_low_bit
#print axioms word_consumption
end
end Coupling
