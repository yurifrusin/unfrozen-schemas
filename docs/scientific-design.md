# Scientific design

This document is an operational summary of `CODEX_SPEC.md`. The specification remains authoritative.

## Programme structure

### Phase I: mandatory causal calibration and gate

Phase I uses deterministic SchemaWorld Core episodes for CONTAINMENT and SUPPORT. It tests whether a language-pretrained model can learn literal dynamics from causally ordered non-linguistic trajectories and whether learning depends on valid action–outcome contingency. Its datasets, item-level results, failures, checkpoints, reports, approvals, and provenance remain a permanent standalone result.

The controlled matrix includes unchanged, literal text-oracle, causal-sensor, passive-sensor, and shuffled-sensor conditions beginning from the same declared base checkpoint.

Phase I reports:

1. **L0 — acquisition** on adaptation episodes;
2. **L1 — held-out literal causal prediction**;
3. **L2 — novel literal templates and configurations**;
4. **L3 — abstract relational transfer**;
5. **L4 — novel metaphorical transfer**.

L0 is insufficient. Gate criteria concern reproducible L1 learning, causal-versus-shuffled separation, L2 transfer, language retention, leakage and parity control, complete seed accounting, and provenance. L3 and L4 are always reported but never determine gate status. A text oracle may outperform the sensor condition without failing Phase I. L1/L2 success without L3/L4 transfer is a meaningful compartmentalisation result and a principal motivation for Phase II.

### Phase II: language-scaffolded active grounding

Phase II uses CausalSchemaLab, a richer controlled microworld with hidden properties, partial observability, delayed effects, altered physics, and multi-step interventions. The primary system observes, predicts, states concise literal hypotheses, selects discriminating actions, measures prediction error, revises confidence, and consolidates verified regularities through a bridge between a latent world model and language-active representations.

The design preserves raw/language, offline/active, active/yoked, causal/shuffled, trained/untrained-schema, human-norm, and closed/open-book comparisons. Closed-book text-only abstract and metaphor evaluation is primary. External language, self-generated language, sensorimotor experience, and compute receive separate accounting.

Phase II scientific work requires a valid primary Phase I `PASS`. A materially different Phase II model stack also requires a compatibility-calibration `PASS`.

### Phase III: neural-colony propagation

Phase III asks whether a sensory/world specialist can change the closed-book abstract and metaphorical behaviour of a separate language specialist through constrained conceptual communication. It compares no communication, literal-language messages, learned latent messages, hybrid communication, disrupted messages, a monolithic system, and compute-matched controls.

Phase III begins only after written review and after Phase II yields either reproducible schema-specific transfer or a stable, well-characterised compartmentalisation result.

## Local model and hardware staging

CPU-only engineering remains the default through M2.4. M2.5 performs prospective hardware qualification and model selection on one NVIDIA RTX 5070 with 12 GB VRAM. The final Phase I benchmark is frozen only after the selected stack demonstrates acceptable likelihood access, hidden-state access, adapter save/reload, dedicated sensor-embedding gradients, VRAM reserve, and practical repeated-run feasibility on that card.

Candidate screening uses quarantined selection and engineering probes that may never be promoted into the final benchmark. BF16 LoRA and NF4 QLoRA are distinct model stacks. The primary lexical embedding matrix remains frozen.

## Interpretation boundary

The programme tests narrow causal claims about learning, integration, transfer, and communication. It does not establish consciousness, human embodiment, a complete neural theory of language, or a generic first claim for embodied learning, metaphor grounding, or conceptual communication.

## Repository-state boundary

A scientific design is not frozen merely because it exists on a branch. Canonical freezes and publishable runs are tied to clean, merged, tagged `origin/main` commits and their associated release or approval artifacts.
