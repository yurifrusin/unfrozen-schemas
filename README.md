# Unfrozen Schemas

Unfrozen Schemas is a reproducible research-software programme testing whether language and direct causal experience complement one another in image-schematic learning and transfer.

The authoritative architecture is `CODEX_SPEC.md` (Revision 6). The project has three scientific phases:

1. **Phase I:** deterministic causal calibration and mandatory gate;
2. **Phase II:** language-scaffolded active grounding;
3. **Phase III:** propagation of grounded structure between specialised neural systems.

Phase I reports literal, abstract, and metaphorical transfer, but only reproducible literal causal learning, causal-versus-shuffled separation, held-out generalisation, retention, integrity, and provenance determine its gate. A text-oracle advantage or null metaphor transfer does not itself fail Phase I.

## Current compute envelope

CPU-only development continues through M2.4. M2.5 moves the project to the owner's NVIDIA RTX 5070 12 GB workstation for prospective hardware qualification and model selection. The primary Phase I target is an approximately 0.8–2.2B text-only base model using BF16 LoRA where qualified; NF4 QLoRA is a separately fingerprinted fallback or replication path.

## Documentation map

- `CODEX_SPEC.md` — authoritative scientific and repository specification.
- `AGENTS.md` — enduring Codex and contributor rules.
- `docs/scientific-design.md` — operational summary of the three phases.
- `docs/implementation-plan.md` — dependency-ordered work packages.
- `docs/phase-gate-protocol.md` — Phase I gate semantics and hash chain.
- `docs/budget-accounting.md` — resource-accounting definitions.
- `docs/release-and-archive-process.md` — branch, PR, merge, tag, release, and archive workflow.
- `docs/document-ingest-workflow.md` — controlled handling of downloaded Markdown documents.
- `PROJECT_HISTORY.md` — chronological project events and milestone record.
- `RESEARCH_LOG.md` — evolution of hypotheses, interpretations, and methodological rationale.
- `docs/open-questions.md` — unresolved decisions only.

## Development

Requirements are Python 3.11 and `uv`.

```bash
uv sync --locked
uv run ruff check .
uv run ruff format --check .
uv run mypy src tests
uv run pytest
uv run unfrozen smoke
```

SchemaWorld Core engineering smoke and replay:

```powershell
uv run unfrozen generate-core --config configs/experiment/milestone1_core_smoke.yaml
uv run unfrozen validate-core --manifest <core_manifest.json>
uv run unfrozen replay-core --manifest <core_manifest.json>
uv run unfrozen inspect-episode --episode-id <episode-id> --manifest <core_manifest.json> --render
```

The M1 path is CPU-only, offline, and engineering-only. Its exact operational contract, dependency
licences, serialization boundaries, and hashing rules are documented in `docs/schemaworld-core.md`.
Generated runs remain under ignored output storage and are not scientific LLM results.

M2.1 benchmark-lifecycle engineering commands:

```powershell
uv run unfrozen build-benchmark `
  --source tests/fixtures/benchmark_lifecycle/source `
  --output <isolated-private-output> `
  --version engineering-benchmark-lifecycle-v1 `
  --purpose engineering
uv run unfrozen validate-benchmark --manifest <candidate_manifest.json>
uv run unfrozen create-engineering-freeze-approval `
  --candidate-manifest <candidate_manifest.json> `
  --output <engineering-approval.json> `
  --signer <engineering-reference>
uv run unfrozen freeze-benchmark `
  --candidate-manifest <candidate_manifest.json> `
  --approval <engineering-approval.json> `
  --output <isolated-frozen-output>
uv run unfrozen validate-benchmark --manifest <frozen_manifest.json>
uv run unfrozen audit-benchmark-git
```

The tracked fixture is non-scientific and non-promotable. M2.1 contains no outcome or selection
item, does no scoring/model/GPU work, and cannot freeze production `v1_core`. See
`docs/benchmark-lifecycle.md` and the unfilled `docs/benchmark-card.md` template.

The unreleased `schemaworld-core-v1` contract fails closed on slack or overlength active
load-bearing tethers, diagonal movement, swept closed-boundary tunnelling, non-canonical action
parameters, incomplete pair identities, invalid state-graph references, relation-vocabulary leakage,
and any independently recomputed step, artifact, budget, configuration, or replay mismatch.

The Milestone 0 smoke path is CPU-only, secret-free, download-free, and offline at execution time.

## Canonical GitHub workflow

`origin/main` is the canonical public history. Work occurs on a dedicated branch and becomes a completed milestone only after:

1. branch push and pull request;
2. CI and human review;
3. merge into `origin/main`;
4. local fast-forward synchronisation;
5. immutable annotated milestone tag and tag push;
6. GitHub Release;
7. current project and research logs.

Published tags are never moved or reused.

## Owner-workstation documentation staging

Downloaded Markdown documents supplied for repository updates are normally available at:

```text
C:\Users\YuriFrusin\Downloads
```

This is an operator staging path only. The project code, configuration, CI, manifests, and scientific runs must not depend on it. See `docs/document-ingest-workflow.md`.

## Licence

Repository, documentation, benchmark, and data licensing remain unresolved pending owner review; see `docs/open-questions.md`.
