# Exact replay and assignment certificates: Lean source bundle

This anonymous source bundle proves mathematical-model results for finite assignment certificates and seeded exact replay. It does **not** verify the research implementation, its experiments, or the entire manuscript.

The principal results are `Replay.seeded_basic_exactness` and `Replay.seeded_runner_exactness`. They compose proved keyed initialization, finite exact nearest-label selection, certificate soundness, exact additive patching and finite-round induction. They conclude equality of the complete indexed center trajectory, including its initial and final states. They do not assume that round outputs are equal.

The bundle also covers the whole-client summary-only initialization result, radii/exact-norm tightness witnesses, the top-three exclusion optimization, outward interval certificate logic, and the algebraic/counting parts of conditional local stability. See `COVERAGE.md` for exact scope and `STATEMENTS.txt` for compiler-printed theorem types. The readable and authoritative definitions and statements are in `proof/`.

## Verification

Pins: Lean **4.19.0**, compiler commit **6caaee842e94**, mathlib **c44e0c8ee63ca166450922a373c7409c5d26b00b**. `DEPENDENCIES.json` records transitive source pins. Python 3 and a Unix system with `fcntl` are required by the verification wrapper. Proof sources are platform independent; the recorded run used the pinned macOS ARM64 compiler.

Reuse an existing matching environment:

```sh
python3 verify.py --env /path/to/ENV_READY.json
```

The descriptor supplies `lean`, `lean_path`, `mathlib`, and optionally `benchmark_lock`. Alternatively supply `--lean`, `--lean-path`, and `--mathlib` explicitly. The mathlib argument identifies its Git checkout, whose revision is checked.

For a separate reviewer environment, the supplied `lean-toolchain` and `lakefile.toml` pin the required dependencies. After provisioning those dependencies and their compiled artifacts, run:

```sh
lake env python3 verify.py --mathlib .lake/packages/mathlib
```

The wrapper never installs or downloads anything. Every proof module is compiled sequentially with `lean -j1 -t0 -DwarningAsError=true`, using a shared exclusive file lock for each short compilation. It verifies the Lean and mathlib pins, then prints and audits the axioms of every theorem declaration. Only `propext`, `Classical.choice`, and `Quot.sound` are permitted; some theorems use fewer. No domain-specific axioms or proof escapes are admitted. The wrapper places fresh receipts and outputs under `build/`.

`evidence/` contains the successful original receipts, complete axiom output and audit, and compiler outputs. Their SHA-256 values are in `MANIFEST.json`. Archived development failure logs are retained privately outside this anonymous bundle. No research data, checkpoints, compiler environment, duplicated mathlib, or binary proof outputs are included.

## Interpretation

The local sampler, server procedure, stream factory and center update are explicit deterministic function parameters. Key namespaces, canonical anchor list construction, retained integer group counts, rational normalization, exact nearest selection, integer statistics and replay control flow are defined in Lean. The actual PCG64/SeedSequence program, floating-point enclosure production, exact comparison code and source-code linkage remain unverified. Correct cache contents and slice-input correspondence are mathematical input contracts.

The event-law lemma formalizes equality under the **same** randomized seed map. Fixed or seed-independent deletion can use it to obtain the manuscript's distributional corollary. It provides no independent fresh-seed guarantee after adaptive checkpoint-dependent deletion, and no checkpoint erasure or full stored-state equality claim.

The manuscript was concurrently edited for presentation. `PAPER_PROVENANCE.json` preserves initial observations and the separately reviewed source hashes. Mapping uses stable LaTeX labels, not theorem numbers. It is scoped to those recorded snapshots and is not a claim about future edits.
