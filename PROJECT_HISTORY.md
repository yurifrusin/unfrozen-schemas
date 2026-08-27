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

### Milestone 2 M2.1 canonical implementation merge and work-package closeout

- M2.1 began from canonical branch point
  `73a787b3f0c25b78962ac13fb3b26c1cc50f0dae`, the target of `milestone-1-complete`.
- Owner approval identified implementation pull request `#5` and exact head
  `c2f78a8512a2db8c547955b50184c406153cc59d`.
- Pull request `https://github.com/yurifrusin/unfrozen-schemas/pull/5` was revalidated as open,
  non-draft, mergeable into `main`, with zero review threads or findings and its required `cpu`
  check passing in workflow run `32918619766` on the exact approved head.
- The implementation was merged normally, without squash, rebase, rewrite, or administrator bypass,
  at `2026-08-26T02:23:18Z`. The canonical implementation merge commit is
  `90c3428f70e03c3cf31e3e2309a65a2340f41cd1`.
- Push-triggered canonical-main workflow run `32922535140` passed job `cpu` on that implementation
  merge commit. Local `main` was then fast-forwarded and verified clean and equal to `origin/main`.
- Revision 6 `CODEX_SPEC.md` remained unchanged at SHA-256
  `e5162c4d0e9e9ef54e86820393d99a4766e934cb3feba2bc2ea6a32b5586a911`.
- M2.1 benchmark schema/lifecycle mechanics, the non-scientific engineering fixture, and the
  pre-merge integrity and canonical-storage corrections are completed and merged. The corrected
  engineering regression identities remain intact.
- M2.1 is complete as an engineering work package. Milestone 2 remains in progress: no Milestone 2,
  benchmark-freeze, or scientific-checkpoint tag or GitHub Release was created, and `v1_core`
  remains unfrozen.
- Advancement decision: M2.2 is the next authorised work package, but it was not begun by this
  closeout. No real benchmark-item authoring, model, tokenizer, training, GPU, or EPS work occurred.

### 2026-08-26 — Milestone 2 M2.2 literal/counterfactual implementation branch

- Began from clean canonical `main` at
  `ee6fff36317665ce729c870c858f273a6b348894`, after verifying the M2.1 implementation merge
  `90c3428f70e03c3cf31e3e2309a65a2340f41cd1`, the published Milestone 1 tag/release, the active
  `main` ruleset, and passing canonical CI.
- Branch: `codex/milestone-2-m2-2-literal-counterfactuals`.
- Added strict separately versioned M2.2 records and hash domains layered over the unchanged M2.1
  source/candidate contracts; deterministic typed source generation; independent actual and
  counterfactual Core replay; reverse-pair, split, lexical-cue, and provenance validation; composite
  M2.1/M2.2 identity; private review bundles and renders; CLI/configuration; and CPU/offline tests.
- Added a tracked non-scientific engineering fixture using synthetic status-code wording. It is
  non-promotable and contains no real candidate prompt, target-domain item, model, scorer, or GPU
  dependency.
- Pull request `#7` first ran CI at head
  `f7696a5bb96c5cb275727649f8d3227d9a1ef954`. The test suite exposed an operating-system-dependent
  PNG container hash in the review-manifest logical regression. The correction retains exact local
  PNG artifact hashes for read-back while binding deterministic raw-pixel hashes in the logical
  review identity, matching the existing rule that render-container metadata is non-scientific.
- The real provisional candidate identity is `m2-2-literal-candidate-v1`, purpose `outcome`, with
  private ignored source, candidate, and review roots. Its generation is deliberately deferred until
  the tracked branch is final, pushed, clean, and CI-green.
- Revision 6 `CODEX_SPEC.md` remained unchanged at SHA-256
  `e5162c4d0e9e9ef54e86820393d99a4766e934cb3feba2bc2ea6a32b5586a911`.
- Status: implementation in progress. No merge, tag, release, freeze, human recruitment, model/GPU
  run, treatment, scientific result, Phase I gate decision, M2.3 work, or EPS-worktree change has
  occurred.

### 2026-08-26 — M2.2 pre-merge semantic and review-integrity correction

- Continued pull request `#7` on `codex/milestone-2-m2-2-literal-counterfactuals` after exact branch,
  head, upstream, pull-request, canonical-main, clean-tree, and protected CPU-check preflight.
- Replaced authoritative free causal/narrative prose and positive/negative option conventions with a
  retained typed authoring snapshot, explicit outcome-code registry, prospective intervention
  contracts, simulator-derived narrative facts, and seed/ID-independent structural signatures.
- Added one-to-one snapshot/source/binding/witness reconciliation; verified L1/L2 exact identity
  separation and L2 structural novelty; corrected lexical findings to remain owner-review pending;
  and bound operational provenance separately from portable logical roots.
- Split explicit candidate materialisation from strictly read-only validation. Source generation,
  candidate materialisation, and review construction now use staged fail-closed publication and
  governed failure records.
- Expanded private review records and deterministic inspection to actual/counterfactual before/after
  renders, decoded Pillow validation, exact PNG artifact hashes, raw-pixel identities, and exact
  snapshot/operation/manifest owner-binding requirements.
- Status: tracked correction and local verification are in progress. The private outcome artifacts
  remain provisional and will be regenerated only from the final pushed, clean, CPU-green head. No
  merge, tag, release, freeze, M2.3, model/GPU, treatment, or EPS-worktree work occurred.

### 2026-08-26 — M2.2 independent scientific-review correction round

- Continued pull request `#7` from exact reviewed head
  `6644e47b6af06e84c0e08804aa25b0a588fdf8c4` after clean branch/upstream, canonical-base,
  pull-request, and protected CPU-check preflight.
- Implemented the six stable scientific-review findings as `IMPLEMENTED_PENDING_VERIFICATION`:
  explicit source/target mechanism transfer with complete prohibited-source comparison; separate
  question, causal-scenario, structural-stratum, matched-variant, and cosmetic-variant accounting;
  natural typed wording; prospectively parallel option forms; finite support-aware category-bound
  lexical review; and retained full-frame plus deterministic zoom review renders.
- Added exact six-family wording, causal-identity invariance, all-L1/prospective-source mutation,
  option-confound, lexical-category, and decoded review-zoom regressions. Tokenizer-specific option
  length remains an explicit pending M2.4 obligation.
- Local locked sync, Ruff lint/format, strict mypy, all 318 tests, offline smoke, fresh Core
  generation/validation/replay, the corrected M2.2 engineering lifecycle, and benchmark Git audit
  passed. The M2.1 engineering build/validation passed; its approval correctly refused the dirty
  pre-commit tree and is scheduled for clean-head repetition.
- Status: the bounded correction commit, exact-head protected CI, clean-head M2.1 completion, and
  private artifact regeneration remain pending in this correction task. No merge, tag, release,
  production freeze, M2.3, model/GPU, treatment, or EPS work occurred.

### 2026-08-27 — M2.2 scientific-convergence correction

- Continued pull request `#7` from exact reviewed head
  `4532e39f9afb75865ee4183c5ceef71770192c5c` after branch, upstream, pull-request, canonical-base,
  clean-tree, private-identity, and protected CPU-check preflight.
- Implemented `US-PR0007-SR-0001`, `US-PR0007-SR-0003`, and `US-PR0007-SR-0005` as
  `IMPLEMENTED_PENDING_VERIFICATION`. Configuration-specific mechanism signatures are retained,
  while a new coarse typed mechanism-kind identity binds the complete L1/prospective prohibited
  sets and the genuine L1-source-to-L2-target mapping.
- Made no-change questions reconstruct from `NOOP`/`WAIT` action status, split lexical findings into
  selective hash-bound scientific subcategories with sentence-local n-grams, and configured an
  exact eight groups per authorised task family.
- Added coordinated mechanism-kind, fitting/undersized prohibited-kind, unchanged-control,
  nuisance/renderer, sentence-boundary, subcategory-membership, and selective-disposition
  regressions. The corrected private authoring migration was first validated entirely in memory.
- Status: local verification, the bounded correction commit, exact-head protected CI, and private
  regeneration remain part of this correction task. No merge, tag, release, freeze, M2.3,
  model/GPU, treatment, scientific result, or EPS work occurred.

### 2026-08-27 — M2.2 engineering-review correction

- Continued pull request `#7` from exact reviewed head
  `fd6b52b40ff0b79a79fe884e5254dcb9a5b2b60f` after clean branch/upstream, pull-request,
  canonical-base, and protected CPU-check preflight.
- Corrected `US-PR0007-ER-0001` so review-publication cleanup preserves the primary failure,
  reports rename/move/removal/invalidation diagnostics, retains the strongest valid governed
  failure record, and prevents a reported-failed destination from remaining validatable whenever
  the filesystem permits invalidation.
- Corrected `US-PR0007-ER-0002` so non-engineering literal source and review validation binds the
  resolved paths to the tracked canonical roots while retaining explicit engineering-fixture and
  internal unpublished-staging support.
- Added compounded fault-injection, failure-record preservation, copied/moved/aliased-root,
  read-only rejection, canonical acceptance, and engineering-override regression coverage.
- Status: complete local verification, the bounded correction commit, exact-head protected CI, and
  clean-head private evidence regeneration remain pending in this correction task. No merge, tag,
  release, freeze, M2.3, model/GPU, treatment, scientific result, or EPS work occurred.

### 2026-08-27 — M2.2 canonical-root alias correction

- Continued pull request `#7` from exact reviewed head
  `211d6abef34f7fd2a4927a7418f3bf4f1f25221d` after clean branch/upstream, pull-request,
  canonical-base, and protected CPU-check preflight.
- Corrected `US-PR0007-ER-0002` so non-engineering outcome source and review roots require exact
  normalized absolute lexical identity before resolution, and reject symbolic-link, junction, or
  other reparse-point components through `lstat` metadata before resolved containment checks.
- Retained canonical relative/absolute spellings and authorised engineering overrides, while adding
  public-validator and CLI regressions for direct canonical aliases, moved copies, and governed
  intermediate aliases on POSIX and Windows.
- Status: full local verification, the bounded correction commit, exact-head protected CI, private
  evidence regeneration, and metadata-only pull-request correction remain pending. No scientific
  content, merge, tag, release, freeze, M2.3, model/GPU, treatment, scientific result, cue
  disposition, closeout, or EPS work occurred.

### 2026-08-27 — Milestone 2 M2.2 canonical implementation merge and work-package closeout

- Owner approval identified implementation pull request `#7` and exact head
  `aa8a828f323f5c3f31a8a6048b5e1857ec314569` against canonical base
  `ee6fff36317665ce729c870c858f273a6b348894`.
- Exact-head review converged as `ENGINEERING_PASS` and `SCIENTIFIC_PASS` at the approved SHA. Pull
  request `https://github.com/yurifrusin/unfrozen-schemas/pull/7` was revalidated as open,
  non-draft, mergeable into `main`, with zero review threads and protected `cpu` workflow run
  `33045178510`, job `98427407684`, passing on that exact head.
- The owner accepted the exact cue-category memberships
  `necessary-causal-condition-vocabulary` at
  `c588337741cdf1d3afde972b1fe8c9cf0362b536f24b98ab8d19cfe7f99e9f4c`,
  `physical-mechanism-correlation` at
  `065ec3948b1fa996bdacc692a7c1081defa1bf8a97dfd0c3f1fb6104ae4d2a51`, and
  `duplicate-or-matched-wording` at
  `074718208b44444beb500953da5df718477355646ca707cdb0a99894e8860152`. No consequential
  finding or category membership was rejected.
- The implementation was merged normally, without squash, rebase, rewrite, or administrator
  bypass, at `2026-08-27T13:32:51Z`. The canonical implementation merge commit is
  `2fb34969c74df359587ac510f0c108c9b4fdccdd`.
- Push-triggered canonical-main workflow run `33077391425` passed job `cpu` (`98535071632`) on that
  implementation merge commit. Local `main` was fast-forwarded and verified clean and equal to
  `origin/main`; the approved head is an ancestor of canonical `main`.
- The approved logical/scientific identities are authoring snapshot
  `94a0c60be95cef05efe4bb62c64f60cd044a99d858043a827bb999b91f9cd409`, literal source bundle
  `030d0dffdc574334844126f97ac65b4b94a086c7ea875e12afc139d06fb6cb59`, M2.1 candidate root
  `935e8c81d2367c55bf8230d7d9aa3e4e0c4ff4f69865c169439af1275133c4fe`, M2.1 source snapshot
  `461a304e7525ed629aaf428c1acafeac8116835fe0fc8584e5627f1d80fcf8d9`, private-answer bundle
  `13988d04ffa9bce8bc6c8d9b48ddf96da0fe14f9c42a5a19c516a30327f684f4`, public-metadata bundle
  `bd6cf587e729fdc1cd68b415e8da777a33b888e63eedc8b2ee16436f2c1c60eb`, quarantine scope
  `51c6d80aafd1873880b1e1417a368433c6b3655dd9c1b48b38f24e74e5585c4f`, partition plan
  `9b5f699ba146c28d0a75fc3ca4243292aa8920d369803b71c177537ce45114a5`, template registry
  `21701a8f3839bb1e599d2b8a13842b62b218a93a1ce4736c9cc0ee0871fd4b53`, item-binding bundle
  `d9392e25ad4197cae9a50a397870ef7e486de952720c46d189d43cb090f4cd9c`, witness bundle
  `8664b84eb78cb31c2b5828b49b3dee88fda9163e9bc24afe02d1636f2f56ce80`, lexical audit
  `23d4e5e11238b8041891f82cf84b24f0fffa8225280b544ec53ee73876b7631e`, split audit
  `a95bf67a75dc15a77895894ae1f849b88b128eca9a67d66b4aef0569da9d2838`, source validation
  `02320201bcdbdbf98c00f465b6b69047589107e811a6b8580758b3c1a1c70900`, candidate validation
  `6d4985bc05d054c68f321b64a8af9d7810db0a03ac16a2ad2a5dad720a226d73`, M2.2 composite root
  `3011c24f0592ecf627e8ada93350d7bb6056e16bbcbf65e9d538d4cbf06afc14`, review-content bundle
  `3d9e10ad32ac0d83d4254cc480eef24396e60431226c5822e944d8f37c4535d4`, and review-manifest
  logical root `cb5b8a445ec2616d0cb11c956637116a3b8271553543a18bf3c1f1439df8bc0e`.
- The mechanically constrained documentation closeout branch is
  `codex/milestone-2-m2-2-closeout`. M2.2 is completed as an engineering/review work package when
  this linked record reaches canonical `main`; it is not a benchmark freeze or empirical result.
- Milestone 2 remains in progress, `v1_core` remains unfrozen, and no Milestone 2,
  benchmark-freeze, or scientific-checkpoint tag or GitHub Release was created.
- Advancement decision: M2.3 is the next authorised work package, but it was not begun by this
  closeout.

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
