# Frozen protocol: canonical whole-client replay with one or two refinement rounds

Frozen before any new training or performance measurements on 26 September 2026. Workspace: `study://Client_Refinement`. Run ID: `client-refinement-20260926-v1`. The accepted C0 workspace is read-only; `C0_PRESERVATION.json` binds all 325 accepted files including its delivery manifest. No manuscript, shared Git or Overleaf change is authorized here. No new optimized learner or compact-state positive-T path is introduced.

## Design, data and source

Exactly the 15 accepted C0 cases are extended to T=1 and T=2: Adult/Bank/Credit, k=10, training seeds 10000-10004, dataset partition seed 0, original client 0 removed in each case. `FROZEN_GRID.json` records 30 settings and the parent grid hash. Preserve every original run client ID and source-client/full-row identity; never renumber survivors. No seed/client/request reselection. Removed counts are Adult 300/30162, Bank 2259/45211, Credit 299/30000; all retain both groups.

Unchanged FTF-1D-descriptor-v1 source aggregate: d76d7c0606512c458147955aff2a0afea992c87246ce30e4c43cc28003602c31. `BASELINE_MANIFEST.json` binds 17 source files plus the map and witness helper to their frozen originals. Only a small source copy is made. Map hash: 7c25a7f41af39859cc4cc254b3a70525380285904e7f67cd45ca8efbe3633d52. b=12, L=6, gamma=0, anchor-Lloyd=0, clips Adult 175 / Bank 121 / Credit 74. Canonical exact statistics, numerical comparison/tie rules, rational weights, keyed PCG64 sampling and descriptor normalization remain unchanged.

`INPUTS.json` and `IDENTITY_REGISTRY.json` are byte-identical copies of accepted C0 pointers. Existing processed artifacts and Python3.12.14/NumPy2.3.5 environment are reused read-only; bytecode writes disabled. Every worker rechecks the processed artifact hash, source identities and departing row IDs against the fixed case. C0 prior quality and performance are historical evidence, with separate run identity `client-c0-20260926-v1`. They are not overwritten, relabeled or measured again.

## Methods, repetitions and correctness gate

Use unchanged canonical Fresh (train_full, build_cache=False), Direct (unlearn mode none), Basic and Runner-up (default abandonment threshold 0.5). The compact C0 candidate is not imported or called. Construct an original-population checkpoint separately at each T, with build_cache=True; it contains the required original trajectory, exact statistics and per-point round caches. Record initial training/cache costs and serialized sizes separately from requests; no new full checkpoint is persisted.

There are 30 dataset/seed/budget settings, 120 distinct method outputs, and 90 DISTINCT replay-versus-fresh comparisons. Four repetitions per setting produce 480 timing observations and 360 repeated replay comparisons, not 360 independent exactness trials. Rotate [fresh,direct,basic,runnerup] left by (setting_index+repetition)%4; each method occupies every position once. No timing-driven exclusions, retries or expansion.

Before the full grid, run only targeted tiny positive-T harness checks: complete indexed C0..CT/final binary64 witnesses, every exact integer N/S/SS, sparse persistent IDs, single/mixed-group whole-client deletion, both groups retained, k=1 certificate pass path, and certificate fallback behavior where exhibited. Compare positive-T canonical methods on identical survivors and record actual executed comparisons. Verify source/input/identity hashes and test timer aggregation with a synthetic nested-timer fixture. This is a harness gate using unchanged canonical arithmetic, not a new independent rational oracle.

For each real setting, every repetition must match matched-budget fresh in full exact_witness (indexed centers and all N/S/SS), and its fresh witness must equal the historical same-population T1/T2 quality-reference witness. Across repetitions require identical witnesses and counters; compare specified extra Phase-I state too. A mismatch aborts the campaign and retains the failure. Preserve partial/failed attempts; no hidden retries. Same-byte output requirements ensure that method timing is not a weaker projection comparison.

## Resident-request timing contract

Use the C0 resident-data contract. Within a single setting's worker, raw input and the required original checkpoint are resident for all methods. Fresh receives shallow survivor dictionary views, omitting the departing client without renumbering; no replay caches are constructed by fresh. Replay receives its original resident checkpoint. One worker/process per setting, serial methods, garbage collection before each observation outside all timers.

Algorithm timer encloses the entire public train_full or unlearn call, including its own validation, encoding, masks, materialization, Phase I and refinement. Request timer starts before survivor-dictionary/request-vector preparation, includes the algorithm, and ends after identical full model projection, JSON serialization and local file write. Output schema is exactly the C0 schema extended by the declared positive budget: map_version, all indexed trajectory/final-center bytes and exact per-round N/S/SS. No fsync. Per-request durable next-state persistence is not required of any method. All methods write the same bytes within a setting.

Dataset loading/identity verification, original checkpoint preparation/serialization-size measurement, interpreter startup, pre-call garbage collection, equality/receipt verification, historical-quality reference checks and reporting stay outside request timing and have separate cost receipts. Do not compare cold fresh to warm replay. No network, physical distributed execution, durable service or personal-data erasure claim.

## Timer audit: disjoint components and overlapping diagnostics

The previous C0 helper is NOT reused: it omitted positive-round work. Here the additive public-algorithm decomposition contains:

1. encoding; input_materialization; cache_construction;
2. sum of phase1_client and phase1_server;
3. shift_bounds;
4. sum over clients AND rounds of phase2_client_certify;
5. sum over clients AND rounds of phase2_client_recompute;
6. phase2_server;
7. residual = observed algorithm time minus all preceding disjoint buckets.

The residual includes validation, uninstrumented group-count work, round digests, bookkeeping and timer/object overhead. It is NOT classified as refinement or scanning by default. Phase-I total is its client+server buckets. Measured refinement buckets are shift bounds + Phase-II certificate/recompute/server; report residual separately. Serial sums are used, not the modeled max-client-per-round latency from timing.totals.

certificate_scan and failed_assignment wrap their respective already-counted client timers. fallback_sunk spans triggering-round work already in shift/client/server timers plus uninstrumented overhead; fallback_rebuild wraps direct rebuild client/server timers. Preserve these four as OVERLAPPING diagnostics, never sum them into the additive decomposition. Include each underlying refinement operation exactly once. Verify every observation's additive buckets sum to algorithm time and request preparation + algorithm + output sum to request time, allowing only clock arithmetic roundoff.

Fallback frequency means a Basic/Runner-up threshold-triggered transition (abandonment_round not None), counted once per distinct setting/method. Direct starts in direct mode and is not a threshold-triggered fallback. The per-round flag alone cannot distinguish triggering rounds from later direct rounds.

N = retained point-rounds; A = attempted certificate point-rounds; P = certificate passes including passes on abandoned rounds; S = useful passes on nonabandoned rounds; J = failed assignments repeated at the triggering rebuild. Save all round rows and pooled counts per unique setting/method. Report P/A only when A>0 (otherwise undefined), S/N, and N-S+J modeled point assignments. Fresh/Direct have A=P=S=J=0 and N=(n-r)*T. Do not multiply counts or case frequencies by timing repetitions; verify that repeated counters are identical.

## Matched quality reuse

Reuse all 15 historical quality files for T0/T1/T2; do not rescore raw data when exact saved witnesses suffice. Before measurement, bind their file/receipt hashes, parent run source hashes, input/identity/grid hashes and full model-witness/center hashes. Each new fresh T1/T2 witness must match the corresponding historical complete trajectory and N/S/SS; this makes the historical quality score applicable without a new scoring run. Record reference loading and verification costs separately. Historical quality_evaluation_seconds is historical; new scoring cost is zero because no new evaluation is executed.

Read exact fractions. Assert Phi=max(Phi_A,Phi_B), G=Phi_A+Phi_B, and pooled_SSE=n_A*Phi_A+n_B*Phi_B. Phi, not G, is the fairness cost. Report all 45 matched budget rows, their provenance, both group costs and worst-group changes. T0/T1/T2 denote refinement rounds; initialization already requires client-to-server summary communication and server initialization, so T0 is not zero communication. Never divide T1/T2 replay time by T0 fresh or vice versa. Compact-fast exists only as historical T0 context, visibly isolated from canonical positive-T curves. The prior record-deletion panels are different requests and are not substituted here.

## Execution bounds and reporting

The parent holds exclusive Python fcntl.flock on `/private/tmp/ftf_benchmark_20260926.lock` across each substantial worker subprocess, never unlinking it. Release between settings. One numerical measurement worker; all five numerical-library thread controls set to 1 before NumPy import. Record environment, background load/top CPU processes and queue/held durations. Any gate training also uses the lock. Queue time is not request latency. No new agents or remote compute.

Per-setting timeout 600 seconds; default scheduling budget 90 minutes. Resume only completed matching settings under unchanged source/protocol/gate bindings; incomplete attempts are preserved and require an explicit new attempt ID with a failure ledger, not a silent overwrite. Stop on correctness failure. Full grid is prioritized over extensions.

Report every setting's four-repetition mean times, paired mean-time ratios, ratio of total observed times, wins/losses/ties, ratio and within-case timing variation, disjoint components, overlapping fallback costs and unique-setting N/A/P/S/J metrics. No heterogeneous-suite IID confidence claim; no selection of the fastest repeat. No target speedup. Deliver Markdown report/protocol/correctness/integration notes, CSV/JSON evidence, setup inventory and reproducible commands. A compact appendix PDF may visualize the unchanged budgets and historical C0 separately. Do not edit or publish the live manuscript; hand evidence to the orchestrator for a later inclusion decision.
