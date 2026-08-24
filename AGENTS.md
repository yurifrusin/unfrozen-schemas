# Unfrozen Schemas engineering and research rules

These rules apply to every change in this repository.

## Required reading and authority

Before changing implementation code or scientific configuration, read in full:

- `CODEX_SPEC.md`;
- `docs/scientific-design.md`;
- `docs/implementation-plan.md`;
- `docs/release-and-archive-process.md`;
- `docs/document-ingest-workflow.md`.

`CODEX_SPEC.md` is authoritative. Frozen preregistrations, benchmarks, model-selection approvals, and phase-gate artifacts govern their declared scopes. `PROJECT_HISTORY.md` and `RESEARCH_LOG.md` preserve history but do not override those sources.

Implement one milestone at a time. Write or update tests before declaring a work package complete. Record genuinely unresolved scientific decisions in `docs/open-questions.md`; never silently guess or change the design.

## Scientific invariants

- Preserve the distinction among Phase I mandatory causal calibration and gate, Phase II language-scaffolded active grounding, and Phase III neural-colony propagation.
- Treat Phase I as a permanent scientific result and mandatory gate, never as a disposable prototype.
- Phase I gate status may depend only on frozen hard-gate evidence: L1 held-out literal causal learning, causal-versus-shuffled separation, L2 transfer beyond memorised templates, language retention, leakage and parity control, reproducibility, complete seed accounting, and provenance integrity.
- Never allow Phase I L3 abstract-transfer or L4 metaphor-transfer scores to affect Phase I gate status. Report them as non-gating outcomes.
- Block Phase II scientific work unless the primary Phase I `PASS` approval and any required model-stack compatibility `PASS` approval are current, hash-matched, and commit-matched.
- Preserve active/yoked, raw/language, causal/shuffled, trained/untrained-schema, and closed/open-book comparisons. Do not replace them with proxies without explicit owner approval.
- Keep model, hardware, operating environment, precision/quantisation, schema, condition, curriculum, benchmark, budget, and gate choices configuration-driven.
- Require the approved M2.5 RTX 5070 hardware and model-selection artifacts before Milestone 3 real-model work.
- Keep the primary lexical tokenizer and embedding matrix frozen; represent opaque sensor/action IDs through separately declared parameters.
- Never use final benchmark items for candidate ranking, hardware tuning, adapter selection, quantisation selection, or memory tuning.
- Preserve frozen benchmark and curriculum versions and refuse in-place alteration after treatment results are visible.
- Stop and report if a proposed change invalidates condition comparability.

## Reproducibility, security, and artifacts

- Account separately for externally supplied language, self-generated language, sensor observations and bytes, environment steps, optimisation steps, forward/backward passes, elapsed/device compute, peak memory, and stored artifacts.
- Preserve failed runs and dirty-working-tree provenance as well as successful clean runs.
- Use no network calls in unit tests. Offline smoke tests must not require CUDA, model downloads, API keys, or secrets.
- Never hard-code secrets, access tokens, model credentials, or runtime dependencies on machine-specific paths.
- Do not commit full model weights, checkpoints, ordinary run outputs, raw or licensed datasets, generated trajectories, or unrelated downloaded files.
- Retain small deterministic fixtures, frozen configurations, source, tests, release notes, approved manifests, and legally distributable scientific metadata.

## GitHub canonical history and milestone closeout

- Treat `origin/main` as the canonical public history. A local merge is incomplete until `main` is pushed; a GitHub merge must be followed by local fast-forward synchronisation.
- Use one dedicated branch per milestone or documentation revision. Never combine milestones on one branch.
- End every implementation task by pushing the branch and leaving an open pull request; do not merge in the implementation task.
- The owner approves an exact pull-request number and exact head SHA. Only that explicit approval authorises a separate Codex closeout task to merge that exact pull request.
- Immediately before merging, revalidate the approved head SHA, mergeability, required CI, and absence of unresolved review findings. Any drift invalidates approval and requires Codex to stop.
- The same approval may authorise a mechanically constrained linked closeout pull request that fills only predetermined release-note, `PROJECT_HISTORY.md`, and `RESEARCH_LOG.md` fields.
- Any code, experimental, dependency, scientific-design, or unanticipated documentation change after approval requires renewed owner review.
- Create tags and releases only after the canonical closeout commit has been merged and verified.
- A milestone is not complete until the reviewed work is merged into `origin/main`, its immutable annotated milestone tag is pushed, a GitHub Release is published, and `PROJECT_HISTORY.md` plus `RESEARCH_LOG.md` are current.
- Never move, delete, or reuse a published milestone or scientific-checkpoint tag. Create a new correction tag and release.
- Start publishable scientific runs only from a clean merged and tagged commit.
- Do not begin the next milestone merely because branch CI passed.

## Downloaded-document ingestion

The current owner-workstation Markdown staging directory is:

```text
C:\Users\YuriFrusin\Downloads
```

When a task names a downloaded document, such as an updated `CODEX_SPEC.md`:

- inspect that directory for the exact filename before asking for another copy;
- report zero, one, or multiple exact candidates;
- never select with wildcards or by newest-file guesswork;
- calculate and report the source SHA-256;
- compare the current repository destination before replacement;
- copy only the explicitly named file;
- inspect and report the complete diff and destination SHA-256;
- leave unrelated Downloads content untouched;
- do not make code, tests, configs, manifests, or CI depend on this path;
- stop and report when the execution environment cannot access the Windows path.

## Engineering workflow

- Make small, reviewable, milestone-scoped changes.
- Run Ruff lint and formatting checks, static typing, pytest, and relevant smoke/integration commands after each work package.
- Review the complete diff against `CODEX_SPEC.md` and state every deviation.
- Update `PROJECT_HISTORY.md` for factual project events and `RESEARCH_LOG.md` for intellectual or methodological changes.
- Leave branch, pull request, tag, and release state explicit in every completion report.
