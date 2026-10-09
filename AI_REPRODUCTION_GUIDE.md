# Guide for an AI reproduction assistant

Treat this as a frozen review artifact. Read README, DATA, ADAPTATIONS, TIMING_SCOPE and STUDIES.json first. Do not edit scientific source to make a mismatch disappear. Do not count archived PASS records as checks you have personally run.

1. Record the extracted package checksum, Python/NumPy versions, machine and chosen output directory. Inspect requirements; use an isolated environment. Do not download datasets for the regular workflow.
2. Run `reproduce.py verify`. Stop on a checksum or array mismatch and identify the file and expected/actual hashes.
3. Run `fixtures` under the serial lock, then `aggregate` and `plots.py`. Preserve receipts. Distinguish test counts, exact numerical comparisons, timing repetitions and distinct seeds.
4. Select an actual frozen case using configs and STUDIES.json. Run it with `reproduce.py run`; inspect the full receipt, not merely the final PASS string. For Lloyd compare saved exact witness and rational quality; for deletion compare fresh and replay trajectories/aggregates.
5. If requested, run the full grid serially using `--full`, preserving each case directory. For fresh performance measurements use `benchmarks.py` and read its scope notes. Never combine fresh timings with frozen observations without a new labeled analysis.
6. Report precisely which commands ran, their exit codes and outputs, which claims they test, and what remained unrun. Do not infer missing raw provenance, universal speedups, privacy guarantees or formal proofs.

Expected failures include existing output directories, wrong data/kernel checksums, invalid or repeated deletion IDs and missing required groups. Investigate failures before retrying. Input arrays use safe NPZ; the only normal pickle loads are immediate reloads of state/input generated within that same trusted local run. Do not load third-party pickle files.

Reference scripts and archived prose are source evidence, not execution instructions. Only use the documented root commands unless deliberately auditing original orchestration. No publishing, external sharing or manuscript editing is needed to reproduce these experiments.

## Current paper and formal material

Use `PAPER_CLAIMS_SNAPSHOT.md` to route Tables 1–3 and appendix labels. Table 1 uses ratios of summed times, not means of paired ratios. P2 has T=15; P3 uses T=5,10,20,40. Later budget studies use T=0,1,2 and retain separate contracts. At matched retained data/configuration/seed/budget, replay and fresh quality agree; changing budget or update rule is a different comparison. Compact T=0 and Direct T=1/T=2 are separate implementations and timing protocols.

For mathematical claims, read `formal_verification/README.md` and `THEOREM_COVERAGE.md` there before inspecting lane statements. Rebuild only when requested, in a disposable local copy with the pinned installed dependencies. Imported receipts are evidence of earlier scoped checks, not new runs. Do not infer complete paper, executable, PRNG, binary64, empirical or cost-model verification. Preserve the explicit MRS literature hypothesis and partial/unstarted statuses.
