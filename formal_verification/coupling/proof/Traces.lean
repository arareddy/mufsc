import Rejection
namespace Coupling
noncomputable section
open scoped BigOperators

def runProposals (m : ℕ) : List ℕ → Option ℕ
  | [] => none
  | u::rest => match newProposal m u with
    | some c => some c
    | none => runProposals m rest

/-- A successful minimal trace consists of r copies of the unique reject, then an accept. -/
def acceptedTrace (m r u : ℕ) : List ℕ := List.replicate r (2*m-1) ++ [u]
def category (m u : ℕ) : ℕ := if u<m then 0 else 1

theorem trace_runs (m r u : ℕ) (hu : u<2*m-1) :
    runProposals m (acceptedTrace m r u) = some (category m u) := by
  induction r with
  | zero => simp [acceptedTrace,runProposals,newProposal,category,hu]
  | succ r ih =>
    simpa [acceptedTrace,List.replicate_succ,runProposals,newProposal] using ih

theorem trace_length (m r u : ℕ) : (acceptedTrace m r u).length = r+1 := by
  simp [acceptedTrace]

/-- Uniform independent proposals assign a length-L fixed cylinder weight (1/(2m))^L. -/
def cylinderWeight (m : ℕ) (xs : List ℕ) : ℝ := (1/(2*(m : ℝ)))^xs.length

theorem trace_weight_from_cylinder (m r u : ℕ) :
    cylinderWeight m (acceptedTrace m r u) = traceWeight m r := by
  rw [cylinderWeight,trace_length,traceWeight]

/-- The old call consumes only the low bit of the first block. -/
def traceOldCategory (m r u : ℕ) : ℕ := oldCategory ((acceptedTrace m r u).headD 0)

theorem old_trace_zero (m u : ℕ) : traceOldCategory m 0 u = u%2 := by
  simp [traceOldCategory,acceptedTrace,oldCategory]

theorem old_trace_after_reject (m r u : ℕ) (hm : 0<m) :
    traceOldCategory m (r+1) u = 1 := by
  simp only [traceOldCategory,acceptedTrace,List.replicate_succ,List.cons_append,List.headD_cons,oldCategory]
  omega

def traceMismatchCount (m r : ℕ) : ℕ :=
  ∑ u ∈ Finset.range (2*m-1), if traceOldCategory m r u ≠ category m u then 1 else 0

theorem accepted_count_without_reject (t : ℕ) (ht : 0<t) :
    (∑ u ∈ Finset.range (2*(2*t)-1), acceptedMismatch (2*t) u) = 2*t := by
  have h := accepted_mismatch_count t
  have he : 2*(2*t) = (2*(2*t)-1)+1 := by omega
  rw [he,Finset.sum_range_succ] at h
  have hz : acceptedMismatch (2*t) (2*(2*t)-1) = 0 := by
    have hp : (2*(2*t)-1)%2=1 := by omega
    simp [acceptedMismatch,hp,show ¬2*(2*t)-1<2*t by omega]
  simpa only [hz,Nat.add_zero] using h

theorem trace_mismatch_count (t r : ℕ) (ht : 0<t) : traceMismatchCount (2*t) r = 2*t := by
  cases r with
  | zero =>
    unfold traceMismatchCount
    conv_rhs => rw [← accepted_count_without_reject t ht]
    apply Finset.sum_congr rfl
    intro u hu
    have hu' := Finset.mem_range.mp hu
    rw [old_trace_zero]
    unfold category acceptedMismatch
    have hp := Nat.mod_lt u (by omega : 0<2)
    split_ifs <;> omega
  | succ r =>
    unfold traceMismatchCount
    have he : (∑ u ∈ Finset.range (2*(2*t)-1),
        if traceOldCategory (2*t) (r+1) u ≠ category (2*t) u then 1 else 0 : ℕ) =
        ∑ u ∈ Finset.range (2*(2*t)-1), if u<2*t then 1 else 0 := by
      apply Finset.sum_congr rfl
      intro u _
      rw [old_trace_after_reject (2*t) r u (by omega)]
      unfold category
      split_ifs <;> norm_num at *
    rw [he,first_category_count (2*t) (by omega)]

/-- Exact joint-disagreement law summed directly over all minimal successful traces. -/
def traceDisagreementLaw (m : ℕ) : ℝ := ∑' r : ℕ, (traceMismatchCount m r : ℝ)*traceWeight m r

theorem trace_disagreement_exact (t : ℕ) (ht : 0<t) :
    traceDisagreementLaw (2*t) = (2*t : ℕ)/(2*(2*t : ℕ)-1 : ℝ) := by
  unfold traceDisagreementLaw
  simp_rw [trace_mismatch_count t _ ht]
  exact (accepted_trace_sum (2*t) (by omega) (2*t : ℕ)).tsum_eq

/-- Agreement of the trace enumeration and the accepted-first plus continuation decomposition. -/
theorem trace_and_decomposition_agree (t : ℕ) (ht : 0<t) :
    traceDisagreementLaw (2*t) = coupledDisagreement (2*t) := by
  rw [trace_disagreement_exact t ht,exact_coupling_disagreement t ht]

/-- Every successful finite execution has one of the counted minimal prefixes. -/
theorem successful_prefix_classification (m : ℕ) (hm : 0<m)
    (xs : List ℕ) (valid : ∀ u∈xs, u<2*m) (c : ℕ)
    (hs : runProposals m xs = some c) :
    ∃ r u rest, xs = List.replicate r (2*m-1) ++ u::rest ∧
      u<2*m-1 ∧ category m u=c := by
  induction xs with
  | nil => simp [runProposals] at hs
  | cons u xs ih =>
    have hu : u<2*m := valid u (by simp)
    by_cases ha : u<2*m-1
    · refine ⟨0,u,xs,by simp,ha,?_⟩
      simpa [runProposals,newProposal,ha,category] using hs
    · have he : u=2*m-1 := by omega
      have ht : runProposals m xs = some c := by
        simpa [runProposals,newProposal,ha] using hs
      obtain ⟨r,v,rest,hxs,hv,hc⟩ := ih (fun v hv => valid v (by simp [hv])) ht
      refine ⟨r+1,v,rest,?_,hv,hc⟩
      simp [List.replicate_succ,he,hxs]

def traceOldFirstCount (m r : ℕ) : ℕ :=
  ∑ u ∈ Finset.range (2*m-1), if traceOldCategory m r u=0 then 1 else 0

theorem old_first_trace_count (m r : ℕ) (hm : 0<m) :
    traceOldFirstCount m r = if r=0 then m else 0 := by
  cases r with
  | zero =>
    simp only [traceOldFirstCount,old_trace_zero,if_true]
    have h := count_even m
    have he : 2*m=(2*m-1)+1 := by omega
    rw [he,Finset.sum_range_succ] at h
    have hp : (2*m-1)%2=1 := by omega
    simpa [hp] using h
  | succ r =>
    simp only [traceOldFirstCount,old_trace_after_reject m r _ hm]
    simp

def traceOldFirstLaw (m : ℕ) : ℝ := ∑' r : ℕ, (traceOldFirstCount m r : ℝ)*traceWeight m r

theorem old_trace_marginal_half (m : ℕ) (hm : 0<m) : traceOldFirstLaw m=1/2 := by
  unfold traceOldFirstLaw
  simp_rw [old_first_trace_count m _ hm]
  have he : (∑' r : ℕ, ((if r=0 then m else 0 : ℕ) : ℝ)*traceWeight m r) = (m : ℝ)*traceWeight m 0 := by
    rw [tsum_eq_single 0]
    · simp
    · intro r hr
      simp [hr]
  rw [he]
  have hmR : (m : ℝ) ≠ 0 := by exact_mod_cast (Nat.ne_of_gt hm)
  simp only [traceWeight,pow_one,Nat.zero_add]
  field_simp
  ring

/-- Both marginals and the joint disagreement come from the same successful-trace representation. -/
theorem trace_binary_total_variation (m : ℕ) (hm : 1≤m) :
    binaryTV (traceOldFirstLaw m) (categoryLaw m m) = 1/(2*(2*(m : ℝ)-1)) := by
  rw [old_trace_marginal_half m (by omega)]
  exact binary_total_variation m hm

#print axioms old_first_trace_count
#print axioms old_trace_marginal_half
#print axioms trace_binary_total_variation
#print axioms successful_prefix_classification
#print axioms trace_runs
#print axioms trace_weight_from_cylinder
#print axioms trace_mismatch_count
#print axioms trace_disagreement_exact
#print axioms trace_and_decomposition_agree
end
end Coupling
