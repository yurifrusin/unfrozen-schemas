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
purpose requires a new authored record and new `item_id`. Every non-engineering source must declare
the complete canonical-root scan over `benchmarks/frozen`, `benchmarks/private`, and
`benchmarks/selection`; omitting any root is invalid. A build stores the canonical manifest paths,
exact manifest-file hashes, identities, item IDs, and purpose-neutral fingerprints in
`quarantine_scope.json`. The scope has its own logical SHA-256 and is bound into the candidate root,
candidate manifest, operation records, freeze approval, receipt, and frozen manifest.

Candidate validation re-scans every declared root. Missing/unreadable roots, malformed manifests,
added or removed external manifests, file changes, changed identities, or scope-hash mismatch fail
closed. Freeze performs the scan both before using the approval and immediately before publication.
Only the exact canonical candidate and its exact canonical FROZEN copy may be excluded as the
current lineage, so the lifecycle does not become self-referential. An arbitrary duplicate elsewhere
in a canonical root is never excluded, even if its IDs and candidate root match or its directory is
named like staging. During one atomic operation, validation may separately omit only the exact
unpublished sibling staging directory created by that operation; direct validation cannot request
that exception. Any other manifest added after construction makes the candidate stale and requires
a new candidate build identity. Engineering fixtures alone use an explicit `engineering_empty`
scope. `--against-manifest` remains a supplemental diagnostic and is never the mandatory quarantine.

Two separately domain-framed, purpose-neutral fingerprints prevent identity laundering:

1. `exact-displayed-input-fingerprint/v1` hashes normalised prompt, instructions, displayed
   normalised option texts in order, and closed/open-book eligibility;
2. `order-neutral-item-content-fingerprint/v1` hashes normalised prompt and instructions plus the
   sorted option-text multiset, excluding every item/option/pair/variant ID, purpose, and
   permutation field.

Equivalence normalises line endings, Unicode to NFC, whitespace, and case. Cross-purpose reuse is
therefore rejected after renamed IDs, changed pair metadata, reversed options, case-only changes, or
Unicode/whitespace presentation changes. Canonical placement is a necessary boundary for every
non-engineering artifact, while the hash-bound content scan remains the quarantine mechanism.

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

Non-engineering storage is exact and repository-relative:

| Purpose | PRIVATE candidate | FROZEN version in M2.1 |
|---|---|---|
| `outcome` | `benchmarks/private/<version>/candidate_manifest.json` | `benchmarks/frozen/<version>/frozen_manifest.json`, where otherwise authorised |
| `retention` | `benchmarks/private/<version>/candidate_manifest.json` | `benchmarks/frozen/<version>/frozen_manifest.json`, where otherwise authorised |
| `selection` | `benchmarks/selection/<version>/candidate_manifest.json` | refused for every selection version throughout M2.1 |
| `engineering` | isolated temporary directory permitted | isolated temporary directory permitted |

A non-engineering build with no `--output` derives this path from purpose and version. A supplied
output must resolve exactly to it. Direct validation, approval use, and freeze reject a candidate
copied or moved elsewhere; frozen validation likewise requires the exact canonical frozen path.
Paths are operational checks only and never enter manifests or logical hashes.

Direct `SOURCE → FROZEN`, every downgrade, candidate overwrite, frozen overwrite, destination
collision, reused frozen version, stale approval, and hash mismatch fail. The writer stages beside
the final destination and atomically renames where supported. Staging failures are removed. A failed
PRIVATE post-publication read-back is moved to a candidate-specific `invalid-private` sibling, while
a failed FROZEN read-back uses `invalid-frozen`; if movement fails, removal is the fail-closed
fallback. Filesystem read-only flags are applied after successful FROZEN publication as a
convenience only. Application refusal, manifests, logical hashes, and version identities provide the
scientific guarantee.

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
permutations. Its canonical `reverse-pair-identity/v1` payload requires equal purpose and benchmark
classification, prompt/instructions, stable option-ID-to-normalised-text mapping, task/transfer/
schema/domain/mechanism/template/partition metadata, book eligibility, scientific annotations,
human-validation record, correct stable option ID, answer provenance, and substantive answer
evidence. The only permitted differences are item/source-record IDs, variant ID, displayed option
order and its exact reversed permutation, plus exactly one `reversed option presentation`
transformation-history entry. `created_from_source_record` is the sole provenance exception; every
other provenance field remains equal.

Item and filesystem order, JSON mapping insertion order, CRLF/LF, absolute build location,
timestamps, and machine identity do not affect logical identity. Strings are newline-normalised and
Unicode NFC-normalised before canonical compact sorted-key JSON hashing. Generated JSON and JSONL
always use UTF-8 and LF.

## Artifact partitions

### Authoring source

Answer-bearing and mutable. `benchmarks/source/*` is ignored except its README.

### PRIVATE candidate

Outcome and retention candidates exist only under `benchmarks/private/<version>`. Selection
candidates exist only under `benchmarks/selection/<version>`. Arbitrary non-engineering manifests
are rejected because they are outside the complete repository quarantine universe scanned by every
candidate capable of approval or freeze. Engineering fixtures remain temporary-path capable.

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
quarantine_scope.json
```

`source_snapshot.json` and `private_answers.jsonl` are answer-bearing. `items.jsonl` contains prompts,
options, annotations, provenance, validation metadata, and per-item logical hashes but no correct
option. All candidate descendants are private and ignored.

### Safe public metadata

Only `public_manifest.json` and `coverage_summary.json` are public views. They contain aggregate
identity, coverage, provenance posture, and bundle roots. They contain no prompts, options, correct
option IDs, answer indices, expected answers, gold labels, rationales, private validation notes,
per-item private-answer hashes, or complete-private-item hashes. Validation recursively visits every
mapping key, scalar mapping value, scalar sequence member, and arbitrarily nested mapping/sequence
combination. It normalises Unicode, line endings, whitespace, and case before comparing exact and
embedded values from prompts, instructions, all option IDs/texts, pair/variant/permutation IDs,
answers/evidence/adjudication references, and per-item logical hashes. Renamed answer-equivalent
keys also fail. The aggregate private-answer bundle root is the only permitted answer-derived public
identity.

A single private-answer bundle root may bind the complete private partition; per-item answer hashes
are never public because small answer spaces permit brute-force recovery.

### FROZEN private version

Every non-engineering frozen version must be exactly
`benchmarks/frozen/<version>/frozen_manifest.json`. M2.1 refuses every `selection`-purpose freeze,
not only `selection_probe_v1`, and continues to refuse production `v1_core`.

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
| Exact displayed input fingerprint | `exact-displayed-input-fingerprint/v1` |
| Order-neutral item-content fingerprint | `order-neutral-item-content-fingerprint/v1` |
| Reverse-pair identity | `reverse-pair-identity/v1` |
| Mandatory quarantine scope | `quarantine-scope/v1` |

The complete domain prefix is `unfrozen-schemas/benchmark/`. Purpose, item identity/revision, or
benchmark version is included wherever applicable. Logical hashes never incorporate JSONL path,
artifact container metadata, operation time, or machine name. Ordinary artifact records separately
hash exact retained file bytes.

## Freeze approval

`freeze_approval.json` is strict and self-hashed. It binds:

- approval schema/class, version, purpose, and engineering status;
- exact candidate-manifest file SHA-256;
- candidate, private-answer, and public-metadata roots;
- exact mandatory quarantine-scope identity;
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
not create a production approval. Every selection-purpose freeze is independently disabled across
M2.1; M2.5 must define and review its eventual selection-freeze procedure.

## Independent validation

Validation parses canonical typed records, requires exact schemas/lifecycle/artifact sets, resolves
paths safely, hashes exact files, reconstructs source/items/answers, recomputes every logical root,
checks correct-option references and reverse groups, reconstructs coverage/public views, scans for
answer leakage, verifies ResourceBudget v2 and operation provenance, and checks approval/receipt/
frozen-manifest chains. It never repairs an artifact or trusts stored hashes merely because they
agree with one another.

The source-snapshot header and candidate manifest must exactly agree on version, purpose, all three
classification flags, item count, governance references, and production prerequisites; every item
must agree with the candidate flags. Engineering and non-engineering origin, answer-provenance, and
governance classifications are mutually exclusive. Build operation validation requires exact Git,
specification, resolved configuration, lifecycle, identity, flags, item count, and the exact
`source_snapshot_sha256`/`quarantine_scope_sha256` input-key set. Freeze operation validation requires
the analogous exact candidate/approval/scope input set. Standalone resource-budget files must be
byte-canonical ResourceBudget JSON, not merely semantically equal JSON.

Optional supplemental cross-purpose comparison remains available:

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

For prospective non-engineering sources, omit `--output` to derive the canonical destination or
supply only that exact destination. Outcome/retention resolve below `benchmarks/private`; selection
resolves below `benchmarks/selection`. Engineering commands continue to require explicit isolated
outputs.

Build and freeze support `--dry-run`; dry-run writes nothing. Existing destinations, invalid source,
duplicates, leakage, corruption, unsafe paths, illegal transitions, missing/mismatched approvals,
and production-readiness failure return non-zero. Non-dry-run failures attempt to preserve a strict
sibling `BenchmarkOperationRecord` containing the original failure reason.

All CLI `--version` values are validated as one lowercase slug before path construction. Version
resolution starts at the repository root and considers the private, selection, and frozen canonical
locations. A selection candidate resolves below `benchmarks/selection`; a compatible private/frozen
pair resolves to its FROZEN manifest. Incompatible duplicates across roots or purposes fail as
ambiguous rather than being guessed. Traversal, slash/backslash, absolute, drive-qualified, empty,
and dot forms fail before filesystem access. `audit-benchmark-git` uses an exact allowlist: the five
reviewed benchmark README files are the only tracked `benchmarks/` paths in M2.1. Every other tracked
file fails regardless of name, extension, or forced-add status.

## Operation provenance and accounting

Every successful build/freeze embeds exact Git commit and dirty state, specification hash, resolved
configuration, logical input hashes, lifecycle states, version/purpose, item count, exact artifact
identities, package/platform metadata, start/end times, status/failure, and ResourceBudget v2.
Elapsed time uses `time.perf_counter`; peak memory means peak traced Python allocation from
`tracemalloc` or is unavailable with a reason; stored artifact count/bytes are derived from retained
hash-stable files. External language, self-generated language, sensor observations/bytes,
environment steps, forward/backward passes, and optimisation steps are truthfully observed zero.

Build and freeze both track atomic publication explicitly. Any non-advisory exception after staging
is moved to the requested destination moves it to a type-correct `invalid-private` or
`invalid-frozen` sibling; if the move itself fails, generated output is removed as the final
fail-closed fallback. The original exception remains the primary failure and cleanup diagnostics are
secondary. Final read-back occurs after publication. Filesystem read-only application is advisory
and its failure cannot turn an otherwise valid FROZEN publication into a reported failed operation.

## Engineering-fixture boundary and M2.6 prerequisites

The only M2.1 item data is `engineering-benchmark-lifecycle-v1` under `tests/fixtures/`. It is a
synthetic exact-code software test with no experimental vocabulary, target domain, published probe,
model, or scientific eligibility. Its hashes are regression-pinned but are not benchmark evidence.

M2.6 must not freeze `v1_core` until final contents/public-private policy, human validation,
ethics/governance, licensing, M2.4 evaluator/leakage/retention interfaces, M2.5 RTX 5070 hardware and
model-selection approval, and owner freeze approval are resolved and exact-hash bound. No M2.1
artifact authorises treatment evaluation.
