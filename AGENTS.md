# Unfrozen Schemas engineering rules

These rules apply to every change in this repository.

## Required reading and scope

- Read `CODEX_SPEC_Unfrozen_Schemas_v4.md`, `docs/scientific-design.md`, and
  `docs/implementation-plan.md` in full before changing implementation code.
- Treat `CODEX_SPEC_Unfrozen_Schemas_v4.md` as the authoritative Revision 4 specification.
- Implement one milestone at a time. Do not begin a later milestone until the current milestone's
  tests and acceptance criteria pass and the work has been reviewed.
- Write or update tests before declaring a milestone complete.
- Record genuinely unresolved scientific decisions in `docs/open-questions.md`; never silently
  guess or change the scientific design.

## Scientific invariants

- Preserve the distinction among Phase I mandatory causal calibration and gate, Phase II
  language-scaffolded active grounding, and Phase III neural-colony propagation.
- Treat Phase I as a permanent scientific result and mandatory gate, never as a disposable
  prototype.
- Phase I gate status may depend only on frozen hard-gate evidence: L1 held-out literal causal
  learning, causal-versus-shuffled separation, L2 transfer beyond memorised templates, language
  retention, leakage and parity control, reproducibility, complete seed accounting, and
  provenance integrity.
- Never allow Phase I L3 abstract-transfer or L4 metaphor-transfer scores to affect Phase I gate
  status. Report them as non-gating scientific outcomes.
- Block Phase II scientific collection, training, and matrix commands unless the required primary
  Phase I `PASS` approval, and any required model-stack compatibility `PASS` approval, are valid,
  current, hash-matched, and tied to the executing Git commit.
- Preserve active/yoked, raw/language, causal/shuffled, trained/untrained-schema, and
  closed/open-book comparisons. Do not replace them with proxies without explicit owner approval.
- Keep model, schema, condition, curriculum, environment, budget, benchmark, and gate choices
  configuration-driven.
- Preserve frozen benchmark and curriculum versions; never overwrite them after viewing treatment
  effects.
- Stop and report if a proposed change would invalidate condition comparability.

## Reproducibility, security, and artifacts

- Account separately for externally supplied language, self-generated language, sensor data,
  environment steps, optimisation steps, forward and backward passes, elapsed compute, peak
  memory, and stored artifacts.
- Preserve failed runs and dirty-working-tree provenance as well as successful clean runs.
- Use no network calls in unit tests. Smoke tests must not require a network, CUDA, model download,
  API key, or secret.
- Never hard-code secrets, access tokens, model credentials, or machine-specific paths.
- Do not commit model weights, checkpoints, ordinary run outputs, raw or licensed datasets, or
  generated experiment artifacts. Small deterministic fixtures, frozen configurations, source,
  tests, and declared scientific metadata remain tracked.

## Engineering workflow

- Make small, reviewable, milestone-scoped changes.
- Run Ruff lint and format checks, static typing, and pytest after each work package.
- Keep generated files out of Git unless they are deterministic fixtures or frozen, reviewed
  scientific metadata.
- Associate every scientific result with the exact Git commit and working-tree dirty state that
  produced it.
