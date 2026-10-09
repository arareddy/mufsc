# Formal verification: scope and reproduction

This accompanying supplementary material contains five frozen Lean proof bundles. Their proof sources, exact statements, dependency pins, compiler receipts and axiom audits are included byte-for-byte. They check mathematical models with explicit hypotheses. They do not establish complete formal verification of the paper or its executable learner, Python/PCG64/binary64 implementation, empirical measurements, or all cost models.

Start with [THEOREM_COVERAGE.md](THEOREM_COVERAGE.md), the label-based global coverage ledger. The original inspected ledger is also preserved under `approximation/THEOREM_COVERAGE.md`. Counts below include helper declarations; they are not counts of manuscript theorems.

| Included lane | Checked mathematical scope | Main boundary |
|---|---|---|
| `fair_update/` | 100 declarations: weak duality and guarded nonincrease, finite-coordinate moments and deterministic statistic-based equivalence, segment projection, weak lambda monotonicity, nondyadic counterexample | Concrete GFU candidate generation, represented arithmetic and executable correspondence remain separate |
| `lower_constructions/` | 72 matched-budget + 24 Merged-1k declarations: finite record laws, real objective optima, exact ratios, rational kappa construction and kappa=8 anchor-Lloyd caveat | Full production random-bit/representation/solver linkage remains open |
| `replay/` | 63 declarations: indexed nearest certificates, composed seeded trajectory replay, one-step compact client initializer, interval certificates under genuine enclosure premises | Deterministic algorithm interfaces and authentic-cache contracts are hypotheses; full sequential compact invariant and implementation linkage are not established |
| `coupling/` | 101 declarations: finite word assembly, rejection traces, coupling obstruction and deletion-work witness calculations | Full adaptive infinite-word execution and actual learner/work linkage remain partial |
| `approximation/` | 105 declarations: weighted finite geometry, split/merged conditional transfer, quantization, rational-copy and touched-mass calculations | MRS exact-k guarantee is an explicit literature hypothesis; full concrete sampler-to-law connection and operation models remain open |

`fair_update/` already includes the prerequisite FairUpdate and Moments sources. No earlier v1/v2 ZIP is needed. `lower_constructions/` includes both the matched and merged-one extensions. Its later `TRUST_AUDIT.md` supplements the earlier ordinary-trust report. The coupling run recorded two nonsemantic tactic-style warnings; do not describe every lane as warning-free.

## Evidence and trust

All lanes pin Lean 4.19.0 and mathlib revision `c44e0c8ee63ca166450922a373c7409c5d26b00b`. Supplied trust-level-zero, single-worker receipts and axiom reports state only the standard logical axioms `propext`, `Classical.choice`, and `Quot.sound`. Inspect each lane's exact statements and receipts for its scope. Packaging checked archive hashes, every supplied manifest, member CRCs, source preservation and anonymity; it did not recompile proofs. Historical intermediate attempts remain distinguishable from final checks.

`BUNDLE_INTAKE.json` records the five source archive identities. Each lane retains its original manifest and original bytes. The root supplement manifest additionally covers every imported file, including nested manifests.

## Rebuilding from a fresh extracted copy

Use a local nonsynced copy on a POSIX system with Python 3, Git, Lean 4.19.0 and the pinned **already compiled** mathlib and transitive libraries. These dependencies are not bundled. Provisioning them may require network access; the scripts below do not download or install them. Run one lane at a time and use one common lock. Build in a disposable copy to preserve supplied logs and manifests. The placeholders below refer to the reviewer's own installation, not a private author environment.

From `formal_verification/`, first create a portable environment descriptor using the included inspector:

```sh
python3 coupling/configure.py --lean /path/to/lean-4.19.0/bin/lean --mathlib /path/to/mathlib --env /tmp/ftf-review-env.json --lock /tmp/ftf-review.lock
```

This descriptor has the `lean`, `lean_version`, `lean_path`, `mathlib`, `mathlib_revision` and `benchmark_lock` fields used by the lanes. No author `ENV_READY.json` is needed. Then use the following commands from `formal_verification/` (each script resolves its own source directory):

```sh
python3 fair_update/build.py --lean /path/to/lean-4.19.0/bin/lean --mathlib /path/to/mathlib --lock /tmp/ftf-review.lock --label reproduction --kernel
python3 lower_constructions/build_trust0.py --env /tmp/ftf-review-env.json --source MatchedBudget.lean --log build_trust0/MatchedBudget.log
python3 lower_constructions/build_trust0.py --env /tmp/ftf-review-env.json --source FiniteRecords.lean --log build_trust0/FiniteRecords.log
python3 lower_constructions/build_trust0.py --env /tmp/ftf-review-env.json --source MergedOne.lean --log build_trust0/MergedOne.log
python3 lower_constructions/build_trust0.py --env /tmp/ftf-review-env.json --source Axioms.lean --log build_trust0/Axioms.log
python3 lower_constructions/build_trust0.py --env /tmp/ftf-review-env.json --source MergedOneAxioms.lean --log build_trust0/MergedOneAxioms.log
python3 replay/verify.py --env /tmp/ftf-review-env.json
python3 coupling/verify.py --env /tmp/ftf-review-env.json
python3 approximation/check_all.py --env /tmp/ftf-review-env.json --tag reproduction
```

These are optional formal rebuilds, separate from experimental `reproduce.py`. Preserve fresh return codes and source hashes; do not count supplied receipts as runs you performed. Read each lane's README/BUILD/SCOPE documents before interpreting results. The packager inspected command interfaces but did not execute these compiler commands.
