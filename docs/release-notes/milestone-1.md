# Milestone 1 Release — SchemaWorld Core

> Draft implementation-branch record. Closeout fields remain placeholders until separate owner
> review, merge, canonical verification, tag creation, and GitHub Release publication.

## Identity

- Tag: `PENDING_CLOSEOUT` (`milestone-1-complete` must not be created by the implementation task)
- Commit: `PENDING_MERGED_COMMIT`
- Pull request: `#3` (`https://github.com/yurifrusin/unfrozen-schemas/pull/3`)
- Release date: `PENDING_RELEASE_DATE`
- Release URL: `PENDING_RELEASE_URL`
- `CODEX_SPEC.md` SHA-256: `e5162c4d0e9e9ef54e86820393d99a4766e934cb3feba2bc2ea6a32b5586a911`
- Final owner approval: `PENDING_EXACT_PR_AND_HEAD_SHA`

## Scope completed

- Work packages: M1.1–M1.5 SchemaWorld Core only.
- Files/components: exact state/actions/events/protocol, containment/support dynamics, relations,
  matched pairs, opaque codec, Parquet persistence, renderer, manifests/accounting, CLI, tests,
  configuration, documentation, and same-job CPU CI smoke.
- Pre-release correction: exact taut tether invariants, exact swept boundary-plane crossings,
  canonical per-kind action fields, complete pre-ID pair identities, independent typed persisted-step
  verification, fail-closed state-graph/reference validation, and complete privileged-relation
  leakage vocabulary.
- Explicitly out of scope: benchmark items, treatments, adaptation, L1–L4 evaluation, model/GPU
  work, CausalSchemaLab, Phase I matrix/gate execution, Phase II, and Phase III.

## Verification

- CI workflow/run: `PENDING_FINAL_CI`
- Ruff: `PASS` on the pre-commit correction tree.
- Formatting: `PASS`; 56 files checked.
- Static typing: `PASS`; 40 source/test files checked by strict mypy.
- Pytest: `PASS`; 148 tests on Windows/Python 3.11.7.
- Smoke/integration commands: `PASS`; Milestone 0 smoke plus 12-episode/6-pair Core generation,
  independent validation, complete replay, and representative tension rendering.
- Hardware/environment: CPU-only Windows owner workstation and GitHub Actions Linux;
  Windows `PASS`, Linux `PENDING_FINAL_CI`.

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
- `schemaworld-core-v1` prohibits slack active load-bearing tethers rather than implementing
  slack-to-taut motion; this is an intentional M1 boundary, not a released compatibility exception.
- Final merged commit, CI, tag, release, approval, and advancement fields require separate closeout.

## Artifacts and hashes

- Representative hashes pinned in `tests/regression/test_schemaworld_hashes.py`:
  - containment matched pair:
    `09bd2fb9ee22cc6fe21af537518e9f57c59022d64f3ac80e4b476b89314949a0`;
  - ordinary platform-support matched pair:
    `d8191a727e0f0c24ed11780a506c76f60157c79aed9f265825c5735ae2031a5f`;
  - tension-support matched pair:
    `1dbcc1d9368e4baf68349ff6f0edeb832c52406c2ecdc6d4a3eed77bf193ef37`;
  - containment opaque observation:
    `692787a3aeb85692cff5a71317cc6133ba81017cc2e09eef7405d6ae755f1c63`;
  - tension final-state raw pixels:
    `73865a3936270878554b10b0b2549fa262819f711b11d4ab88c21c79f78a8448`.
- All three pair hashes changed because the pair and episode IDs now derive from the complete causal
  pre-ID payload. The tension pair also changes its tether field from maximum range to exact length.
  The opaque and raw-pixel hashes remain unchanged because their canonical containment observation
  bytes and final tension pixels are unchanged.
- Ordinary generated runs remain ignored; final review records canonical hashes rather than run
  directories.

## Advancement decision

- Milestone status: `PENDING_OWNER_REVIEW_AND_CANONICAL_CLOSEOUT`
- Next authorised milestone or repair: `PENDING_ADVANCEMENT_DECISION`
- Owner/reviewer: `PENDING_FINAL_OWNER_APPROVAL`
