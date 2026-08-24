# Unfrozen Schemas
## Experimental Architecture and Codex Repository Specification

**Working research title:** *Unfreezing Embodiment: Language-Scaffolded Active Grounding and Image-Schematic Transfer in a Pretrained Language Model*

**Repository name:** `unfrozen-schemas`

**Status:** revision 4 implementation specification. This revision formalises Phase I as a mandatory, auditable scientific gate; separates hard advancement criteria from non-gating abstract and metaphorical diagnostics; requires a compatibility calibration when the Phase II model stack changes; and retains the richer language-scaffolded Phase II and neural-colony Phase III programme.

---

## 1. Scientific purpose

Build a reproducible experimental platform to test a **complementarity hypothesis** rather than forcing language and sensorimotor experience into an unnecessarily adversarial contest.

The project begins from two premises:

1. a language-pretrained model may already contain a powerful, culturally inherited approximation of embodied conceptual structure; and
2. direct perception and action can provide causal, temporal, proprioceptive, and counterfactual constraints that ordinary linguistic summaries omit or compress.

A genuinely information-complete text oracle is therefore not an ideal primary opponent. If it losslessly serialises every observation, action, hidden state, and consequence into the model's native modality, it may predictably equal or outperform a newly learned sensor channel. Such a result would say little about whether experience can enrich language. The lossless oracle is treated as an **information ceiling**, while the primary question is whether language and active experience work better together than either does alone under controlled budgets.

The programme has three phases:

### Phase I — causal calibration and mandatory scientific gate

Use a minimal deterministic SchemaWorld to establish that the model can learn literal CONTAINMENT and SUPPORT dynamics from non-linguistic trajectories, that correct action–outcome contingency matters, and that the evaluation and provenance pipeline works. This phase preserves the clean controls from revision 2.

Phase I is not a disposable prototype or an optional demonstration. Its complete results remain a permanent standalone calibration dataset, and a machine-readable Phase I gate report determines whether Phase II scientific runs may begin. Phase I must describe where transfer stops along the following ladder:

```text
training-episode acquisition
        ↓
held-out literal causal prediction
        ↓
novel literal templates and configurations
        ↓
abstract relational transfer
        ↓
novel metaphorical transfer
```

Only reproducible literal causal learning, transfer beyond memorised templates, causal-control integrity, language retention, leakage control, and provenance integrity are hard advancement criteria. Abstract and metaphorical transfer are scientifically important diagnostics, but they must not determine the Phase I pass/fail decision. A null metaphor result is one of the principal motivations for Phase II.

### Phase II — language-scaffolded active grounding

Use a richer but still controlled causal microworld in which the model:

- receives sensory and proprioceptive input;
- forms concise literal hypotheses in language;
- predicts outcomes;
- chooses interventions that distinguish competing hypotheses;
- observes prediction errors;
- consolidates verified regularities into a language-linked latent world model;
- and is then evaluated, without the world or its notebook, on unseen abstract and metaphorical instantiations.

Language is used as a semantic prior, planning medium, compression mechanism, and shared workspace. Sensorimotor experience supplies the evidence that constrains and corrects that prior.

### Phase III — neural-colony propagation

Test whether grounding acquired by a sensory specialist can alter the closed-book linguistic and metaphorical behaviour of a separate language specialist through constrained conceptual communication.

The project is not intended to prove consciousness, human embodiment, or a complete neural theory of language. It tests narrowly specified causal claims about learning, integration, transfer, and communication.

---

## 2. Novelty boundary

The broad intellectual territory is established. The project must not claim that any of the following ideas is wholly new:

1. Language may encode a collective world model derived from the embodied experience of a linguistic community.
2. Language models can be fine-tuned on experiences collected from simulated worlds.
3. Language models and vision-language models can be adapted while acting in embodied environments.
4. Multimodal and vision-language-action systems can combine semantic priors with perception and motor control.
5. Image schemas can be probed in language models.
6. Sensorimotor information can affect metaphor processing, and text-only LMs can fail to use it in human-like ways.
7. Connectionist and robotic systems can ground concrete and some abstract words in perception and action.
8. Neural systems can acquire abstract concepts from sensory tasks and communicate conceptual representations between networks.
9. Sensorimotor supervision can steer language-model representations toward human sensorimotor norms.
10. Latent world-model or intent bottlenecks can preserve high-level semantic competence while handling physical dynamics that are inefficient to verbalise exhaustively.

The intended contribution is the **controlled intersection** of these strands:

> A matched intervention beginning with a language-pretrained model, coupling a language-based hypothesis-and-consolidation workspace to action-contingent non-linguistic experience, and measuring whether the joint system produces schema-specific closed-book transfer to unseen abstract structures and novel metaphors beyond language-only, sensor-only, passive, shuffled-causality, yoked-experience, and explicit sensorimotor-norm controls.

The project has two successively stronger defensible claims:

### Phase I claim

> We test whether direct causal grounding of a literal image schema selectively changes a pretrained language model's generalisation to unseen abstract and metaphorical instances, beyond equivalent linguistic exposure and non-causal multimodal exposure.

### Phase II claim

> We test whether language-mediated active exploration and sensorimotor learning are complementary: whether a model that uses language to predict, plan, compress, and consolidate its own causal experience exhibits greater and more efficient closed-book schema transfer than either language-only exposure or sensorimotor learning without the language bridge.

Do not use stronger language such as “the first embodied language model,” “the first grounding of metaphor,” or “the first transfer of concepts between neural networks.”

### Closest prior work to distinguish from this project

- **Taniguchi et al. (2025), *Large Language Model is a Collective World Model*, arXiv:2501.00226.** This provides a theoretical account close to the premise: society encodes grounded internal representations into language and an LLM reconstructs a latent approximation. It does not run the proposed controlled re-grounding intervention.
- **Xiang et al. (NeurIPS 2023), *Language Models Meet World Models: Embodied Experiences Enhance Language Models*.** It fine-tunes LMs using VirtualHome trajectories and evaluates physical reasoning, planning, and tracking. Its experiences are substantially predicate-like or textualised, and it does not test image-schema-specific closed-book transfer to unseen metaphor under matched language, agency, and causal controls.
- **Tan et al. (ICLR 2024), *True Knowledge Comes from Practice*.** It adapts an LLM policy with PPO in Overcooked and VirtualHome and tests embodied decision-making. It does not ask whether the intervention reorganises general linguistic or metaphorical competence.
- **Bisk et al.-style embodied-language research and the 2024 ACL review *Embodied Language Learning: Opportunities, Challenges, and Future Directions*.** This literature identifies the gap between robotics-centred evaluation and changes in general language understanding, including figurative language, but does not supply the present controlled design.
- **Wicke and Wachowiak (ACL 2024), *Exploring Spatial Schema Intuitions in Large Language and Vision Models*.** It diagnoses existing schema intuitions; it does not administer new causal experience.
- **Jones and Trott (LREC-COLING 2024), *Multimodal Language Models Show Evidence of Embodied Simulation*.** It diagnoses implicit embodied effects in existing models rather than testing a developmental intervention.
- **Mangiaterra et al. (2025), *On choosing the vehicles of metaphors without a body*.** It motivates the intervention by showing reduced sensitivity to sensorimotor variables in text-only models.
- **Sun et al. (Nature Human Behaviour 2025), *Large language models without grounding recover non-sensorimotor but not sensorimotor features of human concepts*.** It identifies a sensorimotor representational gap and some benefit from visual learning, but compares existing model families rather than matched causal treatments.
- **Wu et al. (2026), *How does fine-tuning improve sensorimotor representations in large language models?*, arXiv:2603.03313.** It shows that explicit sensorimotor supervision can reorganise model representations, with transfer depending strongly on the training objective. It motivates the `human_sensorimotor_norms` control but does not use direct action-contingent experience or test image-schema-to-metaphor transfer.
- **Proietti et al. (LREC 2026), *Mechanistic Interpretability Meets Cognitive Linguistics*.** It provides methods for image-schema-related mechanistic analysis but not sensorimotor adaptation.
- **DIAL (2026), *Decoupling Intent and Action via Latent World Modeling*.** It uses a latent intent/world-model bottleneck to preserve and refine high-level vision-language representations while learning action. It targets robot manipulation rather than closed-book conceptual-metaphorical transfer, but it motivates the project's bidirectional concept bridge and two-speed optimisation.
- **LaST0 (2026), *Latent Spatio-Temporal Chain-of-Thought for Robotic Vision–Language–Action Model*.** It argues that explicit linguistic reasoning is a bottleneck for fine physical dynamics and combines a latent spatiotemporal world model with a semantic multimodal backbone. It motivates retaining a non-linguistic latent channel rather than verbalising every physical detail.
- **Guo et al. (Nature Computational Science 2026), CATS Net.** It learns compact concepts from sensory tasks and transfers conceptual structure between networks through conceptual communication. It pre-empts a generic “first conceptual communication” claim. The distinct Phase III question here is whether a grounded specialist can change a separate language-pretrained specialist's ordinary abstract and metaphorical language.
- **Wang and Liao (ICCDC 2025), *When Cognition Meets Data: An Investigation into Large Language Models' Acquisition of Image Schemas and Their Limitations*.** The full text proposes text-only probes for CONTAINER and SOURCE–PATH–GOAL and explicitly labels its numerical section “HYPOTHETICAL RESULTS.” It does not adapt a model, provide sensorimotor trajectories, manipulate action–outcome contingency, or compare pre/post transfer.

### Consequences of the Wang–Liao full-text review

Treat Wang and Liao as a conceptual and methodological precursor, not as evidence that its numerical tables were obtained from completed experiments. The repository and any eventual paper must:

1. never cite its illustrative numerical values as observed empirical findings;
2. avoid novelty claims for diagnosing CONTAINER or SOURCE–PATH–GOAL, novel metaphor probes, literal-versus-metaphorical comparison, calibration, or the general proposal of embodied training;
3. label any clean-room diagnostic `wang_liao_inspired`, not a direct replication;
4. use named, versioned, open-weight models for hidden-state analysis;
5. distinguish simulated, exploratory, pilot, and confirmatory results unmistakably.

The paper itself frames image schemas as embodied structures and recommends future systems that unite text, perception, and action. The present project operationalises that recommendation while testing whether language can function as the integration layer rather than merely as a competing data format.

---

## 3. Research questions and hypotheses

### Phase I calibration question

Can a language-pretrained model learn literal CONTAINMENT and SUPPORT dynamics from causally ordered non-linguistic trajectories, and does any transfer depend on correct contingency rather than generic adaptation?

### Phase I hypotheses and transfer profile

- **P1-H1 — literal acquisition:** `sensor_causal` improves held-out literal causal prediction relative to its own pre-adaptation score and the unchanged baseline.
- **P1-H2 — contingency:** `sensor_causal` outperforms `sensor_shuffled` on held-out literal dynamics when token marginals, episode counts, and optimisation budgets are matched.
- **P1-H3 — transfer beyond templates:** the literal effect generalises to unseen templates, object identities, positions, and counterfactual configurations rather than remaining confined to training episodes.
- **P1-H4 — retention:** the intervention preserves declared general-language and base-model capabilities within a preregistered tolerance.
- **P1-H5 — graded permeability:** abstract relational and novel metaphor transfer may emerge, but these are measured as higher rungs of a transfer profile rather than required gate outcomes.

The Phase I report must score five levels separately:

```text
L0  acquisition on adaptation episodes
L1  held-out literal causal prediction
L2  novel literal templates and configurations
L3  abstract relational transfer
L4  novel metaphorical transfer
```

L0 alone is never sufficient. The Phase I advancement gate is based on L1, L2, contingency, retention, leakage, reproducibility, and provenance. L3 and L4 are non-gating scientific outcomes. In particular, failure at L3 or L4 must not be reclassified as a failed sensor-learning pipeline when L1 and L2 succeed.

### Phase II primary research question

> Does a language-scaffolded, actively exploring model show greater and more efficient schema-specific closed-book transfer to unseen abstract and metaphorical cases than (a) language-only interaction, (b) sensorimotor learning without linguistic consolidation, and (c) passive exposure to the same experience?

### Phase II primary hypotheses

- **H1 — language–experience complementarity:** `active_sensor_language` produces a larger closed-book pre/post gain than both `text_interactive_oracle` and `active_sensor_raw` under preregistered resource budgets.
- **H2 — language bridge:** on an identical fixed trajectory corpus, `offline_sensor_language` outperforms `offline_sensor_raw`. This isolates linguistic hypothesis formation and consolidation from differences in experience selection.
- **H3 — agency:** `active_sensor_language` outperforms its `yoked_passive_language` control, which receives the same observations, actions, outcomes, and linguistic token budget but cannot choose interventions or update the next experiment from its own uncertainty.
- **H4 — contingency:** correctly ordered active experience outperforms `active_sensor_language_shuffled`, in which action–outcome alignment is broken while marginals and budgets are preserved.
- **H5 — closed-book permeability:** gains remain when the simulator, hypothesis ledger, generated summaries, and sensor projector are unavailable at text-only evaluation. Open-book system performance is secondary.
- **H6 — schema specificity:** grounding one schema changes transfer for that schema more than for an untrained schema.
- **H7 — efficiency:** the joint system reaches a given transfer level with fewer externally supplied language tokens than language-only controls. Report performance against environment steps, external language tokens, total generated tokens, optimiser steps, forward passes, and GPU time.
- **H8 — norm comparison:** direct experience plus language is compared with explicit `human_sensorimotor_norms` supervision. This distinguishes experiential grounding from direct semantic steering.
- **H9 — representational integration:** literal physical, abstract relational, and metaphorical instances of a grounded schema become more aligned in language-active layers, not only inside the sensory projector or external ledger.

### Planned contrasts

Let `G(condition, schema)` be the pre-to-post change in the preregistered schema-margin score.

Language-bridge effect on identical offline trajectories:

```text
Δlanguage = G(offline_sensor_language)
          - G(offline_sensor_raw)
```

Agency effect under a yoked design:

```text
Δagency = G(active_sensor_language)
        - G(yoked_passive_language)
```

Joint advantage under the primary budget:

```text
Δjoint_text   = G(active_sensor_language) - G(text_interactive_oracle)
Δjoint_sensor = G(active_sensor_language) - G(active_sensor_raw)
```

Schema-specific difference-in-differences:

```text
Δschema = Δjoint(trained_schema) - Δjoint(untrained_schema)
```

An exploratory superadditivity estimate may be computed in a fixed-policy 2×2 dataset where agency/presentation and language consolidation are factorially crossed. Do not call the effect superadditive unless all four cells receive genuinely comparable evidence and compute.

### Falsification and diagnostic outcomes

The strong complementarity hypothesis is not supported if:

- the joint condition fails both primary comparisons;
- apparent gains occur equally for untrained schemas;
- shuffled or passive experience produces the same effect;
- improvements exist only when the notebook is available;
- transfer is explained by lexical overlap, option order, benchmark contamination, generic adapter drift, or catastrophic forgetting;
- the model never demonstrably learns the literal causal regularities;
- or the result vanishes when external-language and compute budgets are accounted for.

A loss to the optional lossless text serialisation is not a falsification. That condition is an information ceiling, not the main ecological comparison.

---

## 4. Experimental scope and staging

### Phase I schemas

Retain two clean schemas:

1. **CONTAINMENT**
   - interior / exterior;
   - boundary;
   - entry / exit;
   - open versus closed boundary;
   - impeded exit.

2. **SUPPORT**
   - stable support;
   - support removal;
   - falling after support loss;
   - apparent contact without functional support;
   - support supplied by lower contact, attachment, or tension.

### Phase II causal richness

Increase complexity in ways that create learnable causal structure, not merely visual decoration. Add:

- multiple interacting objects;
- nested and moving containers;
- supports with load limits;
- tethers, suspension, attachment, and lateral bracing;
- permeability and leakage;
- friction, mass, compliance, elasticity, adhesion, and break thresholds;
- occlusion and partial observability;
- delayed consequences;
- stochastic but seed-controlled sensor noise;
- multi-step interventions;
- altered-physics test worlds;
- compositional episodes combining CONTAINMENT, SUPPORT, PATH, BLOCKAGE, and FORCE without naming those schemas in the observations.

Complexity follows a curriculum and must remain exactly auditable. Do not begin with photorealistic simulation, Minecraft, or an unrestricted robotics environment.

### Model posture

Phase I primary model:

- open-weight 1–2B base causal LM;
- frozen base plus LoRA and sensor embeddings;
- clean likelihood-based evaluation.

Phase II primary model:

- open-weight 1.5–4B instruction-capable or chat-capable transformer, configuration-driven;
- a language workspace capable of structured prediction, hypothesis, action, and consolidation outputs;
- trainable sensor projector, concept bridge, world-model head, and selected LoRA paths;
- a base-model or second-family replication after the pilot.

No model identity is hard-coded. Record repository, revision, licence, tokenizer hash, quantisation, and exact trainable parameter count.

### Model-stack continuity requirement

The Phase I gate validates a particular learning stack, not all possible later models. If Phase II changes the base checkpoint, tokenizer, instruction-tuning posture, sensor codec or projector, adapter placement, trainable component set, or objective family, run a reduced **Phase I compatibility calibration** on the exact Phase II stack before the Phase II pilot. The compatibility run must pass the literal-learning, contingency, retention, leakage, reproducibility, and provenance criteria. It need not repeat the full L3/L4 abstract and metaphor battery.

A Phase I pass from one model family may not be silently treated as evidence that another model family can use the sensor pathway.

### Hardware posture

All smoke and unit tests remain CPU-only. Phase I and a reduced Phase II pilot must run sequentially on one consumer NVIDIA GPU. The architecture must support checkpointing, gradient accumulation, QLoRA where compatible, and offline trajectory collection so that expensive online interaction is not repeated unnecessarily.

---

## 5. Experimental conditions

All conditions must begin from the same declared base checkpoint. Where a comparison claims matched information, experience, or compute, the repository must verify and report the match rather than merely asserting it.

### Phase I calibration matrix

#### P1-C0 — `no_adaptation`

Unchanged base model.

#### P1-C1 — `text_oracle`

Complete literal natural-language descriptions of the minimal deterministic episodes. This remains a strong calibration baseline.

#### P1-C2 — `sensor_causal`

Opaque correctly ordered observation–action–observation sequences with newly initialised sensor embeddings.

#### P1-C3 — `sensor_passive`

The same observations as P1-C2 with action and proprioceptive signals masked.

#### P1-C4 — `sensor_shuffled`

The same marginal tokens and episode statistics with action–outcome pairings permuted within matched strata.

#### Optional P1-C5 — `random_adaptation`

Unrelated literal material under the same optimiser and replay budget.

### Phase I interpretation rules

1. `sensor_causal` is **not required** to outperform `text_oracle` for Phase I to pass.
2. Abstract or metaphorical transfer is **not required** for Phase I to pass.
3. `sensor_passive` is primarily diagnostic. A causal–passive difference is informative, but its absence does not by itself invalidate the sensor pathway if contingency and held-out literal learning are established.
4. Failure to separate `sensor_causal` from `sensor_shuffled` on the preregistered literal causal measure is a hard no-go unless a concrete implementation or data defect is identified and the affected matrix is rerun from the frozen configuration.
5. Training-set fit without held-out template and configuration transfer is a hard no-go.
6. Phase I datasets, checkpoints, item-level scores, failed runs, and gate decisions remain archived after Phase II begins and may not be overwritten by later reruns.

### Phase II principal matrix

#### P2-C0 — `no_adaptation`

Unchanged Phase II base model.

#### P2-C1 — `text_summary`

Concise literal descriptions of episodes and causal outcomes at a fixed external-language budget. This approximates ordinary teaching or narration rather than lossless state serialisation.

#### P2-C2 — `text_interactive_oracle`

The model may choose interventions through the same action API, but all returned evidence is expressed in schema-neutral literal language at a fixed bandwidth. This control preserves active questioning and linguistic reasoning while removing the non-linguistic sensory channel.

#### P2-C3 — `offline_sensor_raw`

A fixed causal trajectory corpus is supplied through sensor and proprioceptive channels. The model receives world-model and prediction objectives but no natural-language hypothesis ledger or consolidation task.

#### P2-C4 — `offline_sensor_language`

Receives the identical fixed trajectory corpus as P2-C3 plus the structured language scaffold. This is the cleanest test of whether language helps experience penetrate the model's language-active representations.

#### P2-C5 — `active_sensor_raw`

The model chooses interventions from the sensor stream but performs no explicit natural-language hypothesis and consolidation cycle. It may use latent state and action policies.

#### P2-C6 — `active_sensor_language`

**Primary condition.** The model predicts, forms a concise literal hypothesis, chooses an informative intervention, observes the result, updates confidence, and periodically consolidates verified regularities in language linked to its latent world model.

#### P2-C7 — `yoked_passive_language`

Receives the exact trajectory, action sequence, outcomes, update schedule, and language-generation budget produced by a paired P2-C6 run, but cannot choose the interventions or adapt the next experiment to its own uncertainty. Pair IDs must be stored.

#### P2-C8 — `active_sensor_language_shuffled`

Matches P2-C6 budgets and sensor marginals but breaks action–outcome contingency within controlled strata.

#### P2-C9 — `human_sensorimotor_norms`

Receives explicit human sensorimotor ratings or norm-derived supervision for matched concepts under a separately declared token and optimiser budget. This condition tests direct semantic steering rather than direct experience and is not described as episode-equivalent.

#### Optional P2-C10 — `text_lossless_log`

A reversible textual or token-based serialisation of every sensor state, action, and result. This is an information ceiling and a representation-format control. It is not ordinary natural-language teaching and is not expected to be beaten in absolute terms.

#### Optional P2-C11 — `sham_language_compute`

Matches the additional generation and optimisation budget of P2-C6 but requires only surface-level, schema-neutral descriptions or unrelated reflection. It helps distinguish meaningful consolidation from extra inference and self-training.

### Budget views

Report results under at least three resource views:

1. **episode matched:** same number of environmental transitions;
2. **external-language matched:** same number of teacher/oracle language tokens;
3. **compute reported:** total generated tokens, forward passes, backward passes, optimiser steps, and GPU time.

Do not claim a fair modality comparison under an unreported unlimited oracle.

---

## 6. Environments: SchemaWorld Core and CausalSchemaLab

### Design principle

Use two nested environments.

- **SchemaWorld Core** is the minimal fixed-point environment required for Phase I causal calibration.
- **CausalSchemaLab** extends the same state machinery with hidden properties, partial observability, multi-object dynamics, and active experimental tasks for Phase II.

The increase in complexity must produce **causal richness and residual information after linguistic compression**, not merely higher-resolution images.

### Shared exact state

Use integer or fixed-point arithmetic for scientific state wherever possible. State may include:

- agent pose and gripper state;
- object pose, velocity, mass class, dimensions, and attachment state;
- containers, openings, gates, latches, and permeability;
- support surfaces, tethers, tension, and load limits;
- friction, adhesion, compliance, elasticity, and break thresholds;
- contact, force, collision, and occlusion;
- environment-specific gravity and delayed-event queues.

Ground-truth relations such as `INSIDE`, `SUPPORTED`, `BLOCKED`, and `CONNECTED` may exist for validation and scoring but must not appear in the primary sensor stream.

### Observation channels

Phase II may combine:

- low-resolution egocentric or scene RGB frames;
- proprioceptive vectors;
- contact and force readings;
- local depth or occupancy readings;
- action-history embeddings;
- optional low-bandwidth auditory event tokens;
- a natural-language task goal that remains literal and schema-neutral.

The model must not receive privileged global relation labels. A separate privileged diagnostic view may be used only by the simulator, verifier, and upper-bound conditions.

### Actions

Minimum action family:

```text
MOVE
ROTATE
GRASP
RELEASE
PUSH
PULL
LIFT
LOWER
OPEN
CLOSE
ATTACH
DETACH
CUT_OR_BREAK
WAIT
PROBE_FORCE
NOOP
```

Actions use structured parameters. The simple Phase I aliases remain available for backward compatibility.

### Active-discovery tasks

A Phase II episode is not merely “observe this transition.” It poses a literal discovery problem, for example:

- determine why an object remains elevated after a lower platform is removed;
- identify which boundary segment prevents exit;
- discover whether leakage depends on aperture, material, pressure, or elapsed time;
- determine the load at which a support fails;
- distinguish friction from attachment;
- infer whether a delayed collapse is caused by accumulated load or a hidden latch;
- identify which intervention most efficiently discriminates two plausible causal hypotheses.

Task prompts must not teach target metaphors or abstract target-domain mappings.

### Curriculum

Implement versioned levels:

- **L0:** single relation, complete observability, deterministic transition;
- **L1:** one hidden property and matched counterfactuals;
- **L2:** two interacting causal factors and distractors;
- **L3:** partial observability, delayed effects, and multi-step intervention;
- **L4:** schema composition and altered-physics transfer.

Progression may be fixed for confirmatory experiments. Adaptive curricula are exploratory unless their selection rule is frozen in advance.

### Determinism and replay

Given environment version, level, template, seed, action sequence, and noise seed, scientific trajectories must reproduce byte-for-byte. Every active trajectory must be replayable to a yoked passive condition. Store state, observation, and render hashes separately.

### Rendering

Provide a simple inspection renderer and a low-resolution model-input renderer. Rendering is optional in Phase I and supported in Phase II. No unit test may require a GPU, display server, or image encoder download.

---

## 7. Sensor, latent-world, and concept-bridge interfaces

### Phase I opaque codec

Retain the reversible opaque discrete codec using semantically meaningless new tokens such as `<u0041>`. It verifies end-to-end learning without relying on pretrained lexical meanings.

### Phase II multimodal projector

Implement a `ContinuousSensorProjector` that can combine:

- a small CNN or frozen configurable vision encoder;
- an MLP for proprioception, contact, and force;
- an action embedding;
- a temporal aggregator;
- projection into a fixed number of soft tokens or cross-attention keys for the language model.

The projector must expose a low-dimensional trajectory representation for world-model prediction and mechanistic analysis.

### Latent world model

Predict future sensory/proprioceptive latents conditioned on candidate actions. The latent world model exists because fine-grained physical dynamics may be cumbersome or lossy when forced entirely through explicit natural language.

Minimum functions:

```text
encode_observation(obs) -> z_t
predict_next(z_t, action) -> z_hat_t1
predict_counterfactual(z_t, candidate_actions) -> {z_hat}
estimate_uncertainty(...) -> scores
```

### Bidirectional concept bridge

The central Phase II component is a small, inspectable bridge between the pretrained semantic space and the latent world model.

```text
language hypothesis / goal
          ↓
 semantic-to-latent conditioning
          ↓
world-model predictions and action selection
          ↓
 trajectory evidence / prediction error
          ↓
 latent-to-language soft tokens and consolidation
```

The bridge must not inject schema labels. It should permit action-aware gradients to affect selected language-model LoRA paths while protecting the broader pretrained semantic representation through replay, KL regularisation, staged training, and ablations.

### Representation controls

Support:

- sensor projector frozen versus trainable;
- concept bridge frozen versus trainable;
- language LoRA enabled versus disabled;
- world-model-only adaptation;
- language-consolidation-only adaptation;
- projector and bridge ablation at evaluation.

These controls locate whether apparent learning remains compartmentalised.

---

## 8. Language-scaffolded active learning and adaptation data

### Core cognitive loop

The primary condition repeats the following auditable cycle:

```text
OBSERVE
  → PREDICT
  → STATE A LITERAL HYPOTHESIS
  → CHOOSE A DISCRIMINATING ACTION
  → ACT
  → OBSERVE OUTCOME
  → SCORE PREDICTION ERROR
  → UPDATE HYPOTHESIS CONFIDENCE
  → CONSOLIDATE PERIODICALLY
```

The language scaffold is not unrestricted chain-of-thought. Store concise structured artifacts:

```text
prediction: structured outcome fields plus confidence
hypothesis: one or two literal sentences
chosen_action: typed tool action
expected_information_gain: optional scalar
outcome_summary: one literal sentence
revision: retain / revise / reject hypothesis
```

### Hypothesis ledger

Maintain a versioned external ledger containing:

- hypothesis ID and text;
- confidence;
- supporting and contradicting episode IDs;
- predictions made before interventions;
- calibration score;
- proposed discriminating experiment;
- status and parent hypothesis.

The ledger supports active learning and interpretability. It must be unavailable in the primary closed-book evaluation.

### Grounded verification

No external teacher supplies schema names or metaphorical explanations. The simulator verifies:

- whether the predicted observable outcome occurred;
- whether a proposed intervention was legal;
- how much uncertainty was reduced under a declared estimator;
- and whether a counterfactual prediction matches the simulator.

Natural-language summaries are retained only with complete provenance. The verifier does not use an LLM judge for the primary learning signal.

### Consolidation

After a fixed block of episodes, produce a literal consolidation record that links:

- a trajectory latent or prototype;
- successful and failed predictions;
- a concise self-generated causal description;
- matched counterfactuals;
- and confidence.

Train selected language LoRA paths and the concept bridge on these grounded records, together with replay and retention objectives. This is the mechanism intended to “unfreeze” the inherited linguistic prior rather than asking opaque tokens to replace it.

### Training objectives

A configurable objective may include:

```text
L_total = w_world      * L_future_latent
        + w_inverse    * L_action_or_inverse_dynamics
        + w_outcome    * L_structured_outcome_prediction
        + w_align      * L_trajectory_language_alignment
        + w_cf         * L_counterfactual_prediction
        + w_calibrate  * L_prediction_calibration
        + w_replay     * L_language_replay
        + w_retention  * L_KL_to_base
```

Every weight and active parameter set must be logged.

### Literal-language policy

External prompts, oracle responses, and retained consolidation text must remain literal. They may describe physical objects, actions, observations, uncertainty, and causal hypotheses. They must not contain evaluation metaphors or abstract target domains.

The model may spontaneously use familiar schema words such as “support,” “inside,” or “blocked”; this is part of leveraging its language prior. However:

- no teacher rewards a word merely for matching a target schema label;
- self-generated statements must earn retention through predictive success;
- known evaluation target-domain vocabulary and metaphor templates are filtered;
- all generated language is archived for leakage audit.

### Human sensorimotor norms condition

Implement a separate dataset adapter for licensed human sensorimotor norms. It may supervise ratings or representational alignment for words and concepts relevant to the schemas. Record dataset version, dimensions, licence, language, and mapping rules. This condition must not be described as equivalent to direct experience; it tests whether direct semantic supervision reaches the evaluation more efficiently.

### Memory and evaluation modes

- **Closed-book primary:** no simulator, sensor stream, ledger, episode summaries, retrieval database, or generated consolidation text is available.
- **Open-book secondary:** the ledger or selected grounded memories may be retrieved.
- **Base-model retention:** ordinary language tests ensure the intervention has not simply damaged or globally shifted the model.

---

## 9. Benchmark architecture

Build and freeze the benchmark before treatment training. Keep the original controlled tasks and add tests that require the richer Phase II causal invariants.

### Task A — controlled abstract structural transfer

Describe an unfamiliar abstract system with nonce entities and minimal spatial cue words, then ask which consequence or analogy preserves the learned causal relation.

### Task B — novel metaphor entailment

Present a newly authored metaphor and ask which continuation preserves its relational and causal mapping. Avoid relying only on familiar conventional metaphors.

### Task C — compositional metaphor

Combine two schemas or two support mechanisms, for example containment plus leakage or support plus delayed failure. The correct answer must depend on causal composition rather than one lexical cue.

### Task D — novel physical analogy

Test whether a regularity learned through one embodiment or mechanism transfers to another, such as platform support to suspension by tension, or rigid containment to a selectively permeable boundary.

### Task E — literal and counterfactual world reasoning

Verify that every treatment learned the source-domain dynamics, including hidden properties, interventions, and counterfactual outcomes.

### Task F — schema specificity

Evaluate trained and untrained schemas to support difference-in-differences analysis.

### Task G — information-seeking and causal discovery

For active conditions, measure whether chosen interventions discriminate plausible hypotheses efficiently. This is a process measure, not the primary metaphor endpoint.

### Task H — external diagnostics

Where licensing permits, support adapters for:

- Wicke and Wachowiak spatial-schema tasks;
- Proietti et al. locative image-schema tasks;
- embodied-knowledge and sensorimotor-norm diagnostics;
- a clean-room `wang_liao_inspired` set;
- metaphor-vehicle tasks with distributional and sensorimotor controls.

### Closed-book primary endpoint

All primary abstract and metaphor tasks are text-only. The model receives no sensor soft tokens, simulator access, notebook, retrieval, or episode summary. This establishes whether learning reached ordinary language-active representations.

### Primary score

For each forced-choice item:

```text
schema_margin = length_normalised_logP(schema-consistent option | prompt)
              - length_normalised_logP(inconsistent option | prompt)
```

Average original and reversed option order.

### Efficiency curves

Report transfer performance as a function of:

- environment transitions;
- external teacher/oracle language tokens;
- self-generated language tokens;
- optimiser updates;
- total forward passes;
- GPU time;
- and stored experience bytes.

The central practical question is not only which condition wins with unlimited information, but which architecture extracts transferable structure with realistic supervision and compute.

### Benchmark item requirements

Retain stable IDs, schema, task type, target-domain family, prompt template, answer options, reverse form, lexical-cue annotations, provenance, human validation, release status, and content hash. Add:

- required causal factors;
- composition depth;
- conventionality estimate;
- source-mechanism family;
- external-language overlap flags;
- and closed/open-book eligibility.

Human validation and ethics requirements remain as in revision 2.

---

## 10. Model and agent architecture

### Phase II architecture

```text
                  literal task goal
                         │
                         ▼
              PRETRAINED LANGUAGE CORE
          ┌──────────────┼────────────────┐
          │              │                │
          ▼              ▼                ▼
 hypothesis ledger   experiment planner   consolidation
          │              │                │
          └──────────────┼────────────────┘
                         ↕
              BIDIRECTIONAL CONCEPT BRIDGE
                         ↕
          ┌──────────────┼────────────────┐
          ▼              ▼                ▼
  sensor projector   latent world model   action decoder
          ▲              │                │
          │              ▼                ▼
   observations     counterfactuals    typed actions
          ▲                               │
          └────────── CausalSchemaLab ◄───┘
```

### Design rationale

The language core should not be reduced to a passive encoder for low-level action. It supplies semantic priors, hypothesis vocabulary, analogy, experiment planning, and compression. The latent world model handles fine temporal and physical detail that may be inefficient or impossible to verbalise completely. The concept bridge allows evidence and prediction errors to modify selected language-active paths without indiscriminately overwriting the pretrained semantic space.

### Training stages

1. **Projector/world-model warm-up:** train the sensor projector and latent dynamics on fixed trajectories while the language core is frozen.
2. **Bridge alignment:** align trajectory latents with literal outcome descriptions and structured predictions.
3. **Active acquisition:** enable intervention selection and online hypothesis updates.
4. **Slow consolidation:** update selected LoRA paths using verified trajectory–prediction–language records with replay and KL protection.
5. **Frozen closed-book evaluation:** disable all external memory and sensor components.

### Trainable components

Configuration may enable:

- sensor projector;
- temporal world model;
- action head;
- concept bridge;
- language LoRA on selected attention and MLP projections;
- new action and sensor token embeddings;
- optional hypothesis-confidence head.

Record both total trainable parameters and parameters active during closed-book text evaluation.

### Compartmentalisation ablations

Evaluate:

- sensor/world model with language LoRA frozen;
- language LoRA with projector detached;
- bridge removed after training;
- ledger-only learning with no weight consolidation;
- weight consolidation with ledger removed;
- open-book versus closed-book;
- ordinary text oracle versus lossless serialisation.

These ablations distinguish learning from **conceptual permeability**.

---

## 11. Evaluation and statistics

### Pre/post gain

For each run, schema, and benchmark family:

```text
G = post_schema_margin - pre_schema_margin
```

### Phase I transfer profile and mandatory gate

Every Phase I matrix produces both an ordinary scientific report and a formal gate report. The gate thresholds and decision logic must be frozen in `configs/gate/phase1.yaml` before the first non-smoke treatment run. Threshold values may be calibrated from benchmark construction, unchanged-base scores, and tiny-model sanity checks, but never from post-treatment condition comparisons.

The hard gate criteria are:

- **G1 — held-out literal learning:** `sensor_causal` shows a preregistered positive gain on L1 held-out literal causal prediction.
- **G2 — causal specificity:** `sensor_causal` exceeds `sensor_shuffled` on the preregistered causal contrast under matched marginals and budgets.
- **G3 — transfer beyond memorisation:** the effect persists on L2 unseen templates, object identities, spatial arrangements, and counterfactual configurations.
- **G4 — reproducibility:** the declared effect direction is reproducible across at least three independent seeds; all completed, failed, and excluded runs are included under the preregistered rules. If uncertainty remains too large, the gate status is `INCONCLUSIVE`, not selectively rerun until favourable.
- **G5 — language retention:** declared retention measures remain within the frozen tolerance, or a clearly bounded trade-off is approved before Phase II.
- **G6 — integrity:** leakage audits, dataset and benchmark hashes, condition parity checks, run manifests, budget ledgers, and checkpoint provenance all pass.

The following outcomes are explicitly **non-gating**:

- whether `sensor_causal` beats `text_oracle`;
- whether `sensor_causal` beats `sensor_passive`;
- whether L3 abstract transfer is significant;
- whether L4 metaphorical transfer is significant;
- whether the sensor condition is the highest-scoring Phase I treatment overall.

The gate evaluator returns exactly one status:

- **`PASS`:** all hard criteria pass. Phase II scientific development and runs may proceed.
- **`INCONCLUSIVE`:** evidence is underpowered, a nontrivial anomaly remains unresolved, or a repair requires a full frozen-matrix rerun. Engineering scaffolding may continue, but no Phase II scientific pilot may begin.
- **`NO_GO`:** literal causal learning, contingency, generalisation, retention, or integrity fails under the declared design. Diagnose or redesign Phase I before beginning Phase II.

Required artifacts:

```text
reports/phase-gates/<group-id>/phase1_gate_report.md
reports/phase-gates/<group-id>/phase1_gate_report.json
reports/phase-gates/<group-id>/phase1_gate_approval.yaml
```

The JSON report must enumerate every criterion, threshold, observed value, confidence interval, seed, failed run, exclusion, artifact hash, and status. The approval file records the report hash, gate-config hash, Git commit, decision, signer, timestamp, and rationale. Changing any referenced result or configuration invalidates the approval.

The report must also preserve the full L0–L4 transfer profile. This profile determines what Phase II is trying to bridge even though L3 and L4 do not affect the gate decision.

### Co-primary Phase II comparisons

Under the preregistered external-language and environment-step budget:

```text
C1 = G(active_sensor_language) - G(text_interactive_oracle)
C2 = G(active_sensor_language) - G(active_sensor_raw)
```

The strongest complementarity claim requires both C1 and C2 to be positive on trained-schema closed-book transfer, with schema specificity.

### Supporting contrasts

```text
Language bridge:
G(offline_sensor_language) - G(offline_sensor_raw)

Agency:
G(active_sensor_language) - G(yoked_passive_language)

Contingency:
G(active_sensor_language) - G(active_sensor_language_shuffled)

Semantic supervision:
G(active_sensor_language) - G(human_sensorimotor_norms)
```

The norms comparison is descriptive unless a defensible resource match is preregistered.

### Schema-specific contrast

```text
ΔDiD = contrast(trained_schema) - contrast(untrained_schema)
```

### Efficiency analysis

Fit learning curves over experience and supervision budgets. Report area under the learning curve and the budget required to reach predefined transfer thresholds. Never compare only final checkpoints when conditions consume very different external language or inference resources.

### Pilot and confirmatory runs

Phase I pilot and gate:

- three seeds per condition and schema at minimum;
- hierarchical bootstrap over items and runs;
- a frozen `configs/gate/phase1.yaml` before treatment runs;
- explicit L0–L4 transfer-profile reporting;
- formal `PASS`, `INCONCLUSIVE`, or `NO_GO` gate output;
- establish held-out literal learning, contingency, generalisation beyond templates, retention, leakage control, and provenance integrity;
- never use L3 or L4 outcomes to decide whether Phase II may begin.

Phase II pilot:

- begin with one rich schema curriculum and at least three seeds for the minimum matrix;
- include an untrained schema evaluation set;
- use the result to estimate variance and training budget, not to select favorable benchmark items.

Phase II confirmatory:

- both schemas;
- at least five seeds per primary condition;
- frozen benchmark and curriculum;
- preregistered co-primary contrasts;
- mixed-effects or hierarchical model with item, run, and paired/yoked effects;
- correction for declared secondary families;
- all completed and failed seeds reported.

A suitable model is:

```text
schema_margin ~ condition * trained_schema * item_schema
              + baseline_margin
              + experience_budget
              + (1 | item_id)
              + (1 | run_id)
              + (1 | yoked_pair_id)
```

Use the yoked random effect only where applicable.

### Evaluation safeguards

- Freeze prompts and scoring before treatment.
- Score primary tasks by model likelihood, not an LLM judge.
- Counterbalance option order.
- Keep the evaluator unaware of condition labels when rendering prompts.
- Preserve raw item-level scores.
- Evaluate both closed-book and open-book, but label closed-book primary.
- Report language retention, calibration, and catastrophic drift.
- Treat the lossless text log as an upper-bound control rather than moving the primary goalpost.

---

## 12. Mechanistic and process analysis

Mechanistic analysis remains secondary to behavioural transfer, with explicit tests of the sensor-to-language path retained in this revision.

### Activation capture

Capture matched pre/post representations for:

- literal observations and descriptions;
- latent world-model states;
- hypotheses before and after disconfirming evidence;
- novel abstract items;
- novel metaphors;
- untrained-schema and non-schema controls.

### Analyses

1. **Representational similarity:** whether physical, abstract, and metaphorical instances converge in language-active layers.
2. **Cross-modal probing:** train probes on trajectory or literal states and test on abstract/metaphorical items, and vice versa.
3. **Bridge tracing:** measure which language layers receive schema-selective gradients and activation changes from the concept bridge.
4. **Prediction-error analysis:** test whether disconfirming interventions cause larger, structured representation updates than expected outcomes.
5. **Adapter and bridge ablation:** determine whether closed-book gains reside in shared language LoRA paths rather than only sensory modules.
6. **Ledger ablation:** compare open-book retrieval with internalised weight change.
7. **Activation patching:** patch representations between raw-sensor, language-scaffolded, text-only, and norm-supervised models.
8. **Causal component ablation:** remove high-change heads, MLPs, bridge tokens, or world-model features and measure selective loss.
9. **Hypothesis-quality process metrics:** prediction calibration, experiment information gain, revision after counterevidence, and compression ratio.

Do not interpret attractive embedding plots as evidence of grounding when the preregistered behavioural effect is absent.

---

## 13. Phase III neural-colony extension

Do not begin this phase until the monolithic language-scaffolded architecture produces either a stable transfer effect or a well-characterised compartmentalisation/null result.

### Colony research question

Can grounding acquired by a sensory specialist alter the closed-book metaphorical and abstract-language behaviour of a separate language specialist that never directly receives the sensor stream?

### Prior-art boundary

CATS Net already demonstrates concept abstraction from sensory tasks and conceptual communication between neural networks. The Phase III novelty cannot be generic concept transfer. It must concern transfer **into a separate pretrained language system** and its effect on ordinary linguistic generalisation.

### Proposed colony

```text
CausalSchemaLab
      │
      ▼
Sensor / World Specialist
      │ verified latent concepts and predictions
      ▼
Concept Translator / Communication Bottleneck
      │
      ├────────► Shared episodic or prototype memory
      │
      ▼
Language Specialist
      │
      ▼
closed-book abstract and metaphor evaluation
```

### Specialists

- **Sensor/world specialist:** multimodal projector and latent world model; may use a small LM but is evaluated primarily on physical prediction and causal discovery.
- **Language specialist:** separate descendant of the same or a matched base LM; receives no raw sensor observations.
- **Concept translator:** constrained learned bottleneck supporting natural-language, typed latent, or hybrid messages.
- **Memory specialist, optional:** stores grounded prototypes with strict evaluation isolation.

### Controls

- no communication;
- literal natural-language summaries;
- learned latent concepts;
- hybrid language-plus-latent messages;
- shuffled, delayed, or capacity-limited messages;
- monolithic active-sensor-language model;
- parameter- and compute-matched extra-inference control.

### Core criterion

The language specialist must be evaluated closed-book after communication and consolidation, with no raw sensor stream and no target benchmark examples. Otherwise the study measures retrieval or ordinary tool use rather than propagation of grounding.

---

## 14. Repository layout

```text
unfrozen-schemas/
├── AGENTS.md
├── CODEX_SPEC.md
├── README.md
├── LICENSE
├── CITATION.cff
├── pyproject.toml
├── uv.lock
├── .python-version
├── .gitignore
├── .env.example
├── docker/
│   ├── Dockerfile.cpu
│   ├── Dockerfile.cuda
│   └── compose.yaml
├── configs/
│   ├── experiment/
│   │   ├── smoke.yaml
│   │   ├── phase1_pilot.yaml
│   │   ├── phase1_confirmatory.yaml
│   │   ├── phase2_pilot.yaml
│   │   └── phase2_confirmatory.yaml
│   ├── model/
│   │   ├── tiny_random.yaml
│   │   ├── phase1_base_lora.yaml
│   │   ├── phase2_instruction_lora.yaml
│   │   └── replication_model.yaml
│   ├── condition/
│   │   ├── no_adaptation.yaml
│   │   ├── text_oracle.yaml
│   │   ├── sensor_causal.yaml
│   │   ├── sensor_passive.yaml
│   │   ├── sensor_shuffled.yaml
│   │   ├── text_summary.yaml
│   │   ├── text_interactive_oracle.yaml
│   │   ├── offline_sensor_raw.yaml
│   │   ├── offline_sensor_language.yaml
│   │   ├── active_sensor_raw.yaml
│   │   ├── active_sensor_language.yaml
│   │   ├── yoked_passive_language.yaml
│   │   ├── active_sensor_language_shuffled.yaml
│   │   ├── human_sensorimotor_norms.yaml
│   │   ├── text_lossless_log.yaml
│   │   └── sham_language_compute.yaml
│   ├── curriculum/
│   │   ├── core_l0.yaml
│   │   ├── causal_l1.yaml
│   │   ├── causal_l2.yaml
│   │   ├── causal_l3.yaml
│   │   └── composition_l4.yaml
│   ├── schema/
│   │   ├── containment.yaml
│   │   ├── support.yaml
│   │   ├── path.yaml
│   │   ├── blockage.yaml
│   │   └── force.yaml
│   ├── evaluation/
│   │   ├── benchmark_v1.yaml
│   │   ├── benchmark_v2_rich.yaml
│   │   └── retention.yaml
│   └── gate/
│       ├── phase1.yaml
│       └── phase1_compatibility.yaml
├── src/
│   └── unfrozen_schemas/
│       ├── __init__.py
│       ├── cli.py
│       ├── config.py
│       ├── constants.py
│       ├── provenance.py
│       ├── envs/
│       │   ├── schema_world/
│       │   │   ├── state.py
│       │   │   ├── actions.py
│       │   │   ├── dynamics.py
│       │   │   ├── relations.py
│       │   │   ├── templates.py
│       │   │   └── renderer.py
│       │   └── causal_schema_lab/
│       │       ├── state.py
│       │       ├── hidden_properties.py
│       │       ├── sensors.py
│       │       ├── actions.py
│       │       ├── fixed_point_physics.py
│       │       ├── tasks.py
│       │       ├── curriculum.py
│       │       └── replay.py
│       ├── codecs/
│       │   ├── protocol.py
│       │   ├── opaque_tokens.py
│       │   ├── text_oracle.py
│       │   ├── lossless_text.py
│       │   └── multimodal_projector.py
│       ├── world_models/
│       │   ├── latent_dynamics.py
│       │   ├── inverse_dynamics.py
│       │   ├── counterfactuals.py
│       │   └── uncertainty.py
│       ├── bridge/
│       │   ├── concept_bridge.py
│       │   ├── soft_tokens.py
│       │   ├── alignment.py
│       │   └── ablations.py
│       ├── agents/
│       │   ├── protocol.py
│       │   ├── planner.py
│       │   ├── hypothesis_ledger.py
│       │   ├── predictor.py
│       │   ├── consolidator.py
│       │   ├── active_loop.py
│       │   └── yoked_replay.py
│       ├── data/
│       │   ├── generate.py
│       │   ├── collect.py
│       │   ├── manifests.py
│       │   ├── splits.py
│       │   ├── transforms.py
│       │   ├── captions.py
│       │   ├── norms.py
│       │   ├── leakage.py
│       │   ├── budgets.py
│       │   └── hashing.py
│       ├── models/
│       │   ├── loader.py
│       │   ├── tokenizer.py
│       │   ├── lora.py
│       │   ├── objectives.py
│       │   ├── sensor_embeddings.py
│       │   └── checkpoint.py
│       ├── training/
│       │   ├── trainer.py
│       │   ├── staged_training.py
│       │   ├── sampler.py
│       │   ├── replay.py
│       │   ├── retention.py
│       │   ├── resume.py
│       │   └── run_manifest.py
│       ├── evaluation/
│       │   ├── benchmark.py
│       │   ├── likelihood.py
│       │   ├── option_order.py
│       │   ├── literal.py
│       │   ├── discovery.py
│       │   ├── transfer_ladder.py
│       │   ├── phase_gate.py
│       │   ├── closed_book.py
│       │   ├── open_book.py
│       │   ├── retention.py
│       │   ├── efficiency.py
│       │   └── metrics.py
│       ├── statistics/
│       │   ├── contrasts.py
│       │   ├── learning_curves.py
│       │   ├── bootstrap.py
│       │   ├── mixed_effects.py
│       │   └── tables.py
│       ├── interpretability/
│       │   ├── hooks.py
│       │   ├── activations.py
│       │   ├── rsa.py
│       │   ├── probes.py
│       │   ├── bridge_trace.py
│       │   ├── patching.py
│       │   └── ablation.py
│       ├── colony/
│       │   ├── protocol.py
│       │   ├── messages.py
│       │   ├── specialists.py
│       │   ├── translator.py
│       │   └── orchestrator.py
│       └── reporting/
│           ├── plots.py
│           ├── report.py
│           ├── phase_gate_report.py
│           └── templates/
├── benchmarks/
│   ├── source/
│   ├── frozen/
│   │   ├── v1_core/
│   │   └── v2_rich/
│   └── private/
├── data/
│   ├── generated/
│   ├── active_trajectories/
│   ├── yoked_trajectories/
│   ├── ledgers/
│   ├── norms/
│   └── replay/
├── docs/
│   ├── novelty-review.md
│   ├── scientific-design.md
│   ├── language-scaffold-protocol.md
│   ├── budget-accounting.md
│   ├── phase-gate-protocol.md
│   ├── preregistration.md
│   ├── benchmark-card.md
│   ├── model-card-template.md
│   ├── data-card.md
│   ├── implementation-plan.md
│   └── open-questions.md
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── regression/
│   └── fixtures/
├── scripts/
│   ├── smoke.ps1
│   ├── smoke.sh
│   ├── run_phase1.ps1
│   ├── run_phase1.sh
│   ├── run_phase2.ps1
│   └── run_phase2.sh
├── runs/
│   └── .gitkeep
└── reports/
    ├── phase-gates/
    │   └── .gitkeep
    └── .gitkeep
```

---

## 15. Technology choices

Use:

- Python 3.11;
- `uv` for dependency and virtual-environment management;
- PyTorch;
- Hugging Face `transformers`, `accelerate`, and `peft`;
- `safetensors` for checkpoints;
- Pydantic for validated configuration;
- Typer for the CLI;
- PyArrow/Parquet for trajectories, ledgers, budgets, and item-level metrics;
- NumPy, SciPy, pandas or Polars for analysis;
- statsmodels and/or a clearly isolated optional Bayesian extra;
- Matplotlib for reports;
- pytest, pytest-cov, Ruff, and mypy or Pyright;
- GitHub Actions for CPU-only lint, test, and smoke checks.

Environment requirements:

- use a custom fixed-point or integer scientific state engine for the primary causal results;
- optional image rendering may use Pillow or Pygame without becoming a scientific dependency;
- expose Gymnasium-style reset/step interfaces without requiring Gymnasium if a smaller internal protocol is sufficient;
- keep optional vision encoders and online-RL libraries behind extras;
- do not require a cloud experiment tracker.

No notebook may contain production logic absent from `src/`. Store local run artifacts and complete provenance first. Make external trackers optional adapters.

---

## 16. Command-line interface

Required Phase I commands:

```bash
uv run unfrozen validate-config --config configs/experiment/smoke.yaml
uv run unfrozen generate-core --config configs/experiment/phase1_pilot.yaml
uv run unfrozen inspect-episode --episode-id <id> --render
uv run unfrozen build-benchmark --source benchmarks/source --output benchmarks/private/v1_core
uv run unfrozen validate-benchmark --version v1_core
uv run unfrozen freeze-benchmark --version v1_core
uv run unfrozen train --config configs/experiment/phase1_pilot.yaml \
  --condition sensor_causal --schema containment --seed 101
uv run unfrozen evaluate --run-id <run-id> --benchmark v1_core --closed-book
uv run unfrozen run-matrix --config configs/experiment/phase1_pilot.yaml
uv run unfrozen evaluate-phase-gate --phase 1 --group <group-id> \
  --gate-config configs/gate/phase1.yaml
uv run unfrozen approve-phase-gate --report \
  reports/phase-gates/<group-id>/phase1_gate_report.json \
  --decision PASS --signer <name>
uv run unfrozen verify-phase-gate --approval \
  reports/phase-gates/<group-id>/phase1_gate_approval.yaml
```

Required Phase II commands:

```bash
uv run unfrozen generate-curriculum --config configs/experiment/phase2_pilot.yaml
uv run unfrozen collect-active --condition active_sensor_language --seed 201
uv run unfrozen validate-trajectory --trajectory-id <id>
uv run unfrozen build-yoked --source-run <run-id>
uv run unfrozen replay-yoked --pair-id <pair-id>
uv run unfrozen audit-language --run-id <run-id>
uv run unfrozen audit-budget --group <group-id>
uv run unfrozen consolidate --run-id <run-id>
uv run unfrozen train-stage --run-id <run-id> --stage bridge
uv run unfrozen train-stage --run-id <run-id> --stage consolidation
uv run unfrozen evaluate --run-id <run-id> --benchmark v2_rich --closed-book
uv run unfrozen evaluate --run-id <run-id> --benchmark v2_rich --open-book
uv run unfrozen run-matrix --config configs/experiment/phase2_pilot.yaml \
  --phase1-approval reports/phase-gates/<phase1-group-id>/phase1_gate_approval.yaml
uv run unfrozen analyse --group <group-id>
uv run unfrozen report --group <group-id>
uv run unfrozen smoke
```

All commands require:

- a valid Phase I `PASS` approval for Phase II scientific collection, training, and matrix commands;
- an `--engineering-only` mode for deterministic fixtures and integration tests that cannot create publishable Phase II results and is unmistakably marked in manifests;
- `--dry-run` where meaningful;
- resumability and idempotent manifests;
- structured JSON logs plus readable console output;
- non-zero exit status on invalid data, leakage, mismatched yoked pairs, unreported budgets, or incomplete provenance;
- no network, CUDA, model download, or secrets for `unfrozen smoke`.

---

## 17. Data formats and resource accounting

### Episode metadata

`episodes.parquet`:

```text
episode_id: string
parent_pair_id: string
schema: enum
curriculum_level: int
template_id: string
seed: int
noise_seed: int
split: enum[train, validation, test]
difficulty: int
hidden_property_profile_id: string
trajectory_source: enum[fixed, active, yoked, shuffled]
yoked_pair_id: optional string
environment_version: string
state_hash: string
observation_hash: string
render_hash: optional string
```

### Step data

`steps.parquet`:

```text
episode_id: string
step_index: int
observation_before: binary/blob or fixed numeric arrays
action_id: int
action_parameters: numeric array
observation_after: binary/blob or fixed numeric arrays
privileged_state_before: reference/hash
privileged_state_after: reference/hash
ground_truth_relations_before: bitset/list
ground_truth_relations_after: bitset/list
prediction_id: optional string
reward_or_success: float/bool
information_gain: optional float
```

### Hypothesis ledger

`hypotheses.parquet`:

```text
hypothesis_id: string
run_id: string
parent_hypothesis_id: optional string
created_after_episode_id: string
literal_text: string
confidence: float
predicted_outcome_struct: json
supporting_episode_ids: list[string]
contradicting_episode_ids: list[string]
proposed_action_struct: json
status: enum[active, revised, rejected, consolidated]
external_language_tokens: int
self_generated_tokens: int
content_hash: string
```

### Budget ledger

`budgets.parquet` records per run and checkpoint:

```text
environment_steps
unique_episodes
external_language_tokens
self_generated_language_tokens
sensor_bytes
forward_passes
backward_passes
optimizer_steps
trainable_parameter_steps
gpu_seconds
wall_seconds
peak_vram_bytes
```

### Benchmark table

Retain revision 2 fields and add:

```text
required_causal_factors: list[string]
composition_depth: int
source_mechanism_family: string
conventionality_mean: optional float
external_language_overlap_flags: list[string]
closed_book_eligible: bool
```

### Phase-gate report and approval

`phase1_gate_report.json` stores:

```text
phase: 1
gate_type: enum[primary, compatibility]
group_id: string
parent_primary_gate_report_hash: optional string
gate_config_hash: string
matrix_manifest_hash: string
model_stack_fingerprint: string
criteria: list[
  criterion_id,
  threshold,
  observed_value,
  confidence_interval,
  passed,
  evidence_paths
]
all_run_ids: list[string]
failed_run_ids: list[string]
excluded_run_ids: list[string]
transfer_profile_L0_to_L4: structured metrics
status: enum[PASS, INCONCLUSIVE, NO_GO]
status_reason: string
report_hash: string
```

`phase1_gate_approval.yaml` stores the gate type, report hash, parent primary-gate hash where applicable, gate-config hash, model-stack fingerprint, Git commit, decision, signer, timestamp, and rationale. Phase II commands reject missing, non-`PASS`, stale, or hash-mismatched primary or compatibility approvals.

### Run manifest

Every run stores:

- run and group IDs;
- condition, phase, schema, curriculum, and yoked-pair IDs;
- Git commit and dirty state;
- resolved configuration;
- model/tokenizer/checkpoint hashes;
- dataset, trajectory, ledger, benchmark, and replay hashes;
- package, CUDA, driver, PyTorch, and GPU metadata;
- seeds;
- trainable parameter counts by component;
- exact resource totals from the budget ledger;
- start/end status, checkpoint hashes, metrics paths, and failure reason.

---

## 18. Testing requirements

### Unit tests

Cover:

- exact fixed-point transitions and delayed events;
- relation derivation from privileged raw state;
- hidden properties absent from ordinary observations;
- matched counterfactual generation;
- opaque-codec reversibility;
- multimodal-projector shape and masking contracts;
- latent world-model deterministic toy predictions;
- action legality and structured tool parsing;
- active trajectory replay;
- byte-identical active/yoked scientific trajectories;
- shuffled-condition marginal preservation;
- text-lossless-log reversibility;
- external and self-generated token accounting;
- hypothesis-ledger lineage and hashes;
- literal-language and benchmark-leakage audits;
- closed-book evaluator denial of ledger, sensor, and retrieval access;
- option-order averaging and likelihood scoring;
- L0–L4 transfer-ladder aggregation;
- gate criteria evaluated only from frozen hard-gate metrics;
- L3 and L4 scores cannot alter Phase I gate status;
- missing or failed required seeds prevent a false `PASS`;
- approval hashes become invalid when reports, gate configs, model-stack fingerprints, or commits change;
- Phase II scientific commands reject absent, stale, or non-`PASS` approvals;
- run-manifest completeness.

### Integration tests

- generate Phase I and tiny Phase II curricula;
- collect a short active trajectory with a deterministic toy policy;
- replay it in a yoked passive condition;
- execute one projector/world-model update;
- generate and store a structured hypothesis artifact;
- perform one bridge/consolidation update on a tiny random transformer;
- save, resume, and evaluate closed-book;
- generate budget and provenance reports;
- require no network or GPU.

### Regression tests

Pin hashes for:

- selected core and rich trajectories;
- fixed curriculum manifests;
- condition transforms;
- yoked pairs;
- language-audit decisions;
- budget calculations;
- primary metric and learning-curve calculations.

### GPU smoke tests

Separately marked tests may load a small real model and optional vision encoder, perform one staged update, save/reload adapters, and score one closed-book item. They are not run in ordinary CI.

---

## 19. Reproducibility and scientific-integrity rules

1. Freeze primary benchmarks before treatment training.
2. Freeze confirmatory curricula, task-selection rules, and language budgets before confirmatory runs.
3. Never generate benchmark answers with the evaluated model.
4. Never silently edit benchmark items, task templates, or hidden-property distributions after viewing treatment effects.
5. Store all active trajectories so yoked and shuffled controls are reproducible.
6. Distinguish external language, self-generated language, raw sensor bytes, and lossless serialisation in every report.
7. Do not describe `text_lossless_log` as ordinary natural language or use its likely advantage to dismiss the main complementarity question.
8. Do not call a comparison information matched unless reversibility or a declared information audit supports it.
9. Primary Phase II results are closed-book. Open-book results must be labelled system-level retrieval performance.
10. No teacher response, consolidation prompt, or retained self-generated record may contain evaluation metaphors or target-domain examples.
11. Archive all generated language and run leakage audits before evaluation.
12. Do not reward a hypothesis because it uses a preferred schema word; reward only predeclared prediction, calibration, information, or task signals.
13. Match or explicitly report optimiser, token, forward-pass, parameter, environment-step, and GPU budgets.
14. Never discard inconvenient seeds or silently rerun them with altered settings.
15. Log failed runs and report them.
16. Distinguish exploratory, pilot, and confirmatory analyses in code, filenames, and reports.
17. Treat null, compartmentalised, and text-dominant results as valid outcomes.
18. Do not describe opaque vectors or simulated interaction as complete biological embodiment.
19. Do not infer consciousness or human understanding from metaphor-score changes.
20. Keep novelty claims bounded by `docs/novelty-review.md`, including the Wang–Liao, human-norm, DIAL, LaST0, and CATS Net precedents.
21. Freeze the Phase I gate configuration before the treatment matrix and version every later change.
22. Never allow abstract or metaphorical outcomes to determine the Phase I gate status.
23. Require a Phase I compatibility calibration whenever the Phase II model stack materially differs from the gated Phase I stack.
24. Preserve Phase I datasets, checkpoints, item-level results, failed runs, reports, and approvals as permanent research artifacts.
25. Phase II scientific commands must refuse to run without a valid, hash-matched Phase I `PASS` approval.

---

## 20. Milestones

### Milestone 0 — repository foundation

Deliver package scaffold, dependency lock, validated config system, Typer CLI, logging, run/budget manifests, CPU-only CI, `AGENTS.md`, and a tiny random model fixture.

Acceptance:

- tests, lint, and static typing pass offline;
- `unfrozen smoke` creates a complete toy run with resource accounting.

### Milestone 1 — SchemaWorld Core

Deliver deterministic CONTAINMENT and SUPPORT state transitions, matched counterfactuals, relation derivation, inspection renderer, Parquet manifests, and hashes.

### Milestone 2 — frozen core benchmark

Deliver controlled abstract transfer, novel metaphor entailment, literal reasoning, option reversal, leakage audit, and immutable benchmark versioning before any treatment run.

### Milestone 3 — Phase I adaptation pipeline

Deliver text, causal sensor, passive, shuffled, LoRA, replay, retention, checkpoint/resume, and likelihood evaluation.

### Milestone 4 — Phase I calibration matrix and mandatory gate

Run two schemas, P1-C0 through P1-C4, and at least three seeds. Freeze the gate configuration before treatment runs. Produce the complete L0–L4 transfer profile, all item-level results, a scientific calibration report, and the formal Phase I gate artifacts.

Milestone 4 acceptance requires:

1. reproducible L1 held-out literal causal learning;
2. a preregistered `sensor_causal > sensor_shuffled` contingency effect;
3. L2 generalisation to unseen templates and configurations;
4. language retention within the frozen tolerance;
5. complete leakage, parity, budget, hash, and provenance checks;
6. inclusion of every completed, failed, and excluded seed under the declared rules;
7. a valid `PASS` approval whose hashes match the matrix, gate config, model stack, and Git commit.

A text-oracle advantage, absence of a causal–passive difference, or null L3/L4 transfer does not prevent a Phase I pass. Phase I remains a permanent scientific result, not merely a discarded preliminary step.

An `INCONCLUSIVE` or `NO_GO` result blocks Phase II scientific runs. Engineering-only fixtures may continue but must not be reported as Phase II evidence.

### Milestone 5 — CausalSchemaLab and latent world model

Requires a valid Phase I `PASS` approval. Deliver hidden properties, partial observations, curriculum levels, structured actions, replayable active trajectories, multimodal projector, future-latent prediction, and uncertainty estimates.

### Milestone 6 — language workspace, bridge, and stack compatibility

Deliver structured prediction/hypothesis protocol, hypothesis ledger, experiment planner, concept bridge, grounded consolidation, language audit, closed-book isolation, and budget ledger.

Before Milestone 7, fingerprint the exact Phase II model stack and run the reduced Phase I compatibility calibration if it differs materially from the original gated stack. Phase II pilot collection and training remain blocked until the compatibility report is `PASS`.

### Milestone 7 — Phase II pilot

Use one rich schema curriculum and the minimum informative conditions:

```text
no_adaptation
text_interactive_oracle
offline_sensor_raw
offline_sensor_language
active_sensor_raw
active_sensor_language
yoked_passive_language
active_sensor_language_shuffled
human_sensorimotor_norms
```

Run at least three seeds, evaluate an untrained schema, and produce learning curves and closed/open-book reports.

### Milestone 8 — Phase II confirmatory study

Deliver both schemas, at least five seeds for primary conditions, human-validated rich benchmark, frozen curriculum, preregistered co-primary contrasts, a second model family, compute/budget robustness, and optional lossless-text and sham-compute controls.

### Milestone 9 — mechanistic integration analysis

Deliver bridge tracing, cross-modal probes, prediction-error analyses, activation patching, ledger/adapter/bridge ablations, and layerwise figures.

### Milestone 10 — Phase III colony

Proceed only after written review. Deliver sensor and language specialists, conceptual translator, communication controls, and monolith-versus-colony budget matching.

---

## 21. `AGENTS.md` requirements

Codex must be instructed to:

- read `CODEX_SPEC.md`, `docs/scientific-design.md`, and `docs/implementation-plan.md` before changing code;
- implement one milestone at a time;
- write or update tests before declaring a milestone complete;
- preserve the distinction between Phase I mandatory calibration/gate and Phase II complementarity;
- ensure abstract and metaphorical Phase I scores never determine gate status;
- block Phase II scientific commands unless the Phase I approval and any required model-stack compatibility approval are valid;
- never replace active/yoked, raw/language, causal/shuffled, or closed/open-book controls with simpler proxies without explicit approval;
- keep model, environment, curriculum, condition, budget, and schema choices configuration-driven;
- use no network calls in unit tests;
- never hard-code secrets or model tokens;
- preserve frozen benchmark and curriculum versions;
- account separately for external language, self-generated language, sensor data, environment steps, and compute;
- stop and report if a requested change invalidates condition comparability;
- record unresolved scientific decisions in `docs/open-questions.md` rather than guessing;
- make small reviewable changes and run lint, type checks, and tests after each task.

---

## 22. Initial Codex kickoff prompt

Paste the following into Codex from an empty repository containing this specification:

```text
You are the lead research-software engineer for the repository described in CODEX_SPEC.md.

Read CODEX_SPEC.md in full. Then:

1. Create AGENTS.md, docs/scientific-design.md, docs/implementation-plan.md, docs/budget-accounting.md, docs/phase-gate-protocol.md, and docs/open-questions.md.
2. In docs/implementation-plan.md, translate Milestones 0–4 into small dependency-ordered work packages. Treat Milestones 5–10 as later roadmap items only.
3. Explicitly describe the distinction between Phase I mandatory causal calibration/gate, Phase II language-scaffolded active grounding, and Phase III colony propagation.
4. Specify that Phase I L3/L4 abstract and metaphorical results are non-gating, while literal learning, contingency, held-out transfer, retention, leakage, reproducibility, and provenance are hard-gate criteria.
5. Implement Milestone 0 only. Do not implement SchemaWorld, active agents, or model training except for the minimal tiny-model fixture required by the smoke test.
6. Use Python 3.11, uv, a src layout, Typer, Pydantic, pytest, Ruff, and static typing.
7. Unit tests and the smoke command must run without network access, external model downloads, CUDA, or secrets.
8. Ensure every toy run has a resolved config, complete provenance manifest, resource-budget ledger, and placeholder gate metadata.
9. Run tests, lint, and type checks; fix failures.
10. Review your diff against CODEX_SPEC.md and state every deviation explicitly.

Do not silently broaden or narrow the scientific claims. Do not proceed to Milestone 1 until Milestone 0 acceptance criteria pass.
```

Use a separate prompt for each later milestone. Do not ask Codex to build the entire research platform in one undifferentiated pass.

---

## 23. Go/no-go decision rules

### Phase I decision

Phase I is a mandatory gate. Proceed to Phase II scientific work only when the generated gate report and approval have status `PASS` and their hashes match the frozen matrix, gate configuration, model-stack fingerprint, benchmark, and Git commit.

A Phase I `PASS` requires:

- reproducible held-out literal causal learning;
- reliable separation of causal and shuffled action–outcome experience;
- generalisation beyond memorised templates and episode identities;
- acceptable language retention under the frozen tolerance;
- passed leakage, parity, budget, benchmark, checkpoint, and provenance audits;
- all required seeds and failures accounted for;
- and, when the Phase II stack differs, a separate compatibility-calibration `PASS` on that exact stack.

The following must not block a pass:

- `text_oracle` outperforming the sensor condition;
- no significant difference between causal and passive observation;
- no abstract transfer at L3;
- no metaphorical transfer at L4.

Those outcomes determine the scientific interpretation and Phase II targets, not whether the Phase I pipeline worked.

A Phase I text advantage is a reason to proceed with the Phase II complementarity design, not a reason to abandon it. A pattern of L1/L2 success but L3/L4 failure is especially informative because it identifies conceptual compartmentalisation as the phenomenon Phase II must attempt to bridge.

An `INCONCLUSIVE` decision requires more preregistered evidence or a full rerun after a documented repair. A `NO_GO` decision requires diagnosis or redesign. Neither permits Phase II scientific pilot runs.

### Proceed from Phase II to Phase III when one of the following holds

1. `active_sensor_language` shows reproducible closed-book schema-specific transfer beyond at least one strong unimodal control and the mechanism appears to involve language-active representations; or
2. Phase II establishes a stable compartmentalisation result in which physical learning succeeds but fails to penetrate language, giving the colony a precise communication problem to solve; or
3. active/yoked results show that experiment selection or communication architecture, rather than raw modality, is the central bottleneck.

Do not proceed to a colony merely because it is architecturally attractive.

---

## 24. Revision 4 implementation consequences

Revision 4 changes implementation behaviour in four concrete ways:

1. Phase I produces an auditable gate decision in addition to ordinary metrics.
2. Phase II scientific commands are technically blocked without a current `PASS` approval.
3. Phase I abstract and metaphorical scores are reported but cannot influence the gate algorithm.
4. A materially changed Phase II model stack must pass a reduced Phase I compatibility calibration before rich-world experiments begin.

These safeguards preserve the clean Phase I experiment while allowing its most theoretically interesting null result—literal learning without distant language transfer—to motivate rather than terminate Phase II.

---

## 25. Expected scientific outcomes

All of the following are informative:

- **Active sensor + language exceeds language-only and sensor-only:** strong evidence for complementarity and conceptual permeability.
- **Offline sensor + language exceeds offline sensor raw:** language successfully scaffolds consolidation even without an agency advantage.
- **Active exceeds yoked passive:** choosing interventions based on uncertainty contributes beyond receiving the same data.
- **Causal exceeds shuffled:** valid action–outcome structure matters.
- **Text interactive remains best, but joint learning approaches it with fewer external language tokens:** language is an efficient interface, while experience reduces supervision requirements.
- **Lossless text log is best:** unsurprising information-ceiling result; interpret through token and compute cost rather than as a refutation of embodiment.
- **Human sensorimotor norms outperform direct experience:** explicit semantic supervision is a more direct route under the tested budget; analyse whether it generalises across tasks and schemas.
- **Direct experience outperforms norms on counterfactual or novel-physics transfer:** causal interaction supplies structure not captured by static ratings.
- **Literal and near transfer improve without metaphor:** the model learns physical dynamics but the learning remains compartmentalised.
- **Open-book improves while closed-book does not:** the system can retrieve grounded knowledge but has not reorganised language-active weights.
- **Broad gains across trained and untrained schemas:** likely generic adaptation, extra computation, or benchmark artefact.
- **All conditions remain near baseline:** the intervention, model scale, objective, bridge, or benchmark may be inadequate; the result does not by itself prove that experiential integration is impossible.

The repository must report these interpretations prospectively so that only one preferred result is not treated as scientific success.

---

