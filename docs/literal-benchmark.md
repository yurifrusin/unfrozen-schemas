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
treatment authoring. The retained snapshot also declares the complete prospective adaptation-source
mechanism-signature set. M2.2 records future treatment overlap as `not_assessed_m2_2`; it never
treats an empty field as evidence that overlap was checked.

## Private storage and execution order

The outcome review candidate is `m2-2-literal-candidate-v1` with purpose `outcome`. Its ignored local
roots are:

```text
benchmarks/source/m2-2-literal-candidate-v1
benchmarks/private/m2-2-literal-candidate-v1
reports/private/m2-2-literal-candidate-v1
```

The private authoring manifest is
`benchmarks/source/m2-2-literal-candidate-v1/literal_authoring.json`. It contains typed scenario
selectors, an explicit typed outcome-text registry, and a closed prompt-renderer registry. Neither
it nor rendered prompts, options, answers,
witnesses, review records, or renders may be committed, printed in a pull request, uploaded as CI
artifacts, copied to Downloads, or copied into another worktree.

Tracked implementation, tests, configuration, and documentation must be final, committed, pushed,
clean, and CI-green before real source generation. If a tracked file changes afterwards, the private
source, M2.1 candidate, composite identity, and review bundle are stale and must be regenerated from
the new clean head. The final private artifacts are retained locally for owner review.

## Structured authoring and rendering

`LiteralAuthoringManifest` contains no authoritative free-form scene, action, causal-factor,
mechanism, or positive/negative option convention. Scenario cases select prospective intervention
contracts; Core state/action records derive narrative facts and outcomes; each option-text record is
explicitly mapped to one typed outcome code. Closed versioned renderers accept only reconstructed
`LiteralNarrativeFacts`. The generator is deterministic and never calls an LLM.

The renderer uses the constant neutral referent `the object` in prompts and options. Scene labels
remain private authoring metadata and are never model-visible. Natural questions do not announce
held-out, novel, or transfer status. Physical analogy prompts state a source causal episode and ask
for the outcome in a distinct target episode; they do not state the target mechanism as the answer.
All option pairs use prospectively parallel sentence form, punctuation, modality, and closely
matched whitespace length. Tokenizer-specific length checks remain an explicit pending M2.4 duty.

Model-visible content is rejected if it contains raw entity/boundary/opening/tether IDs, 64-character
hashes, raw four-digit coordinates, privileged machine schema labels, transition fields, or abstract/
metaphorical target-domain vocabulary. The private outcome wording may use necessary natural
physical terms, but reviewed cue annotations and structural balance are mandatory.

## Source and lifecycle composition

The generated source retains the exact M2.1-supported `source_manifest.json` plus `items.jsonl` form.
M2.2 records are stored beneath the private `.literal` sidecar directory, including a canonical
retained authoring snapshot with separate logical and exact-file identities. M2.1 models and logical
domains are unchanged. The existing M2.1 builder creates the exact mandatory PRIVATE artifact set;
M2.2 does not add files to that candidate directory.

Each M2.1 source item records immutable purpose, reverse-pair identity, transfer level, partition,
source mechanism, stable option IDs, private simulator answer, and governance status. Outcome items
are simulator-derived, scientifically intended candidate content but non-promotable. Rights and
ethics remain unresolved, human validation is `not_started` with zero validators, adjudication is
`not_started`, and external overlap is `not_assessed_m2_2`.

## Witness and independent verification

One `LiteralWitnessRecord` binds every semantic group to both item IDs, explicit schema, level,
family, separate typed source and target mechanisms, prompt template, partition, intervention
contract, structural signatures,
reconstructed narrative facts, seeds, actual and counterfactual states/actions, observations,
transitions, relations, observed differences, outcome codes, stable correct option, and witness hash.

Validation does not trust the stored answer. It reparses typed Core records, independently calls the
released transition engine, derives relations, reconstructs state/action/observation/transition
hashes, checks every difference against a case-specific prospective allowlist, requires exact equality
outside that allowlist, equal declared horizons, and the prospective outcome change, reconstructs
narrative and structural signatures, derives the stable outcome and correct option, verifies both
reverse variants, and requires each M2.1 private answer and simulator reference to match. Mutation of
any bound semantic field fails even when affected hashes are refreshed.

## Cue and split audits

The deterministic lexical audit normalises Unicode, line endings, whitespace, and case; checks raw
identifier/hash/coordinate exclusion, option length and answer-position balance, exact and near
duplicates, template/action/source-mechanism/target-mechanism answer classes, and per-family
token/outcome associations. Every association records occurrence support, semantic-group support,
answer-class counts, and enumerated item/group membership. Support-one observations remain recorded
but do not require individual owner acceptance. Versioned categories distinguish necessary causal
vocabulary, task/meta vocabulary, nuisance identifiers, answer-correlated wording, and duplicate or
near-duplicate wording. Each category binds its sorted finding IDs with a reconstructible membership
hash; category-level disposition is permitted only for that exact membership. Consequential
findings remain item-addressable. Prompt length and option length/style are compared by correct
answer class. Integrity failures fail generation.

The split audit requires exact L1/L2 state, observation, action, group, and witness identities to be
disjoint. Seed-, noise-, entity-ID-, and filesystem-independent signatures cover world topology,
qualitative geometry, actions, counterfactual intervention, mechanism mapping, templates,
observation structure, target causal scenario, order-independent structural stratum, and combined
witness configuration. Novel templates are withheld from L1;
novel configurations have a qualitative signature absent from L1; physical analogies change the
declared mechanism mapping relative to their same-schema L1 reference. Every L2 mechanism-transfer
target is rejected if its target signature occurs anywhere in the complete L1 or prospective
adaptation-source prohibited sets. Repeated causal scenarios require one explicit matched stratum.
The audit reports question groups, unique causal scenarios, independent structural strata,
cross-family matched variants, and same-family cosmetic variants separately. Only genuine causal
scenarios and declared cross-family variants satisfy the scientific coverage floors; cosmetic
repeats do not. Future treatment overlap remains `not_assessed_m2_2`.

## Hash chain

M2.2 uses separate domains for the retained authoring snapshot, structural signatures, partition
plans, templates and the private registry, item bindings, witnesses, lexical and split audits,
validation reports, review content, review manifests, the composite candidate root, and operation
records. Logical identities exclude absolute paths,
timestamps, machine/platform fields, filesystem ordering, and render-container metadata.

The composite root binds the M2.1 candidate root, source snapshot, private-answer/public/quarantine
roots, M2.2 source bundle, partition/registry/binding/witness/audit/report roots, and logical review
content. The exact M2.1 candidate-manifest file hash and Git state are retained in the composite
record for owner review but are excluded from its cross-platform logical hash; owner approval must
bind those operational facts separately.

The review manifest independently binds the composite root, snapshot, source-generation,
candidate-materialisation and review operations, validation and witness roots, logical review
content, four full-frame scientific renders plus four review zooms per group, and the exact hash/size
of every retained review file
other than the necessarily self-referential manifest itself. Review validation decodes every PNG as
128x128 RGB and requires its pixels and raw-pixel identity to reconstruct independently. Full-frame
scientific identities remain unchanged. Each zoom adds deterministic connection geometry, crops and
nearest-neighbour magnifies the inspectable scene, and binds its raw identity to the source full
frame. PNG exact container hashes remain separate from raw-pixel logical identities.

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
uv run unfrozen materialize-literal-candidate --version m2-2-literal-candidate-v1
uv run unfrozen validate-literal-benchmark --version m2-2-literal-candidate-v1
uv run unfrozen build-literal-review `
  --version m2-2-literal-candidate-v1 `
  --output reports/private/m2-2-literal-candidate-v1
uv run unfrozen validate-literal-review `
  --source benchmarks/source/m2-2-literal-candidate-v1 `
  --review reports/private/m2-2-literal-candidate-v1
```

Generation supports `--dry-run` and refuses generated-file overwrite. Candidate materialisation is
an explicit write-once operation. Every `validate-*` command is strictly read-only and repeated
validation reconstructs and compares without creating or editing a file. Source generation,
candidate materialisation, and review construction stage complete sibling artifacts, validate before
publication, publish, and perform final read-back; fatal post-publication failures quarantine or
remove the requested output while retaining a governed failure record. Default command output is
aggregate-only. `inspect-literal-item` requires an exact
private item ID and intentionally discloses that one local record; `--render` must be paired with an
explicit output path.

## Operation accounting

Generation, candidate materialisation, and review build retain exact Git/spec/configuration/input/output,
artifact, package, platform, timing, and ResourceBudget v2 records. SchemaWorld transitions and
primary observations are measured. Stored artifacts are derived. External/self-generated language
tokens, optimisation steps, forward passes, and backward passes are observed zero. Deterministic
template rendering is not LLM-generated language.

## Engineering fixture

`tests/fixtures/literal_benchmark/authoring.json` is deliberately non-scientific and non-promotable.
Its visible text uses synthetic setup and result terms, while internal temporary
states exercise both Core schemas, L1/L2 partitions, actual/counterfactual replay, reverse options,
audits, the M2.1 builder/validator, composite validation, review rendering, and manifest read-back.
CI runs entirely on CPU with network, model, GPU, and secrets disabled. Its pinned identities are
software regressions only and cannot support a scientific claim.

## Owner review

The ignored review bundle contains aggregate summary, per-group private review records, audits,
candidate validation, witnesses, four full-frame and four zoom renders per group, a category-bound
cue-disposition template, and a checklist.
Owner approval must identify the exact pull request and head SHA; exact authoring snapshot/file;
source-generation, candidate-materialisation, and review-operation hashes; exact M2.1 candidate
manifest and candidate root; M2.2 composite, source snapshot, witness and validation roots; and both
the logical review-manifest root and its exact file hash.
Approval cannot substitute for later human validation, rights/ethics decisions, M2.3-M2.5, or M2.6.
