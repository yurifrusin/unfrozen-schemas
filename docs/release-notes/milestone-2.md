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
  documentation. It contains no real benchmark item.
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

- Source snapshot: `983cfab2c885718e828eec131f3c10b52a29608f10e16344ab1c37245acede54`.
- Representative model-visible item:
  `2c0e44064cd0168b8d7bf93b21a28274f17e8df388b48b643d4b9d48ac9165e5`.
- Representative private answer:
  `2410ad382661e343aa9866d616a300d9d2d5b55a412e54f03d866a7a453f7628`.
- Candidate bundle root:
  `bf9a798de640766ae410f683f01edd8e51dd7e3ba991b650e261094225b66e32`.
- Public metadata bundle:
  `1c12719cd84e110ffc4494d3f3c4b2a836c2134232c47549798924b293292567`.
- Frozen-manifest logical-domain regression:
  `e52723e10f03bf446ec527c6045b2796e6042211db6dd8654b14f4519a9b0935`.

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
