# Benchmark artifact boundary

Only this documentation and later explicitly reviewed safe public metadata belong in Git. Ordinary
authoring sources, private candidates, answer artifacts, and frozen private bundles are ignored.

- `source/` is local answer-bearing authoring material in lifecycle state `SOURCE`.
- `private/` holds built, validated candidates in state `PRIVATE`.
- `frozen/` will hold approved write-once versions; M2.1 creates no production version here.
- `selection/` is reserved for separately reviewed selection-only material in M2.5.

Purpose is bound into records, hashes, manifests, and approvals. Directory placement is not the
quarantine mechanism. Outcome, selection, retention, and engineering items cannot be promoted or
reused across purposes. In particular, `selection_probe_v1` is selection-only, `v1_core` is reserved
for the M2.6 production freeze, and the tracked engineering fixture cannot enter either namespace.

Never add answer-bearing source, `private_answers.jsonl`, source snapshots, candidate manifests, or
generated private/frozen output to Git. Use `git check-ignore -v` before authoring, and run:

```text
uv run unfrozen audit-benchmark-git
```

M2.6 may freeze `v1_core` only after the separately reviewed M2.2–M2.5 item, validation, evaluator,
hardware, model-selection, rights, ethics, and owner-approval hashes exist.
