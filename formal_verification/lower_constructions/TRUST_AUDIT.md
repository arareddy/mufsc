# Additional trust-level-zero audit

After the original matched bundle was frozen, the unchanged `MatchedBudget.lean`, `FiniteRecords.lean`, and final `MergedOne.lean` each passed a separate Lean 4.19.0 check with `-t0 -j1 -DwarningAsError=true`. Actual source-matched receipts and full stdout are in `evidence_trust0/`. No proof source was altered for this audit. The original `REPORT.md` describes its earlier ordinary-import-trust gate; this later audit supplements it.

`build_trust0.py` reproduces these calls and records the trust level explicitly. It uses the same pinned toolchain and shared dependency paths, one compiler worker, and a parent-held benchmark lock released between modules. No claim is made that the Lean compiler binary itself was rebuilt or independently verified.

Across the two source families, all 96 exported theorem declarations were inspected with `#print axioms`. The only reported axioms are `propext`, `Classical.choice`, and `Quot.sound`. No domain axioms, placeholder proofs or native proof-oracle dependencies occur. The axiom inspection sources and their actual output are retained.
