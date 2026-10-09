# Sampler coupling and deletion-work formalization

Anonymous, portable Lean source supplement for manuscript labels `lem:s2-word-coupling` and `prop:s2-deletion-work`.

The bundle proves 101 named theorems in an explicit finite-word, rejection-trace, and finite-record mathematical model. It does **not** claim a complete verification of the executable FTF-1 sampler or the full manuscript proposition. Read `COVERAGE.md` for the remaining stream, initialization, and numerical-interface obligations.

## Reproduce

Use an existing Lean 4.19.0 / mathlib installation at the exact pins in `DEPENDENCIES.json`. No tool downloads or duplicates mathlib.

```sh
python3 configure.py --lean /path/to/lean-4.19.0/bin/lean --mathlib /path/to/mathlib --env /tmp/coupling-env.json
python3 verify.py --env /tmp/coupling-env.json
```

If an environment descriptor already exists, only the second command is needed. The descriptor includes the Lean executable, import paths, version, mathlib revision, and a shared advisory-lock path. `build.py` holds that lock in its parent process only during each Lean invocation, uses `-j1 --trust=0`, and releases it after the child exits. It does not acquire a lock for downloads or other network work. The lock file is never unlinked.

The 12 compilation units (11 proof modules and the exhaustive axiom audit) are compiled sequentially. `verify.py` fails on a compiler error, proof placeholders, prohibited source constructs, missing audit entries, or any axiom outside `propext`, `Classical.choice`, and `Quot.sound`. These are Lean's standard logical foundations, not domain-specific axioms. `#check` and `#print axioms` output for every theorem is in `logs/final_AxiomAudit.log`.

## Files

- `proof/`: readable Lean source and full axiom audit.
- `COVERAGE.md`: statement mapping, scope, dependencies, and remaining obligations.
- `THEOREM_INDEX.json`: every theorem and source module.
- `PAPER_INPUTS.json` and `PAPER_INPUTS_AT_FINISH.json`: initial and later saved manuscript hashes, including concurrent editorial changes, without identifying machine paths.
- `DEPENDENCIES.json`: exact Lean, mathlib, and package pins.
- `logs/final_*.json` and `.log`: fresh compiler receipts and outputs.
- `AXIOM_AUDIT.json`: exhaustive audit summary.
- `MANIFEST.json`: portable-package file hashes.

The original development failures and full local invocation context remain private in the development workspace and are not included in the anonymous bundle. Their errors have not been edited into successes. No experiments, sampling tests, manuscript edits, uploads, or publication were performed. Build artifacts and the shared mathlib installation are intentionally omitted.
