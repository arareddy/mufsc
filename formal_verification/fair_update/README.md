# Final bounded geometry extension

20 new checked lemmas covering the three remaining requested claims: segment projection, ideal lambda-curve monotonicity, and the non-dyadic nature of 5/9. The bundle includes byte-identical FairUpdate and Moments prerequisites (80 lemmas). Earlier v1/v2 sources, logs, manifests, and ZIPs remain unchanged.

See REPORT.md, COVERAGE.md, VERIFIED_THEOREMS.md and the exact logs. Rebuild offline against the pinned existing Lean/mathlib environment:

```sh
python3 build.py --lean /path/to/lean-4.19.0/bin/lean \
  --mathlib /path/to/mathlib --lock /path/to/shared.lock \
  --label reproduction --kernel
```

The script compiles FairUpdate, Moments and Geometry with `--trust=0 -j1`, then imports Geometry for every theorem's type/axiom audit. LEAN_PATH includes its local build output plus the existing pinned library/package directories. The Python parent holds an exclusive advisory lock per compiler command, releases between commands, uses one worker, never unlinks the lock, and performs no installation/download. Each command has a 300-second timeout; a lock busy for 30 seconds causes exit 75.

The portable payload excludes machine-specific invocation paths, generated .olean files, toolchains, datasets, manuscript text, and external sharing. Hash/label-only input provenance is included. Local storage requires a separately chosen backup.
