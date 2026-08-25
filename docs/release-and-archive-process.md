# Release and archive process

This document defines how reviewed work becomes canonical project history. `CODEX_SPEC.md` remains authoritative.

## Canonical state

- Canonical remote: `https://github.com/yurifrusin/unfrozen-schemas`
- Canonical branch: `origin/main`
- Local branches and unmerged pull requests are work in progress.
- A GitHub pull-request merge is already remote, but local workstations must still synchronise with `git pull --ff-only origin main`.
- A local merge is incomplete until `main` is pushed.

## Milestone lifecycle

1. Create a dedicated branch from current `origin/main`.
2. Implement one milestone or documentation revision only.
3. Run all required checks and inspect the complete diff.
4. Push the task branch.
5. Open or update a pull request into `main` and end the implementation task with that PR open.
6. Require GitHub Actions and owner review of the exact PR number and exact head SHA.
7. Start a separate Codex closeout task only after that explicit approval.
8. Immediately revalidate the approved head SHA, mergeability, required CI, and absence of unresolved review findings; stop if any state has drifted.
9. Merge only the exact approved pull request.
10. If authorised and necessary, create a mechanically constrained linked closeout PR that fills only predetermined release-note, `PROJECT_HISTORY.md`, and `RESEARCH_LOG.md` fields.
11. Merge the authorised closeout fields and verify the resulting canonical commit.
12. Synchronise local `main` by fast-forward only and verify the clean matching state.
13. Create and explicitly push the annotated milestone tag.
14. Publish a GitHub Release from the tag.
15. Confirm `PROJECT_HISTORY.md` and `RESEARCH_LOG.md` are current.
16. Begin the next milestone from the tagged `main` commit.

## Codex closeout authority

Implementation authority ends with an open pull request. An owner approval is valid only for the
exact pull-request number and exact head SHA stated by the owner. A separate Codex closeout task may
merge only after checking that the approved SHA is still the head, the PR remains mergeable, every
required CI check passes, and no unresolved review finding remains. Any drift invalidates approval
and requires Codex to stop.

The same approval may cover a linked closeout pull request only when its diff mechanically fills
predetermined release-note, `PROJECT_HISTORY.md`, and `RESEARCH_LOG.md` fields. Any code,
experimental, dependency, scientific-design, or unanticipated documentation change requires renewed
owner review. Tags and GitHub Releases are created only after the canonical closeout commit is merged
and verified.

## Milestone tags

Use:

```text
milestone-0-complete
milestone-1-complete
...
milestone-10-complete
```

Corrections use new immutable tags:

```text
milestone-1-correction-1
milestone-1-correction-2
```

Never force-move, delete, or reuse a published tag.

Example local closeout:

```powershell
git switch main
git pull --ff-only origin main
git status --short
git tag -a milestone-0-complete -m "Milestone 0 — repository foundation"
git push origin milestone-0-complete
```

Do not tag a dirty tree or a commit different from the reviewed merged commit.

## Scientific-checkpoint tags

Keep scientific checkpoints distinct from software milestones:

```text
benchmark-v1-core-frozen
phase1-preregistered-v1
phase1-calibration-v1
phase1-gate-v1
phase2-pilot-v1
paper-submission-YYYY-MM-DD
```

A gate tag does not encode `PASS`, `INCONCLUSIVE`, or `NO_GO`; the signed report and release notes do.

## GitHub Release content

Every milestone or scientific-checkpoint release records:

- title, tag, and exact commit;
- pull request and review reference;
- `CODEX_SPEC.md` SHA-256;
- relevant frozen config, benchmark, model-stack, and approval hashes;
- CI workflow and result;
- completed scope and work packages;
- scientific invariants checked;
- failed or excluded work that must remain visible;
- known limitations and unresolved decisions;
- artifact manifest and legally distributable links;
- advancement decision and next authorised work.

Do not attach full model weights, unlicensed datasets, secrets, or ordinary generated runs merely for convenience.

## Merge strategy and scientific provenance

Squash merge is acceptable for ordinary engineering work provided publishable scientific runs begin only after the resulting merged `main` commit is tagged. Never promote a scientific result solely because it was generated from an unmerged branch commit. A frozen scientific run must identify the exact clean canonical commit that produced it.

## Project and research records

`PROJECT_HISTORY.md` records factual chronology: branches, pull requests, merged milestones, tags, releases, specification revisions, and decisions.

`RESEARCH_LOG.md` records intellectual evolution: hypotheses considered, reasons for design changes, expected outcomes, interpretations, and unresolved scientific tensions.

Neither file replaces a preregistration, phase-gate report, benchmark card, model-selection approval, or release manifest.

## Main-branch protection

After Milestone 0, enable repository settings that require pull requests and the declared CI checks before changes enter `main`. Direct pushes to `main` should be exceptional and documented.
