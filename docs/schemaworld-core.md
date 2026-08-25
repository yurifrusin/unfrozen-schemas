# SchemaWorld Core operational contract

This document defines Milestone 1 SchemaWorld Core. `CODEX_SPEC.md` remains authoritative.
SchemaWorld Core is deterministic Phase I apparatus for literal CONTAINMENT and SUPPORT calibration;
it is not CausalSchemaLab, a benchmark, a treatment dataset, an LLM component, or scientific evidence
that a model acquires image schemas.

## Identity and arithmetic

- Environment version: `schemaworld-core-v1`.
- Version posture: Milestone 1 is still unreleased, so these corrections replace the pre-release
  contract in place and the environment remains `schemaworld-core-v1`. No published core artifact
  or compatibility promise exists to preserve, and a version bump would incorrectly imply two
  released scientific environments.
- State schema version: `1`.
- Coordinate unit: integer `microunit`.
- Fixed-point scale: `1`; no floating-point value participates in scientific transitions.
- Global coordinate bounds: inclusive lower bound `0`, exclusive entity-extent upper bound `10000`.
- Axes: `x` increases rightward and `y` increases upward.
- Gravity: a configured non-positive integer velocity increment per accepted step; the tracked smoke
  configuration uses `-100 microunit/step²`.
- Shapes: axis-aligned rectangles represented by an exact lower-left position and positive integer
  dimensions.
- Deterministic generator: the repository-owned `splitmix64-v1` implementation. It uses unsigned
  64-bit arithmetic and rejection sampling and never reads or seeds Python's global random state.
  Its algorithm and version are included in core manifests.

## Identifiers and immutable privileged state

All scientific records use frozen, extra-forbidden Pydantic models and canonical tuple ordering.
Identifiers are stable, semantic-neutral strings:

| Record | Identifier form |
|---|---|
| Entity | `eNNNN` |
| Boundary | `bNNNN` |
| Opening | `oNNNN` |
| Attachment | `aNNNN` |
| Tether | `tNNNN` |
| Delayed event | `vNNNN` |
| Episode | `ep-<16 hex>-<condition>` |
| Pair | `pair-<16 hex>` |

The privileged `WorldState` contains:

- environment, unit, bounds, scale, gravity, seed, noise seed, step index, horizon, and ended state;
- entity role; integer position, dimensions, quarter-turn orientation, velocity, mass class, active,
  movable, gravity, and gripper fields;
- container boundary reference, thickness, and closed/open state;
- opening boundary/side, span, enabled state, and optional gate entity;
- direct attachment endpoints, active state, and load-bearing property;
- tether endpoints, exact declared length, active state, and load-bearing property;
- delayed events with due step, declared priority, insertion order, kind, and target.

Agent, object, container, gate, support, anchor, and distractor roles share this exact entity record.
Role-specific behavior is validated by the state, transition, and relation layers. References must
exist, identifiers must be globally unique, and every collection must use its declared canonical
order. Opening spans must lie on the referenced container side excluding its corner squares. A
referenced gate must be active and its rectangle must exactly cover the aperture segment. Delayed
events must name an existing target of the type required by their event kind. Attachments and
tethers must connect an object to an anchor; active connections require active endpoints. An active
load-bearing tether must also satisfy the exact taut invariant defined below.

## Primary observation boundary

`PrimaryObservation` is derived from raw state. It exposes version/unit/step information, integer
geometry and motion, numeric entity-kind codes, boundary geometry, aperture state, and observable
mechanical edges. It does not expose entity-role words, load-bearing annotations, transition traces,
or verifier relations.

The serializer constructs its forbidden vocabulary from every privileged `RelationKind` plus the
declared human-readable synonyms and rejects any occurrence case-insensitively:

```text
INTERIOR EXTERIOR FUNCTIONAL_SUPPORT BLOCKAGE CONNECTION MOVEMENT FALLING
INSIDE OUTSIDE SUPPORTED UNSUPPORTED BLOCKED CONNECTED CONTAINMENT SUPPORT
```

Verifier/scorer records may contain relation names. They are persisted only in privileged step data
and never in primary observations or opaque symbol streams.

## Action contract

Every action has schema version and kind. The serialized model has actor, target, integer delta, and
magnitude slots, but their non-default use is governed by this strict matrix; every field not listed
for a kind is rejected:

| Action kinds | Required non-default fields | Additional rule |
|---|---|---|
| `WAIT`, `NOOP` | none | actor, target, deltas, and magnitude are forbidden |
| `MOVE`, `ENTER`, `EXIT` | `target_id`, exactly one of `delta_x`/`delta_y` | one non-zero axis only; actor and magnitude forbidden |
| `OPEN`, `CLOSE`, `OPEN_GATE`, `CLOSE_GATE` | `target_id` | target only |
| `DETACH`, `CUT_OR_BREAK` | `target_id` | connection target only |
| `REMOVE_SUPPORT` | `target_id` | support target only |
| `ROTATE` | `target_id`, positive `magnitude` | prospective and unsupported in M1 |
| `GRASP`, `RELEASE`, `ATTACH` | `actor_id`, `target_id` | prospective and unsupported in M1 |
| `PUSH`, `PULL`, `LIFT`, `LOWER`, `PROBE_FORCE` | `actor_id`, `target_id`, positive `magnitude` | prospective and unsupported in M1 |

The full prospective family is:

```text
MOVE ROTATE GRASP RELEASE PUSH PULL LIFT LOWER OPEN CLOSE ATTACH DETACH
CUT_OR_BREAK WAIT PROBE_FORCE NOOP
```

The Phase I aliases are:

```text
ENTER EXIT OPEN_GATE CLOSE_GATE REMOVE_SUPPORT
```

Implemented M1 semantics are `MOVE`, `OPEN`, `CLOSE`, `DETACH`, `CUT_OR_BREAK`, `WAIT`, `NOOP`, and
the aliases above. `NOOP` is an explicit accepted action. `ROTATE`, `GRASP`, `RELEASE`, `PUSH`,
`PULL`, `LIFT`, `LOWER`, `ATTACH`, and `PROBE_FORCE` raise `UnsupportedActionError`; they never
silently become `NOOP`. A malformed or state-invalid implemented action raises
`IllegalActionError`. Both derive from `SchemaWorldError`. Rejected actions do not increment the
environment-step budget.

## Reset, step, and episode ending

`SchemaWorld` supplies a typed Gymnasium-style internal protocol without depending on Gymnasium:

```text
reset(seed, noise_seed) -> ResetResult(observation, privileged_state, info)
step(action) -> StepResult(observation, privileged_state, reward, terminated,
                           truncated, info, transition_hash)
```

Reset deterministically selects the declared template, counterfactual condition, seed, and noise
seed. M1 has no reward-bearing task termination, so `reward` is integer zero and `terminated` is
false. Reaching `max_steps` makes the state ended and returns `truncated=true`. Further steps raise
`IllegalActionError`. The pure `transition(state, action)` function remains the scientific engine;
the stateful wrapper adds no dynamics.

## Exact transition order

Every accepted step executes these stages in this exact order:

1. action application;
2. contact resolution;
3. functional-support evaluation;
4. gravity;
5. collision resolution;
6. delayed events;
7. relation derivation.

Consequences of the order are explicit:

- a removed lower support is absent when support is evaluated, so the object falls in that step;
- contact is geometric, while functional support additionally requires a lower support surface,
  active load-bearing attachment, or active load-bearing tension;
- side contact and overlap do not provide functional support;
- gravity updates integer vertical velocity before integer position;
- collision candidates are chosen by highest top surface, then stable entity ID;
- delayed events due together sort by due step, numeric priority, insertion order, and event ID;
- delayed events execute after collision, so a support disabled by a due event affects gravity on
  the next accepted step;
- derived relations observe the post-event state and the privileged trace.

The version-1 event priorities are attachment disable `10`, tether disable `20`, entity disable
`30`, and opening enable `40`.

## CONTAINMENT mechanics

Container interior is the outer rectangle inset by boundary thickness. `INTERIOR` is derived when a
movable body lies wholly inside that inset rectangle; otherwise `EXTERIOR` is derived. `MOVE`,
`ENTER`, and `EXIT` are axis-aligned only; diagonal actions are malformed and rejected before a
transition.

For a prospective movement, the verifier forms the exact axis-aligned swept rectangle. On the
movement axis it tests the open interval from the minimum starting/proposed lower edge to the maximum
starting/proposed upper edge against every left/right or bottom/top interior boundary plane of every
closed container. Every intersected plane is a crossing, including both planes in an
outside-to-outside leap and a plane already partially intersecting the starting rectangle. Each
crossing requires an enabled opening on that exact side whose inclusive span contains the complete
orthogonal object extent at the crossing. Missing, undersized, or misaligned apertures leave the body
unchanged and produce privileged blockage evidence. A boundary with `closed=false` is open along its
whole perimeter and imposes no crossing check. World bounds remain mandatory.

Touching without penetration uses exact open-interval semantics: a body touching a plane and moving
away does not cross it; moving through it does. A partially overlapping starting body is fail-closed
for perpendicular movement unless a correctly aligned enabled opening covers it. Parallel movement
does not cross that plane. An object wholly outside that moves parallel to a boundary remains the
declared non-blocked negative case.

The matched containment pair has equal planned motion and differs only in the opening's initial
enabled field. Its parity auditor requires that single declared leaf difference.

## SUPPORT mechanics

A lower-surface contact exists when an object's bottom equals another active body's top and their
horizontal intervals overlap positively. It is functional lower support only when the lower body has
the support role. Side contact, zero-width contact, and geometric overlap are non-supporting.

An active load-bearing direct attachment supports its object while both endpoints are active. In
`schemaworld-core-v1`, an active load-bearing tether is a taut inextensible link, not a maximum-range
constraint. Its anchor centre must be above the object centre and the squared doubled-centre distance
must equal `(2 * declared_length)²` exactly. Overlength and underlength/slack active load-bearing
states are invalid. M1 does not implement slack-to-taut motion, so it does not admit slack
load-bearing tethers. Inactive and active non-load-bearing tethers may be slack but never provide
functional support. A movement that would break an active load-bearing tether invariant raises
`IllegalActionError`; it is not accepted as a blocked or malformed successor. Every accepted final
state is revalidated against the invariant. This comparison uses no square root or floating point.

The ordinary platform pair begins from one identical state and contrasts actual platform removal
with explicit `NOOP`. The tension pair begins from one identical state with visible side contact and
a genuinely taut 350-microunit load-bearing tether; it contrasts removal of the visible
non-supporting body with removal of the true tether mechanism. Pair generation fails if any
undeclared leaf differs.

## Privileged relations and transition traces

Relations are derived from geometry, active contacts, attachment/tether mechanics, and the current
transition trace. M1 verifier kinds are `INTERIOR`, `EXTERIOR`, `FUNCTIONAL_SUPPORT`, `BLOCKAGE`,
`CONNECTION`, `MOVEMENT`, and `FALLING`. No unexplained authoritative target-relation flag exists.

`TransitionTrace` records the structured action, frozen stage order, geometric contacts, functional
mechanisms, blockers, moved/falling/collision entity IDs, processed event IDs, and audit notes. It is
privileged evidence explaining a transition and is not part of the primary observation.

## Canonical serialization and hashes

Canonical logical JSON is UTF-8 with sorted mapping keys, compact separators, Unicode preserved,
and exactly one final newline. It contains no current timestamp, absolute artifact path, filesystem
ordering, Python hash ordering, or Parquet metadata. The following identities are separate:

- initial state hash: canonical initial privileged state;
- initial observation hash: canonical initial primary observation;
- state hash: canonical ordered state sequence;
- observation hash: canonical ordered observation sequence;
- action-sequence hash: canonical ordered structured actions;
- trajectory hash: canonical ordered step logical records, including privileged trace and relations;
- render hash: SHA-256 of renderer version, mode, dimensions, and raw RGB pixels;
- artifact hash: ordinary SHA-256 of each retained file, including Parquet and budget files.

`pair_id` is the first 16 hexadecimal characters of a canonical pre-ID payload containing
environment version, template family, seed, noise seed, gravity, maximum steps, both complete initial
states, both complete action sequences, the target-factor declaration, and the declared difference
paths. The payload contains neither the final pair ID nor episode IDs. Each episode ID is derived
from that same pre-ID payload plus its condition index. This makes IDs sensitive to every causal
input without circular hashing.

The PNG hash and raw Parquet file hashes are artifact identities only. Neither replaces the render or
trajectory identity.

## Opaque codec

`opaque-byte-v1` canonicalizes an observation or action, maps each byte through a pinned SplitMix64
permutation into one of 256 identifiers `u0000` through `u0255`, and records the canonical logical
hash. Decoding reconstructs the exact canonical bytes and verifies the hash before JSON parsing.
The table is versioned, deterministic, reversible, identical across matched records, independent of
any tokenizer, and contains no schema/relation words. M1 adds no vocabulary tokens, embedding table,
language model, LoRA, or model dependency.

## Parquet persistence

PyArrow writes `episodes.parquet` and `steps.parquet` with explicit field order, nullability, integer
widths, schema name, and schema version. Dictionary encoding, compression, and writer statistics are
disabled in the M1 writer. The episode table stores pair/template/schema provenance, seed and noise
seed, audited factor/path declarations, all canonical hashes, and canonical plan/final-state bytes.
The step table stores canonical before/action/after state and observation bytes, opaque streams,
privileged trace/relations, and per-step hashes.

`validate-core` is an independent verifier, not a replay-result assertion. It checks every episode
row against its typed `EpisodePlan`; requires the exact planned step count and contiguous indices;
parses canonical typed before/after states and observations, actions, traces, relations, and opaque
records; checks initial state and inter-step continuity; compares stored and planned actions;
recomputes both observations; independently calls `transition`; and requires exact state, trace,
transition-hash, relation, per-step hash, opaque, aggregate state/observation/trajectory, final-state,
and raw-pixel-render equality.

It also requires the exact mandatory artifact set, canonical safe run-relative paths, artifact hashes,
an external `resource_budget.json` equal to the embedded budget, and an external
`resolved_core_config.json` equal to the embedded configuration. Absolute paths, backslashes, empty
segments, `.`/`..` traversal, duplicate artifact paths, duplicate episode IDs, duplicate pair IDs,
duplicate step keys, missing pair members, and unexpected step episodes fail closed. Replay manifests
retain the resolved configuration and a typed report containing both complete source and replayed
episode digests; validation requires those digests, IDs, pair membership, and source-manifest hash to
agree exactly. Scientific identity remains the canonical logical record even if future compatible
Parquet container metadata differs.

## Renderer

`schemaworld-raster-v1` is a CPU-only, display-free integer rasterizer. It uses fixed RGB colors,
axis-aligned fills, no fonts, no encoder download, no current time, and no machine metadata. Raw
pixels are rendered in repository code; Pillow only packages the already-determined pixels into a
human inspection PNG. Rendering is never consulted by state transitions.

## Configuration, manifests, and accounting

The tracked `configs/experiment/milestone1_core_smoke.yaml` declares environment version, units,
bounds, gravity, event/stage order, template families, seeds, output root, generator, codec,
renderer, CPU/offline posture, and engineering-only status.

`CoreRunManifest` schema version `1` is separate from the released Milestone 0 `RunManifest` and
`BootstrapFailureRecord`. It records exact Git commit and dirty state, `CODEX_SPEC.md` hash, resolved
configuration, package/platform information, generator/codec/renderer identities, timestamps,
success/failure, source replay hash, episode/pair hashes, relative artifact paths/hashes, and the
unchanged Milestone 0 resource-budget schema version `2`.

Core generation and replay measure accepted environment steps, primary observation count and bytes,
`time.perf_counter` elapsed time, peak traced Python allocations via `tracemalloc`, and retained
artifact count/bytes. External language, self-generated language, forward passes, backward passes,
and optimisation steps are observed zero. Failed runs close their accounting interval and preserve a
validated failure manifest whenever the run directory can still be written.

## Dependencies and licences

| Dependency | Exact M1 version | Purpose | Upstream licence |
|---|---:|---|---|
| PyArrow | `25.0.1` | Explicit Parquet schemas and round trips | Apache-2.0 |
| Pillow | `12.3.0` | Packaging deterministic raw RGB pixels as inspection PNG | MIT-CMU |

No PyTorch, Transformers, PEFT, Accelerate, bitsandbytes, Gymnasium, model weights, GPU runtime, or
network service is added by Milestone 1.

## Commands

```text
uv run unfrozen generate-core --config configs/experiment/milestone1_core_smoke.yaml
uv run unfrozen validate-core --manifest <core_manifest.json>
uv run unfrozen replay-core --manifest <core_manifest.json>
uv run unfrozen inspect-episode --episode-id <episode-id> --manifest <core_manifest.json> --render
```

`inspect-episode` may omit `--manifest` only when the episode ID occurs in exactly one generated run
under `runs/`; ambiguity fails rather than choosing by timestamp or platform-specific file order.
