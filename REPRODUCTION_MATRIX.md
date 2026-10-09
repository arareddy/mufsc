# Reproduction matrix

Status below describes commands actually run during packaging, on Python 3.12.14 / NumPy 2.3.5 / macOS arm64. Full grids are provided but were not rerun. All regular commands use included data; dependencies must already be installed.

| Level / component | Actually tested | Result | What remains unrun |
|---|---|---|---|
| Offline integrity | All 11 dataset containers, array bytes/dtypes/shapes and frozen numerical module hashes | PASS | Final archive checksum check recorded author-side after creation |
| Fixtures | 193 core/independent tests; 96 literal P1 comparisons; 7 Lloyd fixtures; scalar client checks; full MG fixture suite | PASS | No claim that the absent legacy pickle-loader tests were rerun |
| Saved tables | 270 exact quality rows, 360 summaries, 108 paired Lloyd summaries; inventory of 98 CSVs | PASS | No new empirical observations created by aggregation |
| Figures | Eleven PDFs regenerated; saved PDFs have unchanged page content and removed metadata | PASS, visual QA | Rendering may vary with versions/fonts |
| P1–P4 | First frozen case/shard in every study; extra Bank P4 splitgroup/gamma0.1 | PASS | Full 800-shard P1, 57-setting P4, 175-case P2 and 95-case P3 grids |
| Round budgets | Adult T0 and Bank T2 | PASS | Remaining cases in 45-case grid |
| Whole-client C0/refinement/diversity | First case each; Bank T2 and second Credit identity c99 | PASS | Remaining 15/30/30-case grids |
| Sequences | First three-step sequence, including actual write/read/reload | PASS | Remaining 14 sequences |
| Multi-group | First real T0 and T2 cases; categorical oracle fixtures | PASS | Remaining real-data cases; synthetic growth command separately tested after the main matrix |
| Matched Lloyd | Adult and Bank record populations; both methods and all T0/T1/T2 witnesses/quality | PASS against saved exact outputs | Remaining 28 cases |
| Benchmark commands | All eight supported types, first case, two timing repeats; six also repeated under isolation | PASS | Full repeated timing campaigns; timings are machine-dependent |
| Isolation | Fresh copied directory, unrelated cwd, original trees denied, network denied; executable hashes matched release afterward | PASS | Not an OS/container sandbox; non-macOS execution not tested |
| Raw ACS | Source hashes/recipe inspected and CLI help tested | Documented only | No re-download or pooled raw rebuild in packaging |
| Optional Lean (v2) | Five frozen archive identities, all supplied manifests, CRCs, member preservation and anonymity checked | INTAKE VERIFIED | No packager compiler rerun; only scoped supplied receipts are claimed; see formal_verification/README.md |

Exact command arguments, durations and counts: `packaging_validation/RESULTS.json`. Failed developmental wrappers were corrected before final validation; no failed command is represented as a pass. The P3 wrapper now creates a separately labeled current-runtime gate only after its fixture command succeeds.

Typical tested durations are seconds for individual scientific cases and roughly 16 seconds for the full fixture command on the packaging machine. Figure regeneration took about one minute with fresh font caches. Full P3 grids may need substantially more time/memory, especially million-row checkpoints; no full-grid runtime estimate has been measured for this portable orchestration.

Version 2 validation is recorded separately in `packaging_validation/V2_INTAKE.json`; earlier scientific validation receipts remain unchanged.
