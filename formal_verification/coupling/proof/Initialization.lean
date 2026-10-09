import Deletion
import Mathlib.Algebra.BigOperators.Fin
namespace Coupling
noncomputable section
open scoped BigOperators

/-- Three coordinate locations; each stands for two ordered local slots, the second of weight 0. -/
def sumLocation (f : Location → ℝ) : ℝ := f .neg + f .pos + f .zero

def serverWeight (a : ℝ) : Location → ℝ
  | .neg => a | .pos => 1-a | .zero => 1

def d2 (x y : Location) : ℝ := (coord x-coord y)^2

def initFirst (a : ℝ) (x : Location) : ℝ := serverWeight a x / sumLocation (serverWeight a)
def initSecond (a : ℝ) (x y : Location) : ℝ :=
  serverWeight a y*d2 y x / sumLocation (fun z => serverWeight a z*d2 z x)
def initPair (a : ℝ) (x y : Location) : ℝ := initFirst a x * initSecond a x y

/-- The six possible ordered distinct-coordinate pairs. -/
def pairTable (a : ℝ) (i : Fin 6) : ℝ :=
  if i.val=0 then a/2 else
  if i.val=1 then (1-a)/2 else
  if i.val=2 then a/(2*(1+4*(1-a))) else
  if i.val=3 then 2*a*(1-a)/(1+4*(1-a)) else
  if i.val=4 then (1-a)/(2*(1+4*a)) else 2*a*(1-a)/(1+4*a)

def pairAt (i : Fin 6) : Location × Location :=
  if i.val=0 then (.zero,.neg) else if i.val=1 then (.zero,.pos) else
  if i.val=2 then (.neg,.zero) else if i.val=3 then (.neg,.pos) else
  if i.val=4 then (.pos,.zero) else (.pos,.neg)

theorem table_is_d2_sampling (a : ℝ) (ha : 0<a) (hb : a<1) (i : Fin 6) :
    initPair a (pairAt i).1 (pairAt i).2 = pairTable a i := by
  have h1 : 1+4*(1-a) ≠ 0 := by linarith
  have h2 : 1+4*a ≠ 0 := by linarith
  have h3 : (1-a)*4+1 ≠ 0 := by linarith
  have h4 : 10-a*8 ≠ 0 := by linarith
  have h5 : a*4+1 ≠ 0 := by linarith
  fin_cases i <;>
    norm_num [pairAt,initPair,initFirst,initSecond,serverWeight,sumLocation,d2,coord,pairTable] <;>
    field_simp [h1,h2,h3,h4,h5] <;> ring_nf <;> simp

theorem diagonal_zero (a : ℝ) (x : Location) : initPair a x x = 0 := by
  cases x <;> simp [initPair,initSecond,d2,coord]

/-- Distinct finite identities with identical coordinates always send coincident representatives. -/
theorem local_representatives_fixed (x : ℝ) (r first second : ℕ) :
    (if |x-x| ≤ |x-x| then 0 else 1 : ℕ) = 0 ∧
    (fun _ : ℕ => x) first = x ∧ (fun _ : ℕ => x) second = x ∧
    (fun _ : ℕ => x) r = x := by simp

def survivorCount (m : ℕ) : Location → ℕ
  | .neg => m | .pos => m-1 | .zero => m

def transferredWeight (m : ℕ) (x : Location) : ℝ :=
  if x=.zero then (survivorCount m x : ℝ)/m
  else (survivorCount m x : ℝ)/(2*(m : ℝ)-1)

theorem record_location_counts (m : ℕ) (x : Location) :
    (∑ r : Retained m, if location r=x then 1 else 0 : ℕ) = survivorCount m x := by
  simp only [Retained,Fintype.sum_sum_type]
  cases x <;> simp [location,survivorCount]

theorem transferred_weights (m : ℕ) (hm : 1 ≤ m) (x : Location) :
    transferredWeight m x = serverWeight ((m : ℝ)/(2*m-1)) x := by
  have hmR : (1 : ℝ) ≤ m := by exact_mod_cast hm
  have hm0 : (m : ℝ) ≠ 0 := by linarith
  have hd : 2*(m : ℝ)-1 ≠ 0 := by linarith
  cases x <;> simp [transferredWeight,survivorCount,serverWeight,Nat.cast_sub hm]
  · field_simp
    ring
  · field_simp

/-- Balanced original group-A endpoints each carry half; B at zero carries one. -/
theorem old_transferred_weights (m : ℝ) (hm : 0<m) : m/(2*m)=1/2 ∧ m/m=1 := by
  have hn := ne_of_gt hm
  constructor <;> field_simp <;> ring

def tupleTV (a : ℝ) : ℝ := (∑ i : Fin 6, |pairTable a i-pairTable (1/2) i|)/2

theorem table_probability_sum (a : ℝ) (ha : 0<a) (hb : a<1) :
    (∑ i : Fin 6, pairTable a i) = 1 := by
  have h1 : 1+4*(1-a) ≠ 0 := by linarith
  have h2 : 1+4*a ≠ 0 := by linarith
  norm_num [Fin.sum_univ_succ,pairTable]
  field_simp
  ring

theorem table_nonnegative (a : ℝ) (ha : 0<a) (hb : a<1) (i : Fin 6) :
    0 ≤ pairTable a i := by
  have h1 : 0<1-a := by linarith
  fin_cases i <;> norm_num [pairTable] <;> positivity

/-- Signs are proved on the exact interval required by m≥4. -/
theorem six_table_signs (a : ℝ) (ha : 1/2<a) (hb : a≤4/7) :
    0 ≤ a/2-1/4 ∧ (1-a)/2-1/4 ≤ 0 ∧
    0 ≤ a/(2*(1+4*(1-a)))-1/12 ∧
    0 ≤ 2*a*(1-a)/(1+4*(1-a))-1/6 ∧
    (1-a)/(2*(1+4*a))-1/12 ≤ 0 ∧
    2*a*(1-a)/(1+4*a)-1/6 ≤ 0 := by
  have hd1 : 0 < 1+4*(1-a) := by linarith
  have hd2 : 0 < 1+4*a := by linarith
  have h2d1 : 0 < 2*(1+4*(1-a)) := by positivity
  have h2d2 : 0 < 2*(1+4*a) := by positivity
  refine ⟨by linarith,by linarith,?_,?_,?_,?_⟩
  · apply sub_nonneg.mpr
    apply (le_div_iff₀ h2d1).2
    linarith
  · apply sub_nonneg.mpr
    apply (le_div_iff₀ hd1).2
    nlinarith [mul_nonneg (show 0≤2*a-1 by linarith) (show 0≤5-6*a by linarith)]
  · apply sub_nonpos.mpr
    apply (div_le_iff₀ h2d2).2
    linarith
  · apply sub_nonpos.mpr
    apply (div_le_iff₀ hd2).2
    nlinarith [sq_nonneg (a-1/2)]

theorem initialization_tuple_TV (a : ℝ) (ha : 1/2<a) (hb : a≤4/7) :
    tupleTV a = a-1/2 := by
  obtain ⟨h0,h1,h2,h3,h4,h5⟩ := six_table_signs a ha hb
  have hd1 : 1+4*(1-a) ≠ 0 := by linarith
  have hd2 : 1+4*a ≠ 0 := by linarith
  unfold tupleTV
  norm_num [Fin.sum_univ_succ,pairTable]
  rw [abs_of_nonneg h0,abs_of_nonpos h1,abs_of_nonneg h2,
    abs_of_nonneg h3,abs_of_nonpos h4,abs_of_nonpos h5]
  field_simp
  ring

theorem retained_parameter_range (m : ℕ) (hm : 4 ≤ m) :
    (1 : ℝ)/2 < m/(2*(m : ℝ)-1) ∧ m/(2*(m : ℝ)-1) ≤ 4/7 := by
  have hmR : (4 : ℝ) ≤ m := by exact_mod_cast hm
  have hd : 0<2*(m : ℝ)-1 := by linarith
  constructor
  · apply (lt_div_iff₀ hd).2; linarith
  · apply (div_le_iff₀ hd).2; linarith

theorem retained_tuple_TV (m : ℕ) (hm : 4 ≤ m) :
    tupleTV ((m : ℝ)/(2*m-1)) = 1/(2*(2*(m : ℝ)-1)) := by
  rw [initialization_tuple_TV _ (retained_parameter_range m hm).1 (retained_parameter_range m hm).2]
  have hmR : (4 : ℝ) ≤ m := by exact_mod_cast hm
  have hd : 2*(m : ℝ)-1 ≠ 0 := by linarith
  field_simp
  ring

#print axioms table_is_d2_sampling
#print axioms record_location_counts
#print axioms transferred_weights
#print axioms table_probability_sum
#print axioms table_nonnegative
#print axioms initialization_tuple_TV
#print axioms retained_tuple_TV
end
end Coupling
