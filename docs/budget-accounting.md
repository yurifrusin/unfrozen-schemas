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

- Each ledger declares its run ID, schema version, checkpoint or interval, start/end timestamps,
  and whether values are measured, derived, or unavailable.
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
