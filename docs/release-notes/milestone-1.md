# Milestone 1 Release — SchemaWorld Core

> Canonical closeout record. Milestone 1 is complete only while the annotated tag and GitHub
> Release identified below remain visible at the canonical linked-closeout commit.

## Identity

- Tag: `milestone-1-complete`
- Milestone 0 branch point and tag target: `a1712c7d6229fd90c5619414fc13fa1a21a4cd22`
  (`milestone-0-complete`)
- Implementation pull request: `https://github.com/yurifrusin/unfrozen-schemas/pull/3`
- Owner-approved implementation head: `e6e6d81128ff619679539ba99cb8545adbd84e8e`
- Canonical implementation merge commit and closeout branch point:
  `cff2840db09dd0dcf3a37b7c42b58aac9cf5e105`
- Linked closeout pull request: `PENDING_LINKED_CLOSEOUT_PR`
- Release date: `2026-08-25`
- Release URL: `https://github.com/yurifrusin/unfrozen-schemas/releases/tag/milestone-1-complete`
- Revision 6 `CODEX_SPEC.md` SHA-256:
  `e5162c4d0e9e9ef54e86820393d99a4766e934cb3feba2bc2ea6a32b5586a911`

## Scope completed

- **M1.1 — exact state and action contracts:** immutable integer/fixed-point state, canonical
  identifiers and ordering, validated references, deterministic `splitmix64-v1` reset inputs,
  delayed-event queues, and a typed Gymnasium-style internal reset/step protocol.
- **M1.2 — CONTAINMENT and SUPPORT dynamics:** pure deterministic transitions, explicit stage/event
  order, impeded exits, support loss, attachment/tension support, gravity, collision, and delayed
  events.
- **M1.3 — relations and matched counterfactuals:** relations derived only from privileged state and
  transition traces, target-factor-only matched-pair auditing, and stable pair/episode identities.
- **M1.4 — opaque codec, persistence, renderer, and inspection:** reversible `opaque-byte-v1`,
  explicit Parquet schemas, canonical logical and artifact hashes, independent validation, complete
  replay, and CPU-only `schemaworld-raster-v1` inspection rendering.
- **M1.5 — integration and acceptance:** both schemas and all three template families generated at
  two seeds, independently validated, replayed, rendered, provenance-recorded, and covered by the
  complete offline quality suite.

Explicitly out of scope were benchmark construction, treatments, L1–L4 evaluation, model or
tokenizer changes, training, GPU work, Phase I matrix/gate execution, CausalSchemaLab, Phase II, and
Phase III.

## Frozen Milestone 1 contracts

- **Tether contract:** in `schemaworld-core-v1`, every active load-bearing tether is an exact taut
  inextensible link. The anchor centre is above the object centre and the squared doubled-centre
  distance equals `(2 * declared_length)^2` using integer arithmetic. Overlength, underlength/slack,
  inactive-endpoint, and non-above-anchor load-bearing states are invalid. Slack-to-taut motion is
  not implemented; an action producing an invalid tether successor raises `IllegalActionError`.
- **Finite-wall containment contract:** an axis-aligned swept movement intersects a left/right or
  bottom/top wall only when the moving body's fixed orthogonal interval positively overlaps the
  container's finite outer orthogonal interval. Exact tangency is non-colliding; one-microunit
  positive overlap is collision-relevant. Every intersected finite wall segment requires an enabled
  opening on that side whose inclusive span contains the full orthogonal object extent.
- **Action contract:** serialized action fields are canonical and kind-specific. M1 implements
  `MOVE`, `OPEN`, `CLOSE`, `DETACH`, `CUT_OR_BREAK`, `WAIT`, `NOOP`, and the Phase I aliases `ENTER`,
  `EXIT`, `OPEN_GATE`, `CLOSE_GATE`, and `REMOVE_SUPPORT`. Unsupported prospective actions raise
  `UnsupportedActionError`; malformed or state-invalid implemented actions raise
  `IllegalActionError`; rejected actions do not consume environment-step budget.
- **Pair-identity contract:** `pair_id` uses the first 16 hexadecimal characters of the canonical
  pre-ID payload covering environment/template identity, both seeds, gravity, horizon, both complete
  initial states and action sequences, target-factor declaration, and declared difference paths.
  The payload excludes final pair and episode IDs. Episode IDs use the same pre-ID payload plus the
  condition index, avoiding circular identity fields while covering every causal input.
- **Validation contract:** `validate-core` independently requires the exact artifact set and safe
  run-relative paths; parses every canonical typed state, observation, action, trace, relation, and
  opaque record; checks plan/row continuity; recomputes observations and transitions; and verifies
  every step, aggregate, final-state, render, budget, configuration, and artifact hash. Replay
  validation additionally verifies both complete episode-digest sets, IDs, pair membership, and the
  source-manifest hash.

## Dependencies and licences

| Dependency | Exact version | Milestone 1 use | Upstream licence |
|---|---:|---|---|
| PyArrow | `25.0.1` | Explicit Parquet schemas and round trips | Apache-2.0 |
| Pillow | `12.3.0` | Packaging deterministic raw RGB pixels as inspection PNG | MIT-CMU |

No PyTorch, Transformers, PEFT, Accelerate, bitsandbytes, Gymnasium, model weights, GPU runtime, or
network service was added.

## Verification

- Implementation PR CI: workflow `ci`, job `cpu`, run
  `https://github.com/yurifrusin/unfrozen-schemas/actions/runs/32831001607`, passed on the exact
  approved head `e6e6d81128ff619679539ba99cb8545adbd84e8e`.
- Canonical implementation-main CI: workflow `ci`, job `cpu`, run
  `https://github.com/yurifrusin/unfrozen-schemas/actions/runs/32843080885`, passed on
  `cff2840db09dd0dcf3a37b7c42b58aac9cf5e105`.
- Final Windows environment: Microsoft Windows 11 Pro 64-bit `10.0.26200` (build `26200`),
  PowerShell `7.6.4`, CPython `3.11.7`, package `unfrozen-schemas 0.1.0`, CPU-only and offline.
- Ruff lint: passed.
- Ruff formatting: passed; 56 files already formatted.
- Strict mypy: passed; 40 source/test files checked.
- Pytest: passed; 161 tests on Windows/Python 3.11.7, including all five pinned regression tests.
- Milestone 0 offline smoke: passed as
  `milestone-0-smoke-20260825T113829114090Z-d8a2ddb84e`.
- Core generation: passed as
  `milestone-1-core-smoke-20260825T113836716214Z-fbc3e0ebf2`; 12 episodes and 6 matched pairs.
- Independent source validation: passed; all 12 episodes and 6 pairs verified.
- Complete replay: passed as
  `milestone-1-core-replay-20260825T113908012344Z-b75946796a`; 12 episodes and 6 pairs.
- Independent replay validation: passed; all replayed episodes, pairs, source identity, and hashes
  verified.
- Representative tension inspection: passed for `ep-4aaab40d3001244c-1`, with raw-pixel render hash
  `73865a3936270878554b10b0b2549fa262819f711b11d4ab88c21c79f78a8448`.
- The local verification used the existing locked project virtual environment because the standalone
  `uv` executable was not available on that shell's `PATH`; canonical GitHub Actions independently
  performed `uv sync --locked` with pinned `uv 0.12.5` before every required check.

## Pinned regression identities

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

All five identities remained unchanged by the final finite-wall containment correction and after
the canonical implementation merge.

## Scientific status and invariants

- Milestone 1 is deterministic experimental apparatus only.
- This release makes no empirical claim about LLM image-schema acquisition, transfer, metaphor,
  grounding, or Phase I gate status.
- Phase I remains a permanent mandatory calibration and gate; L3 abstract and L4 metaphor outcomes
  remain non-gating.
- Required future causal/shuffled, active/yoked, raw/language, trained/untrained-schema, and
  closed/open-book comparisons remain explicit and unimplemented.
- No benchmark, LLM, tokenizer, training, or GPU work occurred during closeout.

## Known limitations and unresolved questions

- Repository and documentation licensing remain unresolved in `docs/open-questions.md`.
- SchemaWorld Core is deliberately minimal deterministic apparatus, not Phase II causal richness.
- Slack-to-taut tether motion is not implemented; active load-bearing tethers must already be taut.
- Rendering is an inspection aid and is not consulted by scientific transitions.
- Ordinary generated runs remain ignored and are not attached to the release; canonical source,
  configuration, regression identities, and run IDs preserve the verification record.

## Advancement decision

- Status: `COMPLETE` when the linked closeout PR is merged and the annotated
  `milestone-1-complete` tag and non-draft, non-prerelease GitHub Release are published from that
  canonical linked-closeout merge commit.
- Next authorised work: Milestone 2 — benchmark construction, hardware qualification, and
  model-stack freeze, only after this closeout is fully published.
- Milestone 2 was not begun by the implementation merge or this closeout.
- Owner/reviewer: Yuri Frusin; approval recorded for pull request `#3` at exact head
  `e6e6d81128ff619679539ba99cb8545adbd84e8e`.
