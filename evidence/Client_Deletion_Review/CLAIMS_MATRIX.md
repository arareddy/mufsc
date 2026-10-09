# Claims matrix

Status is scientific scope, not a human endorsement. Proofs and finite tests are kept separate. Task B snapshot-specific findings belong in IMPLEMENTATION_REVIEW.md / REVIEW_READY.json.

| Claim | Status | Basis and limit |
| --- | --- | --- |
| Dropping whole-client summaries, exact current counts and fresh server replay returns the frozen learner's indexed C0 | PROVED, conditional on stated map assumptions | THEORY_REVIEW section 3; initializer specialization of existing replay theorem |
| Surviving local summaries, group counts and canonical table equal fresh mathematical counterparts | PROVED | Same local inputs/keys; exact count sums; no full-cache equality |
| Fixed-request distributional equality over the same seed law | PROVED COROLLARY | Pointwise equality; independent-seed/adaptive claim excluded |
| All tested whole-client configurations match frozen fresh T=0 | TESTED | 196 valid tiny cases, 14 configurations; results/fixtures_initial.json; no proof by testing |
| Gaps, repeated locations, zero mass, saturation, quantization and optional anchor Lloyd handled on tiny inputs | TESTED | Independent scalar geometry/arithmetic; NumPy RNG primitive shared |
| Invalid/empty-group requests rejected by conceptual oracle and selected frozen record API tests | TESTED | 28 empty subsets, 9 invalid oracle client requests, 8 invalid record requests; does not certify candidate API |
| Persistent-ID renumbering or row reordering preserves the same-seed map | FALSE IN GENERAL | Explicit finite seed-0 counterexamples |
| Global fair normalization always forces scanning surviving raw data | FALSE | Exact per-client/group counts and local summaries suffice at T=0 |
| A uniform exact global scaling within a separated local slice changes its canonical sampler | FALSE | Common factor cancels from canonical integer masses; unequal mixed-group factors can change it |
| Old weights/server centers can always be kept after whole-client deletion | FALSE | Retained first-draw probabilities 1/2 vs stale 1/3 |
| Whole global group deletion is valid for the same binary fair objective | FALSE | n'_g=0 makes objective/weights undefined; map rejects |
| Deleting unselected records permits keeping every local summary field | FALSE | Multiplicity changes even when representatives survive |
| Naive ideal prefix repair equals the current indexed saturation map | FALSE | Fresh (0,1) deterministically vs repaired (1,0) probability 1/3 |
| Whole restart only on seed-hit preserves ideal local law | FALSE | Unordered {0,1}: 7/30 fresh vs 257/1260 on four-point example |
| Ordinary ideal prefix repair matches fresh on the four-point positive-potential example | EXACTLY ENUMERATED | Full ordered law agrees; no universal finite-PCG64 proof implied |
| Pan's whole-client drop-and-server-retrain architecture is a relevant precedent | PRIMARY-SOURCE VERIFIED | Section 5.3 and Algorithm 4; fixed group normalization/indexed contract supplied here |
| Pan's locally sampled weights are our MERGED-1K demographic weights | FALSE ATTRIBUTION | Original ordinary initialization; locally balanced merged learner is our adaptation |
| Pan's 84x predicts 10x for matched T=0 FTF | UNRESOLVED / NOT IMPLIED | Different learner, timing boundary and baseline; no reproduced Pan run |
| Compact T=0 request may avoid raw-data access | PROVED POSSIBILITY; IMPLEMENTATION-SPECIFIC | Only counts and compact anchors needed; validate actual boundary separately |
| 10x gain against matched fresh T=0 | CONDITIONAL, UNMEASURED HERE | F>=10U; include server, cache, data access, setup amortization and output |
| T=0 quality is acceptable relative to original T | UNRESOLVED HERE | Same-map equality does not certify cross-map utility |
| T>0 can use only the initialization summaries at no further raw-data cost | NOT ESTABLISHED | New assignments/statistics generally required |
| Candidate v1 matches the independent scalar oracle | TESTED / SCOPED PASS | 196 valid cases, 28 invalid empty subsets; exact snapshot in IMPLEMENTATION_REVIEW.md |
| Candidate compact-state invariant over valid whole-client sequences | PROVED BY INDUCTION + TESTED | 84 sequential steps; trusted unchanged state, original keys; not original full replay cache or erasure |
| Candidate compaction and resident request avoid raw-data access | SOURCE-REVIEWED + TESTED | Access traps, no local training/encoding, equal 510-byte output through actual wrapper |
| Full original cache/state erasure, original API fresh-cache service, adaptive fresh-independent guarantee | OUT OF SCOPE | No such service implemented or tested |
