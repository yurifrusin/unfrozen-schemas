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
