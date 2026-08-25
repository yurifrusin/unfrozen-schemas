# Milestone 1 Release — SchemaWorld Core

> Draft implementation-branch record. Closeout fields remain placeholders until separate owner
> review, merge, canonical verification, tag creation, and GitHub Release publication.

## Identity

- Tag: `PENDING_CLOSEOUT` (`milestone-1-complete` must not be created by the implementation task)
- Commit: `PENDING_MERGED_COMMIT`
- Pull request: `PENDING_IMPLEMENTATION_PR`
- Release date: `PENDING_RELEASE_DATE`
- Release URL: `PENDING_RELEASE_URL`
- `CODEX_SPEC.md` SHA-256: `e5162c4d0e9e9ef54e86820393d99a4766e934cb3feba2bc2ea6a32b5586a911`
- Final owner approval: `PENDING_EXACT_PR_AND_HEAD_SHA`

## Scope completed

- Work packages: M1.1–M1.5 SchemaWorld Core only.
- Files/components: exact state/actions/events/protocol, containment/support dynamics, relations,
  matched pairs, opaque codec, Parquet persistence, renderer, manifests/accounting, CLI, tests,
  configuration, documentation, and same-job CPU CI smoke.
- Explicitly out of scope: benchmark items, treatments, adaptation, L1–L4 evaluation, model/GPU
  work, CausalSchemaLab, Phase I matrix/gate execution, Phase II, and Phase III.

## Verification

- CI workflow/run: `PENDING_FINAL_CI`
- Ruff: `PENDING_FINAL_RESULT`
- Formatting: `PENDING_FINAL_RESULT`
- Static typing: `PENDING_FINAL_RESULT`
- Pytest: `PENDING_FINAL_RESULT`
- Smoke/integration commands: `PENDING_FINAL_RESULT`
- Hardware/environment: CPU-only Windows owner workstation and GitHub Actions Linux;
  `PENDING_CROSS_PLATFORM_CONFIRMATION`.

## Scientific invariants checked

- [x] Phase boundaries preserved.
- [x] Required future controls remain explicit and unimplemented.
- [x] Released Milestone 0 schema-version-2 artifacts and `unfrozen smoke` remain unchanged.
- [x] Provenance and failed-run handling are covered.
- [x] No unlicensed data, weights, secrets, ordinary runs, benchmarks, or model artifacts are
  committed.
- [x] No scientific LLM or image-schema acquisition result is claimed.

## Known limitations and unresolved questions

- Repository and documentation licensing remain unresolved as recorded in `docs/open-questions.md`.
- SchemaWorld Core is deliberately minimal, deterministic apparatus and not Phase II causal richness.
- Final merged commit, CI, tag, release, approval, and advancement fields require separate closeout.

## Artifacts and hashes

- Representative matched-pair, opaque-codec, and raw-pixel hashes are pinned in
  `tests/regression/test_schemaworld_hashes.py`.
- Ordinary generated runs remain ignored; final review records canonical hashes rather than run
  directories.

## Advancement decision

- Milestone status: `PENDING_OWNER_REVIEW_AND_CANONICAL_CLOSEOUT`
- Next authorised milestone or repair: `PENDING_ADVANCEMENT_DECISION`
- Owner/reviewer: `PENDING_FINAL_OWNER_APPROVAL`
