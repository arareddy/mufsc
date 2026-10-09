# Frozen saved-evidence protocol

Frozen before derived analysis and figure production, 26 September 2026. This is a bounded first pass; no new learning, timing measurements, case selection, tuning, downloads, archive restoration, manuscript edits, or positive-refinement-task inputs.

## Cases and inputs

A: corrected record-deletion run `round-budget-20260926T064431Z`; Adult/Bank/Credit, seeds 10000..10004, T=0,1,2 refinement rounds, k=10. Exactly 45 scientific quality rows; verify all four saved gate methods (180 outputs) and their exact quality/model equality, then count Fresh once. Independent saved requests remove 30/45/30 records; counts may vary by seed. Use CURRENT reports, never superseded reporting files.

B: completed whole-client run `client-c0-20260926-v1`; the same three datasets and five seeds, selected client 0, T=0,1,2 fresh quality references. Exactly 45 scientific quality rows in 15 saved quality.json files. Verify same-population T0 core linkage, frozen grid, registry, completion receipts and source bindings. No positive-T unlearning result is inferred.

Populations stay separate even where source processed files coincide. Expected 90 quality rows, 180 group rows, 90 paired case transitions (0->1,1->2,0->2 across 30 dataset/seed/population cases). No outcome exclusions; failures stop dependent analysis and remain in receipts. Both groups must have positive counts.

`freeze.py` records exact input paths, SHA256, sizes and mtimes in INPUT_MANIFEST.json and captures only small contextual source snapshots, including live manuscript context. The live manuscript may change in another task: those snapshots document reading time and are never restored. Execution checks all frozen input hashes. Original artifacts remain read-only. Input pickle files are streamed for hash verification only; no datasets or checkpoints are copied or unpickled and no quality is rescored from raw coordinates.

## Definitions and aggregation

Each saved fraction is read as an integer numerator/positive denominator. For each seed and budget check Phi=max(Phi_0,Phi_1) and G=Phi_0+Phi_1 EXACTLY. Compute pooled SSE=n_0 Phi_0+n_1 Phi_1 and population-average cost=SSE/(n_0+n_1). Verify B's saved SSE. A counts come from the same retained T1/T2 exact N statistics, cross-checked against retained total and original counts; T0 uses that same retained population. Identity mapping is checked independently from the saved original metadata and request records; no new raw preprocessing-provenance claim.

Summaries take the arithmetic mean across five seeds of each case-level metric, with sample SD (n-1), min and max. The plotted mean worst-group cost is mean_s[max_g Phi_sg], never max_g[mean_s Phi_sg]; save both and their exact difference to expose group switching. Exact means and variances are retained; square roots and display decimals are derived only after exact arithmetic.

Paired changes are value(T_to)-value(T_from) within dataset/seed/population for all three transitions. Negative is a decrease. Relative decrease=(before-after)/before; a zero denominator produces an empty numeric value plus explicit undefined status. Save exact fractions and signed changes for individual groups, Phi, G, population mean and SSE. Descriptive group gap=abs(Phi_0-Phi_1); optional ratio=max/min, undefined if min=0. These are descriptive statistics, not new fairness definitions or equalization guarantees. Count each transition with any group increase despite strict Phi decrease, preserve every identity and magnitude, and also report distinct seed cases to avoid overlapping-transition inflation. Five seeds are the units; timing repetitions never enter quality sample size or inference. No confidence intervals or significance claims.

## Figures and boundaries

Two compact vector PDFs, one per population. Columns are datasets, upper panels individual group costs, lower panels case-level worst-group and population-average cost. Separate axes by dataset; all cost axes use squared-distance per record, with nonzero origins clearly visible. Show all five paired seed trajectories plus mean and one sample SD; x-axis T=0,1,2 REFINEMENT ROUNDS. Group definitions follow frozen mask semantics: Adult group0=complement of male mask, group1=male; Bank group0=not married, group1=married; Credit group0=other education codes, group1=EDUCATION in {1,2}. Preserve Adult/Credit upstream provenance caveats. No ordinary-k-means advantage without a matched ordinary baseline.

Ghadiri Section4/Figures5,9 motivate showing group means and distinguishing population from worst-group objectives; its numbers, trial counts and convergence are not targets. Briefly inspect current P4 protocol, saved metadata and centralized source for ordinary-Lloyd comparison. If absent, document an optional future matched-start Lloyd/fair-update experiment and stop; no P4 rerun or obsolete runtime import.

All substantial hash/analysis/render work runs as one worker with five numerical thread environment limits=1, while its parent holds exclusive fcntl.flock on /private/tmp/ftf_benchmark_20260926.lock. The lockfile is never unlinked; release between freeze, analysis and rendering batches. Record queue/acquire/release UTC, load averages and top CPU process snapshots. No timing ratios are measured, so balanced timing order is not applicable here. The lock does not suppress unrelated desktop load. Preserve failed attempts and resumable batch receipts.

## Deliverables and claim boundaries

REPORT.md; this protocol and immutable hash receipt; verification/lock receipts; exact and descriptive CSVs; plotting and reproduction commands; two visually inspected PDFs; input/output manifests; INTEGRATION_NOTES.md with main-text/appendix caption proposals. Algebraic identities, tested saved-evidence checks, inherited conditional theory and unresolved questions are separate. No optimality, internal-cache equality, erasure, adaptive distributional guarantee or application adequacy is inferred from same-seed model equality. No publication or integration. Local-only outputs need a separately chosen backup.
