# Milestone 2 Release — Benchmark, qualification, and stack freeze

> Draft work-in-progress record. M2.1 and M2.2 are completed and merged, but Milestone 2 is not
> complete, `v1_core` is not frozen, and no tag or release is authorised by the M2.2 closeout.

## Identity

- Tag: `<blocked until all M2.1-M2.6 work and canonical closeout>`
- Commit: `<pending final Milestone 2 canonical merge>`
- Implementation pull requests: `M2.1: #5 merged; M2.2: #7 merged; M2.3-M2.6 pending`
- Final milestone merge: `<pending>`
- Release date: `<pending>`
- Release URL: `<pending>`
- `CODEX_SPEC.md` SHA-256:
  `e5162c4d0e9e9ef54e86820393d99a4766e934cb3feba2bc2ea6a32b5586a911`

## Work-package status

- **M2.1 — benchmark schema and lifecycle:** completed and merged through pull request `#5` at
  approved head `c2f78a8512a2db8c547955b50184c406153cc59d`; canonical implementation merge
  `90c3428f70e03c3cf31e3e2309a65a2340f41cd1`; final implementation-main workflow run
  `32922535140`, job `cpu`, passed. Implements
  purpose quarantine, strict item/answer/approval records, distinct hash domains, answer-isolated
  deterministic build, independent validation, governed write-once engineering freeze, tests, and
  documentation. The pre-merge correction makes quarantine a mandatory hash-bound canonical-root
  scan; adds purpose-neutral exact-display and order-neutral fingerprints; freezes the reverse-pair
  equivalence contract; completes recursive public isolation and cross-record consistency; makes
  post-publication failure atomic; and replaces version-path and tracked-file heuristics with
  fail-closed validation. The final storage correction binds every non-engineering candidate and
  frozen manifest to its exact purpose-specific repository location, resolves selection versions
  from their own root, refuses every M2.1 selection freeze, and gives PRIVATE publication the same
  fail-closed post-rename handling as FROZEN publication. It contains no real benchmark item.
  The engineering fixture is regression evidence for the lifecycle implementation only and is not
  scientific benchmark evidence. No empirical LLM result is claimed.
- **M2.2 — literal/counterfactual families:** completed and merged through pull request `#7` at
  approved head `aa8a828f323f5c3f31a8a6048b5e1857ec314569`; exact-head review converged as
  `ENGINEERING_PASS` and `SCIENTIFIC_PASS`; canonical implementation merge
  `2fb34969c74df359587ac510f0c108c9b4fdccdd`; final implementation-main workflow run
  `33077391425`, job `cpu` (`98535071632`), passed. The owner accepted the exact category
  memberships for necessary causal-condition vocabulary
  (`c588337741cdf1d3afde972b1fe8c9cf0362b536f24b98ab8d19cfe7f99e9f4c`), physical-mechanism
  correlation (`065ec3948b1fa996bdacc692a7c1081defa1bf8a97dfd0c3f1fb6104ae4d2a51`), and
  duplicate/matched wording (`074718208b44444beb500953da5df718477355646ca707cdb0a99894e8860152`).
  Approved aggregate identities include literal source bundle
  `030d0dffdc574334844126f97ac65b4b94a086c7ea875e12afc139d06fb6cb59`, M2.1 candidate root
  `935e8c81d2367c55bf8230d7d9aa3e4e0c4ff4f69865c169439af1275133c4fe`, lexical audit
  `23d4e5e11238b8041891f82cf84b24f0fffa8225280b544ec53ee73876b7631e`, M2.2 composite root
  `3011c24f0592ecf627e8ada93350d7bb6056e16bbcbf65e9d538d4cbf06afc14`, review-content bundle
  `3d9e10ad32ac0d83d4254cc480eef24396e60431226c5822e944d8f37c4535d4`, and review-manifest
  logical root `cb5b8a445ec2616d0cb11c956637116a3b8271553543a18bf3c1f1439df8bc0e`.
  This acceptance makes no lexical-neutrality or empirical claim. Duplicate/matched wording remains
  non-independent and creates an M2.4 clustering/weighting obligation; tokenizer-specific and
  broader model-facing cue checks remain pending. Human validation, rights, ethics, and future
  treatment overlap remain unresolved.
- **M2.3 — abstract/metaphorical families:** pending.
- **M2.4 — scoring, option order, leakage, retention:** pending.
- **M2.5 — RTX 5070 qualification/model selection and `selection_probe_v1`:** pending.
- **M2.6 — approved production `v1_core` freeze:** pending and blocked by M2.3-M2.5 plus owner
  decisions/approvals.

## Explicit M2.1-M2.2 exclusions

- No real Phase I question, final target domain, external diagnostic, or Wang–Liao-derived content.
- No selection probe, scoring/evaluator, leakage comparison against treatment data, retention
  evaluation, model, tokenizer, LoRA/QLoRA, PyTorch, CUDA, GPU, or model download.
- No human recruitment or fabricated validation, rights, ethics, licence, seed, threshold, stack,
  public/private-release, or durable-archive decision.
- No `v1_core` production freeze, benchmark/scientific tag, release, or Milestone 2 completion claim.
- No empirical result or Phase I gate claim; owner cue acceptance does not establish lexical
  neutrality or independent evidence from cosmetic variants.

## Verification

- Final M2.1 branch CI: workflow run `32918619766`, job `cpu`, passed on approved head
  `c2f78a8512a2db8c547955b50184c406153cc59d`.
- Final implementation-main CI: workflow run `32922535140`, job `cpu`, passed on canonical merge
  `90c3428f70e03c3cf31e3e2309a65a2340f41cd1`.
- The successful `cpu` jobs ran Ruff lint and formatting, strict static typing, pytest, offline CPU
  smoke, SchemaWorld Core generation/replay smoke, and benchmark lifecycle engineering smoke.
- Revision 6 `CODEX_SPEC.md` SHA-256 remained
  `e5162c4d0e9e9ef54e86820393d99a4766e934cb3feba2bc2ea6a32b5586a911`.

## Final Milestone 2 artifacts still required

- Approved final benchmark and card: `<pending>`
- Model-selection report/approval: `<pending>`
- Frozen `v1_core` checkpoint/tag/release: `<pending>`
- Final CI, tag, release date, release URL, and advancement decision: `<pending>`

## M2.1 engineering-fixture regression identities

The canonical-storage correction changes only operational path validation. Paths remain excluded
from logical records and hashes, so all corrected engineering-fixture identities below remain
unchanged by this pass.

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

These identities are engineering regression data only and are not scientific benchmark evidence.
They support no empirical claim about LLM behaviour, image-schema acquisition, or transfer.

## Known limitations and unresolved questions

All existing `docs/open-questions.md` entries remain unresolved. In particular, benchmark contents,
public/private split, human-validation protocol, ethics determination, repository/benchmark
licensing, model stack, Phase I seeds/thresholds, and durable external archive remain owner decisions.

## Advancement decision

- Milestone status: `IN PROGRESS`.
- M2.1 status: `COMPLETED AND MERGED` as an engineering work package; this does not complete
  Milestone 2.
- M2.2 status: `COMPLETED AND MERGED` as a literal-candidate engineering/review work package; this
  does not freeze or approve `v1_core` and does not establish a scientific result.
- `v1_core` remains unfrozen. Every Milestone 2 tag, GitHub Release, final benchmark,
  model-selection, and advancement field remains pending.
- Next authorised work after M2.2 closeout: M2.3, which was not begun by this closeout.
