# Implementation plan: Milestones 0-4

This plan translates Revision 4 into dependency-ordered, reviewable work packages. Only the active
milestone may be implemented. Milestones 5-10 are roadmap items, not executable work packages.

Phase I is a permanent scientific result and mandatory gate, not a disposable prototype. Its hard
gate criteria concern literal causal learning, held-out transfer, causal-versus-shuffled separation,
language retention, leakage control, reproducibility, complete seed accounting, and provenance.
L3 abstract and L4 metaphor transfer are reported but non-gating. `text_oracle` outperforming a
sensor condition does not cause Phase I to fail. Literal L1/L2 learning without distant linguistic
transfer is a scientifically meaningful compartmentalisation result and a primary motivation for
Phase II. Phase II and Phase III cannot begin merely because their architectures are attractive.

## Milestone 0: repository foundation

### M0.1 — Governance and scientific guardrails

- **Objective:** Encode the enduring scientific, artifact, gate, and engineering rules before code
  is introduced.
- **Dependencies:** Revision 4 specification read in full; clean repository preflight.
- **Files:** `AGENTS.md`, `docs/scientific-design.md`, `docs/implementation-plan.md`,
  `docs/budget-accounting.md`, `docs/phase-gate-protocol.md`, `docs/open-questions.md`.
- **Implementation steps:** Summarise the three phases; define the transfer ladder, accounting, gate
  semantics, invalidation, workflow, and only genuinely unresolved decisions.
- **Acceptance tests:** Manual cross-check against all specification sections; verify L3/L4 never
  appear among hard-gate inputs; verify each requested governance file exists.
- **Scientific invariants:** Phase I remains permanent and mandatory; all named controls and
  comparisons remain explicit; unresolved decisions are not guessed.
- **Artifacts:** Reviewed Markdown governance set.
- **Failure modes and risks:** Accidentally weakening a requirement, treating a null L3/L4 result as
  failure, or turning settled requirements into open questions.
- **Completion criteria:** All six documents are internally consistent and faithful to Revision 4.
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
  success, and failure states.
- **Acceptance tests:** Round-trip every model; test clean and dirty temporary Git repositories;
  test deterministic seeds and IDs; ensure failures retain a reason and partial accounting.
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
- **Implementation steps:** Load the local fixture; make one deterministic tiny forward pass; create
  an isolated run directory; write resolved config, toy output, budget ledger, placeholder gate
  metadata, JSONL logs, and final provenance manifest; print a concise summary; preserve a complete
  failed run on exceptions.
- **Acceptance tests:** CLI exits zero offline without CUDA, secrets, downloads, or network; expected
  files exist and hashes match; repeated seeded model computation agrees; injected fixture failure
  exits non-zero and records its cause.
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
  diff is reviewed against Revision 4.
- **Stop conditions:** Any acceptance failure blocks the milestone commit.

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
- **Completion criteria:** Milestone 1 deliverables and tests pass and receive review.
- **Stop conditions:** Any nondeterminism or unmatched counterfactual blocks acceptance.

## Milestone 2: frozen core benchmark

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

### M2.5 — Freeze `v1_core`

- **Objective:** Freeze the complete Phase I benchmark before any treatment run.
- **Dependencies:** M2.1-M2.4 and owner approval of open benchmark decisions.
- **Files:** `benchmarks/frozen/v1_core/`, benchmark config/card, immutable manifest and hashes.
- **Implementation steps:** Final validation; human sign-off; produce content manifest; mark release
  and private partitions; commit and tag the benchmark version.
- **Acceptance tests:** Rebuild/hash equality, mutation rejection, coverage matrix, leakage audit, and
  secret-answer isolation.
- **Scientific invariants:** No post-treatment item editing; changes create a new benchmark version.
- **Artifacts:** Frozen `v1_core` and benchmark card.
- **Failure modes and risks:** Premature freezing, accidental answer publication, or incomplete
  validation provenance.
- **Completion criteria:** Exact Git commit and hashes identify the approved frozen benchmark.
- **Stop conditions:** Owner/human-validator approval or licensing is missing.

## Milestone 3: Phase I adaptation pipeline

### M3.1 — Phase I treatment datasets and codecs

- **Objective:** Generate matched `text_oracle`, `sensor_causal`, `sensor_passive`, and
  `sensor_shuffled` data from frozen core curricula.
- **Dependencies:** Accepted M2.
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

### M3.2 — Model loader, sensor embeddings, and LoRA contracts

- **Objective:** Load the configuration-selected open model stack with a frozen base and precisely
  declared trainable components.
- **Dependencies:** M3.1 and owner resolution of the Phase I model stack.
- **Files:** model/tokenizer/LoRA/sensor loader modules, model config, CPU toy tests, optional GPU tests.
- **Implementation steps:** Verify repository/revision/licence/tokenizer hashes; add new opaque sensor
  embeddings; configure LoRA targets; count trainable parameters; support CPU tiny fixtures and
  consumer-GPU modes.
- **Acceptance tests:** Offline cached load, hash mismatch refusal, frozen base, trainable-count
  accuracy, save/reload adapters, and no real download in ordinary CI.
- **Scientific invariants:** Model identity is configuration-driven; all conditions use the same
  declared base.
- **Artifacts:** Model-stack fingerprint and tiny adapter fixture.
- **Failure modes and risks:** Silent revision drift, unintended trainable base weights, or licence
  incompatibility.
- **Completion criteria:** Exact stack provenance and trainable paths are reproducible.
- **Stop conditions:** Missing licence approval, unavailable weights, or material stack change.

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
- **Dependencies:** M2.5 and M3.3-M3.4.
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
- **Completion criteria:** Review confirms the pipeline is ready for a preregistered matrix.
- **Stop conditions:** Any integrity audit failure blocks Milestone 4.

## Milestone 4: Phase I calibration matrix and mandatory gate

### M4.1 — Freeze gate and matrix configuration

- **Objective:** Preregister hard thresholds, seeds, exclusions, budgets, model fingerprint, benchmark,
  curricula, and decision logic before treatment runs.
- **Dependencies:** Accepted M3 and owner decisions for gate thresholds/seeds.
- **Files:** `configs/gate/phase1.yaml`, confirmatory experiment config, frozen matrix manifest,
  preregistration record.
- **Implementation steps:** Resolve all configurations; hash inputs; validate two schemas, P1-C0 to
  P1-C4, and at least three seeds; obtain owner review; commit before execution.
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
  scientific decision.
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

## Git and GitHub workflow

- Use `codex/<milestone>-<short-purpose>` branches unless an existing Codex task branch must be
  retained. Never combine milestones on one branch.
- Make small, milestone-scoped commits whose messages describe one reviewed work package. The final
  milestone commit may aggregate only when every included change is part of that milestone.
- Require human review before merge. Never auto-merge a scientific milestone or begin the next
  milestone merely because CI passed.
- GitHub Actions must install from the lock, run Ruff lint and formatting, strict mypy, pytest, and
  the offline smoke path on CPU. Optional GPU checks remain separately marked and non-blocking unless
  explicitly promoted.
- Every run manifest records the exact Git commit and dirty state. Clean and dirty results are never
  pooled without an explicit frozen policy; dirty provenance is retained rather than rewritten.
- Generated ordinary runs, reports, checkpoints, model weights, downloaded models, raw/licensed
  datasets, and temporary logs remain outside Git. Durable scientific artifacts live in approved
  artifact storage with hashes and archive indexes.
- Do not commit third-party datasets or licensed materials without documented redistribution rights.
  Record dataset source, version, licence, hashes, and local acquisition procedure.
- Never commit secrets, access tokens, model credentials, private keys, full model weights,
  checkpoints, or machine-specific paths.
- Retain small deterministic fixtures, regression hashes, frozen configurations, benchmark
  manifests/cards, and declared scientific metadata when they are reviewable and legally
  distributable.
- Every scientific table, figure, metric, and gate report must resolve to its run/group manifest,
  artifact hashes, frozen inputs, and exact Git commit. A changed commit or hashed input produces a
  new result identity rather than silently updating the old result.
