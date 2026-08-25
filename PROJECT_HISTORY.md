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
