# Phase I gate protocol

Phase I is a mandatory, permanent scientific calibration. The gate is an auditable advancement
decision, not a summary of whether every desirable transfer outcome occurred.

## Status meanings

- **`PASS`:** every frozen hard criterion passes, all required seeds and failures are accounted for,
  integrity checks pass, and the report and approval hashes match. Scientific work authorised by
  that gate may proceed.
- **`INCONCLUSIVE`:** evidence is underpowered, a material anomaly is unresolved, or a repair
  requires a complete rerun of the frozen matrix. Engineering-only fixtures may continue, but no
  Phase II scientific pilot may begin.
- **`NO_GO`:** literal causal learning, contingency, generalisation, retention, or integrity fails
  under the declared design. Phase I must be diagnosed or redesigned before Phase II begins.

These are the only scientific gate statuses. Milestone 0 placeholder metadata uses
`NOT_EVALUATED`, is explicitly non-scientific, and can never authorise Phase II.

## Hard and non-gating evidence

The primary gate uses only frozen criteria for L1 held-out literal causal learning,
`sensor_causal > sensor_shuffled` contingency, L2 unseen-template/configuration transfer,
reproducibility across required seeds, language retention, and integrity checks covering leakage,
parity, budgets, benchmarks, checkpoints, and provenance.

L3 abstract transfer and L4 metaphor transfer must be reported in the transfer profile but are
prohibited as gate inputs. Neither a text-oracle advantage, absence of a causal-passive difference,
nor null L3/L4 outcomes can turn an otherwise valid hard-gate result into failure.

## Primary and compatibility gates

- A **primary gate** covers the complete Phase I matrix on the declared Phase I model stack and
  retains the full L0-L4 profile.
- A **compatibility gate** is a reduced Phase I calibration on the exact proposed Phase II stack
  after a material change to checkpoint, tokenizer, instruction posture, sensor codec/projector,
  adapter placement, trainable components, or objective family. It must pass literal learning,
  contingency, retention, leakage, reproducibility, and provenance. It references its parent
  primary report hash and need not repeat the full L3/L4 battery.

Phase II commands require the primary approval and, when applicable, its compatibility approval.

## Hash and commit chain

The machine-readable report records the gate type, group ID, parent primary-report hash when
applicable, gate-configuration hash, matrix-manifest hash, model-stack fingerprint, criterion
evidence, all/failed/excluded run IDs, L0-L4 profile, decision, reason, and report hash. The report
hash is calculated from a canonical form that omits the hash field itself.

The signed approval records the report hash, parent hash where applicable, gate-configuration hash,
model-stack fingerprint, exact Git commit, decision, signer, timestamp, and rationale. Verification
recomputes every referenced hash and requires the approval's Git commit to match the scientific
command's executing commit. A dirty tree is never silently treated as the approved commit; its
handling must follow the frozen run policy.

## Invalidation

An approval becomes invalid if any report, evidence artifact, matrix manifest, gate configuration,
benchmark, model-stack fingerprint, referenced checkpoint, or Git commit differs from the approved
value; if a required artifact is missing; if a required seed or failure is omitted; or if the
approval is not `PASS`. Editing or reserialising hashed content requires a new report and approval.
Compatibility approval is also invalid when its parent primary report changes.

Phase II scientific collection, training, and matrix commands must fail closed on a missing, stale,
non-`PASS`, commit-mismatched, or hash-mismatched approval.
