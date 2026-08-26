# Milestone 2 Release — Benchmark, qualification, and stack freeze

> Draft work-in-progress record. Milestone 2 is not complete, `v1_core` is not frozen, and no tag or
> release is authorised by M2.1.

## Identity

- Tag: `<blocked until all M2.1-M2.6 work and canonical closeout>`
- Commit: `<pending final Milestone 2 canonical merge>`
- Implementation pull requests: `<M2.1 pending; M2.2-M2.6 pending>`
- Final milestone merge: `<pending>`
- Release date: `<pending>`
- Release URL: `<pending>`
- `CODEX_SPEC.md` SHA-256:
  `e5162c4d0e9e9ef54e86820393d99a4766e934cb3feba2bc2ea6a32b5586a911`

## Work-package status

- **M2.1 — benchmark schema and lifecycle:** work in progress on a dedicated branch. Implements
  purpose quarantine, strict item/answer/approval records, distinct hash domains, answer-isolated
  deterministic build, independent validation, governed write-once engineering freeze, tests, and
  documentation. The pre-merge correction makes quarantine a mandatory hash-bound canonical-root
  scan; adds purpose-neutral exact-display and order-neutral fingerprints; freezes the reverse-pair
  equivalence contract; completes recursive public isolation and cross-record consistency; makes
  post-publication failure atomic; and replaces version-path and tracked-file heuristics with
  fail-closed validation. It contains no real benchmark item.
- **M2.2 — literal/counterfactual families:** pending.
- **M2.3 — abstract/metaphorical families:** pending.
- **M2.4 — scoring, option order, leakage, retention:** pending.
- **M2.5 — RTX 5070 qualification/model selection and `selection_probe_v1`:** pending.
- **M2.6 — approved production `v1_core` freeze:** pending and blocked by M2.2-M2.5 plus owner
  decisions/approvals.

## Explicit M2.1 exclusions

- No real Phase I question, final target domain, external diagnostic, or Wang–Liao-derived content.
- No selection probe, scoring/evaluator, leakage comparison against treatment data, retention
  evaluation, model, tokenizer, LoRA/QLoRA, PyTorch, CUDA, GPU, or model download.
- No human recruitment or fabricated validation, rights, ethics, licence, seed, threshold, stack,
  public/private-release, or durable-archive decision.
- No `v1_core` production freeze, benchmark/scientific tag, release, or Milestone 2 completion claim.

## Verification

- Final M2.1 branch CI: `<pending exact cpu run>`
- Ruff: `<pending final>`
- Formatting: `<pending final>`
- Static typing: `<pending final>`
- Pytest: `<pending final>`
- Benchmark lifecycle smoke: `<pending final>`
- Existing M0/M1 smoke and SchemaWorld generation/replay: `<pending final>`

## Final Milestone 2 artifacts still required

- Approved final benchmark and card: `<pending>`
- Model-selection report/approval: `<pending>`
- Frozen `v1_core` checkpoint/tag/release: `<pending>`
- Final CI, tag, release date, release URL, and advancement decision: `<pending>`

## M2.1 engineering-fixture regression identities

| Identity | Previous | Corrected | Reason |
|---|---|---|---|
| Source snapshot | `983cfab2c885718e828eec131f3c10b52a29608f10e16344ab1c37245acede54` | `ad8d51beea8582ab88533d928e3fee91a7449f0424518da4e0360cfb9fa078e3` | The source header now binds the mandatory quarantine declaration. |
| Representative model-visible item | `2c0e44064cd0168b8d7bf93b21a28274f17e8df388b48b643d4b9d48ac9165e5` | unchanged | Its purpose-bound visible-item domain did not change. |
| Representative private answer | `2410ad382661e343aa9866d616a300d9d2d5b55a412e54f03d866a7a453f7628` | unchanged | The private-answer record domain did not change. |
| Private-answer bundle | `06347cb6ccea1e406efb8a5e5fa5c3336e1749f0836ebd1e685f08649c6eac0e` | unchanged | Neither private answers nor their bundle framing changed. |
| Candidate bundle root | `bf9a798de640766ae410f683f01edd8e51dd7e3ba991b650e261094225b66e32` | `4cad3f2bc0d4696906ad8f1653350c59d73aeac88ec6db2473e809a349025243` | It now binds the quarantine scope and built items contain the two new content fingerprints. |
| Public metadata bundle | `1c12719cd84e110ffc4494d3f3c4b2a836c2134232c47549798924b293292567` | `fe5e99d452c7002aee635d7ef93dcbe3548d23244b8a1579957ac956b2768496` | Safe public metadata now binds the quarantine-scope identity and corrected candidate root. |
| Frozen-manifest logical-domain regression | `e52723e10f03bf446ec527c6045b2796e6042211db6dd8654b14f4519a9b0935` | `4055288eff1e25ed5bcd710e8ad2922b62175dc0aea4a6b994807127a6008a41` | The frozen manifest now binds the quarantine-scope identity. |

New identities have no obsolete predecessor:

- Engineering-empty quarantine scope:
  `a06591a6eb3808f687f2a9f3ac9d5315cf0bef9d653714f30158e3ff65b8ac07`.
- Representative exact displayed-input fingerprint:
  `01b00a5aadd302f0e9aab72032279f2b70ab8ea058cc3f32889b1dd597c6788e`.
- Representative order-neutral item-content fingerprint:
  `d432c21c9ce5037cb3e4f4e124d83da37faca14b8c329fcec9f84469059c3a2f`.

These identities are engineering regression data only and are not benchmark evidence.

## Known limitations and unresolved questions

All existing `docs/open-questions.md` entries remain unresolved. In particular, benchmark contents,
public/private split, human-validation protocol, ethics determination, repository/benchmark
licensing, model stack, Phase I seeds/thresholds, and durable external archive remain owner decisions.

## Advancement decision

- Milestone status: `IN PROGRESS`.
- M2.1 merge, when separately approved, will not complete Milestone 2.
- Next authorised work after M2.1 closeout: only the separately scoped subsequent Milestone 2 work
  package; do not begin it in the M2.1 implementation task.
