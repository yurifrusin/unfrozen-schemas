# Budget accounting

Every run and comparison must expose resource use at run and checkpoint granularity. A zero is an
observed absence; `null` means unavailable and requires a reason. Counters must never combine
modalities that the scientific design treats separately.

## Required ledger fields

| Resource | Definition | Unit and counting rule |
|---|---|---|
| External language | Teacher, oracle, prompt, task, and supplied natural-language content presented to the model | Tokenizer tokens, counted once when consumed; identify tokenizer and exclude self-generated text |
| Self-generated language | Predictions, hypotheses, action rationales, summaries, and consolidation text produced by the model | Tokenizer tokens at generation time, including discarded outputs; never merge with external language |
| Sensor observations | Discrete observation events delivered through non-language channels | Observation count, plus raw encoded bytes in a separate `sensor_bytes` field |
| Environment steps | Accepted state transitions, including declared `WAIT` or `NOOP` actions | Transition count; rejected actions are recorded separately and do not silently increment it |
| Optimisation steps | Parameter-update attempts | Optimiser step count; record skipped/non-finite steps separately when relevant |
| Forward passes | Model forward invocations | Invocation count, with batch and sequence-shape metadata where needed for interpretation |
| Backward passes | Gradient backpropagation invocations | Invocation count; gradient accumulation must not be collapsed into optimiser steps |
| Elapsed compute | Measured execution time for the accounted work | Monotonic wall seconds; later GPU work also records device/GPU seconds separately |
| Peak memory | Maximum measured process/device allocation during the run | Bytes; identify measurement method and distinguish host RAM from VRAM |
| Stored artifacts | Files retained by the run | Artifact count and bytes, with relative path, media type where known, and SHA-256 |

Future scientific ledgers may also record unique episodes, trainable-parameter steps, GPU seconds,
and peak VRAM. These extend rather than replace the required fields.

## Accounting boundaries

- Milestone 0 uses resource-budget schema version `2`. Because no Milestone 0 release used version
  `1`, version `2` replaces that underspecified schema without a compatibility layer. The enclosing
  run-manifest and bootstrap-failure schemas also move to version `2` because they embed and validate
  this contract.
- Each ledger declares its run ID, interval kind, timezone-aware interval start, and interval end.
  The end may be `null` only while the interval is open; every success, started-run failure, and
  bootstrap-failure record closes the interval.
- Every resource field has exactly one typed measurement-basis entry with a non-empty method and one
  of four statuses: `measured`, `derived`, `observed_zero`, or `unavailable`.
- `observed_zero` requires a numeric zero. `unavailable` requires a `null` value and reason.
  `measured` and `derived` require non-null values. Interval end cannot precede interval start.
- Run manifests require the embedded budget run ID and timestamps to match the surrounding manifest.
  Terminal success and failure manifests require the same non-null end timestamp in both records.
- Token totals name the tokenizer version and separate lossless serialisation from ordinary natural
  language.
- Active and yoked runs retain pair IDs. Byte-identical trajectory claims require matching artifact
  hashes, not only equal step counts.
- Failed runs retain the work performed before failure. Retries become new runs unless an approved,
  idempotent resume protocol preserves the original manifest.
- Cached trajectory collection is charged when originally produced; consumers record stored bytes
  read and their own compute. Reports must show both acquisition and reuse views.
- Resource matching is asserted only after parity checks. Unmatched dimensions remain visible in
  tables and plots.

## Required reporting views

Phase II results must report episode-matched, external-language-matched, and compute-reported views.
Efficiency curves include environment transitions, external and self-generated language tokens,
optimiser steps, forward passes, elapsed/device compute, and stored experience bytes. A lossless text
log is an information ceiling and must not be described as ordinary natural-language teaching.

Milestone 0 serialises the ledger as JSON for a complete offline toy run. Later milestones may add
the specified Parquet representation without changing the meaning of existing counters.

For the Milestone 0 smoke path, elapsed time is measured with `time.perf_counter`. Peak memory is
measured with `tracemalloc` and means peak traced Python allocations, not total process RSS or system
RAM; it is unavailable with a reason if tracing never starts. Stored artifact count and bytes are
derived from the hash-stable retained run files. Forward invocations are counted. External and
self-generated language, sensor observations and bytes, environment steps, backward passes, and
optimisation steps are observed zero.
