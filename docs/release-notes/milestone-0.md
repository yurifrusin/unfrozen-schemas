# Milestone 0 Release — Repository Foundation

> Draft only. Finalise after the pull request is approved and merged. Do not describe Milestone 0 as complete until the tag and GitHub Release exist.

## Identity

- Planned tag: `milestone-0-complete`
- Canonical merged commit: `<fill after merge>`
- Pull request: `https://github.com/yurifrusin/unfrozen-schemas/pull/1`
- Release date: `<fill after release>`
- Revision 6 `CODEX_SPEC.md` SHA-256: `658592b974d24ab6f0b9f742fa68d26cb4515a4a727239392bab0c5971fb864a`

## Scope completed

- repository governance and authoritative specification;
- Python 3.11 and `uv` project scaffold;
- strict validated smoke configuration;
- Typer CLI;
- canonical JSON provenance, Git state, package/platform metadata, resource-budget ledger, and artifact hashes;
- offline CPU-only tiny-model smoke run;
- success and failure-path tests;
- Ruff, strict mypy, pytest, and GitHub Actions;
- Revision 6 GitHub milestone closeout, release, project-history, research-log, and downloaded-document-ingest governance;
- prospective M2.5 RTX 5070 12 GB hardware-qualification/model-selection plan.

## Explicitly out of scope

- SchemaWorld scientific dynamics;
- Phase I benchmark items or treatment data;
- local LLM downloads or LoRA training;
- GPU scientific runs;
- Phase I gate evidence;
- Phase II or Phase III implementation.

## Verification

- CI workflow/run: `<fill after final branch push and merge>`
- `uv sync --locked`: passed locally; 28 packages resolved and 27 checked
- Ruff lint: passed locally
- Ruff formatting: passed locally; 26 files already formatted
- strict mypy: passed locally; 12 source files checked
- pytest: passed locally; 24 tests
- offline smoke: passed locally; run `milestone-0-smoke-20260824T134648910348Z-984b6be49b`
- merged tree clean and equal to `origin/main`: pending merge and post-merge closeout

## Scientific invariants checked

- [x] Phase I remains mandatory and permanent.
- [x] L3/L4 outcomes remain non-gating.
- [x] A text-oracle advantage does not fail Phase I.
- [x] No Phase II work is authorised without the gate.
- [x] M2.5 uses quarantined selection resources rather than final benchmark items.
- [x] The lexical embedding matrix remains frozen in the primary model posture.
- [x] This release makes no empirical claim about image-schema learning.

## Known limitations and unresolved questions

- Repository and documentation licensing remain unresolved.
- The exact Phase I model stack, gate thresholds, seeds, benchmark contents, and durable artifact archive remain open.
- Milestone 0 is engineering infrastructure only.

## Advancement decision

- Status: `NOT READY` — pending human review, merge, canonical sync, tag, and GitHub Release.
- Next authorised work after release: Milestone 1 — SchemaWorld Core.
- Owner/reviewer: `<fill after review>`
