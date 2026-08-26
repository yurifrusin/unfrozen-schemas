# Benchmark artifact boundary

Only this documentation and later explicitly reviewed safe public metadata belong in Git. Ordinary
authoring sources, private candidates, answer artifacts, and frozen private bundles are ignored.

- `source/` is local answer-bearing authoring material in lifecycle state `SOURCE`.
- `private/<version>/` is the only candidate location for outcome and retention purposes.
- `frozen/<version>/` is the only non-engineering FROZEN location; M2.1 creates no production
  version here.
- `selection/<version>/` is the only selection-candidate location and remains reserved for
  separately reviewed M2.5 work.

Purpose is bound into records, hashes, manifests, and approvals. Canonical placement is mandatory
but does not replace content quarantine. Every non-engineering build must scan the complete roots
`frozen/`, `private/`, and `selection/` and retain a hash-bound `quarantine_scope.json`; candidate
validation and freeze re-scan that exact scope and reject additions, removals, unreadable records,
or hash drift. Only engineering fixtures may declare an explicitly empty scope. Exact displayed
input and order-neutral content fingerprints reject cross-purpose copies after ID renaming, option
reversal, or declared case/whitespace/Unicode-equivalent changes. Outcome, selection, retention, and
engineering items cannot be promoted or reused across purposes. In particular,
`selection_probe_v1` is selection-only, `v1_core` is reserved for the M2.6 production freeze, and the
tracked engineering fixture cannot enter either namespace.

Non-engineering outputs and direct manifest validation must resolve exactly to the purpose-specific
paths above. Copied or moved scientific candidates and frozen manifests are invalid even when their
contents and hashes remain unchanged. Selection-version lookup uses `selection/`; incompatible
duplicates across canonical roots fail as ambiguous. Every selection-purpose freeze remains refused
throughout M2.1 pending a separately reviewed M2.5 procedure. Engineering fixtures alone may use
isolated temporary candidate and frozen paths.

Never add answer-bearing source, `private_answers.jsonl`, source snapshots, candidate manifests, or
generated private/frozen output to Git. Use `git check-ignore -v` before authoring, and run:

```text
uv run unfrozen audit-benchmark-git
```

During M2.1 that audit is a strict safe allowlist: exactly this README and the four directory README
files may be tracked below `benchmarks/`. Any other tracked path fails, including a file force-added
under an arbitrary or misleading name.

M2.6 may freeze `v1_core` only after the separately reviewed M2.2–M2.5 item, validation, evaluator,
hardware, model-selection, rights, ethics, and owner-approval hashes exist.
