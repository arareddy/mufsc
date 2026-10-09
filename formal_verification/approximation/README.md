# Finite approximation proof supplement

This anonymous source supplement checks the original weighted geometry, finite probability transfer, and exact constants behind `thm:warmstart` and the upper half of `thm:kappa`. The k-means++ approximation theorem is a **named literature premise**, not a new Lean axiom and not re-proved here.

All 14 proof modules and one exhaustive audit pass Lean 4.19.0 with `--trust=0 -j1` and warnings as errors. There are 105 theorem/helper declarations, not 105 manuscript theorems. Their only reported logical axioms are `propext`, `Classical.choice`, and `Quot.sound`. The Lean sources use no `sorry`, `admit`, domain-specific axioms, `native_decide`, or unsafe escape.

Start with `REPORT.md` and `SCOPE.md`. `STATEMENTS.txt` contains the exact elaborated types; `proof/Audit.lean` recreates those types and their axiom reports. `THEOREM_COVERAGE.md` is the complete labelled/unnumbered manuscript inventory, including inspected separate proof bundles and explicit remaining obligations.

## Reproduce

Use an existing environment with the exact Lean and mathlib revisions in `DEPENDENCIES.json`. No mathlib, toolchain, dataset, environment, compiled object, or manuscript copy is packaged here.

```sh
python3 make_env.py --lean /path/to/lean-4.19.0/bin/lean --mathlib /path/to/mathlib --output /tmp/ftf-approx-env.json
python3 check_all.py --env /tmp/ftf-approx-env.json
```

`make_env.py` only inspects supplied installations; it installs or downloads nothing. Mathlib and its pinned dependencies must already have the imported compiled modules available. The tested environment uses official pinned release/cache artifacts; it does not bootstrap or prove the compiler itself. A shared setup owner can supply `ENV_READY.json` directly instead of running `make_env.py`.

Each compilation takes an exclusive parent-held flock, runs one worker, and releases the lock between modules. The default lock is `/private/tmp/ftf_benchmark_20260926.lock`; use the same lock when sharing the environment. The build runner waits at most 20 seconds to acquire it without holding it, then exits 75 for a later retry. A compilation is capped at 90 seconds. Compilation produces local `build/` and private exact invocations/logs; supplied final portable receipts are in `COMPILER_RECEIPTS.json` and `logs/`.

## Boundaries

The proved models contain finite records, actual nearest-center metric costs, explicit normalized finite laws and conditional products. They are not arbitrary expected-cost scalar placeholders. The full ideal-bit sampler-to-finite-law refinement, complete concrete D² state-machine instantiation of all named literature calls, and executable Python/binary64 linkage remain open. Empirical measurements are not verified. All reference-center results hold for arbitrary reference tuples; selecting the manuscript's optimum requires its intended minimizer interpretation, not a newly assumed transfer inequality.

Only small source/evidence artifacts are included. Everything was kept outside synced storage; no archive/dataset restoration, experiment rerun, manuscript edit or publication occurred. Local storage requires a separately chosen backup.
