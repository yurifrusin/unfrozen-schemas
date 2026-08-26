# M2.2 literal and counterfactual benchmark candidate

This document defines the Milestone 2 work-package M2.2 implementation. `CODEX_SPEC.md` remains
authoritative. M2.2 creates a private review candidate and the offline software needed to generate,
replay, audit, and inspect it. It does not freeze `v1_core`, score a model, run a treatment, recruit
validators, approve rights or ethics, or report a scientific result.

## Scientific boundary

M2.2 covers only literal physical CONTAINMENT and SUPPORT tasks using released SchemaWorld Core
dynamics. Every semantic group has exactly two option-order variants and one independently replayed
actual/counterfactual witness. L1 means held-out literal prediction within the released mechanisms.
L2 requires structural novelty beyond a new identity or seed and is partitioned into novel-template,
novel-configuration, or physical-mechanism-transfer strata.

The following remain outside M2.2:

- abstract and metaphorical L3/L4 content (M2.3);
- likelihood scoring, score averaging, treatment-corpus leakage, and retention (M2.4);
- model, tokenizer, adapter, CUDA, GPU, or hardware qualification (M2.5);
- human validation, ethics approval, rights clearance, production approval, and `v1_core` freezing
  (M2.6 or another separately authorised task);
- any Phase I gate status or empirical LLM claim.

The prospective adaptation strata, semantic-group IDs, and prompt-template IDs are reserved before
treatment authoring. M2.2 records future treatment overlap as `not_assessed_m2_2`; it never treats an
empty field as evidence that overlap was checked.

## Private storage and execution order

The outcome review candidate is `m2-2-literal-candidate-v1` with purpose `outcome`. Its ignored local
roots are:

```text
benchmarks/source/m2-2-literal-candidate-v1
benchmarks/private/m2-2-literal-candidate-v1
reports/private/m2-2-literal-candidate-v1
```

The private authoring manifest is
`benchmarks/source/m2-2-literal-candidate-v1/literal_authoring.json`. It contains typed scenario facts
and the private prompt-template registry. Neither it nor rendered prompts, options, answers,
witnesses, review records, or renders may be committed, printed in a pull request, uploaded as CI
artifacts, copied to Downloads, or copied into another worktree.

Tracked implementation, tests, configuration, and documentation must be final, committed, pushed,
clean, and CI-green before real source generation. If a tracked file changes afterwards, the private
source, M2.1 candidate, composite identity, and review bundle are stale and must be regenerated from
the new clean head. The final private artifacts are retained locally for owner review.

## Structured authoring and rendering

`LiteralAuthoringManifest` separates typed scenario facts from model-visible wording. Templates may
interpolate only `scene_description`, `actual_action_description`, and
`counterfactual_action_description`; conversions, format specifications, and unknown placeholders
are rejected. The generator is deterministic and never calls an LLM.

Model-visible content is rejected if it contains raw entity/boundary/opening/tether IDs, 64-character
hashes, raw four-digit coordinates, privileged machine schema labels, transition fields, or abstract/
metaphorical target-domain vocabulary. The private outcome wording may use necessary natural
physical terms, but reviewed cue annotations and structural balance are mandatory.

## Source and lifecycle composition

The generated source retains the exact M2.1-supported `source_manifest.json` plus `items.jsonl` form.
M2.2 records are stored beneath the private `.literal` sidecar directory, so M2.1 models and logical
domains are unchanged. The existing M2.1 builder creates the exact mandatory PRIVATE artifact set;
M2.2 does not add files to that candidate directory.

Each M2.1 source item records immutable purpose, reverse-pair identity, transfer level, partition,
source mechanism, stable option IDs, private simulator answer, and governance status. Outcome items
are simulator-derived, scientifically intended candidate content but non-promotable. Rights and
ethics remain unresolved, human validation is `not_started` with zero validators, adjudication is
`not_started`, and external overlap is `not_assessed_m2_2`.

## Witness and independent verification

One `LiteralWitnessRecord` binds every semantic group to both item IDs, explicit schema, level,
family, mechanism, prompt template, partition, seeds, actual and counterfactual states/actions,
observations, transitions, relations, declared differences, outcome codes, stable correct option,
and witness hash.

Validation does not trust the stored answer. It reparses typed Core records, independently calls the
released transition engine, derives relations, reconstructs state/action/observation/transition
hashes, checks the exact declared state and action differences, requires equal horizons and differing
outcomes, derives the stable outcome and correct option, verifies both reverse variants, and requires
each M2.1 private answer and simulator reference to match. Mutation of any bound field fails.

## Cue and split audits

The deterministic lexical audit normalises Unicode, line endings, whitespace, and case; checks raw
identifier/hash/coordinate exclusion, option length and answer-position balance, exact and near
duplicates, template/action/mechanism answer classes, and per-family token/outcome associations.
Necessary causal terms that perfectly associate in a small declared family are retained as explicit
`reviewed-causal` findings rather than silently erased. Integrity failures fail generation.

The split audit binds L1/L2 membership, structural novelty dimensions, unique state/action/witness
identities, duplicate prompts, and the explicit pending future-treatment overlap status. L2 records
whose novelty is only a new entity name or seed are invalid.

## Hash chain

M2.2 uses separate domains for partition plans, templates and the private registry, item bindings,
witnesses, lexical and split audits, validation reports, review content, review manifests, the
composite candidate root, and operation records. Logical identities exclude absolute paths,
timestamps, machine/platform fields, filesystem ordering, and render-container metadata.

The composite root binds the M2.1 candidate root, source snapshot, private-answer/public/quarantine
roots, M2.2 source bundle, partition/registry/binding/witness/audit/report roots, and logical review
content. The exact M2.1 candidate-manifest file hash and Git state are retained in the composite
record for owner review but are excluded from its cross-platform logical hash; owner approval must
bind those operational facts separately.

The review manifest independently binds the composite root, validation and witness roots, logical
review content, and the exact file hash/size of every retained review file other than the necessarily
self-referential manifest itself. PNGs are inspection aids and do not define scientific state.

## Status semantics

A successful composite report is
`CANDIDATE_VALIDATED_OWNER_REVIEW_PENDING`. It explicitly records simulator correctness,
counterfactual parity, split integrity, reverse equivalence, lexical and option balance, provenance,
M2.1 validation, pending external overlap, pending human validation/rights/ethics, and
`freeze_eligibility=false`.

It is not `FROZEN`, `EVALUATION_READY`, `HUMAN_VALIDATED`, `V1_CORE_APPROVED`, a scientific result, or
a Phase I pass. M2.2 does not create `literal_items_approval_sha256`.

## Commands

Outcome candidate commands use canonical paths:

```powershell
uv run unfrozen generate-literal-source `
  --config configs/evaluation/m2_2_literal_candidate.yaml
uv run unfrozen validate-literal-source `
  --source benchmarks/source/m2-2-literal-candidate-v1
uv run unfrozen build-benchmark `
  --source benchmarks/source/m2-2-literal-candidate-v1 `
  --version m2-2-literal-candidate-v1 `
  --purpose outcome
uv run unfrozen validate-benchmark --version m2-2-literal-candidate-v1
uv run unfrozen validate-literal-benchmark --version m2-2-literal-candidate-v1
uv run unfrozen build-literal-review `
  --version m2-2-literal-candidate-v1 `
  --output reports/private/m2-2-literal-candidate-v1
uv run unfrozen validate-literal-review `
  --source benchmarks/source/m2-2-literal-candidate-v1 `
  --review reports/private/m2-2-literal-candidate-v1
```

Generation supports `--dry-run` and refuses generated-file overwrite. Validation is read-only and
idempotent except that the first composite validation persists its derived report, composite record,
and operation provenance beside the private source; subsequent runs reconstruct and compare them
without change. Default command output is aggregate-only. `inspect-literal-item` requires an exact
private item ID and intentionally discloses that one local record; `--render` must be paired with an
explicit output path.

## Operation accounting

Generation, composite validation, and review build retain exact Git/spec/configuration/input/output,
artifact, package, platform, timing, and ResourceBudget v2 records. SchemaWorld transitions and
primary observations are measured. Stored artifacts are derived. External/self-generated language
tokens, optimisation steps, forward passes, and backward passes are observed zero. Deterministic
template rendering is not LLM-generated language.

## Engineering fixture

`tests/fixtures/literal_benchmark/authoring.json` is deliberately non-scientific and non-promotable.
Its visible text uses synthetic panels, codes, tokens, and status labels, while internal temporary
states exercise both Core schemas, L1/L2 partitions, actual/counterfactual replay, reverse options,
audits, the M2.1 builder/validator, composite validation, review rendering, and manifest read-back.
CI runs entirely on CPU with network, model, GPU, and secrets disabled. Its pinned identities are
software regressions only and cannot support a scientific claim.

## Owner review

The ignored review bundle contains aggregate summary, per-group private review records, audits,
candidate validation, witnesses, before/after renders, and a checklist. Owner approval must identify
the exact pull request and head SHA, exact M2.1 candidate-manifest file hash, M2.1 candidate root,
M2.2 composite root, source snapshot, witness root, validation-report root, and review-manifest hash.
Approval cannot substitute for later human validation, rights/ethics decisions, M2.3-M2.5, or M2.6.
