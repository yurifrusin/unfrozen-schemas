# Downloaded-document ingest workflow

This workflow controls the movement of owner-provided Markdown documents into the repository.

## Current owner-workstation staging directory

```text
C:\Users\YuriFrusin\Downloads
```

This path is an operator convenience. Source code, tests, configurations, manifests, CI, and scientific runs must not depend on it.

## When Codex should use it

When a task says an updated Markdown file has been downloaded—for example `CODEX_SPEC.md`, an amendment, a prompt, or a release-note template—Codex should inspect the staging directory for the exact named file before asking the owner to provide it again.

Codex cloud or another environment without local Windows filesystem access must state that limitation and stop. It must not silently use an older repository version.

## Controlled ingest procedure

1. Confirm repository root, branch, clean/dirty state, and target destination.
2. List exact matches for the requested filename in `C:\Users\YuriFrusin\Downloads`.
3. Report whether there are zero, one, or multiple exact matches.
4. Refuse ambiguous selection. Do not choose by newest timestamp unless the owner explicitly instructs it.
5. Calculate the source SHA-256.
6. Calculate the current destination SHA-256 when the destination exists.
7. Read or compare both files before replacement.
8. Copy only the explicitly named source file.
9. Preserve repository line-ending rules.
10. Inspect `git diff --check`, the complete content diff, and repository-wide filename references.
11. Calculate and report the destination SHA-256 after copying.
12. Leave unrelated Downloads files untouched.
13. Run all validation required by the affected documents or code.

## Prohibited behaviour

- wildcard copying from Downloads;
- recursive copying of the entire Downloads directory;
- guessing among `CODEX_SPEC (1).md`, `CODEX_SPEC (2).md`, or similarly duplicated names;
- committing unrelated downloads;
- deleting source downloads automatically;
- embedding the owner path into runtime code, tests, experiment configurations, manifests, or CI;
- replacing an authoritative file without reporting source and destination hashes;
- continuing when the source file is inaccessible or materially differs from the task description.

## Recommended PowerShell inspection

```powershell
$Downloads = 'C:\Users\YuriFrusin\Downloads'
Get-ChildItem -LiteralPath $Downloads -File -Filter 'CODEX_SPEC.md'
Get-FileHash -Algorithm SHA256 -LiteralPath "$Downloads\CODEX_SPEC.md"
```

Copy only after reviewing the candidate:

```powershell
Copy-Item -LiteralPath "$Downloads\CODEX_SPEC.md" -Destination '.\CODEX_SPEC.md'
git diff --check
git diff -- CODEX_SPEC.md
Get-FileHash -Algorithm SHA256 -LiteralPath '.\CODEX_SPEC.md'
```
