# Reproduce the checked matched-budget subset

Pinned versions and exact dependency commits are in `requirements.json`; `lean-toolchain` pins Lean 4.19.0. The tested checker consumes the separately installed environment's `ENV_READY.json`. That private file supplies absolute `lean`, `lake`, `lean_path`, and benchmark-lock paths; it is intentionally not embedded in the shareable artifacts.

From this folder, set `FTF_LEAN_ENV` to that manifest and run, in order:

```sh
python3 build.py --env "$FTF_LEAN_ENV" --source MatchedBudget.lean --log build/lean.stdout.log
python3 build.py --env "$FTF_LEAN_ENV" --source FiniteRecords.lean --log build/records.stdout.log
python3 build.py --env "$FTF_LEAN_ENV" --source Axioms.lean --log build/axioms.stdout.log
```

The checker invokes the pinned `lean` directly with `-j1 -DwarningAsError=true -o build/<module>.olean <source>`, using the task-local build directory and shared read-only dependency paths in `LEAN_PATH`. It acquires the persistent benchmark lock in the Python parent, invokes one compiler process, and releases the lock. It records UTC times, source SHA-256, exit code, Lean version, and stdout location. Network/setup work is separate.

For a fresh environment, use the official Lean 4.19.0 release for the host architecture and the exact mathlib revision in `requirements.json`. Install that manifest's pinned dependencies and fetch the listed import roots' official mathlib cache. Only one shared environment is needed. The local setup used official cache hashing/download functions directly because unrelated ProofWidgets browser-asset download failed; theorem cache files were fetched without editing mathematical dependency sources. This alternate cache wrapper and all exact setup commands are retained privately alongside the environment.

`evidence/` is the frozen successful run. Rebuilding writes `build/` and does not overwrite that evidence. Exit zero certifies the current source only when its recorded hash matches. Do not infer current success from an older `.olean` or receipt after editing.
