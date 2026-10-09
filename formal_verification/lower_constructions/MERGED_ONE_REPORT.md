# Merged-1k lower construction — checked extension

**Status:** all 24 exported declarations in `MergedOne.lean` compiled cleanly with Lean 4.19.0 and warnings as errors. The same source also passed a separate `-t0 -j1` check. The source hash is `42dd0ec85ef742b3b13852169898513835fa4e3048760bba3577e49117dbc267`. Actual build receipts, stdout and all `#print axioms` output are in `evidence_merged_one/` and `evidence_trust0/`.

**Manuscript coverage:** the lower half of `thm:kappa`, its construction in `app:kappa-proof`, the ownership definition `eq:kappa`, and the stated κ=8 one-step anchor-Lloyd caveat. This extension does not claim the theorem's upper half, `eq:merged-root`, or `eq:merged-zero`.

The earlier matched-slot source, receipts and `frozen/matched_budget_checked_20260926.zip` remain unchanged. `MergedOne.lean` imports the checked finite-record infrastructure but changes the geometry: both client-0 B blocks are at the same positive coordinate L, and each client sends one anchor. It does not substitute Merged-2k for Merged-1k.

## Exact definitions and conclusions

`Record u v` supplies distinct tagged finite identities. Client 0 has 2u A records at 0 and 2v B records at L; client 1 has 2v A and 2u B records at 0. The imported cardinality and rational-realizability proofs give equal client/global-group sizes N=2(u+v), ε=v/(u+v), and κ=u/v for every rational κ≥1. Ownership is geometry-independent; `declared_ownership_parameter` also checks the outer maximum with one in `eq:kappa`.

`firstProb` sums locally balanced weights over actual client-0 records and normalizes. `local_first_law` derives probability 1/2 for each site. `anchorWeight` divides the whole-client integer group counts by the global group size; `anchor_weight_one` proves both weights are one. `serverProb` is the normalized categorical distribution on the two ordered anchors. `outputLaw` composes these finite conditional laws. `output_law` derives probabilities 3/4 at 0 and 1/4 at L; normalization and nonnegativity are checked.

`recordCostA` and `recordCostB` are real-valued finite-record group averages. `record_group_costs` proves their agreement with c² and c²−2εLc+εL². `record_optima` proves attained global minima for **all real centers**, not only rational centers:

- G*=ε(1−ε/2)L², attained at εL/2.
- Φ*=ε(1−ε)L², attained at εL for 0≤ε≤1/2.

`positive_optima` justifies division when 0<ε≤1/2 and L>0. Expectations are computed from the record-derived output law, yielding EG=(1+ε)L²/2 and EΦ=(1+3ε)L²/4. `exact_ratios` proves the exact fractions. `finite_record_lower_bounds` then proves EG/G*≥κ/2 and EΦ/Φ*≥κ/4 using the actual finite-record objectives. `rational_kappa_lower_construction` constructs finite counts for every rational κ≥1 and any real L>0, with the correct cardinalities and ownership ratio.

`lloydCenter` is the exact weighted centroid of the two retained anchors. `lloyd_center` proves it equals 0 or L/2 depending on the local first site. `lloydExpectation` uses that actual first-selection law. `lloyd_caveat_kappa_eight` proves, at u=8,v=1,L=1, ratios 99/34 and 117/64 and proves they are below 8/2 and 8/4. Thus the paper's refinement limitation is checked as a finite mathematical counterexample.

## Hypotheses and remaining implementation boundary

Finite-record theorems require natural u≥v>0; the existence theorem requires rational κ≥1. Real objective lemmas state their ε interval explicitly. Ratio and lower-bound theorems require L>0. No theorem assumes a desired sampling probability, objective formula, optimum, or approximation inequality as a premise.

The model is exact arithmetic, d=k=1, one local representative per client, γ=0 and no anchor refinement for the lower-bound result. The separate Lloyd caveat covers one exact weighted centroid update only. The source does not implement the production random-bit/PCG64 interfaces, binary64/grid encoding, clipping, or preprocessing. The geometric theorem is stated for all real L>0; choosing L=1 gives the intended exactly representable witness mathematically, while correspondence with the production representation is an explicit unformalized bridge. No equality of finite seed frequencies with ideal probabilities is claimed.

There is no post-fair-refinement lower-bound claim. No upper-bound or external k-means++ theorem is assumed or verified here. This is a checked finite mathematical lower construction, not a proof of the whole declared training program or the whole paper.

## Axioms and reproduction

All 24 `MergedOne` results report only `propext`, `Classical.choice` and `Quot.sound`. The source has no `sorry`, `admit`, added axioms, `native_decide`, unsafe proof escapes or native oracle shortcuts. Standard proof-producing tactics were used. The ordinary check finished at 09:50:05 UTC and the trust-level-zero check at 09:51:02 UTC on 26 September 2026. The source was read after generation.

Use the pinned shared environment described in `BUILD.md`; it needs no dependencies beyond those already used by the matched proof. After building `MatchedBudget.lean` and `FiniteRecords.lean`, run:

```sh
python3 build.py --env "$FTF_LEAN_ENV" --source MergedOne.lean --log build/merged_one.stdout.log
python3 build.py --env "$FTF_LEAN_ENV" --source MergedOneAxioms.lean --log build/merged_one_axioms.stdout.log
python3 build_trust0.py --env "$FTF_LEAN_ENV" --source MergedOne.lean --log build_trust0/merged_one.stdout.log
```

The final command adds `-t0` to the one-worker direct Lean invocation and keeps its output separate. All compiler calls use the shared parent-held benchmark lock and release it between batches. Private absolute paths remain outside the shareable folder.
