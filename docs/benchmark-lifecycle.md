# Benchmark lifecycle

This document defines the M2.1 benchmark-integrity machinery. `CODEX_SPEC.md` remains authoritative.
M2.1 supplies contracts and one non-scientific fixture only. It does not author an outcome,
selection, retention, literal, abstract, metaphorical, external-diagnostic, or production benchmark.

## Purpose quarantine

Every source item, built item, private answer, manifest, logical hash, operation record, and approval
binds one immutable purpose:

- `outcome` — treatment outcomes; never usable for model or hardware selection;
- `selection` — candidate/model-stack selection only; never promotable to an outcome;
- `engineering` — software fixtures only; non-scientific and never promotable;
- `retention` — a prospective separately reviewed namespace; M2.1 contains no retention items.

`identity_purpose` records the purpose at creation and must equal the current purpose. Changing
purpose requires a new authored record and new `item_id`. Validation can compare any number of
candidate/frozen manifests with repeated `--against-manifest` options and rejects an item ID,
purpose-bound model-input hash, or equivalent model-visible content fingerprint across purposes.
Canonical repository use must compare all relevant existing manifests; directory names alone are
not quarantine.

`selection_probe_v1` is reserved for M2.5 selection use. `v1_core` is reserved for the M2.6 outcome
freeze. Neither name may identify an engineering fixture.

## Lifecycle and visibility

Lifecycle state and visibility are distinct fields. The sole transitions are:

```text
SOURCE → PRIVATE → FROZEN
```

- `SOURCE` is mutable, answer-bearing authoring material. It is local/private, not evaluation-ready,
  and not scientific evidence. Each item declares provenance, rights, human-validation, and
  ethics/governance status even when a later decision remains unresolved.
- `PRIVATE` is a deterministic, content-addressed candidate with model-visible records and private
  answers in separate artifacts. A new build identity replaces it; no in-place overwrite occurs.
  It is neither frozen nor permitted for treatment evaluation.
- `FROZEN` is a write-once copy of one independently revalidated PRIVATE candidate plus an exact
  affirmative approval, immutable receipt, and new operation record. Corrections require a new
  benchmark version.

Direct `SOURCE → FROZEN`, every downgrade, candidate overwrite, frozen overwrite, destination
collision, reused frozen version, stale approval, and hash mismatch fail. The writer stages beside
the final destination and atomically renames where supported. Staging failures are removed; a failed
post-publication validation is moved to a clearly invalid quarantine name. Filesystem read-only
flags are applied after successful publication as a convenience only. Application refusal,
manifests, logical hashes, and version identities provide the scientific guarantee.

## Source format, stable IDs, and revisions

M2.1 accepts exactly one source form:

```text
source_manifest.json
items.jsonl
```

The source manifest declares `canonical-jsonl-v1`, purpose, version, status flags, item count,
governance references, and optional prospective production prerequisite hashes. Items are strict,
frozen, extra-forbidden Pydantic records.

`item_id` is a persistent authored identity and is never derived from prompt text, answer position,
path, clock, host, or build directory. An intentional correction increments `item_revision` while
retaining `item_id`; a purpose change requires a new ID. A candidate contains at most one revision
of an ID. Model-visible changes alter its model-input hash; answer changes alter both the private
answer and complete-private-record hashes; metadata changes alter annotation and complete hashes.

Ordered option records carry stable IDs independent of text. At least two unique IDs and unique
normalised texts are required. `option_permutation` exactly names the displayed order. A reverse
group has exactly two distinct items/variants with the same option-ID set and exactly reversed
permutations.

Item and filesystem order, JSON mapping insertion order, CRLF/LF, absolute build location,
timestamps, and machine identity do not affect logical identity. Strings are newline-normalised and
Unicode NFC-normalised before canonical compact sorted-key JSON hashing. Generated JSON and JSONL
always use UTF-8 and LF.

## Artifact partitions

### Authoring source

Answer-bearing and mutable. `benchmarks/source/*` is ignored except its README.

### PRIVATE candidate

The mandatory files are:

```text
candidate_manifest.json
source_snapshot.json
resolved_benchmark_config.json
items.jsonl
private_answers.jsonl
public_manifest.json
coverage_summary.json
validation_report.json
resource_budget.json
operation_record.json
```

`source_snapshot.json` and `private_answers.jsonl` are answer-bearing. `items.jsonl` contains prompts,
options, annotations, provenance, validation metadata, and per-item logical hashes but no correct
option. All candidate descendants are private and ignored.

### Safe public metadata

Only `public_manifest.json` and `coverage_summary.json` are public views. They contain aggregate
identity, coverage, provenance posture, and bundle roots. They contain no prompts, options, correct
option IDs, answer indices, expected answers, gold labels, rationales, private validation notes,
per-item private-answer hashes, or complete-private-item hashes. Validation recursively scans keys
and values, compares them with every private answer and model-visible value, and fails closed.

A single private-answer bundle root may bind the complete private partition; per-item answer hashes
are never public because small answer spaces permit brute-force recovery.

### FROZEN private version

A frozen directory contains exact candidate artifacts plus:

```text
candidate_manifest.json
freeze_approval.json
immutable_receipt.json
freeze_resource_budget.json
freeze_operation.json
frozen_manifest.json
```

Every declared path is canonical run-relative POSIX form. Empty components, `.`/`..`, absolute
POSIX paths, Windows drive/absolute paths, backslashes, duplicates, missing files, and symlink escape
fail. Artifact-file SHA-256 and size are separate from logical scientific hashes.

## SHA-256 domains

M2.1 uses standard-library SHA-256 with an explicit `domain` frame:

| Logical identity | Domain suffix |
|---|---|
| Source snapshot | `source-snapshot/v1` |
| Model-visible item | `model-visible-item/v1` |
| Private answer record | `private-answer-record/v1` |
| Complete private item | `complete-private-item/v1` |
| Annotation/metadata | `annotation-metadata/v1` |
| Model-visible bundle | `model-visible-bundle/v1` |
| Private answer bundle | `private-answer-bundle/v1` |
| Annotation/metadata bundle | `annotation-metadata-bundle/v1` |
| Candidate bundle root | `candidate-bundle-root/v1` |
| Public metadata bundle | `public-metadata-bundle/v1` |
| Freeze approval | `freeze-approval/v1` |
| Frozen manifest | `frozen-manifest/v1` |

The complete domain prefix is `unfrozen-schemas/benchmark/`. Purpose, item identity/revision, or
benchmark version is included wherever applicable. Logical hashes never incorporate JSONL path,
artifact container metadata, operation time, or machine name. Ordinary artifact records separately
hash exact retained file bytes.

## Freeze approval

`freeze_approval.json` is strict and self-hashed. It binds:

- approval schema/class, version, purpose, and engineering status;
- exact candidate-manifest file SHA-256;
- candidate, private-answer, and public-metadata roots;
- exact `CODEX_SPEC.md` SHA-256 and clean Git commit;
- `PRIVATE → FROZEN` transition;
- rights/licensing, human-validation, and ethics/governance references;
- model-selection approval where production requires it;
- explicit M2.2 literal-item, M2.3 transfer-validation, M2.4 scoring/leakage/retention, M2.5
  hardware/model-selection, and owner-freeze prerequisite hashes;
- affirmative/rejected decision, signer, timezone-aware timestamp, and rationale.

Engineering approval is possible only for `engineering-benchmark-lifecycle-v1`, has class
`engineering_fixture`, uses explicit not-applicable governance states, and cannot carry production
or model-selection fields. Production freezing requires every item to have resolved rights,
licence, human-validation, adjudication, and ethics references. `v1_core` remains additionally
disabled in M2.1 until the separately implemented and reviewed M2.2–M2.5 evidence exists; M2.1 does
not create a production approval.

## Independent validation

Validation parses canonical typed records, requires exact schemas/lifecycle/artifact sets, resolves
paths safely, hashes exact files, reconstructs source/items/answers, recomputes every logical root,
checks correct-option references and reverse groups, reconstructs coverage/public views, scans for
answer leakage, verifies ResourceBudget v2 and operation provenance, and checks approval/receipt/
frozen-manifest chains. It never repairs an artifact or trusts stored hashes merely because they
agree with one another.

Cross-purpose comparison is explicit:

```text
uv run unfrozen validate-benchmark --manifest <manifest> \
  --against-manifest <other-manifest>
```

## Commands

```text
uv run unfrozen build-benchmark \
  --source tests/fixtures/benchmark_lifecycle/source \
  --output <isolated-private-destination> \
  --version engineering-benchmark-lifecycle-v1 \
  --purpose engineering

uv run unfrozen validate-benchmark --manifest <candidate_manifest.json>

uv run unfrozen create-engineering-freeze-approval \
  --candidate-manifest <candidate_manifest.json> \
  --output <engineering-approval.json> \
  --signer <non-production-reference>

uv run unfrozen freeze-benchmark \
  --candidate-manifest <candidate_manifest.json> \
  --approval <engineering-approval.json> \
  --output <isolated-frozen-destination>

uv run unfrozen validate-benchmark --manifest <frozen_manifest.json>
uv run unfrozen audit-benchmark-git
```

Build and freeze support `--dry-run`; dry-run writes nothing. Existing destinations, invalid source,
duplicates, leakage, corruption, unsafe paths, illegal transitions, missing/mismatched approvals,
and production-readiness failure return non-zero. Non-dry-run failures attempt to preserve a strict
sibling `BenchmarkOperationRecord` containing the original failure reason.

## Operation provenance and accounting

Every successful build/freeze embeds exact Git commit and dirty state, specification hash, resolved
configuration, logical input hashes, lifecycle states, version/purpose, item count, exact artifact
identities, package/platform metadata, start/end times, status/failure, and ResourceBudget v2.
Elapsed time uses `time.perf_counter`; peak memory means peak traced Python allocation from
`tracemalloc` or is unavailable with a reason; stored artifact count/bytes are derived from retained
hash-stable files. External language, self-generated language, sensor observations/bytes,
environment steps, forward/backward passes, and optimisation steps are truthfully observed zero.

## Engineering-fixture boundary and M2.6 prerequisites

The only M2.1 item data is `engineering-benchmark-lifecycle-v1` under `tests/fixtures/`. It is a
synthetic exact-code software test with no experimental vocabulary, target domain, published probe,
model, or scientific eligibility. Its hashes are regression-pinned but are not benchmark evidence.

M2.6 must not freeze `v1_core` until final contents/public-private policy, human validation,
ethics/governance, licensing, M2.4 evaluator/leakage/retention interfaces, M2.5 RTX 5070 hardware and
model-selection approval, and owner freeze approval are resolved and exact-hash bound. No M2.1
artifact authorises treatment evaluation.
