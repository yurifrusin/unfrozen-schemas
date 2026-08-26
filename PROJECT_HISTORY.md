# Project history

This file records factual project chronology. It does not override `CODEX_SPEC.md`, frozen scientific artifacts, or Git history.

## 2026-08-24

### Initial repository specification

- Repository created as `yurifrusin/unfrozen-schemas`.
- Revision 4 specification committed to `main` at `27ab8dfa479343b0df4985746faf70558e76e506`.
- Phase I was formalised as a mandatory permanent calibration and gate.
- Phase I L3 abstract and L4 metaphorical transfer were explicitly made non-gating.

### Milestone 0 foundation branch

- Branch: `codex/milestone-0-foundation`.
- Initial implementation commit: `69ad9a644ead01289d1d9a86da2aa94b5633ee42`.
- Implemented governance documents, Python/uv scaffold, configuration validation, provenance and budget records, offline smoke execution, tests, and CPU-only CI.
- Pre-merge hardening commit: `ba027b46acb41b87e57718935b6f26af045c86e2`.
- Pull request: `https://github.com/yurifrusin/unfrozen-schemas/pull/1`.
- Bootstrap failures, failure-artifact validation, original-exception preservation, and immutable checkout pinning were completed before Revision 6 ingestion.
- Status at the time of this entry: pending Revision 6 review, merge, milestone tag, and GitHub Release.

### Revision 5 hardware envelope

- Local compute constraint recorded as one NVIDIA RTX 5070 with 12 GB VRAM.
- M2.5 hardware qualification and model selection inserted before final benchmark freeze.
- Primary model envelope narrowed to approximately 0.8–2.2B text-only base models, preferring BF16 LoRA when qualified.
- QLoRA retained as a separately fingerprinted fallback or replication path.

### Revision 6 repository governance

- Documentation archive `unfrozen-schemas-revision6-documentation.zip` verified at SHA-256 `6d7cdf3108db1c15627d542ff585f44a8a26a748bebd72189abce50887680473` before ingestion.
- Revision 6 `CODEX_SPEC.md` installed at SHA-256 `658592b974d24ab6f0b9f742fa68d26cb4515a4a727239392bab0c5971fb864a`.
- `origin/main` established as canonical public history.
- Milestone closeout defined as reviewed merge, local synchronisation, immutable annotated tag, pushed tag, GitHub Release, and current project/research records.
- `PROJECT_HISTORY.md` and `RESEARCH_LOG.md` introduced.
- Controlled document ingestion from the owner-workstation staging directory documented.

## 2026-08-25

### Milestone 0 canonical closeout

- Owner approval identified pull request `#1` and exact head `b48ea734e41595ef1d071e52ee8a943c503ded44`.
- Pull request `https://github.com/yurifrusin/unfrozen-schemas/pull/1` was revalidated as mergeable with its required `cpu` check passing and no unresolved review threads, then merged into `origin/main` at `98e4a932cff37351efcf6873702aeb5c904fe53e`.
- Local `main` was fast-forwarded to that canonical implementation merge and verified clean and equal to `origin/main`.
- Post-merge verification passed: locked dependency synchronisation, Ruff lint and formatting, strict mypy over 12 source files, all 31 pytest tests, and offline CPU smoke run `milestone-0-smoke-20260825T034715219278Z-1cccce044e`.
- Revision 6 `CODEX_SPEC.md` remained unchanged at SHA-256 `e5162c4d0e9e9ef54e86820393d99a4766e934cb3feba2bc2ea6a32b5586a911`.
- Linked closeout pull request: `https://github.com/yurifrusin/unfrozen-schemas/pull/2`.
- The immutable annotated tag is `milestone-0-complete`; its GitHub Release is `https://github.com/yurifrusin/unfrozen-schemas/releases/tag/milestone-0-complete`.
- Repository and documentation licensing remain unresolved.
- Advancement decision: Milestone 0 is complete only after the linked closeout record is merged and that tag and release are published from canonical `main`; Milestone 1 is then authorised but is not begun by this closeout.

### Main protection and Milestone 1 branch start

- Canonical branch point: `a1712c7d6229fd90c5619414fc13fa1a21a4cd22`, equal to local
  `main`, `origin/main`, and the target of `milestone-0-complete` at task preflight.
- Repository ruleset `21295385` was activated specifically for `refs/heads/main` after its initial
  empty branch target was found ineffective.
- Effective rules require pull requests, the strict/up-to-date `cpu` check from GitHub Actions app
  ID `15368`, zero approving reviews, and resolved review conversations; they prohibit branch
  deletion and non-fast-forward pushes.
- CODEOWNERS review, signed commits, linear history, merge queue, and automatic merging are not
  required. Repository administrators retain a bypass for exceptional recovery, not routine
  milestone work.
- Milestone 1 branch started as `codex/milestone-1-schemaworld-core` from the exact canonical branch
  point above.
- Status: Milestone 1 implementation is in progress and is not a completed, merged, tagged, or
  released milestone.

### Milestone 1 pre-release causal-contract correction

- Continued on `codex/milestone-1-schemaworld-core` and pull request
  `https://github.com/yurifrusin/unfrozen-schemas/pull/3` from pre-correction head
  `34735ae73515cd6271d7b0c5e546b440bf82971d`.
- Tightened the unreleased SchemaWorld Core contract for exact taut tether support, swept containment
  crossings, canonical per-kind action parameters, complete pair identities, independent persisted
  trajectory verification, state-graph references, explicit observation codes, and relation leakage.
- The environment remains `schemaworld-core-v1` because no Milestone 1 compatibility promise or
  scientific artifact has been released.
- Status: correction work remains on the open implementation pull request and is not merged, tagged,
  released, scientifically frozen, or a completed milestone.

### Milestone 1 finite-wall containment correction

- Continued on `codex/milestone-1-schemaworld-core` and pull request
  `https://github.com/yurifrusin/unfrozen-schemas/pull/3` from pre-correction head
  `4d2c14a8bd1b40eddf3319cbb357f872270618d3`.
- Constrained swept containment checks to finite rectangular wall extents: a movement-axis plane is
  relevant only when the object's fixed orthogonal interval positively overlaps the container's
  outer orthogonal interval; exact tangency remains non-colliding.
- The tracked template states and actions remain unchanged, and all five pinned pair, opaque-codec,
  and raw-render regression identities remain unchanged.
- Status: the correction remains on the open implementation pull request and is not merged, tagged,
  released, scientifically frozen, or a completed milestone.

### Milestone 1 canonical implementation merge and closeout

- Milestone 1 began from canonical branch point
  `a1712c7d6229fd90c5619414fc13fa1a21a4cd22`, the target of `milestone-0-complete`.
- Owner approval identified implementation pull request `#3` and exact head
  `e6e6d81128ff619679539ba99cb8545adbd84e8e`.
- Pull request `https://github.com/yurifrusin/unfrozen-schemas/pull/3` was revalidated as open,
  non-draft, mergeable into `main`, with zero review threads or findings and its required `cpu`
  check passing in workflow run `32831001607` on the exact approved head.
- The implementation was merged normally, without squash, rebase, rewrite, or administrator bypass,
  at `2026-08-25T11:35:12Z`. The canonical implementation merge commit is
  `cff2840db09dd0dcf3a37b7c42b58aac9cf5e105`.
- Push-triggered canonical-main workflow run `32843080885` passed job `cpu` on that merge commit.
- Local `main` was fast-forwarded to the canonical implementation merge and verified clean, equal to
  `origin/main`, and unchanged at Revision 6 `CODEX_SPEC.md` SHA-256
  `e5162c4d0e9e9ef54e86820393d99a4766e934cb3feba2bc2ea6a32b5586a911`.
- The linked documentation-only closeout branch is `codex/milestone-1-closeout`, created from exact
  branch point `cff2840db09dd0dcf3a37b7c42b58aac9cf5e105`; linked closeout pull request:
  `https://github.com/yurifrusin/unfrozen-schemas/pull/4`.
- Final Windows verification passed Ruff lint and formatting, strict mypy over 40 source/test files,
  all 161 pytest tests on Python 3.11.7, Milestone 0 offline smoke, 12-episode/6-pair Core
  generation, independent source validation, complete replay, independent replay validation, and
  representative tension rendering. All five pinned regression identities remained unchanged.
- The released environment identity is `schemaworld-core-v1`, with integer scientific state,
  `splitmix64-v1`, `opaque-byte-v1`, and `schemaworld-raster-v1`. Direct M1 dependencies are
  PyArrow `25.0.1` (Apache-2.0) and Pillow `12.3.0` (MIT-CMU).
- The effective active `main` ruleset remained `21295385`: pull request required, strict/up-to-date
  `cpu` required, conversations resolved, deletion and non-fast-forward updates prohibited, and zero
  approving reviews required. The administrator bypass was not used.
- Completion depends on merging the linked closeout PR and publishing the immutable annotated
  `milestone-1-complete` tag and GitHub Release from its canonical merge commit.
- Milestone 1 is deterministic experimental apparatus only and makes no empirical claim about LLM
  image-schema acquisition. Repository and documentation licensing remain unresolved.
- Advancement decision: Milestone 2 is the next authorised work only after complete publication of
  this closeout; Milestone 2 was not begun. No benchmark, LLM, tokenizer, training, or GPU work
  occurred during closeout.

### 2026-08-25 — Milestone 2 M2.1 branch start

- Canonical branch point: `73a787b3f0c25b78962ac13fb3b26c1cc50f0dae`, equal to local
  `main`, `origin/main`, and the target of annotated `milestone-1-complete` at preflight.
- Branch: `codex/milestone-2-m2-1-benchmark-lifecycle`.
- Prior tag object: `21a5e615553cf63ddb1da91000889bb8ee657a21`.
- Revision 6 `CODEX_SPEC.md` SHA-256:
  `e5162c4d0e9e9ef54e86820393d99a4766e934cb3feba2bc2ea6a32b5586a911`.
- Active main ruleset: `21295385`, requiring pull requests, resolved conversations, and strict
  required `cpu`; deletion and non-fast-forward updates remain prohibited.
- Work is limited to M2.1 benchmark schema/lifecycle mechanics and one non-scientific engineering
  fixture. No M2.2-M2.6 content, model, GPU, selection probe, or production freeze is part of it.
- Status: implementation work in progress; no merge, tag, release, benchmark freeze, or Milestone 2
  completion has occurred.

## 2026-08-26

### Milestone 2 M2.1 pre-merge integrity correction

- Continued on `codex/milestone-2-m2-1-benchmark-lifecycle` and pull request
  `https://github.com/yurifrusin/unfrozen-schemas/pull/5` from pre-correction head
  `e68bd1fc91a32674008383121df5779722110522`.
- Replaced optional operator-supplied purpose comparison with a mandatory hash-bound scan of every
  canonical benchmark root for non-engineering candidates; engineering fixtures retain only an
  explicit empty scope.
- Hardened purpose-neutral fingerprints, reverse-pair equivalence, recursive public-data isolation,
  candidate/header and operation consistency, atomic post-publication failure, benchmark-version
  path resolution, and the tracked benchmark-path allowlist.
- Recalculated the engineering-only regression identities because quarantine declarations and
  identities now participate in the source, candidate, public, approval, and frozen chains. The
  purpose-bound representative visible-item and private-answer hashes remain unchanged.
- Status: correction remains part of the open M2.1 implementation PR. No merge, tag, release,
  production benchmark content, M2.2 work, model access, or GPU work has occurred.

### Milestone 2 M2.1 canonical-storage correction

- Continued on `codex/milestone-2-m2-1-benchmark-lifecycle` and pull request
  `https://github.com/yurifrusin/unfrozen-schemas/pull/5` from pre-correction head
  `23ce324f6fa8865d3d5acbcbb9deae270f4e7209`.
- Bound outcome/retention candidates to `benchmarks/private/<version>`, selection candidates to
  `benchmarks/selection/<version>`, and otherwise authorised non-engineering frozen versions to
  `benchmarks/frozen/<version>`; copied or arbitrary scientific locations now fail validation,
  approval use, and freeze.
- Added selection-root version lookup with incompatible-root ambiguity refusal, refused every
  selection-purpose freeze throughout M2.1, and made PRIVATE post-publication read-back failure
  quarantine or remove the candidate while preserving the original exception.
- Paths remain outside logical identities, and all engineering-fixture regression identities remain
  unchanged.
- Status: correction remains part of the open M2.1 implementation PR. No merge, tag, release,
  production benchmark content, M2.2 work, model access, or GPU work has occurred.

## Entry template

### YYYY-MM-DD — <event>

- Branch or canonical tag:
- Pull request:
- Merged commit:
- Specification revision and hash:
- Work completed:
- Tests and CI:
- Known limitations:
- Advancement decision:
- Next authorised work:
