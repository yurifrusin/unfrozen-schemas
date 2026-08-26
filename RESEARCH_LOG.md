# Research log

This is a chronological record of the project's intellectual development. It is not a preregistration and does not override `CODEX_SPEC.md`, frozen benchmarks, or signed gate artifacts.

## 2026-08-24 — Language as inherited embodiment

The project began from the possibility that natural language is not merely arbitrary text but a lossy cultural trace of embodied human cognition. If bodily and neural structures shape conceptual metaphor and linguistic organisation, a language-pretrained neural model may inherit a partial approximation of those structures before receiving direct sensorimotor input.

The working metaphor was that embodiment is partly “frozen” or “fossilised” in language and might be reorganised when an artificial neural system is coupled back to a world.

## 2026-08-24 — From an LLM agent to a neural colony

The broader programme considered a recurrent ecology of specialised neural systems rather than one monolithic language model. Potential specialists included perception, action, prediction, memory, mapping, simulation, and language. The decisive future question became whether grounded structure acquired by one specialist could alter the ordinary linguistic and metaphorical behaviour of another specialist through constrained communication.

The colony was deferred to Phase III because beginning with it would confound grounding, ensemble effects, orchestration, role prompting, memory, and communication.

## 2026-08-24 — Narrowing the first causal experiment

The first proposed test asked whether causally ordered non-linguistic experience of CONTAINMENT and SUPPORT would change zero-shot abstract and metaphorical transfer in a language-pretrained model.

Phase I was retained as a minimal deterministic calibration because it can identify where transfer stops:

```text
literal acquisition → held-out causal prediction → novel literal transfer → abstract transfer → metaphor transfer
```

Literal learning and contingency are gating. Abstract and metaphorical transfer are diagnostics rather than prerequisites for advancing to Phase II.

## 2026-08-24 — Rejecting a simplistic sensor-versus-language contest

A perfectly informative text oracle is already an expert compression of the world into the model's native modality. Requiring a newly learned opaque sensor channel to defeat that oracle would make the test unnecessarily adversarial and could obscure the more important hypothesis.

The central question was therefore revised from:

> Can sensor experience beat language?

into:

> Can language and active sensorimotor experience work complementarily, with language supporting hypothesis formation and consolidation while experience supplies causal constraint and correction?

The lossless text condition became an information ceiling rather than the principal opponent.

## 2026-08-24 — Active grounding as experimental inquiry

Phase II was redesigned around an observe–predict–hypothesise–intervene–revise–consolidate loop. Useful complexity means hidden causal properties, partial observability, delayed consequences, competing explanations, and interventions that distinguish them—not merely photorealistic rendering.

The expected risk is not that the model cannot learn any physical regularity. The more plausible risk is compartmentalisation: learning may remain in a sensor projector, adapter, task head, or local circuit without penetrating language-active representations. Closed-book transfer is therefore primary.

## 2026-08-24 — Local hardware becomes a prospective scientific constraint

The available workstation has an NVIDIA RTX 5070 with 12 GB VRAM. Rather than treating this as a late inconvenience, the design now qualifies the model stack prospectively at M2.5.

The preferred primary organism is a relatively small unquantised text-only base model that leaves room for adapters, sensor embeddings, likelihood evaluation, hidden-state access, and repeated seeds. A squeezed 7B model is not considered intrinsically better than a cleaner 1–2B intervention. BF16 LoRA and NF4 QLoRA remain scientifically distinct stacks.

## 2026-08-24 — Repository history as part of the apparatus

Because later claims depend on exact checkpoints, benchmarks, configurations, code, and gate decisions, repository history is part of the experimental apparatus. A milestone now becomes complete only when reviewed work is merged into canonical `main`, immutably tagged, released, and recorded.

This discipline is intended to preserve null, text-dominant, and compartmentalised outcomes just as carefully as preferred positive results.

## 2026-08-25 — Milestone 0 closes without a scientific result

Milestone 0 established the governed software, provenance, resource-accounting, testing, and archival foundation needed for later experiments. Its closeout does not report evidence for image-schema learning and does not constitute a Phase I gate result.

The specification and scientific design were not changed during closeout. Milestone 1 becomes authorised only after the reviewed closeout record is merged and the immutable `milestone-0-complete` tag and GitHub Release are published from canonical `main`; no Milestone 1 implementation is part of this event.

## 2026-08-25 — Causal validity requires path and constraint semantics

Pre-release review of SchemaWorld Core exposed two apparatus-level ambiguities. Treating every tether
shorter than a maximum range as tension allowed slack links to support objects, and checking only
containment membership at movement endpoints allowed large actions to tunnel through a closed
container.

Milestone 1 therefore adopts an exact taut inextensible-link contract for active load-bearing
tethers and exact swept boundary-plane checks for axis-aligned containment movement. Slack-to-taut
motion is deliberately absent from the minimal core, so slack active load-bearing states are invalid.
Every closed plane crossed by a swept body requires its own correctly aligned aperture. These are
corrections to the deterministic causal apparatus, not new hypotheses, benchmark choices, treatment
conditions, or scientific findings. They preserve condition comparability by making the intended
causal distinction explicit before release.

## 2026-08-25 — Containment walls are finite geometric segments

Final pre-release review found that movement-axis plane crossing alone implicitly extended each
container wall infinitely along its orthogonal axis. That artifact could make a distant container
block motion occurring entirely above, below, left, or right of it.

SchemaWorld Core now treats a wall crossing as the conjunction of two exact integer conditions: the
swept movement interval intersects the relevant inset wall plane, and the moving body's fixed
orthogonal interval positively overlaps the container's finite outer orthogonal interval. Zero-width
tangential contact is non-colliding, while a one-microunit overlap remains collision-relevant and
must satisfy the existing aperture contract. This narrows the implementation to the intended finite
rectangular apparatus without changing templates, actions, experimental conditions, or pinned
scientific identities.

## 2026-08-25 — Milestone 1 closes as apparatus, not a learning result

Canonical Milestone 1 closeout fixes the scientific identity of the minimal deterministic
SchemaWorld Core apparatus before benchmark construction or model work begins. The completed M1.1–
M1.5 scope establishes exact integer state, action, tether, finite-wall, relation, matched-pair,
opaque-codec, persistence, validation, replay, and rendering contracts for CONTAINMENT and SUPPORT.

The exact taut-tether and finite-wall corrections are retained as causal-validity clarifications.
They ensure that apparent support requires a physically active declared mechanism and that
containment blockage is caused by a finite wall actually intersected by the swept body. Canonical
pair and episode identities cover every causal pre-ID input, and the independent verifier recomputes
transitions and identities instead of trusting generated rows or replay assertions.

This release is deterministic experimental apparatus only. It contains no benchmark, language
model, tokenizer change, treatment, training, GPU execution, L1–L4 measurement, or Phase I gate
evidence, and it makes no empirical claim that an LLM acquires or transfers an image schema.
Repository and documentation licensing remain unresolved.

After the linked documentation closeout is merged and `milestone-1-complete` is tagged and released
from canonical `main`, governance authorises Milestone 2 as the next engineering milestone. That
authorisation does not begin Milestone 2, and no Milestone 2 work occurred during this closeout.

### 2026-08-25 — Benchmark identity, visibility, answers, and hash domains are separated

M2.1 treats lifecycle state independently from release visibility: SOURCE authoring, PRIVATE
candidate, and FROZEN write-once status do not imply that prompts, answers, or metadata are public.
Answers remain in a distinct private artifact, while public output is aggregate metadata scanned
recursively against private values.

Outcome, selection, engineering, and prospective retention purposes are bound into item identity,
logical hashes, manifests, and approvals. An item cannot change purpose in place, and cross-purpose
validation compares both stable IDs and equivalent model-visible content. This keeps model-selection
material and software fixtures from becoming outcome evidence.

Scientific logical hashes are calculated from typed canonical records with explicit domains and are
separate from exact file/container hashes. This preserves identity across path, timestamp, JSON-key,
line-ending, and filesystem-order differences while retaining ordinary artifact hashes for byte-level
provenance. These are prospective integrity decisions, not benchmark-content or scientific-result
decisions; all open content, validation, ethics, licensing, stack, and archive questions remain open.

### 2026-08-26 — Quarantine must describe the comparison universe, not an operator action

Pre-merge adversarial review showed that purpose isolation was incomplete when validation depended
on optional repeated manifest arguments. It also showed that a fingerprint containing authored IDs
could be evaded without changing the question shown to the evaluated model.

M2.1 therefore treats the complete canonical manifest scan as an immutable candidate input. Exact
displayed input and order-neutral content receive separate purpose-neutral identities: the first
preserves option presentation and book eligibility, while the second detects copied content after
ID replacement or option reversal. A changed comparison universe invalidates the candidate rather
than relying on an operator to remember which manifests existed.

The same review makes reverse-option variants a controlled transformation rather than a loose
grouping convention. Pair members may differ only in enumerated presentation/source-record fields;
prompt, annotations, validation, causal classification, correct stable answer, and substantive
evidence remain equal. Complete recursive public isolation and exact independent provenance checks
then protect those private semantics even against coordinated manifest edits. These are prospective
integrity corrections before benchmark authoring or treatment results, not new benchmark content,
scientific findings, or changes to the experimental design.

### 2026-08-26 — The quarantine universe requires canonical membership

A complete manifest scan cannot protect a scientific candidate stored outside every scanned root.
M2.1 therefore treats canonical repository membership as a necessary precondition for quarantine:
outcome and retention candidates inhabit the private root, selection candidates inhabit their
separate selection root, and eligible frozen outcome/retention versions inhabit the frozen root.
Content fingerprints and scope hashes still determine cross-purpose equivalence; location is not
itself scientific identity and never enters logical hashes.

This closes an evasion path without scanning arbitrary disks or owner directories. Any
non-engineering artifact capable of approval or freeze must first be a member of the complete
repository quarantine universe. Selection freeze remains disabled until M2.5 reviews a procedure,
and atomic PRIVATE publication now fails closed for the same reason as FROZEN publication: a command
must not report failure while leaving a valid artifact at the requested governed destination. This
is methodological integrity rationale, not benchmark content or a Phase I result.

### 2026-08-26 — Literal answers require replayable causal witnesses, not authored labels

M2.2 treats a literal benchmark answer as a derived consequence of a typed Core state/action pair,
not as an authoritative field supplied by an author. Each semantic group therefore binds actual and
counterfactual states, actions, transitions, relations, declared differences, outcomes, and stable
option identity in one witness. Validation independently replays both plans and derives the answer
before checking the private answer record. Reverse-option variants change presentation only.

This design separates three identities that serve different purposes: the unchanged M2.1 lifecycle
root isolates answers and benchmark purpose; the M2.2 composite root binds literal scientific
structure and audits; and the review manifest binds exact local inspection files. Timestamped
operation/platform provenance remains retained but does not perturb cross-platform logical identity.
The exact M2.1 candidate-manifest file and clean Git head remain explicit owner-review facts rather
than being mistaken for simulator semantics.

L2 novelty is declared structurally and rejects new-name/new-seed-only claims. Cue auditing records
necessary causal terms as reviewed findings while failing raw identifiers, hashes, coordinates,
unbalanced general templates/actions/mechanisms, and duplicate groups. Broader treatment overlap is
explicitly `not_assessed_m2_2`; M2.2 cannot infer that future treatment text is disjoint before M2.4
implements that comparison.

The outcome remains a private candidate pending owner content review, publication-quality human
validation, rights and ethics decisions, and M2.3-M2.6. Simulator agreement supports answer
correctness for the declared toy physics; it does not establish naturalness, construct validity for
humans, model learning, transfer, or any Phase I gate result.

Cross-operating-system CI confirmed that PNG container bytes are not stable scientific identities.
The review manifest therefore retains exact PNG hashes for local file-integrity checks but derives
its portable logical root from deterministic raw RGB pixel hashes plus all non-render review
artifacts. This preserves both byte-level review provenance and the prior scientific rule that an
inspection container cannot define state identity.

## Entry template

### YYYY-MM-DD — <decision or observation>

- Question or hypothesis:
- Alternatives considered:
- Evidence or reasoning:
- Decision:
- Expected consequences:
- What could falsify or revise it:
- Authoritative artifact affected:
