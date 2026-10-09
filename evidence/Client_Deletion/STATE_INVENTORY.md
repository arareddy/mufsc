# State, preparation and cost inventory

Sizes and times below summarize `tables/preparation_storage.csv`. All objects are local and trusted. “Smaller state” means the serialized object measured in this experiment; no raw input was deleted and no disk or deployed RAM saving was measured.

| Object/stage | Produced when | Contents / scope | Charged where |
| --- | --- | --- | --- |
| Fixed processed input | Existing frozen data release | Raw processed coordinates, group arrays, original source-client and full-row identity maps | Reused read-only; per-worker data-load/identity-verification seconds reported separately |
| Canonical initial T=0 checkpoint | One original training per dataset/seed | Represented and encoded client arrays, groups, summaries, group counts, original C0, empty T=0 point-cache/round-stat structures and timings | Full training cost in each preparation.json; no new checkpoint pickle persisted |
| Canonical local summary | Initial local Phase I | Anchors, unsnapped reps, multiplicities, selected indices, k_e and n_e | Already included in canonical training; no uncharged request reconstruction |
| Compact C0 state | Once after initial training | Deep copies of compact summary arrays, active persistent client IDs, per-client (n_0,n_1), global counts, seed/k/gamma/anchor-Lloyd settings | Measured incremental compaction; counts use existing n_e, with summary-only checks and no raw scan |
| Compact state serialized size | After compaction, before timed requests | Protocol-5 pickle bytes in memory | Serialization time reported separately; not a request obligation and not saved to disk |
| Fresh request input | Inside broader request timer | Dictionaries referencing unchanged survivor raw arrays, with departing client omitted | Request-preparation time; train_full then validates/encodes within algorithm timer |
| Direct request | Inside broader request timer | Vector enumerating all departing original local row IDs | Request-preparation time; existing raw masks/group scans/materialization remain inside canonical algorithm timer |
| Fast request | Inside broader request timer | Client ID list, metadata validation/subtraction, filtered active dictionaries, fresh rational anchor table and server result | Request preparation plus algorithm time; no raw survivor data access |
| Next compact state | During fast deletion | New active dictionaries/counts sharing unchanged read-only summary arrays | Inside fast algorithm timer; returned in memory. Durable next-state serialization is not measured per request |
| Required output | End of every measured request | Exact same JSON model projection: indexed trajectory/final-center bytes and empty T=0 N/S/SS list | Witness construction, JSON encoding and local file write included in request E2E; no fsync |
| Correctness/quality evidence | After timed calls, still under batch lock where CPU work occurs | Extra state reference, model equality checks, exact group costs/fractions and T=1/T=2 statistics | Separate from request timing; exact quality evaluation cost retained |

Mean initial training / additional compaction: Adult 251.805 / 1.178 ms; Bank 231.292 / 0.173 ms; Credit 167.754 / 0.669 ms. All setup fields per seed, including serialization costs, remain in the CSV.

Mean protocol-5 checkpoint / compact-state sizes: Adult 55,030,623 / 3,351,441 bytes; Bank 31,178,477 / 280,225 bytes; Credit 12,508,311 / 791,090 bytes. Last-byte differences among full checkpoints arise from timing metadata serialization. Compact states have 2,000/400/2,000 original summary slots; after client 0 departs the server sees 1,980/380/1,980 slots respectively. No dense synthetic expansion is created.

The compactor preserves selected indices within the original surviving group slices. Whole-client removal leaves every surviving slice order unchanged, so no per-row remapping or new survivor ID allocation is needed. External provenance maps stay in `IDENTITY_REGISTRY.json` and the original frozen identities; active IDs determine which clients remain. The state does not embed a full per-row raw-data registry.

The candidate state uses O(C k d) array storage plus O(C) metadata. The original checkpoint carries O(n d) represented and encoded arrays even at T=0. This prototype invokes canonical training and then compacts it; it does not eliminate the initial checkpoint peak. Integrating a direct compact-state producer into training could reduce that peak, but it is not implemented or measured here.

Keeping the original training cost common to systems that already need an original model, incremental break-even is `ceil(compaction / (baseline request - fast request))`: one request for all 15 measured cases against either fresh or direct. Charging the entire initial training plus compaction gives two independent requests against fresh in every case. This arithmetic does not establish sequential-service costs; the performance grid measures independent requests, and only small logical sequence fixtures were run.

Read-only arrays and a frozen dataclass do not make nested dictionaries secure or immutable. Internal state must not be externally modified. The returned next state contains no departing summaries, but prior state references, original data, historical checkpoints and experiment witnesses may retain personal information. New per-case full checkpoints were resident only during their worker and were not persisted. No secure erasure, backup purge, transport, durable-state commit or cache-equality guarantee is supplied.
