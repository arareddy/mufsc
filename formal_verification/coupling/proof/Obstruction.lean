import WorkProbability
import Initialization
import WordBlocks
import Traces
namespace Coupling
noncomputable section
open scoped BigOperators

theorem power_parameter (h : ℕ) (hh : 2≤h) :
    4≤2^h ∧ ∃ t : ℕ, 0<t ∧ 2^h=2*t := by
  constructor
  · obtain ⟨j,rfl⟩ := Nat.exists_eq_add_of_le hh
    have hp : 0<(2:ℕ)^j := by positivity
    simp only [pow_add]
    norm_num
    omega
  · exact power_is_even h (by omega)

/-- Ideal block/trace event probability; the branch records the manuscript's width split.
For a wide first block the old second selection reads word 1's low bit. -/
def deletionEventProbability (h : ℕ) : ℝ :=
  if h+2≤64 then narrowEventProbability (2^h)
  else wideEventProbability (2^h) (fun u => (u/2^64)%2)

theorem event_probability_lower (h : ℕ) (hh : 2≤h) :
    beta (2^h : ℕ) ≤ deletionEventProbability h ∧
    1/16 < deletionEventProbability h := by
  obtain ⟨hm,t,ht,he⟩ := power_parameter h hh
  have hl : beta (2^h : ℕ) ≤ deletionEventProbability h := by
    unfold deletionEventProbability
    rw [he]
    split_ifs
    · exact narrow_event_lower t ht
    · exact wide_event_lower t ht _
  refine ⟨hl,lt_of_lt_of_le ?_ hl⟩
  exact beta_gt_sixteenth _ (by exact_mod_cast hm)

theorem initialization_word_offsets (h : ℕ) :
    wordsNeeded 2=1 ∧
    (h+2≤64 → wordsNeeded (h+2)=1) ∧
    (64<h+2 → 1<wordsNeeded (h+2)) := by
  constructor
  · norm_num [wordsNeeded]
  constructor
  · intro hb
    exact (word_consumption (h+2)).2.1.mpr ⟨by omega,hb⟩
  · intro hb
    have hw := (word_consumption (h+2)).2.2.2 hb
    omega

theorem each_variant_event_counts (m : ℕ) (hm : 4≤m) (v : Variant) :
    2*m-1 ≤ failures m v .neg ∧
    saved (3*m-1) (failures m v .neg)=0 ∧
    duplicated (3*m-1) (failures m v .neg)=failures m v .neg := by
  have hf := failure_counts m (by omega) .neg (by decide)
  have hp := round_zero_policy m hm .neg (by decide)
  cases v
  · rw [hf.1]
    exact ⟨by omega, by simpa [hf.1] using hp.2.2.1,
      by simpa [hf.1] using hp.2.2.2.2.1⟩
  · rw [hf.2]
    exact ⟨le_refl _, by simpa [hf.2] using hp.2.2.2.1,
      by simpa [hf.2] using hp.2.2.2.2.2⟩

/-- Event contribution to point-work, derived from the record-level certificate and policy counts. -/
theorem event_work_contribution (h : ℕ) (hh : 2≤h) (v : Variant) :
    (((2^h : ℕ) : ℝ)-1)^2/(4*(2^h : ℕ)) ≤
      deletionEventProbability h*(failures (2^h) v .neg : ℝ) ∧
    (((2^h : ℕ) : ℝ)-1)^2/(4*(2^h : ℕ)) ≤
      deletionEventProbability h*(duplicated (3*(2^h)-1) (failures (2^h) v .neg) : ℝ) := by
  have hm := (power_parameter h hh).1
  have hmR : (4 : ℝ) ≤ (2^h : ℕ) := by exact_mod_cast hm
  have hc := each_variant_event_counts (2^h) hm v
  have hf : 2*((2^h : ℕ) : ℝ)-1 ≤ (failures (2^h) v .neg : ℝ) := by
    have hn : 1≤2*(2^h) := by omega
    exact_mod_cast hc.1
  have hp := (event_probability_lower h hh).1
  have hp0 : 0≤deletionEventProbability h := le_of_lt (lt_trans (by norm_num) (event_probability_lower h hh).2)
  have hb0 : 0≤beta ((2^h : ℕ) : ℝ) := le_of_lt (lt_trans (by norm_num) (beta_gt_sixteenth _ hmR))
  have hx : (((2^h : ℕ) : ℝ)-1)^2/(4*(2^h : ℕ)) ≤
      deletionEventProbability h*(failures (2^h) v .neg : ℝ) := by
    rw [← beta_times_failed _ hmR]
    calc
      _ ≤ deletionEventProbability h*(2*((2^h : ℕ) : ℝ)-1) := mul_le_mul_of_nonneg_right hp (by linarith)
      _ ≤ _ := mul_le_mul_of_nonneg_left hf hp0
  exact ⟨hx,by rw [hc.2.2];exact hx⟩

/-- A conditional finite-law theorem whose event work is computed from actual model records.
Only the joint event mass/link to a chosen probability space remains an external premise. -/
theorem finite_law_expected_work {Ω : Type*} [Fintype Ω]
    (h : ℕ) (hh : 2≤h) (v : Variant) (weight : Ω→ℝ)
    (event : Ω→Prop) [DecidablePred event] (F J : Ω→ℝ)
    (hw : ∀ x,0≤weight x) (hF : ∀ x,0≤F x) (hJ : ∀ x,0≤J x)
    (mass : deletionEventProbability h ≤ ∑ x,if event x then weight x else 0)
    (failures_on_event : ∀ x,event x → F x=(failures (2^h) v .neg : ℝ))
    (duplication_on_event : ∀ x,event x → J x=(duplicated (3*(2^h)-1) (failures (2^h) v .neg) : ℝ)) :
    (((2^h : ℕ) : ℝ)-1)^2/(4*(2^h : ℕ)) ≤ ∑ x,weight x*F x ∧
    (((2^h : ℕ) : ℝ)-1)^2/(4*(2^h : ℕ)) ≤ ∑ x,weight x*J x := by
  have hm := (power_parameter h hh).1
  have hc := each_variant_event_counts (2^h) hm v
  have hn : 1≤2*(2^h) := by omega
  have hf : 2*((2^h : ℕ) : ℝ)-1 ≤ (failures (2^h) v .neg : ℝ) := by exact_mod_cast hc.1
  apply obstruction_expectation (2^h) hm weight F J event hw hF hJ
  · exact le_trans (event_probability_lower h hh).1 mass
  · intro x hx; rw [failures_on_event x hx];exact hf
  · intro x hx; rw [duplication_on_event x hx,hc.2.2];exact hf

/-- Consolidated mathematical witness, keyed to manuscript labels rather than numbering. -/
theorem deletion_witness_summary (h : ℕ) (hh : 2≤h) :
    Fintype.card (Original (2^h))=3*(2^h) ∧
    Fintype.card (Retained (2^h))=3*(2^h)-1 ∧
    tupleTV (((2^h : ℕ) : ℝ)/(2*(2^h : ℕ)-1))=1/(2*(2*(2^h : ℕ)-1) : ℝ) ∧
    beta (2^h : ℕ)≤deletionEventProbability h ∧
    1/16<deletionEventProbability h ∧
    ∀ v : Variant,
      saved (3*(2^h)-1) (failures (2^h) v .neg)=0 ∧
      (((2^h : ℕ) : ℝ)-1)^2/(4*(2^h : ℕ)) ≤
        deletionEventProbability h*(duplicated (3*(2^h)-1) (failures (2^h) v .neg) : ℝ) := by
  have hm := (power_parameter h hh).1
  refine ⟨(dataset_sizes _ hm).1,(dataset_sizes _ hm).2.1,
    retained_tuple_TV _ hm,(event_probability_lower h hh).1,
    (event_probability_lower h hh).2,?_⟩
  intro v
  exact ⟨(each_variant_event_counts _ hm v).2.1,(event_work_contribution h hh v).2⟩

#print axioms event_probability_lower
#print axioms initialization_word_offsets
#print axioms event_work_contribution
#print axioms finite_law_expected_work
#print axioms deletion_witness_summary
end
end Coupling
