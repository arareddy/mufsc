# Timing scope

Published observations are frozen under `evidence/*/tables`. Repeated timings on another machine need not equal them. Exactness assertions concern numerical outputs, not elapsed time. Network transport is unmeasured; serialized bytes and modeled parallel computation are not network measurements.

`reproduce.py run` is the scientific replay path. Its timer diagnostics are single-process fresh computations; data verification, independent scoring and correctness checks are outside those measured calls. Do not insert these diagnostic times into published benchmark tables.

`benchmarks.py run` uses the following timing boundaries:

| Study | Portable measurement path | Important scope |
|---|---|---|
| P2 | Original isolated `execution_worker.py` | Includes original per-call and comparable E2E accounting; new input/checkpoint pickle is created locally and removed after the case. |
| P3 | Original observer-equipped P3 worker, import paths adapted | Original assignment counters and E2E accounting retained. Original accepted source gate is verified against unchanged numerical hashes. A new portable fixture suite runs first and binds the current runtime in a separately labeled execution gate; no historical gate is rewritten. |
| Round_Budgets | Original P2 isolated worker at frozen T0/T1/T2 settings | Same numerical requests and four methods. Campaign orchestration is portable; new cold-process time is recorded separately. |
| Client_Deletion | Original `measured_request` function, extracted unchanged | Three resident methods; identical model output serialization; three timing repeats by default. |
| Client_Refinement | Original `measured_request` and accounting functions | Four resident methods at matched T1/T2; four repeats. No compact positive-T method is introduced. |
| Client_Diversity | Original Client_Deletion measurement function on diversity cases | Same numerical request/output boundary; portable setup is per case, instead of sharing one setup across two selected clients. Do not compare setup amortization to original tables. |
| Client_Sequences | Original request and persistence functions | Fresh survivor ledger and compact state; actual buffered write/read/reload checks; no fsync durability claim; three correlated steps within each sequence. |
| Multigroup | Original `output_call` function | Separate categorical map; compact path only at T0. Model-output boundary unchanged. |

Default repetitions for P2/P3 are three fresh timing observations requested by the portable wrapper, not a claim about the original campaign's repetition count. Their original individual observations remain in evidence. Use an explicit `--repeats` when following a particular saved protocol. Full sequence timing always resets to the same initial state per repeat and uses the reloaded state for the next request.

Record CPU/OS/runtime and load when comparing performance. All benchmark commands force one numerical-library thread and execute serially. Use `serial.py` so independent local commands honor the same lock. No fresh benchmarking result is silently merged into frozen CSVs.
