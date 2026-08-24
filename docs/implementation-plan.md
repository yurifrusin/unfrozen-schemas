# Implementation plan: Milestones 0-4

This plan translates Revision 6 into dependency-ordered, reviewable work packages. Only the active
milestone may be implemented. Milestones 5-10 are roadmap items, not executable work packages.

Phase I is a permanent scientific result and mandatory gate, not a disposable prototype. Its hard
gate criteria concern literal causal learning, held-out transfer, causal-versus-shuffled separation,
language retention, leakage control, reproducibility, complete seed accounting, and provenance.
L3 abstract and L4 metaphor transfer are reported but non-gating. `text_oracle` outperforming a
sensor condition does not cause Phase I to fail. Literal L1/L2 learning without distant linguistic
transfer is a scientifically meaningful compartmentalisation result and a primary motivation for
Phase II. Phase II and Phase III cannot begin merely because their architectures are attractive.

The governance set also includes `PROJECT_HISTORY.md`, `RESEARCH_LOG.md`,
`docs/release-and-archive-process.md`, and `docs/document-ingest-workflow.md`. `origin/main` is the
canonical public history; work on a feature branch is not a completed milestone.

## Cross-cutting Milestone 0-10 closeout gate

The final acceptance section for every Milestone 0-10 incorporates this sequence by reference. A
milestone is not complete, and the next milestone is not authorised, until all steps finish:

1. complete the scoped work on its dedicated branch and inspect the complete diff;
2. push the branch and open or update a pull request into `main`;
3. require declared CI checks and human review;
4. merge the reviewed result into `origin/main`;
5. synchronise local `main` using a fast-forward-only pull and verify a clean matching commit;
6. create the immutable annotated engineering tag `milestone-N-complete`;
7. push the tag explicitly;
8. publish a GitHub Release containing the exact commit, specification hash, CI result, scope,
   limitations, artifact hashes, advancement decision, and next authorised work;
9. ensure `PROJECT_HISTORY.md` and `RESEARCH_LOG.md` are current; and
10. begin the next milestone only from the tagged canonical commit.

Engineering milestone tags remain distinct from scientific checkpoint tags such as
`benchmark-v1-core-frozen`, `phase1-preregistered-v1`, and `phase1-gate-v1`. Published tags are
immutable; corrections receive a new correction tag and release.

## Milestone 0: repository foundation

### M0.1 — Governance and scientific guardrails

- **Objective:** Encode the enduring scientific, artifact, gate, and engineering rules before code
  is introduced.
- **Dependencies:** Revision 6 specification read in full; clean repository preflight.
- **Files:** `AGENTS.md`, `docs/scientific-design.md`, `docs/implementation-plan.md`,
  `docs/budget-accounting.md`, `docs/phase-gate-protocol.md`, `docs/open-questions.md`,
  `PROJECT_HISTORY.md`, `RESEARCH_LOG.md`, `docs/release-and-archive-process.md`, and
  `docs/document-ingest-workflow.md`.
- **Implementation steps:** Summarise the three phases; define the transfer ladder, accounting, gate
  semantics, invalidation, workflow, and only genuinely unresolved decisions.
- **Acceptance tests:** Manual cross-check against all specification sections; verify L3/L4 never
  appear among hard-gate inputs; verify each requested governance file exists.
- **Scientific invariants:** Phase I remains permanent and mandatory; all named controls and
  comparisons remain explicit; unresolved decisions are not guessed.
- **Artifacts:** Reviewed Markdown governance set.
- **Failure modes and risks:** Accidentally weakening a requirement, treating a null L3/L4 result as
  failure, or turning settled requirements into open questions.
- **Completion criteria:** The governance set is internally consistent and faithful to Revision 6.
- **Stop conditions:** Any conflict within the specification or any proposed narrowing of the
  controlled design requires owner review.

### M0.2 — Package, dependency, and repository scaffold

- **Objective:** Establish a Python 3.11 `uv` project with a `src` layout and safe artifact
  boundaries.
- **Dependencies:** M0.1.
- **Files:** `pyproject.toml`, `uv.lock`, `.python-version`, `.gitignore`, `.env.example`,
  `README.md`, `.github/workflows/ci.yml`, `src/unfrozen_schemas/__init__.py`, `py.typed`, tracked
  placeholders under `runs/` and `reports/`, and configuration/test directories.
- **Implementation steps:** Define runtime and development dependencies; expose the `unfrozen`
  entry point; configure Ruff and strict mypy; pin the lock; ignore secrets, weights, datasets,
  checkpoints, logs, builds, and ordinary runs while retaining deterministic fixtures and frozen
  metadata.
- **Acceptance tests:** `uv sync --locked`; import package; inspect `git check-ignore` samples; ensure
  `.env.example`, fixtures, source, tests, and frozen configuration remain trackable.
- **Scientific invariants:** No cloud tracker, secret, model download, scientific dynamics, or
  mutable benchmark is introduced.
- **Artifacts:** Reproducible dependency environment and reviewable repository skeleton.
- **Failure modes and risks:** Broad ignore patterns hide scientific metadata; unconstrained
  dependencies make the lock irreproducible; heavy model packages make CPU CI impractical.
- **Completion criteria:** A clean Python 3.11 environment installs from `uv.lock` and exposes the
  CLI.
- **Stop conditions:** Licence selection or inclusion of licensed data requires owner review.

### M0.3 — Validated, layered smoke configuration

- **Objective:** Make all Milestone 0 behaviour configuration-driven and fail closed on unsupported
  scientific or hardware settings.
- **Dependencies:** M0.2.
- **Files:** `src/unfrozen_schemas/config.py`, `configs/experiment/smoke.yaml`,
  `configs/model/tiny_random.yaml`, configuration tests.
- **Implementation steps:** Define strict Pydantic models; load YAML safely; resolve repository-
  relative paths; pin and validate the tiny fixture hash; require CPU, offline, secret-free,
  engineering-only execution.
- **Acceptance tests:** Valid configuration resolves; missing files, unknown keys, invalid seeds,
  online mode, CUDA, and a fixture hash mismatch fail with clear errors.
- **Scientific invariants:** Smoke artifacts are never publishable Phase II evidence; model and run
  choices are not hard-coded into the runner.
- **Artifacts:** Canonical resolved configuration serialisable to JSON.
- **Failure modes and risks:** Machine-specific paths leak into tracked files; permissive validation
  silently accepts misspelled fields.
- **Completion criteria:** All declared settings validate before work begins and the resolved form is
  written into each run.
- **Stop conditions:** Adding a real model, network dependency, secret, or scientific condition is
  outside Milestone 0.

### M0.4 — Provenance, budget, and artifact models

- **Objective:** Produce complete, serialisable records for every successful or failed toy run.
- **Dependencies:** M0.3.
- **Files:** `src/unfrozen_schemas/provenance.py`, `src/unfrozen_schemas/budgets.py`,
  `src/unfrozen_schemas/smoke.py`, related unit tests.
- **Implementation steps:** Implement deterministic run-ID construction with injectable inputs;
  seed handling; Git commit/dirty capture; platform, Python, and installed-package capture; canonical
  JSON; SHA-256 artifact records; required budget fields; placeholder gate metadata; manifest start,
  success, and failure states; and an explicit bootstrap-failure record for failures before a valid
  initial `RUNNING` manifest exists.
- **Acceptance tests:** Round-trip every model; test clean and dirty temporary Git repositories;
  test deterministic seeds and IDs; ensure bootstrap and started-run failures retain the original
  reason, the strongest valid record, partial artifacts, and partial accounting.
- **Scientific invariants:** Dirty state is never suppressed; external/self-generated language,
  sensor, environment, and compute fields remain separate; placeholder gate data cannot authorise
  Phase II.
- **Artifacts:** Versioned JSON schemas embodied by strict Pydantic models.
- **Failure modes and risks:** Self-referential hashes, nondeterministic serialisation, missing
  failure manifests, or confusing `NOT_EVALUATED` with a gate status.
- **Completion criteria:** Manifests contain all required provenance, inline resource totals,
  artifact hashes, statuses, and failure information.
- **Stop conditions:** Any request to manufacture an approval or omit dirty/failure provenance.

### M0.5 — Offline smoke runner and CLI

- **Objective:** Make `uv run unfrozen smoke` exercise the complete Milestone 0 path on CPU.
- **Dependencies:** M0.3-M0.4.
- **Files:** `src/unfrozen_schemas/cli.py`, `src/unfrozen_schemas/smoke.py`, structured logging module,
  `tests/fixtures/tiny_random_model.json`, integration tests.
- **Implementation steps:** Capture provenance before run creation; load the local fixture; make one
  deterministic tiny forward pass; create
  an isolated run directory; write resolved config, toy output, budget ledger, placeholder gate
  metadata, JSONL logs, and final provenance manifest; protect every operation after directory
  creation; print a concise summary; preserve a complete failure manifest for started runs or an
  explicit validated bootstrap record when a complete manifest is not valid.
- **Acceptance tests:** CLI exits zero offline without CUDA, secrets, downloads, or network; expected
  files exist and hashes match; repeated seeded model computation agrees; one-shot initial writes,
  logging setup, initial-manifest construction, fixture failures, and secondary recording failures
  exit non-zero without masking the original cause or claiming an invalid artifact.
- **Scientific invariants:** The fixture is engineering-only and implements no SchemaWorld dynamics,
  treatment generation, LoRA, active agent, projector, Phase II experiment, or colony component.
- **Artifacts:** Complete ignored `runs/<run-id>/` toy run.
- **Failure modes and risks:** Hidden network access, stale artifact hashes, incomplete failure paths,
  or accidental dependence on the current machine.
- **Completion criteria:** The exact required command terminates successfully with complete,
  validated artifacts and resource accounting.
- **Stop conditions:** Real model loading, CUDA, or scientific data generation requires a later
  milestone and owner review.

### M0.6 — Verification and CPU-only CI

- **Objective:** Enforce Milestone 0 acceptance locally and in GitHub Actions.
- **Dependencies:** M0.2-M0.5.
- **Files:** unit/integration tests, `.github/workflows/ci.yml`, `README.md`.
- **Implementation steps:** Cover configuration, seeds, run IDs, Git state, provenance, manifest and
  budget serialisation, placeholder gate data, clean failure reporting, and offline smoke; run Ruff,
  Ruff format, strict mypy, pytest, and the CLI in CPU-only CI.
- **Acceptance tests:** `uv run ruff check .`, `uv run ruff format --check .`,
  `uv run mypy src tests`, `uv run pytest`, and `uv run unfrozen smoke` all pass.
- **Scientific invariants:** Tests make no network call and retain the fixture; CI does not claim a
  scientific gate or begin Milestone 1.
- **Artifacts:** Passing check logs and a review-ready milestone commit.
- **Failure modes and risks:** Tests pass only with local cache, CI writes tracked artifacts, or
  static typing excludes tests.
- **Completion criteria:** All five required checks pass from the locked environment and the complete
  diff is reviewed against Revision 6.
- **Stop conditions:** Any acceptance failure blocks the milestone commit.

### M0.7 — Canonical GitHub closeout and release infrastructure

- **Objective:** Establish canonical milestone closeout, history, release templates, and controlled
  document ingestion.
- **Dependencies:** M0.1-M0.6 and completion of pre-merge smoke-run hardening.
- **Files:** `PROJECT_HISTORY.md`, `RESEARCH_LOG.md`, `docs/release-and-archive-process.md`,
  `docs/document-ingest-workflow.md`, `docs/release-notes/milestone-template.md`,
  `docs/release-notes/scientific-checkpoint-template.md`, `docs/release-notes/milestone-0.md`,
  `AGENTS.md`, and `README.md`.
- **Implementation steps:** Document canonical `origin/main`; exact branch/PR/merge/tag/release flow;
  immutable tag rules; scientific checkpoint namespace; release content; owner Downloads ingest
  procedure; history/log responsibilities; and recommended main protection.
- **Acceptance tests:** Repository-wide references use `CODEX_SPEC.md`; the exact staging path
  appears only in operator documentation/rules; no code, config, test, manifest, or CI depends on
  it; templates contain commit/specification/CI/artifact/decision fields; branch completion cannot
  be confused with milestone completion.
- **Scientific invariants:** A software release cannot masquerade as a scientific freeze or gate;
  publishable runs require a clean merged tagged commit; tags are immutable.
- **Artifacts:** Complete governance set and a draft `docs/release-notes/milestone-0.md`.
- **Failure modes and risks:** Tagging an unmerged commit, moving a tag, omitting failed work,
  copying unrelated Downloads content, or beginning Milestone 1 before release closeout.
- **Completion criteria:** After human approval and merge, local `main` is synchronised,
  `milestone-0-complete` is pushed, a GitHub Release exists, and history/log records are current.
- **Stop conditions:** Failed CI, unresolved review, dirty tag target, missing source-document hash,
  or inconsistent remote state.

## Milestone 1: SchemaWorld Core

### M1.1 — Exact state and action contracts

- **Objective:** Define immutable integer/fixed-point state, legal actions, seeds, delayed-event
  queues, and Gymnasium-style reset/step protocols for CONTAINMENT and SUPPORT.
- **Dependencies:** Accepted M0.
- **Files:** `envs/schema_world/state.py`, `actions.py`, constants, configuration, unit tests.
- **Implementation steps:** Specify units and bounds; implement typed state/action validation;
  separate privileged scientific state from ordinary observations; define deterministic resets.
- **Acceptance tests:** Boundary values, illegal actions, serialisation, reset determinism, and hidden
  relation-label exclusion.
- **Scientific invariants:** No floating-point scientific state where exact arithmetic is possible;
  no privileged relation names enter the primary sensor stream.
- **Artifacts:** Versioned state/action schemas and fixtures.
- **Failure modes and risks:** Platform-dependent arithmetic, ambiguous units, or leaked labels.
- **Completion criteria:** Identical inputs yield byte-identical validated initial states and actions.
- **Stop conditions:** A state simplification that prevents required counterfactual matching or
  comparability requires owner review.

### M1.2 — CONTAINMENT and SUPPORT dynamics

- **Objective:** Implement the minimal deterministic causal transitions, including impeded exit,
  support loss, attachment/tension support, and delayed events required by Phase I.
- **Dependencies:** M1.1.
- **Files:** `dynamics.py`, schema-specific templates/configuration, transition tests.
- **Implementation steps:** Implement pure transition functions; order simultaneous events; expose
  transition traces; cover open/closed boundaries and functional/non-functional support.
- **Acceptance tests:** Exact expected states for every core transition, delayed-event sequence, and
  repeated-seed regression.
- **Scientific invariants:** Dynamics encode causal structure without rendering dependence or target
  language labels.
- **Artifacts:** Deterministic transition engine and golden state fixtures.
- **Failure modes and risks:** Update-order artifacts, accidental nondeterminism, or conflating contact
  with support.
- **Completion criteria:** All declared Phase I literal mechanisms have exact, documented tests.
- **Stop conditions:** Underspecified simultaneous-event semantics require an open question and owner
  decision before implementation.

### M1.3 — Relations and matched counterfactuals

- **Objective:** Derive ground-truth relations from privileged raw state and generate causally matched
  pairs differing only in the intended factor.
- **Dependencies:** M1.2.
- **Files:** `relations.py`, `templates.py`, counterfactual utilities, tests.
- **Implementation steps:** Implement relation derivation; define match strata; generate paired
  initial states/actions; audit all non-target fields and transition budgets.
- **Acceptance tests:** Relation truth tables, no relation leakage, pair parity, target-factor-only
  differences, deterministic hashes.
- **Scientific invariants:** Relations are verifier/scorer data only; matched claims require audited
  equality.
- **Artifacts:** Pair manifests with state, observation, and relation hashes.
- **Failure modes and risks:** Hidden confounds, pair ID drift, or direct labels in observations.
- **Completion criteria:** Every core mechanism has validated positive/negative matched pairs.
- **Stop conditions:** A required contrast cannot be matched under the state design.

### M1.4 — Opaque codec, manifests, hashes, and inspection renderer

- **Objective:** Make core episodes reversible, inspectable, versioned, and persistable without
  introducing model training.
- **Dependencies:** M1.1-M1.3.
- **Files:** `codecs/opaque_tokens.py`, data manifest/hashing modules, renderer, Parquet schemas,
  CLI inspection/generation commands, tests.
- **Implementation steps:** Map observations/actions to meaningless reversible tokens; write episode
  and step Parquet; hash state/observation/render separately; add a CPU renderer and textual
  inspection path.
- **Acceptance tests:** Codec reversibility, Parquet round-trip, pinned hashes, headless rendering,
  and CLI dry runs.
- **Scientific invariants:** Opaque tokens carry no pretrained lexical semantics; rendering is not a
  scientific dependency.
- **Artifacts:** Tiny deterministic curriculum and inspection output.
- **Failure modes and risks:** Semantic token leakage, unstable Parquet ordering, or display/GPU
  requirements.
- **Completion criteria:** Generated episodes replay and hash identically across supported CPU
  environments.
- **Stop conditions:** A serialization change would invalidate already frozen artifacts.

### M1.5 — Core integration and milestone acceptance

- **Objective:** Validate end-to-end generation, replay, counterfactual parity, provenance, and budget
  accounting for SchemaWorld Core.
- **Dependencies:** M1.1-M1.4.
- **Files:** integration/regression tests, core config, README/docs updates.
- **Implementation steps:** Generate both schemas at multiple seeds; replay; compare hashes; inspect;
  record manifests and ledgers; run all quality checks.
- **Acceptance tests:** Byte-identical replay, pinned selected trajectories, no network/GPU, lint,
  typing, and complete tests.
- **Scientific invariants:** No benchmark treatment or adaptation work begins.
- **Artifacts:** Reviewed deterministic core fixture set and milestone report.
- **Failure modes and risks:** Cross-platform hash drift or unreported generated artifacts.
- **Completion criteria:** Milestone 1 deliverables and tests pass, then the cross-cutting canonical
  closeout gate completes through merge, local sync, immutable annotated tag push, GitHub Release,
  and current project/research records.
- **Stop conditions:** Any nondeterminism or unmatched counterfactual blocks acceptance.

## Milestone 2: benchmark construction, hardware qualification, and model-stack freeze

### M2.1 — Benchmark schema and lifecycle

- **Objective:** Define validated item metadata, content hashes, source/private/frozen states, and an
  immutable versioning workflow before treatment training.
- **Dependencies:** Accepted M1.
- **Files:** benchmark models, build/validate/freeze CLI commands, configs, tests.
- **Implementation steps:** Implement stable IDs and required annotations; canonicalise/hide answers;
  enforce state transitions and write-once frozen versions.
- **Acceptance tests:** Schema validation, duplicate IDs, hash mismatch, mutation refusal, and clean
  rebuild from source.
- **Scientific invariants:** No evaluated model generates answers; frozen items never change in
  place.
- **Artifacts:** Versioned empty/private benchmark skeleton and manifest.
- **Failure modes and risks:** Answer leakage, content-hash instability, or mutable frozen files.
- **Completion criteria:** Lifecycle commands fail closed on every integrity violation.
- **Stop conditions:** Release/licensing or human-subject questions require owner review.

### M2.2 — Literal and counterfactual evaluation families

- **Objective:** Build L1/L2 literal, novel-template, novel-configuration, and counterfactual tasks
  that verify source-domain learning.
- **Dependencies:** M2.1 and SchemaWorld interfaces.
- **Files:** benchmark source templates/items, literal evaluator, regression fixtures, tests.
- **Implementation steps:** Author clean splits; vary identities, positions, mechanisms, and
  counterfactuals; annotate causal factors and source families; audit training overlap.
- **Acceptance tests:** Split disjointness, answer correctness against simulator, lexical-cue checks,
  and reverse-option equivalence.
- **Scientific invariants:** L0 fit cannot substitute for L1/L2; hidden test content stays isolated.
- **Artifacts:** Reviewed private literal benchmark candidates.
- **Failure modes and risks:** Template memorisation, source/test overlap, or single-cue answers.
- **Completion criteria:** Independent review confirms every item measures declared literal structure.
- **Stop conditions:** Any item depends on unsettled dynamics or leaks treatment templates.

### M2.3 — Abstract and metaphorical evaluation families

- **Objective:** Build controlled L3 abstract relational and L4 novel metaphor tasks plus
  trained/untrained-schema controls.
- **Dependencies:** M2.1; conceptual review of M2.2.
- **Files:** authored item sources, annotations, validation records, tests.
- **Implementation steps:** Use nonce entities and new target domains; author compositional and novel
  physical analogies; annotate conventionality, lexical cues, causal factors, and overlap.
- **Acceptance tests:** Human answer agreement, option reversal, cue ablations, trained/untrained
  balance, and target-domain disjointness.
- **Scientific invariants:** L3/L4 are scientifically important but cannot affect gate status;
  evaluation metaphors never enter treatment language.
- **Artifacts:** Human-reviewed private L3/L4 candidates and validation metadata.
- **Failure modes and risks:** Conventional metaphor contamination, ambiguous mappings, or schema word
  shortcuts.
- **Completion criteria:** Items pass frozen human-validation and leakage rules.
- **Stop conditions:** Insufficient agreement or unresolved licensing prevents freezing.

### M2.4 — Scoring, option order, leakage, and retention fixtures

- **Objective:** Implement condition-blind length-normalised likelihood scoring, option-order
  averaging, raw item retention, and leakage auditing.
- **Dependencies:** M2.2-M2.3.
- **Files:** likelihood/option-order/leakage modules, retention config, tests.
- **Implementation steps:** Define schema margins; render original/reversed forms; prohibit external
  memory in closed-book mode; scan treatment text overlap; define retention interface without
  choosing unresolved thresholds.
- **Acceptance tests:** Hand-calculated likelihoods, order invariance, closed-book denial, leakage
  positives/negatives, and full item-level serialization.
- **Scientific invariants:** Primary scoring uses model likelihood, not an LLM judge; closed-book is
  primary.
- **Artifacts:** Deterministic scoring and audit fixtures.
- **Failure modes and risks:** Token-length bias, condition leakage into prompts, or hidden retrieval.
- **Completion criteria:** Scoring reproduces pinned examples and fails closed on prohibited access.
- **Stop conditions:** A model API cannot expose defensible likelihoods without changing the endpoint.

### M2.5 — RTX 5070 hardware qualification and model selection

- **Objective:** Prospectively select and approve a real local Phase I model stack that fits one
  RTX 5070 12 GB card without using final benchmark outcomes.
- **Dependencies:** Accepted M2.1-M2.4; quarantined `selection_probe_v1`; engineering adaptation
  fixture; owner access to the RTX workstation.
- **Files:** Hardware and candidate configs; CUDA/VRAM profiling; candidate registry;
  sensor-embedding injection tests; qualification report; model-selection approval.
- **Implementation steps:** Qualify sequence lengths 256/512/1024 with optional 2048, microbatch 1,
  fixed effective batch by accumulation, LoRA rank 8/16 with optional 32, BF16 LoRA and separately
  declared NF4 QLoRA, gradient checkpointing, standard PyTorch SDPA, and no CPU offload. Evaluate an
  approximately 0.8-2.2B text-only base-model primary envelope with frozen tokenizer and lexical
  embedding matrix, separate sensor/action embeddings, logits and hidden-state access, and no
  mandatory remote code.
- **Acceptance tests:** Verify exact model/tokenizer revisions and licences; offline reload;
  gradients only in approved sensor/LoRA parameters; adapter save/reload; likelihood and hidden-state
  access; no fatal probe floor/ceiling; measured reserve of `max(15% VRAM, 1.5 GiB)`; practical
  projected matrix runtime; and complete clean-commit provenance.
- **Scientific invariants:** No final benchmark item or target domain is used; BF16 and QLoRA remain
  distinct; no OOM-triggered silent configuration change; native Windows and WSL2/Linux remain
  distinct fingerprints until tested; the lexical embedding matrix remains frozen and the
  sensor/action path remains separate.
- **Artifacts:** Hardware qualification, candidate comparison, and signed model-selection approval
  identifying exactly one `QUALIFIED_PRIMARY` stack plus declared fallback/replication posture.
- **Failure modes and risks:** Candidate selection from final outcomes, hidden offload or precision
  drift, inadequate VRAM reserve, unreviewed remote code, or reopened model choice after approval.
- **Completion criteria:** One exact primary stack is approved; candidates are classified as
  `QUALIFIED_PRIMARY`, `QUALIFIED_REPLICATION`, `CONDITIONAL`, or `REJECTED`; and every qualified
  envelope is hash- and commit-bound.
- **Stop conditions:** No candidate satisfies licence, access, frozen-embedding, VRAM, determinism,
  runtime, or provenance requirements.

### M2.6 — Freeze `v1_core`

- **Objective:** Freeze the complete Phase I benchmark before any treatment run.
- **Dependencies:** M2.1-M2.4, approved M2.5 model-selection artifacts, and owner approval of open
  benchmark decisions.
- **Files:** `benchmarks/frozen/v1_core/`, benchmark config/card, immutable manifest and hashes.
- **Implementation steps:** Final validation; human sign-off; produce content manifest; mark release
  and private partitions; commit and tag the benchmark version.
- **Acceptance tests:** Rebuild/hash equality, mutation rejection, coverage matrix, leakage audit, and
  secret-answer isolation.
- **Scientific invariants:** No post-treatment item editing; changes create a new benchmark version;
  no final item may have been used to choose hardware, model, adapter, precision, quantisation, or
  memory settings.
- **Artifacts:** Frozen `v1_core` and benchmark card.
- **Failure modes and risks:** Premature freezing, accidental answer publication, or incomplete
  validation provenance.
- **Completion criteria:** Exact Git commit and hashes identify the approved frozen benchmark, its
  distinct scientific-checkpoint release is published, and Milestone 2 then completes the
  cross-cutting engineering closeout gate before Milestone 3 begins.
- **Stop conditions:** Owner/human-validator approval or licensing is missing.

## Milestone 3: Phase I adaptation pipeline

### M3.1 — Phase I treatment datasets and codecs

- **Objective:** Generate matched `text_oracle`, `sensor_causal`, `sensor_passive`, and
  `sensor_shuffled` data from frozen core curricula.
- **Dependencies:** Accepted M2.6 frozen benchmark and approved M2.5 model-selection artifacts.
- **Files:** data generators/transforms, condition configs, manifests, tests.
- **Implementation steps:** Serialize literal oracle text; apply opaque codec; mask action/proprioceptive
  inputs; shuffle within frozen strata; preserve token marginals, episodes, and budgets.
- **Acceptance tests:** Oracle completeness, codec reversibility, passive masks, shuffled marginal
  equality/contingency break, and dataset hashes.
- **Scientific invariants:** Comparisons begin from identical base checkpoint and audited matched
  evidence; no evaluation metaphors enter treatment data.
- **Artifacts:** Versioned treatment manifests and tiny deterministic fixtures.
- **Failure modes and risks:** Shuffling changes marginals, masks leak action, or text templates overlap
  evaluation.
- **Completion criteria:** Every condition transformation is deterministic, audited, and reviewed.
- **Stop conditions:** A matching failure or leakage finding blocks training.

### M3.2 — Approved model loader, separate sensor embeddings, and LoRA contracts

- **Objective:** Implement the already approved M2.5 model stack with a frozen base, frozen lexical
  embedding matrix, separate sensor/action embedding path, and precisely declared trainable
  components; do not reopen model selection.
- **Dependencies:** M3.1 and the exact approved M2.5 primary-stack fingerprint.
- **Files:** model/tokenizer/LoRA/sensor loader modules, model config, CPU toy tests, optional GPU tests.
- **Implementation steps:** Verify repository/revision/licence/tokenizer/qualification hashes; inject
  dedicated opaque sensor/action embeddings without training the lexical matrix; configure only the
  approved LoRA targets, precision, quantisation, sequence envelope, operating environment, and
  offload posture; count trainable parameters; support CPU tiny fixtures and the qualified GPU mode.
- **Acceptance tests:** Offline cached load, hash mismatch refusal, frozen base and lexical
  embeddings, gradients only in approved sensor/LoRA parameters, trainable-count accuracy,
  save/reload adapters, likelihood and hidden-state access, and no real download in ordinary CI.
- **Scientific invariants:** Model identity is configuration-driven; all conditions use the same
  declared base.
- **Artifacts:** Model-stack fingerprint and tiny adapter fixture.
- **Failure modes and risks:** Silent revision drift, unintended trainable base weights, or licence
  incompatibility.
- **Completion criteria:** Exact stack provenance and trainable paths are reproducible.
- **Stop conditions:** Missing licence or M2.5 approval, unavailable weights, or any change to model,
  tokenizer, precision, quantisation, sequence envelope, LoRA placement, sensor pathway, operating
  environment, or offload posture without a new qualification artifact.

### M3.3 — Training, replay, checkpoint, and resume engine

- **Objective:** Execute bounded LoRA/sensor adaptation with language retention, checkpointing, and
  exact budget/provenance capture.
- **Dependencies:** M3.1-M3.2.
- **Files:** trainer/objectives/sampler/replay/checkpoint/resume modules, configs, tests.
- **Implementation steps:** Implement deterministic sampling; adaptation and replay objectives;
  gradient accumulation; periodic checkpoints; atomic manifests; idempotent resume; failed-run
  retention.
- **Acceptance tests:** One-step CPU training fixture, deterministic resume equivalence, checkpoint
  hashes, frozen-base invariant, and accurate forward/backward/optimiser counters.
- **Scientific invariants:** Never discard failed seeds; retention objective and budgets stay visible;
  no cloud tracker is required.
- **Artifacts:** Tiny training/resume runs and adapter checkpoints.
- **Failure modes and risks:** Resume duplicates steps, budget undercounting, RNG drift, or catastrophic
  forgetting.
- **Completion criteria:** Interrupted and uninterrupted tiny runs converge to hash-equivalent state.
- **Stop conditions:** Nondeterministic scientific sampling or unaccounted compute.

### M3.4 — Condition parity and matrix-ready execution

- **Objective:** Apply a shared execution protocol across P1-C0 through P1-C4 without condition-
  specific provenance gaps.
- **Dependencies:** M3.3.
- **Files:** condition runner, parity audits, run manifests, tests.
- **Implementation steps:** Bind condition/schema/seed configs; enforce base-checkpoint identity;
  compare episode/token/optimiser budgets; record exclusions and failures; expose dry-run plans.
- **Acceptance tests:** Matched-condition fixtures, deliberate parity failure, no-adaptation identity,
  and complete manifests for every outcome.
- **Scientific invariants:** `sensor_passive` remains diagnostic; `text_oracle` is not a gate opponent;
  `sensor_shuffled` is the hard contingency control.
- **Artifacts:** Validated run plans and parity reports.
- **Failure modes and risks:** Condition-specific defaults, silent seed retries, or unequal training
  exposure.
- **Completion criteria:** A dry-run matrix proves all planned cells are comparable and auditable.
- **Stop conditions:** Any comparability violation requires owner review and a frozen-plan revision.

### M3.5 — Pre/post, retention, and L0-L4 evaluation

- **Objective:** Evaluate frozen benchmark items closed-book and preserve ordinary language retention
  and complete item-level outputs.
- **Dependencies:** Frozen M2.6 benchmark artifacts and M3.3-M3.4.
- **Files:** evaluators, transfer aggregation, retention modules, metrics manifests, tests.
- **Implementation steps:** Score pre/post schema margins and option reversals; disable sensors,
  ledgers, and retrieval; aggregate without gate decisions; record checkpoint and benchmark hashes.
- **Acceptance tests:** Baseline identity, closed-book denial, hand-computed gains, L0-L4 separation,
  retention serialization, and failed-checkpoint handling.
- **Scientific invariants:** L3/L4 remain independent fields and cannot influence gate computation.
- **Artifacts:** Item-level scores, retention results, and transfer profiles.
- **Failure modes and risks:** Open-book leakage, averaging hides item order, or checkpoint mismatch.
- **Completion criteria:** Every run produces reproducible item-level and aggregate evaluation data.
- **Stop conditions:** Frozen benchmark mismatch or unavailable retention policy.

### M3.6 — Pipeline integration and acceptance

- **Objective:** Validate the complete Phase I adaptation path without running the scientific matrix.
- **Dependencies:** M3.1-M3.5.
- **Files:** CPU integration tests, separately marked GPU smoke, documentation.
- **Implementation steps:** Execute tiny fixtures for all conditions; save/resume; evaluate; audit
  budgets, parity, leakage, manifests, and hashes; run all quality checks.
- **Acceptance tests:** Offline CPU integration suite and opt-in cached-model GPU smoke pass.
- **Scientific invariants:** Tiny fixtures are engineering evidence only and cannot produce `PASS`.
- **Artifacts:** Pipeline acceptance report and pinned regression hashes.
- **Failure modes and risks:** Fixture success is mistaken for scientific calibration.
- **Completion criteria:** Review confirms the pipeline is ready for a preregistered matrix, then
  the cross-cutting canonical closeout gate completes before Milestone 4 begins.
- **Stop conditions:** Any integrity audit failure blocks Milestone 4.

## Milestone 4: Phase I calibration matrix and mandatory gate

### M4.1 — Freeze gate and matrix configuration

- **Objective:** Preregister hard thresholds, seeds, exclusions, budgets, model fingerprint, benchmark,
  curricula, and decision logic before treatment runs.
- **Dependencies:** Accepted M3, the exact qualified M2.5 model-stack fingerprint, frozen M2.6
  benchmark artifacts, and owner decisions for gate thresholds/seeds.
- **Files:** `configs/gate/phase1.yaml`, confirmatory experiment config, frozen matrix manifest,
  preregistration record.
- **Implementation steps:** Resolve all configurations; freeze the qualified model-stack and
  hardware-environment fingerprints; hash inputs; validate two schemas, P1-C0 to P1-C4, and at
  least three seeds; obtain owner review; commit before execution.
- **Acceptance tests:** Completeness, immutable hashes, no post-treatment metrics available, and
  explicit proof that L3/L4 fields are absent from decision inputs.
- **Scientific invariants:** Thresholds cannot be calibrated from post-treatment comparisons.
- **Artifacts:** Approved frozen gate configuration and matrix manifest.
- **Failure modes and risks:** Data-dependent thresholds, missing seeds, or ambiguous exclusions.
- **Completion criteria:** A clean committed configuration uniquely defines the matrix and decision.
- **Stop conditions:** Any unresolved open question affecting criteria, budget, or model stack.

### M4.2 — Auditable matrix execution

- **Objective:** Run both schemas, P1-C0 through P1-C4, and every frozen seed while retaining successes,
  failures, and exclusions.
- **Dependencies:** M4.1.
- **Files:** run matrix records under ignored artifact storage; group manifest; progress/failure logs.
- **Implementation steps:** Verify clean/approved commit policy; execute cells; checkpoint/resume only
  under declared rules; never cherry-pick seeds; hash every output; audit resource parity.
- **Acceptance tests:** Planned-versus-observed cell reconciliation, all seed accounting, no duplicate
  IDs, checkpoint verification, and budget/parity audit.
- **Scientific invariants:** No inconvenient run is discarded or silently rerun with altered settings.
- **Artifacts:** Complete permanent Phase I calibration dataset and group manifest.
- **Failure modes and risks:** Hardware interruptions, selective reruns, corrupted checkpoints, or
  unrecorded dirty changes.
- **Completion criteria:** Every planned cell has an accepted, failed, or preregistered-excluded state.
- **Stop conditions:** Config/hash drift or comparability failure stops the matrix and requires a
  documented full-rerun decision.

### M4.3 — Transfer profile and hard-gate evaluator

- **Objective:** Compute L0-L4 scientific outcomes and one of `PASS`, `INCONCLUSIVE`, or `NO_GO` from
  frozen hard criteria only.
- **Dependencies:** M4.2.
- **Files:** transfer aggregation, gate evaluator, statistical utilities, regression tests.
- **Implementation steps:** Aggregate item/run uncertainty; evaluate G1-G6; account for failed and
  excluded runs; keep L3/L4 in the report-only profile; return an exact status and reason.
- **Acceptance tests:** Synthetic PASS/INCONCLUSIVE/NO_GO cases; missing-seed refusal; report order
  invariance; metamorphic tests proving arbitrary L3/L4 changes never alter status.
- **Scientific invariants:** Text-oracle rank and causal-passive difference are non-gating; L3/L4 are
  prohibited inputs.
- **Artifacts:** Deterministic gate-decision data and full transfer profile.
- **Failure modes and risks:** Accidental metric coupling, inappropriate seed exclusion, or confidence
  intervals computed at the wrong unit.
- **Completion criteria:** Independent review can reproduce the status from frozen inputs.
- **Stop conditions:** Any hard criterion lacks preregistered evidence or statistical interpretation.

### M4.4 — Gate reports, approvals, and verification

- **Objective:** Produce human- and machine-readable reports plus hash- and commit-bound approval
  artifacts.
- **Dependencies:** M4.3.
- **Files:** report generator/templates, `phase1_gate_report.md/json`, approval and verification CLI,
  tests.
- **Implementation steps:** Render all criteria, thresholds, intervals, seeds, failures, exclusions,
  artifacts, L0-L4 outcomes, status, and reason; canonicalise report hash; record signer/decision/
  rationale; verify hash chain and Git commit.
- **Acceptance tests:** Golden report, tamper tests for every referenced hash, stale commit, non-PASS,
  changed parent/config/stack, and missing evidence.
- **Scientific invariants:** Approval cannot conceal null L3/L4 outcomes or omit failures.
- **Artifacts:** Permanent report and approval trio under `reports/phase-gates/<group-id>/`.
- **Failure modes and risks:** Self-referential hashing, signature ambiguity, or stale approvals.
- **Completion criteria:** Verification succeeds only for the exact approved evidence and commit.
- **Stop conditions:** Human signer or rationale is absent; generated decision differs from requested
  approval.

### M4.5 — Scientific acceptance and advancement decision

- **Objective:** Close Phase I as a permanent result and enforce the resulting advancement state.
- **Dependencies:** M4.1-M4.4.
- **Files:** scientific calibration report, data/model cards, Phase II command guard, archive index.
- **Implementation steps:** Review complete artifacts; publish prospective interpretations including
  text-dominant and compartmentalised outcomes; archive results; verify Phase II commands fail closed
  without the exact valid approval.
- **Acceptance tests:** Archive completeness; command denial for missing/stale/INCONCLUSIVE/NO_GO
  approvals; valid `PASS` path; compatibility requirement when stack fingerprint changes.
- **Scientific invariants:** `INCONCLUSIVE` and `NO_GO` block Phase II; `PASS` does not erase Phase I;
  a later stack change triggers compatibility calibration.
- **Artifacts:** Reviewed Phase I result, advancement decision, and immutable archive index.
- **Failure modes and risks:** Treating Phase I as disposable, overstating a result, or bypassing the
  compatibility gate.
- **Completion criteria:** Human review accepts the report/archive and the technical gate matches the
  scientific decision; the scientific checkpoint uses its distinct immutable tag/release, and the
  cross-cutting Milestone 4 engineering closeout gate completes before any authorised advancement.
- **Stop conditions:** Any unresolved integrity concern, approval mismatch, or missing permanent
  artifact blocks advancement.

## Roadmap only: Milestones 5-10

No executable work packages are authorised for these milestones at this stage:

- **Milestone 5:** CausalSchemaLab, multimodal projector, latent world model, uncertainty, and active
  replay, gated by Phase I `PASS`.
- **Milestone 6:** language workspace, hypothesis ledger, concept bridge, consolidation, and exact
  Phase II stack compatibility calibration.
- **Milestone 7:** minimum Phase II pilot matrix with at least three seeds and an untrained-schema
  evaluation.
- **Milestone 8:** frozen confirmatory Phase II study with both schemas, stronger seed counts, model-
  family replication, and robustness analyses.
- **Milestone 9:** secondary mechanistic integration analysis.
- **Milestone 10:** separately reviewed Phase III neural-colony experiment.

Phase II defaults to a locally hardware-qualified 1.5-3B stack. Any different or multimodally
pretrained stack requires its own qualification and the mandated Phase I compatibility calibration.
Each roadmap milestone remains subject to the cross-cutting Milestone 0-10 closeout gate: PR, CI,
human review, merge, local fast-forward sync, immutable annotated engineering tag and tag push,
GitHub Release, and current project/research records.

## Git and GitHub workflow

- Use dedicated `codex/<milestone>-<purpose>` or `docs/<revision>-<purpose>` branches. Never combine
  milestones on one branch and never declare a milestone complete on a local or remote feature
  branch.
- Treat `origin/main` as canonical. Push every task branch, review it through a pull request into
  `main`, and require declared CI plus human review before merge.
- After a GitHub merge, synchronise local `main` with `git pull --ff-only origin main`; after a local
  merge, push `main`. Verify the canonical commit and clean tree before tagging.
- Create and explicitly push immutable annotated engineering tags `milestone-N-complete`. Never
  move, delete, or reuse a published tag; corrections use a new correction tag and release.
- Keep engineering milestone tags distinct from scientific tags such as
  `benchmark-v1-core-frozen`, `phase1-preregistered-v1`, and `phase1-gate-v1`.
- Publish a GitHub Release for every milestone and major scientific checkpoint. Release notes record
  the exact commit, `CODEX_SPEC.md` hash, CI result, scope, limitations, artifact hashes,
  advancement decision, and next authorised work.
- Update `PROJECT_HISTORY.md` for factual chronology and `RESEARCH_LOG.md` for intellectual or
  methodological changes. Neither overrides a frozen scientific artifact.
- Start publishable scientific runs only from a clean merged tagged commit. Branch-head runs remain
  exploratory unless separately frozen and approved.
- GitHub Actions install from the lock and run Ruff lint/format, strict mypy, pytest, and offline CPU
  smoke. Optional GPU qualification remains separately marked and cannot silently become a CI
  dependency.
- Every run manifest records the exact Git commit and dirty state. Clean and dirty results are never
  pooled without an explicit frozen policy; dirty provenance is retained rather than rewritten.
- Generated runs, reports, checkpoints, model weights, downloaded models, raw/licensed datasets,
  and temporary logs remain outside Git. Durable scientific artifacts live in approved storage with
  hashes and archive indexes.
- Do not commit third-party data without redistribution rights, or any secret, token, credential,
  private key, full model weight, checkpoint, or machine-specific runtime dependency.
- Retain small deterministic fixtures, regression hashes, frozen configurations, benchmark
  manifests/cards, release notes, approved manifests, and legally distributable scientific metadata.
- Every scientific table, figure, metric, and gate report resolves to its run/group manifest,
  artifact hashes, frozen inputs, and exact canonical commit. Changed content produces a new result
  identity rather than silently updating the old result.
