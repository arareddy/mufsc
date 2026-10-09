# Geometry extension report

**SCOPED PASS: all three requested claims checked.** The separate extension adds 20 lemmas, with 100 audited declarations including 80 unchanged prerequisite lemmas. These counts include helpers. Three source compiles and the imported-module type/axiom audit all passed using Lean 4.19.0 `--trust=0 -j1`, exit codes `[0,0,0,0]`, with empty source compiler logs.

The general lambda result derives the two objective directions from weighted minimization inequalities and connects them to constructed quadratic minimizers. An additional theorem states the manuscript's alpha/mean formula explicitly in arbitrary finite dimension, including lambda endpoints with positive cell masses. Zero-mass cases are covered by the general quadratic minimizer theorem with selected fallbacks. The result is weak monotonicity, not unconditional strict decrease/increase.

The projection proof constructs the clamped dot-product parameter, proves its whole-segment distance-minimizing property for distinct endpoints, derives simultaneous squared-distance nonincrease to both endpoints, and handles coincident endpoints separately. Nonnegative group masses preserve these inequalities. The proof does not assume the desired projection property.

The non-dyadic theorem quantifies over every integer numerator m and natural exponent n and proves 5/9≠m/2^n using exact integer remainder arithmetic. It is not a bounded numerical test.

## Evidence and scope

Geometry source SHA-256: `040ae55c98d76ce541621503148d1f2aa81d707fa2a36ce4eaa9524229dcdb46`. The exact source and dependency hashes are in logs/final_receipt.json and DEPENDENCIES.json. All 100 `#print axioms` outputs contain exactly `propext`, `Classical.choice`, `Quot.sound`; these are standard logical foundations, not added domain assumptions. No sorry/admit, new axiom, native proof oracle, or unsafe escape appears in the proof sources. Lean and its import mechanism remain trusted; no independent compiler rebuild is claimed.

COVERAGE.md maps the three source passages precisely. MANUSCRIPT_INPUTS.json records initial/final manuscript hashes, labels and target line hashes. The target passages were unchanged at final inspection during the active editorial workflow. No manuscript text was copied and no manuscript/research code was edited. Version 1 and version 2 manifested payloads and ZIP hashes were rechecked unchanged. This extension supersedes only the three corresponding “remaining mathematical gaps” listed in the version-2 report; all production/executable limitations there remain.

No binary64/Fraction/program correctness, full GFU_L finite branch/order/tie implementation, replay theorem, new sampling claim, empirical claim, or whole-paper verification is asserted here. The broader abstract selected-minimizer lemma explicitly assumes its minimizing premise; the concrete quadratic and explicit mean-curve results establish the required minima using the existing completion-of-squares proofs.

## Actual attempts and bounded resources

The first batch g01 reported two superfluous tactics after goals were already solved and two missing sum-distribution steps in residual identities. The corrected g02 compiled the initial lambda/projection results; g03 added checked whole-segment minimality and non-dyadic arithmetic; g04 added the explicit mean-form specialization. All failed and successful compiler logs/receipts are retained. The final trust-zero batch checked the frozen final source with no warnings.

The pass began at about 10:05 UTC; final proof/audit completion was 2026-09-26T10:13:19.369637+00:00, inside the requested 20–25-minute bound. The final four commands held the shared advisory lock for 16.561 seconds total; all recorded development commands held it for 71.645 seconds total. The parent process held the lock, used one compiler worker, released it between commands, and never unlinked it. These are resource receipts, not timing benchmarks. No installation, dependency download, subagent, new task, or external publication was performed.

The portable anonymous proof ZIP includes source, exact logs, statement inventory, hash-only provenance, pins and manifest, and was read back against every manifest entry. No further proof is running and no integration wait is required.
