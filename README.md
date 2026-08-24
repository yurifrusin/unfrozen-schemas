# Unfrozen Schemas

Unfrozen Schemas is a reproducible research-software platform for testing whether direct causal
experience and language scaffolding complement one another in image-schematic transfer. Revision 4
of the authoritative architecture is in `CODEX_SPEC_Unfrozen_Schemas_v4.md`.

This branch implements **Milestone 0 only**: governance, packaging, validated configuration,
structured local logging, provenance and resource accounting, an offline CPU smoke command, tests,
and CI. It does not implement SchemaWorld dynamics, scientific treatments, model downloads, LoRA,
active agents, multimodal projectors, Phase II experiments, or Phase III colony components.

## Development

Requirements are Python 3.11 and `uv`.

```bash
uv sync
uv run ruff check .
uv run ruff format --check .
uv run mypy src tests
uv run pytest
```

Strict mypy is the project's selected static type checker.

## Offline smoke run

```bash
uv run unfrozen validate-config --config configs/experiment/smoke.yaml
uv run unfrozen smoke
```

The smoke command requires no CUDA, model download, API key, or network call. It loads a tiny local
linear-model fixture and writes an ignored `runs/<run-id>/` directory containing:

- a fully resolved configuration;
- deterministic toy-model input and output;
- a resource-budget ledger;
- explicit non-authorising Phase I placeholder gate metadata;
- structured JSONL logs; and
- a provenance manifest with Git commit/dirty state, packages, platform, seed, statuses, hashes, and
  failure information.

Use `uv run unfrozen smoke --help` for configuration and output overrides intended for testing.

## Scientific governance

Read `AGENTS.md`, `docs/scientific-design.md`, and `docs/implementation-plan.md` before changing
implementation code. Phase I is a permanent mandatory scientific gate. Its L3 abstract-transfer and
L4 metaphor-transfer outcomes are reported but never determine gate status.

The repository licence is deliberately unresolved pending owner review; see
`docs/open-questions.md`.
