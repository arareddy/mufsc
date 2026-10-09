# Correctness and validation receipt

**Complete pass for the fixed extension.** All 30 settings produced four distinct canonical method outputs and four timing repetitions per method: 120 distinct outputs, 90 distinct replay-versus-fresh comparisons, 480 observations. The 360 repeated replay comparisons are repeated checks, not 360 independent scientific trials. No setting failed or was excluded/retried.

Before full measurement, `preflight.py` verified 19 copied source/map/helper files against the frozen FTF-1D originals; all three processed data hashes and all three source-identity hashes; original C0 run source/input/identity bindings; 15 historical quality files and their receipts; and all 45 exact Phi/G/pooled-SSE identities. These checks required no training or new quality scoring. `QUALITY_REFERENCE_MANIFEST.json` binds their actual hashes.

Three targeted tests ran under the shared lock and passed (`HARNESS_GATE.json`):

- Twelve positive-budget replay comparisons from k in {1,3}, T in {1,2}, and Direct/Basic/Runner-up on a sparse-ID fixture. Full indexed trajectory/final bytes and exact N/S/SS matched fresh; all claimed Phase-I state matched; input arrays/groups stayed unchanged. The k=1 certificate path saved all survivor assignments without threshold fallback.
- A synthetic timer fixture checked summation over every client and round, and proved that overlapping diagnostics do not enter the additive decomposition.
- A synthetic triggering-round/later-direct counter fixture checked N/A/P/S/J, undefined P/A for no attempts, and that Direct's initial mode is not counted as threshold fallback.

All real workers checked the immutable input hash, original client mapping, ordered row-identity hashes and exact departing source rows before measuring. Fresh omits the departed dictionary key; surviving IDs remain unchanged. Checkpoints are built separately for each T on the original population and contain required T-round caches. No compact C0 API is imported or called.

Each of the four repetitions checks the complete exact model witness against fresh. This includes every indexed C0..CT and final binary64 byte, plus every integer in every N/S/SS array. No tolerance, permutation match or digest-only surrogate is used. Replay's group counts, surviving summary fields and rational-weight anchor table also equal fresh. Witnesses and N/A/P/S/J counters must agree across timing repetitions.

Each setting's fresh witness also equals the complete prior T1/T2 quality-reference witness (not only final centers). The prior source, grid, input/identity, witness and center hashes are verified, so deterministic exact quality scores can be reused on the same retained representation. Phi=max(Phi_A,Phi_B), G=Phi_A+Phi_B and pooled_SSE=n_A*Phi_A+n_B*Phi_B are checked from saved fractions. All 45 exact quality rows remain in `tables/quality_exact.csv`. No new quality-evaluation execution is claimed.

After the grid, `aggregate.py` independently reread all 480 output files, verified hashes and full witnesses, checked 120 distinct method-counter records against every repeat, confirmed balanced positions and all additive timer/request sums, and rechecked all 30 historical full-witness matches. “Independently reread” describes saved-file verification by this task; it is not an independent numerical oracle or external reviewer. Results are in `RESULTS_VERIFICATION.json`.

The final delivery verifier binds source files, run manifests, all accepted C0 file hashes, completed grid counts, exact quality identities, log lock pairs, setup accounting and PDF validation. This experiment supplies canonical-reference harness evidence, not a new proof of arithmetic kernels. Task C's earlier scoped review belongs to the compact C0 snapshot and is not represented as review of this extension.

No all-cache equality, deleted-data erasure, adaptive fresh-independent law, cold-storage/durable-service latency or deployed-network result follows from this output equality. Initialization communicates at T=0; T counts only fair-refinement rounds.
