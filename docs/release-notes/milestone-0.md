# Milestone 0 Release — Repository Foundation

> Canonical closeout record. Milestone 0 is complete only while the annotated tag and GitHub Release identified below remain visible at the canonical closeout commit.

## Identity

- Tag: `milestone-0-complete`
- Canonical implementation merge commit: `98e4a932cff37351efcf6873702aeb5c904fe53e`
- Implementation pull request: `https://github.com/yurifrusin/unfrozen-schemas/pull/1`
- Linked closeout pull request: `<fill from the mechanically constrained closeout pull request>`
- Release date: `2026-08-25`
- Release URL: `https://github.com/yurifrusin/unfrozen-schemas/releases/tag/milestone-0-complete`
- Revision 6 `CODEX_SPEC.md` SHA-256: `e5162c4d0e9e9ef54e86820393d99a4766e934cb3feba2bc2ea6a32b5586a911`

## Scope completed

- repository governance and authoritative specification;
- Python 3.11 and `uv` project scaffold;
- strict validated smoke configuration;
- Typer CLI;
- canonical JSON provenance, Git state, package/platform metadata, resource-budget schema version `2` with typed measurement bases, and artifact hashes;
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

- Final implementation CI workflow/run: `cpu` passed at `https://github.com/yurifrusin/unfrozen-schemas/actions/runs/32783255504/job/97609688068`
- `uv sync --locked`: passed locally with `uv 0.12.5`; 28 packages resolved
- Ruff lint: passed locally
- Ruff formatting: passed locally; 26 files already formatted
- strict mypy: passed locally; 12 source files checked
- pytest: passed locally; 31 tests passed
- offline smoke: passed locally; run `milestone-0-smoke-20260825T034715219278Z-1cccce044e`
- merged implementation tree: clean and equal to `origin/main` at `98e4a932cff37351efcf6873702aeb5c904fe53e` before the linked closeout record

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

- Status: `COMPLETE` when the declared annotated tag and GitHub Release are published from the merged linked-closeout commit
- Next authorised work: Milestone 1 — SchemaWorld Core, only after this closeout is published; Milestone 1 is not begun by this release
- Owner/reviewer: Yuri Frusin; approval recorded for pull request `#1` at exact head `b48ea734e41595ef1d071e52ee8a943c503ded44`
