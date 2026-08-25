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

## Entry template

### YYYY-MM-DD — <decision or observation>

- Question or hypothesis:
- Alternatives considered:
- Evidence or reasoning:
- Decision:
- Expected consequences:
- What could falsify or revise it:
- Authoritative artifact affected:
