from pathlib import Path
import csv,json,statistics as st
ROOT=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text())
rows=lambda p:list(csv.DictReader(p.open()))
summary=read(ROOT/'SUMMARY.json');verify=read(ROOT/'VERIFICATION.json');grid=read(ROOT/'FROZEN_GRID.json')
pairs=rows(ROOT/'tables/paired_steps.csv');cum=rows(ROOT/'tables/cumulative.csv');setup=rows(ROOT/'tables/setup.csv');obs=rows(ROOT/'tables/observations.csv');quality=rows(ROOT/'tables/quality.csv')
mean=lambda rs,k:st.mean(float(x[k]) for x in rs)
run=ROOT/'runs/sequences-20260926-v1'
identity=[]
for d,seq in grid['sequences'].items():
 for s in seq['steps']:
  identity.append(f"| {d.title()} | {s['step']} | {s['client_id']} | {s['removed_n']:,} | {s['removed_group_counts'][0]:,} / {s['removed_group_counts'][1]:,} | {s['retained_n']:,} | {s['retained_group_counts'][0]:,} / {s['retained_group_counts'][1]:,} |")
step_table=[];cumulative_table=[]
for s in summary['dataset_steps']:
 step_table.append(f"| {s['dataset'].title()} | {s['step']} | {1000*s['fresh_request_seconds_mean']:.3f} | {1000*s['compact_request_seconds_mean']:.3f} | {s['request_seconds_ratio']:.2f} | {1000*s['fresh_persistence_seconds_mean']:.3f} | {1000*s['compact_persistence_seconds_mean']:.3f} | {s['operational_seconds_ratio']:.2f} |")
 cumulative_table.append(f"| {s['dataset'].title()} | {s['step']} | {1000*s['fresh_cumulative_request_seconds_mean']:.3f} | {1000*s['compact_cumulative_request_seconds_mean']:.3f} | {s['cumulative_request_seconds_ratio']:.2f} | {s['cumulative_request_seconds_ratio_seed_min']:.2f}–{s['cumulative_request_seconds_ratio_seed_max']:.2f} | {1000*s['fresh_cumulative_operational_seconds_mean']:.3f} | {1000*s['compact_cumulative_operational_seconds_mean']:.3f} | {s['cumulative_operational_seconds_ratio']:.2f} |")
setup_table=[];storage_table=[];quality_table=[];setup_inclusive=[]
for d in ('adult','bank','credit'):
 ss=[x for x in setup if x['dataset']==d];cc=[x for x in cum if x['dataset']==d and x['step']=='3']
 setup_table.append(f"| {d.title()} | {1000*mean(ss,'data_load_identity_seconds'):.3f} | {1000*mean(ss,'initial_training_seconds'):.3f} | {1000*mean(ss,'compaction_seconds'):.3f} | {1000*mean(ss,'original_compact_serialization_seconds'):.3f} | {1000*mean(ss,'full_checkpoint_serialization_seconds'):.3f} |")
 last=next(x for x in summary['dataset_steps'] if x['dataset']==d and x['step']==3)
 storage_table.append(f"| {d.title()} | {mean(ss,'full_checkpoint_pickle_bytes'):,.0f} | {mean(ss,'original_compact_pickle_bytes'):,.0f} | {last['compact_state_bytes_mean']:,.0f} | {last['fresh_state_bytes_mean']:,.0f} |")
 setup_inclusive.append(f"| {d.title()} | {mean(cc,'fresh_operational_seconds')/mean(cc,'compact_incremental_setup_operational_seconds'):.2f} | {mean(cc,'fresh_common_training_operational_seconds')/mean(cc,'compact_common_training_operational_seconds'):.2f} |")
 for n in (1,2,3):
  q=[x for x in quality if x['dataset']==d and x['step']==str(n)]
  quality_table.append(f"| {d.title()} | {n} | {mean(q,'Phi'):.6f} | {min(float(x['Phi']) for x in q):.6f}–{max(float(x['Phi']) for x in q):.6f} | {mean(q,'G'):.6f} |")
compact=[x for x in obs if x['method']=='compact'];fresh=[x for x in obs if x['method']=='fresh']
matchwins=sum(float(x['request_seconds_ratio'])>1 for x in pairs);opwins=sum(float(x['operational_seconds_ratio'])>1 for x in pairs)
wall=read(run/'STATUS.json')['elapsed_seconds'];quality_time=sum(float(x['scoring_seconds']) for x in quality)
report=f'''# Three sequential whole-client withdrawals at T=0

Completed 26 September 2026; run `sequences-20260926-v1`. The unchanged reviewed compact-state method passed **135/135 full indexed model comparisons and compact-state checks** over 45 request cases (15 dataset/seed sequences, three correlated steps each), with three timing repeats of each full sequence. **Pooled matched resident model-output speed ratio: {summary['pooled_matched_ratio']:.2f}x. Separate operational ratio including each method's buffered state write/reload: {summary['pooled_operational_ratio']:.2f}x.** The algorithm-only ratio is {summary['pooled_algorithm_ratio']:.2f}x. No exclusions, failed workers, correctness failures, selected reruns, method revisions or T>0 experiments occurred.

These are same-T0 comparisons against fresh T0 on the current survivors. They establish a bounded local sequential-service result under trusted state, fixed preprocessing and persistent identity. They do not establish quality adequacy, optimality, full-cache identity, independent randomness for model-adaptive requests, physical erasure, durability, network performance, failure recovery or long-sequence performance. Historical immutable datasets and experiment artifacts remain intentionally preserved.

## Frozen input and sequences

Canonical Adult/Bank/Credit seed-0 partitions; k=10; seeds 10000–10004; T=0, L=6, scale bits 12, gamma=0, zero anchor Lloyd; original clips 175/121/74. In ascending original persistent-ID order, choose the first three distinct valid withdrawals, skipping only those emptying a required global group. This selected **0,1,2 for each dataset, with zero skips**. Source-client IDs here also equal 0,1,2. The same sequence is reused across the five seeds. Both original groups remain present; IDs/row order are never renumbered.

| Dataset | Step | Client | Rows removed now | Removed group 0 / 1 | Rows retained | Retained group 0 / 1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
{chr(10).join(identity)}

`FROZEN_GRID.json` preserves every removed processed full-row ID, ordered removed/retained row hashes, current active IDs and group counts. `IDENTITY_REGISTRY.json` binds all original client slices to source clients and ordered row hashes. `INPUTS.json` binds datasets/identity files to the accepted corrected release. The worker revalidates the input hashes, original row maps and every current survivor hash. Upstream fitted preprocessing influence and inherited Adult/Credit raw provenance gaps remain outside this fixed-artifact guarantee.

`INPUT_MANIFEST.json` records completed antecedent reports/review/source hashes and a read-only live manuscript hash snapshot. The separate positive-refinement task was not read or used. The 17 canonical numerical modules and all copied map/driver files match the frozen baseline; `client_c0.py` is byte-identical to reviewed v1 (`6d7b8d993ed9e9fcda896192ee6e6299a434ab7cdc25ab9907fc6b4bc1cf3dde`). The new wrapper does not modify the learning/deletion method.

## What the measurements include

**Primary matched model-output request:** resident input/prior state; request translation and survivor dictionary views; the whole public training/deletion call; full exact indexed model witness serialization and equal-schema buffered local output write/close. Fresh uses `build_cache=False`. Compact returns its next in-memory state within this timer. Both output identical bytes at a given seed/step. Prior checkpoint loads, state persistence, initial preparation, pre-call GC, audit comparison and quality evaluation are outside both primary timers. This is the same output boundary as the completed single-withdrawal T0 study, but the new figures are not pooled with its observations.

**Separate state persistence:** immediately after each primary call, compact serializes the returned next state with protocol-5 pickle, writes/closes a local file, reads/deserializes it, verifies bytes and validates all state fields/arrays and exact counts against the just-returned state. Fresh serializes/writes/reads/validates its current active-client ledger; fixed input and service configuration stay resident/external. Fresh requires no model-dependent checkpoint to retrain its next population. Both paths include their necessary state work. Secondary operational time is primary plus this persistence/reload total; it is a sum of charged components, not a network E2E or a single continuous transaction timer.

**Storage semantics:** ordinary buffered local I/O, no fsync or cache eviction. No durable-write timing or atomic commit is claimed. Pickle files are trusted locally produced data; the reload check is not a malicious-state validator. The worker still holds raw data for fresh references and quality, although compact requests use only compact state and the departing ID. One current state file per method/case is overwritten as this simulation advances; only final checkpoints plus every intermediate hash/receipt are retained. This overwriting does not securely erase old physical bytes or purge original data/history.

At the next step the compact input is the **validated reloaded object returned by the previous step**, and fresh uses its reloaded ledger. Receipt chains bind before/after content hashes and checkpoint-byte hashes. Each timing repetition explicitly resets to the legitimately prepared original state; no previous or original checkpoint is passed as a current state within a sequence. Initial original training/compaction occurs once per dataset/seed, shared across its three timing repetitions; no setup cost is silently multiplied by repeats.

## Per-step timings

Means use all five seeds and all three repeats, in milliseconds. Ratios divide summed fresh time by summed compact time at the same step; all 45 seed/step means favor compact ({matchwins}/45 matched and {opwins}/45 operational). Matched case-mean ratios range {summary['matched_case_ratio_range'][0]:.2f}–{summary['matched_case_ratio_range'][1]:.2f}x; operational ratios range {summary['operational_case_ratio_range'][0]:.2f}–{summary['operational_case_ratio_range'][1]:.2f}x. These are observed descriptive results, not a guaranteed threshold.

| Dataset | Step | Fresh matched ms | Compact matched ms | Matched ratio | Fresh persistence ms | Compact persistence ms | Operational ratio |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
{chr(10).join(step_table)}

Pooled ratios across all 135 timing pairs weight settings by measured time. They are not an average of the displayed ratios. `paired_steps.csv` retains all 45 seed/step means, min/max timing values and the within-case repeat-ratio range. `observations.csv` preserves every duration, order, component, byte count and output/state hash. Timing repeats are not independent scientific sequences.

## Cumulative sequence timings

Each cumulative observation is the actual sum of completed steps within its repetition, then averaged over repetitions/seeds. No unlike refinement budgets are compared.

| Dataset | Through step | Fresh matched ms | Compact matched ms | Matched ratio | Five-seed ratio range | Fresh operational ms | Compact operational ms | Operational ratio |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
{chr(10).join(cumulative_table)}

`figures/sequence_cumulative.pdf` is the appendix-ready plot. Lines show ratios of summed times and shading shows five-seed ranges of paired cumulative ratios; the shaded band is not a confidence interval. Axes use separate scales by dataset. Correlated steps and repeated timings are not treated as IID. The fixed early-ID withdrawals have similar group proportions and sizes within each dataset; this is limited client coverage, not a heterogeneous/adaptive removal campaign.

## Setup and storage overhead

Means over five legitimate original preparations per dataset. Full-checkpoint serialization is a size/cost diagnostic performed once; the full raw checkpoint blob is not persisted. It is not necessary per request. The compact serialization diagnostic is also separate from measured per-request persistence. Original compact state sizes and final state sizes are measured protocol-5 bytes, not disk savings or total deployed RAM.

| Dataset | Load/identity ms | Original training ms | Extra compaction ms | Original compact serialization ms | Full-checkpoint serialization ms |
| --- | ---: | ---: | ---: | ---: | ---: |
{chr(10).join(setup_table)}

| Dataset | Original full-checkpoint bytes | Original compact bytes | Compact bytes after step 3 | Fresh active-ledger bytes after step 3 |
| --- | ---: | ---: | ---: | ---: |
{chr(10).join(storage_table)}

Incremental setup below adds compaction once to compact's three-request operational sum. The second view charges measured original training to **both** systems plus compaction to compact, as an explicit common-original-model scenario. It is not a claim that a fresh-only service must build a cache-enabled original checkpoint. Load/startup/diagnostic serialization remain separately disclosed, outside these illustrative setup views.

| Dataset | Three-request operational ratio with extra compaction | Ratio charging common original training too |
| --- | ---: | ---: |
{chr(10).join(setup_inclusive)}

CSV `cumulative.csv` supplies the actual seconds for these views and each seed. Experimental resets are just assignments to the unchanged prepared original state and original fresh ledger; their recorded durations appear in each completion receipt. These resets are a repeat mechanism, not recovery latency. The initial producer still constructs a full original checkpoint before compacting it, so peak memory is not reduced to compact-state size. `setup.csv` records observed process maximum RSS.

## Exactness and quality

Before the real-data campaign, the copied 10-method gate passed with 22 exact fixture/sequence comparisons; new fixtures added three serialized/reloaded sequence steps, 30 malformed/domain-invalid request rejections, malformed-pickle rejection and the exact objective example Phi0=2, Phi1=25, G=27, Phi=25. These are new executions of focused tests, not relabeled historical gates.

All 135 timed compact calls matched fresh in the complete indexed C0 trajectory/final center bytes, every surviving summary field (representatives, selected indices, multiplicities and metadata), exact per-client/global counts, active client IDs and ordered anchor owner/coordinate/rational-weight table. Returned and reloaded compact states matched fresh compaction. No permutation or tolerance comparison was used. At T=0 the round-statistic list is empty, so no nonempty N/S/SS replay claim follows.

`VERIFICATION.json` independently re-parses all 270 saved model files with standard-library binary64 decoding, exact shapes/finite values/hex representations, checks equal fresh/compact bytes and repeat invariance, 135 state-chain/equality receipts, all artifact/source hashes, 30 final checkpoint-file hashes, 270 reload receipts, 45 exact fraction quality rows, component sums and order balance. Full compact-array comparisons execute in the worker; the reporting verifier rechecks their saved digest/chain receipts rather than independently reconstructing those arrays. Numerical training/quality arithmetic shares the canonical kernel; this is not a newly independent arithmetic oracle or external review of this wrapper.

Quality is scored once per distinct seed/population (45 rows) outside timings. Compact inherits the same score by exact model equality. Every row asserts **Phi=max(Phi0,Phi1)** and **G=Phi0+Phi1** with exact fractions; pooled SSE is separately n0*Phi0+n1*Phi1. The sum G is never labeled worst-group cost.

| Dataset | Step | Mean worst-group Phi | Five-seed Phi range | Mean sum G |
| --- | ---: | ---: | ---: | ---: |
{chr(10).join(quality_table)}

These populations change after every deletion, so changes in Phi are not improvements on one fixed population. No T>0 training was run, no T0 quality adequacy threshold was chosen, and no T0/T1/T2 exact-unlearning ratio is reported. The completed earlier single-client/round-budget studies' quality cautions remain relevant background, not new sequence quality evidence at positive refinement budgets.

## Execution conditions and limitations

Campaign wall time was {wall:.2f} seconds; 15 exclusive-lock dataset/seed batches completed, releasing the shared lock between them. Logged lock wait totaled {verify['wait_seconds']:.4f} seconds. One numerical worker at a time; all five numerical-library thread controls were one, with NumPy runtime receipts. The reused environment lacks threadpoolctl, so these receipts verify configured limits and runtime/SIMD information, not introspected actual backend thread counts. Method-first counts are 68/67 as prespecified for 135 pairs; each step experiences both orders across three repeats. No extra warmup or timed retry was selected. Exact quality scoring accounted for {quality_time:.2f} seconds outside measured request/persistence work; detailed audit durations are in comparison receipts.

One-minute load averages ranged {verify['load_average_1min_range'][0]:.2f}–{verify['load_average_1min_range'][1]:.2f}. Boundary snapshots show unrelated desktop activity, including uarpd using approximately one CPU core and WindowServer activity. The lock coordinates participating research workers; it does not isolate the machine, control thermal state, guarantee fairness of lock scheduling or establish deployment latency. Small millisecond latencies and buffered page-cache effects are material. No statistical confidence/generalization claim is attached to these five-seed summaries.

An additional new-process verification reloads all 15 final trusted compact files and reconstructs their C0 with the canonical server; all match the saved step-3 models. The first-step full model bytes also match all 15 completed historical single-client T0 cases. No training or timing rerun is used for this check; FINAL_STATE_VERIFICATION.json records its scope.

All work is under this local workspace. No data/environment copies, archive extraction, package installation, cloud export, external sharing, manuscript edits, usage reset or historical source/Git mutation occurred. The new wrapper imports only local copied method code and the read-only frozen dataset/environment; final local-only artifacts need a separately selected backup. Reported serialized reductions are not actual measured disk savings.

## Claim status

- **Proved under the reviewed assumptions:** whole-client removal leaves surviving local slices and keyed local streams unchanged; subtracting exact counts and rebuilding canonical normalized anchors/server input gives fresh-equal indexed C0. Induction gives the returned-state invariant over any valid finite sequence. This proof is inherited from the completed theory/implementation review, not established by timing measurements.
- **Tested here:** three fixed valid withdrawals on three datasets and five seeds, full repeated equality checks, ordinary local checkpoint round trips, exact objective definitions and the specified timing/storage boundaries. All outcomes are preserved.
- **Conditional:** transfer to another dataset/sequence/machine depends on valid groups, fixed preprocessing/identity/configuration, compatible numerical environment and trusted unchanged state; speed depends on fresh local work, server size and persistence overhead.
- **Unresolved/out of scope:** T>0 compact-only service, record-level cached service, longer/adaptive sequences, application quality/optimality, malicious/corrupt-state robustness, fresh-independent adaptive laws, physical erasure, network and durable/recovery behavior.

Pan et al. Section 5.3/Algorithm 4 already provides the whole-client-removal/server-recomputation architecture. Ghadiri et al. Section 3 already treats m groups. This contribution is the scoped group-normalized persistent-ID implementation invariant plus bounded sequential measurements, not novelty for either general idea. Local supplied primary texts were checked; no new literature campaign or cross-paper speed comparison was performed.

See `INTEGRATION_NOTES.md` for an appendix-only proposal and cautions, `REPRODUCE.md` for exact commands, and `DELIVERABLE_MANIFEST.json` for final artifact hashes.
'''
(ROOT/'REPORT.md').write_text(report)
notes=f'''# Integration notes: proposed appendix evidence only

No manuscript source was changed. The live main/appendix hashes recorded in INPUT_MANIFEST are a read-only point-in-time snapshot; another authorized task may edit them. Do not silently replace current manuscript source or describe its current build as verified by this experiment.

## Proposed concise appendix paragraph

We tested three sequential whole-client withdrawals at T=0 on Adult, Bank and Credit, with k=10 and seeds 10000–10004. Clients were chosen in original persistent-ID order, excluding only requests that would empty a required global group; all three datasets selected IDs 0,1,2 without exclusions. Each step consumed the preceding returned and reloaded compact state. Across 45 seed/step cases and three full-sequence timing repeats, all 135 compact outputs matched fresh T=0 exactly in indexed model, surviving summaries, group counts and canonical anchor ordering. The pooled resident model-output ratio was {summary['pooled_matched_ratio']:.2f}x; a separate operational ratio including each method's necessary ordinary buffered state write/reload was {summary['pooled_operational_ratio']:.2f}x. These local measurements exclude durable commit, physical erasure, transport and recovery, and do not establish T0 quality adequacy or longer/adaptive sequence behavior.

## Figure caption proposal

Three sequential whole-client withdrawals at matched T=0. Lines show ratios of cumulative fresh/compact time summed over five seeds and three timing repetitions per seed. Blue includes identical model-output serialization/write; orange additionally includes each method's necessary ordinary buffered state persistence and validated reload. Shading spans the five paired seed ratios and is descriptive, not a confidence interval. Repetitions and sequential steps are correlated; per-dataset vertical scales differ. No fsync, cold-cache or network latency is measured. See PROTOCOL and REPORT for setup and state requirements.

## Editorial constraints

Keep internal pickle/ledger/locking details in an appendix/report. Do not replace existing single-withdrawal 35.79x with 34.99x as though this were a corrected rerun; it is a distinct sequential experiment and must be labeled separately. Do not combine this campaign's 135 comparisons with the original 810 or with other grids without identifying disjoint scope. Do not count 135 timing pairs as independent scientific trials. Matched ratio excludes persistence equally; operational ratio explicitly has different necessary state work. Initial training and incremental compaction remain separate.

Phi is the maximum group-average cost, G their sum. Do not infer that lower values between deletion steps improve quality on a fixed population. No T>0 result from the concurrent refinement task was consumed. The local machine was not idle. The reviewed method stayed byte-identical, but the new persistence/measurement wrapper has only this task's testing and saved-evidence verification, not the earlier reviewer's sign-off.

Retain fixed preprocessing, binary nonempty group universe, persistent identity/order, same seed and trusted state. Compact next-state equality is not fresh raw-cache equality or personal-data erasure. Cite Pan Section 5.3/Algorithm 4 as architectural precedent and Ghadiri Section 3 for m-group scope; do not claim novelty for either. Nothing is submitted or ready for automatic external publication.
'''
(ROOT/'INTEGRATION_NOTES.md').write_text(notes)
print('Report and integration notes generated')
