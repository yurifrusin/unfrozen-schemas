"""Independent M2.2 literal-source and composite-candidate validation."""

from __future__ import annotations

import re
import unicodedata
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from itertools import pairwise
from pathlib import Path
from typing import Any

from unfrozen_schemas.config import sha256_file
from unfrozen_schemas.envs.schema_world.dynamics import transition
from unfrozen_schemas.envs.schema_world.relations import derive_relations
from unfrozen_schemas.envs.schema_world.serialization import canonical_hash, primary_observation
from unfrozen_schemas.evaluation.benchmark_hashing import canonical_logical_bytes
from unfrozen_schemas.evaluation.benchmark_models import SourceItemRecord, SourceManifest
from unfrozen_schemas.evaluation.benchmark_persistence import (
    read_canonical_model,
    read_jsonl_models,
    verify_artifact_records,
)
from unfrozen_schemas.evaluation.benchmark_validation import (
    load_source_directory,
    validate_reverse_pairs,
)
from unfrozen_schemas.evaluation.literal_hashing import (
    item_binding_bundle_hash,
    item_binding_hash,
    lexical_audit_hash,
    operation_hash,
    partition_plan_hash,
    source_bundle_hash,
    split_audit_hash,
    template_hash,
    template_registry_hash,
    validation_report_hash,
    witness_bundle_hash,
    witness_hash,
)
from unfrozen_schemas.evaluation.literal_models import (
    LiteralItemBinding,
    LiteralItemBindingBundle,
    LiteralLexicalAudit,
    LiteralLexicalFinding,
    LiteralOperationRecord,
    LiteralPartitionPlan,
    LiteralPendingOwnerReview,
    LiteralSourceBundleManifest,
    LiteralSplitAudit,
    LiteralTemplate,
    LiteralTemplateRegistryManifest,
    LiteralTransferLevel,
    LiteralValidationReport,
    LiteralWitnessBundle,
    LiteralWitnessRecord,
)

LITERAL_DIRECTORY = ".literal"
PARTITION_PLAN_FILE = "partition_plan.json"
TEMPLATE_REGISTRY_FILE = "template_registry.json"
ITEM_BINDINGS_FILE = "item_bindings.json"
WITNESS_BUNDLE_FILE = "witness_bundle.json"
LEXICAL_AUDIT_FILE = "lexical_audit.json"
SPLIT_AUDIT_FILE = "split_audit.json"
VALIDATION_REPORT_FILE = "literal_validation_report.json"
SOURCE_BUNDLE_FILE = "literal_source_bundle.json"
GENERATION_OPERATION_FILE = "generation_operation_record.json"
COMPOSITE_CANDIDATE_FILE = "literal_candidate_manifest.json"
CANDIDATE_VALIDATION_REPORT_FILE = "candidate_literal_validation_report.json"
CANDIDATE_VALIDATION_OPERATION_FILE = "candidate_validation_operation_record.json"
REVIEW_OPERATION_FILE = "review_operation_record.json"

_RAW_VISIBLE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("raw-entity-id", re.compile(r"\b(?:e|b|o|t)\d{4}\b", re.IGNORECASE)),
    ("raw-sha256", re.compile(r"\b[a-f0-9]{64}\b", re.IGNORECASE)),
    ("raw-coordinate", re.compile(r"\b(?:10000|[1-9]\d{3})\b")),
    (
        "machine-schema-label",
        re.compile(r"\b(?:CONTAINMENT|SUPPORT|load_bearing|transition_trace)\b"),
    ),
    (
        "nonliteral-target-vocabulary",
        re.compile(
            r"\b(?:metaphor(?:ical)?|abstract schema|social relation|argument structure)\b", re.I
        ),
    ),
    (
        "private-answer-code",
        re.compile(r"\b(?:movement-(?:succeeds|blocked)|object-(?:falls|stays))\b", re.I),
    ),
)


@dataclass(frozen=True, slots=True)
class LoadedLiteralSource:
    root: Path
    source_manifest: SourceManifest
    items: tuple[SourceItemRecord, ...]
    partition_plan: LiteralPartitionPlan
    template_registry: LiteralTemplateRegistryManifest
    item_bindings: LiteralItemBindingBundle
    witness_bundle: LiteralWitnessBundle
    lexical_audit: LiteralLexicalAudit
    split_audit: LiteralSplitAudit
    validation_report: LiteralValidationReport
    source_bundle: LiteralSourceBundleManifest


def _normalise_text(value: str) -> str:
    normalised = unicodedata.normalize("NFC", value.replace("\r\n", "\n").replace("\r", "\n"))
    return " ".join(normalised.split()).casefold()


def _tokens(value: str) -> tuple[str, ...]:
    return tuple(re.findall(r"[a-z]+(?:-[a-z]+)?", _normalise_text(value)))


def _count(values: Iterable[str]) -> dict[str, int]:
    return dict(sorted(Counter(values).items()))


def _answer_counts(bindings: Sequence[LiteralItemBinding], key: str) -> dict[str, dict[str, int]]:
    grouped: dict[str, Counter[str]] = defaultdict(Counter)
    for binding in bindings:
        grouped[str(getattr(binding, key))][binding.stable_correct_option_id] += 1
    return {
        group: dict(sorted(answer_counts.items()))
        for group, answer_counts in sorted(grouped.items())
    }


def _displayed_text(item: SourceItemRecord) -> str:
    content = item.model_visible
    return "\n".join(
        (
            content.prompt,
            content.instructions or "",
            *(option.text for option in content.ordered_options),
        )
    )


def build_lexical_audit(
    *,
    candidate_version: str,
    items: Sequence[SourceItemRecord],
    bindings: Sequence[LiteralItemBinding],
) -> LiteralLexicalAudit:
    """Derive the deterministic, source-local M2.2 cue audit."""

    item_by_id = {item.item_id: item for item in items}
    findings: list[LiteralLexicalFinding] = []
    answer_position_counts: Counter[str] = Counter()
    prompt_by_group: dict[str, str] = {}
    token_outcomes: dict[tuple[str, str], set[str]] = defaultdict(set)
    for binding in bindings:
        left = item_by_id[binding.item_ids[0]]
        right = item_by_id[binding.item_ids[1]]
        if left.model_visible.prompt != right.model_visible.prompt:
            raise ValueError(f"Reverse group {binding.semantic_group_id} changes its prompt")
        prompt_by_group[binding.semantic_group_id] = _normalise_text(left.model_visible.prompt)
        for item in (left, right):
            permutation = item.model_visible.option_permutation
            answer_position_counts[
                str(permutation.index(binding.stable_correct_option_id) + 1)
            ] += 1
            visible = _displayed_text(item)
            if visible != unicodedata.normalize(
                "NFC", visible.replace("\r\n", "\n").replace("\r", "\n")
            ):
                raise ValueError(f"Item {item.item_id} is not Unicode/line-ending normalised")
            for kind, pattern in _RAW_VISIBLE_PATTERNS:
                match = pattern.search(visible)
                if match:
                    findings.append(
                        LiteralLexicalFinding(
                            finding_kind=kind,
                            scope=item.item_id,
                            value=match.group(0),
                            disposition="fail",
                        )
                    )
            normalised_prompt = _normalise_text(item.model_visible.prompt)
            if any(
                _normalise_text(option.text) in normalised_prompt
                for option in item.model_visible.ordered_options
            ):
                findings.append(
                    LiteralLexicalFinding(
                        finding_kind="prompt-states-option-consequence",
                        scope=item.item_id,
                        value="option text appears in prompt",
                        disposition="fail",
                    )
                )
            option_lengths = [
                len(_tokens(option.text)) for option in item.model_visible.ordered_options
            ]
            if max(option_lengths) - min(option_lengths) > 4:
                findings.append(
                    LiteralLexicalFinding(
                        finding_kind="option-length-imbalance",
                        scope=item.item_id,
                        value=str(option_lengths),
                        disposition="fail",
                    )
                )
        prompt_tokens = _tokens(left.model_visible.prompt)
        ngrams = set(prompt_tokens)
        ngrams.update(f"{first} {second}" for first, second in pairwise(prompt_tokens))
        for token in ngrams:
            token_outcomes[(binding.task_family.value, token)].add(binding.stable_correct_option_id)

    duplicate_groups: list[tuple[str, str]] = []
    group_ids = sorted(prompt_by_group)
    for index, left_id in enumerate(group_ids):
        for right_id in group_ids[index + 1 :]:
            if prompt_by_group[left_id] == prompt_by_group[right_id]:
                duplicate_groups.append((left_id, right_id))

    near_pairs: list[tuple[str, str]] = []
    token_sets = {group: set(_tokens(prompt)) for group, prompt in prompt_by_group.items()}
    for index, left_id in enumerate(group_ids):
        for right_id in group_ids[index + 1 :]:
            left_tokens = token_sets[left_id]
            right_tokens = token_sets[right_id]
            union = left_tokens | right_tokens
            if union and len(left_tokens & right_tokens) / len(union) >= 0.92:
                near_pairs.append((left_id, right_id))

    for (family, token), outcomes in sorted(token_outcomes.items()):
        if len(outcomes) == 1:
            findings.append(
                LiteralLexicalFinding(
                    finding_kind="perfect-family-token-association",
                    scope=family,
                    value=token,
                    disposition="reviewed-causal",
                )
            )

    template_counts = _answer_counts(bindings, "prompt_template_id")
    action_counts = _answer_counts(bindings, "action_word")
    mechanism_counts = _answer_counts(bindings, "source_mechanism_family")
    for label, groups in (
        ("template", template_counts),
        ("action-word", action_counts),
        ("source-mechanism", mechanism_counts),
    ):
        for group, counts in groups.items():
            if len(counts) < 2:
                findings.append(
                    LiteralLexicalFinding(
                        finding_kind=f"{label}-single-answer-class",
                        scope=group,
                        value=next(iter(counts)),
                        disposition="fail",
                    )
                )
    if duplicate_groups:
        findings.append(
            LiteralLexicalFinding(
                finding_kind="exact-prompt-duplicate",
                scope="semantic-groups",
                value=str(len(duplicate_groups)),
                disposition="fail",
            )
        )
    failures = [finding for finding in findings if finding.disposition == "fail"]
    if failures:
        first = failures[0]
        raise ValueError(
            f"Literal lexical audit failed: {first.finding_kind} at {first.scope}: {first.value}"
        )
    provisional = LiteralLexicalAudit(
        candidate_version=candidate_version,
        semantic_group_count=len(bindings),
        source_item_count=len(items),
        answer_position_counts=dict(sorted(answer_position_counts.items())),
        template_answer_counts=template_counts,
        action_word_answer_counts=action_counts,
        source_mechanism_answer_counts=mechanism_counts,
        exact_duplicate_group_count=len(duplicate_groups),
        near_duplicate_group_pairs=tuple(near_pairs),
        findings=tuple(findings),
        lexical_audit_sha256="0" * 64,
    )
    return provisional.model_copy(update={"lexical_audit_sha256": lexical_audit_hash(provisional)})


def build_split_audit(
    *,
    candidate_version: str,
    items: Sequence[SourceItemRecord],
    bindings: Sequence[LiteralItemBinding],
    witnesses: Sequence[LiteralWitnessRecord],
) -> LiteralSplitAudit:
    prompt_counts = Counter(_normalise_text(item.model_visible.prompt) for item in items[::2])
    duplicates = sum(count - 1 for count in prompt_counts.values() if count > 1)
    l2_dimensions = {
        binding.semantic_group_id: binding.structural_novelty_dimensions
        for binding in bindings
        if binding.transfer_level is LiteralTransferLevel.L2
    }
    provisional = LiteralSplitAudit(
        candidate_version=candidate_version,
        semantic_group_count=len(bindings),
        l1_group_count=sum(
            binding.transfer_level is LiteralTransferLevel.L1 for binding in bindings
        ),
        l2_group_count=sum(
            binding.transfer_level is LiteralTransferLevel.L2 for binding in bindings
        ),
        unique_state_hash_count=len({item.initial_state_hash for item in witnesses}),
        unique_action_hash_count=len({item.action_sequence_hash for item in witnesses}),
        unique_witness_hash_count=len({item.witness_sha256 for item in witnesses}),
        l2_structural_novelty_dimensions=dict(sorted(l2_dimensions.items())),
        exact_prompt_duplicate_count=duplicates,
        split_audit_sha256="0" * 64,
    )
    return provisional.model_copy(update={"split_audit_sha256": split_audit_hash(provisional)})


def _replay_witness(witness: LiteralWitnessRecord) -> None:
    for (
        prefix,
        initial,
        actions,
        expected_final,
        expected_traces,
        expected_hashes,
        expected_relations,
    ) in (
        (
            "actual",
            witness.initial_privileged_state,
            witness.actual_actions,
            witness.actual_final_state,
            witness.actual_transition_traces,
            witness.actual_transition_hashes,
            witness.actual_relations,
        ),
        (
            "counterfactual",
            witness.counterfactual_initial_privileged_state,
            witness.counterfactual_actions,
            witness.counterfactual_final_state,
            witness.counterfactual_transition_traces,
            witness.counterfactual_transition_hashes,
            witness.counterfactual_relations,
        ),
    ):
        state = initial
        traces = []
        hashes = []
        relations: tuple[Any, ...] = ()
        for action in actions:
            result = transition(state, action)
            state = result.state
            traces.append(result.trace)
            hashes.append(result.transition_hash)
            relations = derive_relations(state, result.trace)
        if state != expected_final:
            raise ValueError(f"{prefix} final state mismatch for {witness.semantic_group_id}")
        if tuple(traces) != expected_traces or tuple(hashes) != expected_hashes:
            raise ValueError(f"{prefix} transition mismatch for {witness.semantic_group_id}")
        if tuple(relations) != expected_relations:
            raise ValueError(f"{prefix} relation mismatch for {witness.semantic_group_id}")


def verify_witness(witness: LiteralWitnessRecord) -> None:
    """Reconstruct all stored witness claims without trusting stored answers."""

    from unfrozen_schemas.evaluation.literal_scenarios import (
        correct_option_id_for_outcome,
        derive_outcome_code,
        difference_paths,
    )

    if canonical_hash(witness.initial_privileged_state) != witness.initial_state_hash:
        raise ValueError(f"Initial-state hash mismatch: {witness.semantic_group_id}")
    if (
        canonical_hash(witness.counterfactual_initial_privileged_state)
        != witness.counterfactual_initial_state_hash
    ):
        raise ValueError(f"Counterfactual initial-state hash mismatch: {witness.semantic_group_id}")
    if (
        canonical_hash(primary_observation(witness.initial_privileged_state))
        != witness.initial_observation_hash
    ):
        raise ValueError(f"Initial-observation hash mismatch: {witness.semantic_group_id}")
    if (
        canonical_hash(primary_observation(witness.counterfactual_initial_privileged_state))
        != witness.counterfactual_initial_observation_hash
    ):
        raise ValueError(f"Counterfactual observation hash mismatch: {witness.semantic_group_id}")
    if canonical_hash(witness.actual_actions) != witness.action_sequence_hash:
        raise ValueError(f"Action hash mismatch: {witness.semantic_group_id}")
    if (
        canonical_hash(witness.counterfactual_actions)
        != witness.counterfactual_action_sequence_hash
    ):
        raise ValueError(f"Counterfactual action hash mismatch: {witness.semantic_group_id}")
    initial_differences = difference_paths(
        witness.initial_privileged_state,
        witness.counterfactual_initial_privileged_state,
    )
    action_differences = difference_paths(witness.actual_actions, witness.counterfactual_actions)
    if initial_differences != witness.declared_initial_difference_paths:
        raise ValueError(f"Undeclared initial-state difference: {witness.semantic_group_id}")
    if action_differences != witness.declared_action_difference_paths:
        raise ValueError(f"Undeclared action difference: {witness.semantic_group_id}")
    if bool(initial_differences) == bool(action_differences):
        raise ValueError(
            f"Counterfactual must change exactly one state-or-action dimension: "
            f"{witness.semantic_group_id}"
        )
    for field in witness.declared_non_target_equality_fields:
        if field == "initial_state":
            equal = (
                witness.initial_privileged_state == witness.counterfactual_initial_privileged_state
            )
        elif field == "transition_horizon":
            equal = len(witness.actual_actions) == len(witness.counterfactual_actions)
        elif hasattr(witness.initial_privileged_state, field):
            equal = getattr(witness.initial_privileged_state, field) == getattr(
                witness.counterfactual_initial_privileged_state, field
            )
        else:
            raise ValueError(
                f"Unknown counterfactual parity declaration {field!r}: {witness.semantic_group_id}"
            )
        if not equal:
            raise ValueError(
                f"Counterfactual parity declaration is false for {field!r}: "
                f"{witness.semantic_group_id}"
            )
    _replay_witness(witness)
    actual = derive_outcome_code(
        witness.schema_identity,
        witness.initial_privileged_state,
        witness.actual_final_state,
    )
    counterfactual = derive_outcome_code(
        witness.schema_identity,
        witness.counterfactual_initial_privileged_state,
        witness.counterfactual_final_state,
    )
    if (
        actual != witness.actual_outcome_code
        or counterfactual != witness.counterfactual_outcome_code
    ):
        raise ValueError(f"Outcome-code mismatch: {witness.semantic_group_id}")
    if actual == counterfactual:
        raise ValueError(f"Counterfactual outcome is unchanged: {witness.semantic_group_id}")
    if correct_option_id_for_outcome(actual) != witness.stable_correct_option_id:
        raise ValueError(f"Correct-option derivation mismatch: {witness.semantic_group_id}")
    if witness_hash(witness) != witness.witness_sha256:
        raise ValueError(f"Witness logical hash mismatch: {witness.semantic_group_id}")


def _literal_path(root: Path, name: str) -> Path:
    path = root / LITERAL_DIRECTORY / name
    if not path.is_file():
        raise ValueError(f"Literal source is missing {LITERAL_DIRECTORY}/{name}")
    return path


def load_literal_source(source_root: Path) -> LoadedLiteralSource:
    root = source_root.resolve()
    source_manifest = read_canonical_model(root / "source_manifest.json", SourceManifest)
    items = read_jsonl_models(
        root / source_manifest.items_file, SourceItemRecord, require_canonical=True
    )
    return LoadedLiteralSource(
        root=root,
        source_manifest=source_manifest,
        items=items,
        partition_plan=read_canonical_model(
            _literal_path(root, PARTITION_PLAN_FILE), LiteralPartitionPlan
        ),
        template_registry=read_canonical_model(
            _literal_path(root, TEMPLATE_REGISTRY_FILE), LiteralTemplateRegistryManifest
        ),
        item_bindings=read_canonical_model(
            _literal_path(root, ITEM_BINDINGS_FILE), LiteralItemBindingBundle
        ),
        witness_bundle=read_canonical_model(
            _literal_path(root, WITNESS_BUNDLE_FILE), LiteralWitnessBundle
        ),
        lexical_audit=read_canonical_model(
            _literal_path(root, LEXICAL_AUDIT_FILE), LiteralLexicalAudit
        ),
        split_audit=read_canonical_model(_literal_path(root, SPLIT_AUDIT_FILE), LiteralSplitAudit),
        validation_report=read_canonical_model(
            _literal_path(root, VALIDATION_REPORT_FILE), LiteralValidationReport
        ),
        source_bundle=read_canonical_model(
            _literal_path(root, SOURCE_BUNDLE_FILE), LiteralSourceBundleManifest
        ),
    )


def _verify_template_registry(
    registry: LiteralTemplateRegistryManifest, templates: Sequence[LiteralTemplate]
) -> None:
    expected = {template.template_id: template_hash(template) for template in templates}
    if registry.template_content_hashes != dict(sorted(expected.items())):
        raise ValueError("Literal template registry content hashes do not reconstruct")
    if template_registry_hash(registry) != registry.template_registry_sha256:
        raise ValueError("Literal template registry hash does not reconstruct")


def validate_loaded_literal_source(
    loaded: LoadedLiteralSource,
    *,
    templates: Sequence[LiteralTemplate] | None = None,
) -> LiteralValidationReport:
    manifest = loaded.source_manifest
    version = manifest.benchmark_version
    purpose = manifest.purpose.value
    if version != loaded.partition_plan.candidate_version:
        raise ValueError("M2.1 and M2.2 source versions differ")
    load_source_directory(loaded.root, benchmark_version=version, purpose=manifest.purpose)
    validate_reverse_pairs(loaded.items)
    bindings = loaded.item_bindings.bindings
    witnesses = loaded.witness_bundle.witnesses
    if len(loaded.items) != 2 * len(bindings) or len(bindings) != len(witnesses):
        raise ValueError("Literal source requires exactly two items and one witness per group")
    if tuple(sorted(binding.semantic_group_id for binding in bindings)) != tuple(
        binding.semantic_group_id for binding in bindings
    ):
        raise ValueError("Literal item bindings are not canonically ordered")
    if tuple(sorted(witness.semantic_group_id for witness in witnesses)) != tuple(
        witness.semantic_group_id for witness in witnesses
    ):
        raise ValueError("Literal witnesses are not canonically ordered")
    witness_by_group = {item.semantic_group_id: item for item in witnesses}
    items_by_id = {item.item_id: item for item in loaded.items}
    for binding in bindings:
        if item_binding_hash(binding) != binding.item_binding_sha256:
            raise ValueError(f"Item-binding hash mismatch: {binding.semantic_group_id}")
        witness = witness_by_group.get(binding.semantic_group_id)
        if witness is None or witness.witness_sha256 != binding.witness_sha256:
            raise ValueError(f"Item binding has no matching witness: {binding.semantic_group_id}")
        verify_witness(witness)
        if (
            binding.item_ids != witness.item_ids
            or binding.stable_correct_option_id != witness.stable_correct_option_id
        ):
            raise ValueError(f"Witness and item binding disagree: {binding.semantic_group_id}")
        pair = tuple(items_by_id[item_id] for item_id in binding.item_ids)
        if any(
            item.private_answer.correct_option_id != binding.stable_correct_option_id
            for item in pair
        ):
            raise ValueError(
                f"Private answer disagrees with simulator: {binding.semantic_group_id}"
            )
        if any(
            item.private_answer.simulator_verification_reference
            != f"literal-witness-sha256:{witness.witness_sha256}"
            for item in pair
        ):
            raise ValueError(
                f"Simulator verification reference mismatch: {binding.semantic_group_id}"
            )
        left, right = pair
        if right.model_visible.option_permutation != tuple(
            reversed(left.model_visible.option_permutation)
        ):
            raise ValueError(f"Reverse option order mismatch: {binding.semantic_group_id}")

    if partition_plan_hash(loaded.partition_plan) != loaded.partition_plan.partition_plan_sha256:
        raise ValueError("Literal partition-plan hash does not reconstruct")
    if (
        item_binding_bundle_hash(loaded.item_bindings)
        != loaded.item_bindings.item_binding_bundle_sha256
    ):
        raise ValueError("Literal item-binding bundle hash does not reconstruct")
    if witness_bundle_hash(loaded.witness_bundle) != loaded.witness_bundle.witness_bundle_sha256:
        raise ValueError("Literal witness-bundle hash does not reconstruct")
    if templates is not None:
        _verify_template_registry(loaded.template_registry, templates)
    elif (
        template_registry_hash(loaded.template_registry)
        != loaded.template_registry.template_registry_sha256
    ):
        raise ValueError("Literal template-registry hash does not reconstruct")
    rebuilt_lexical = build_lexical_audit(
        candidate_version=version,
        items=loaded.items,
        bindings=bindings,
    )
    if rebuilt_lexical != loaded.lexical_audit:
        raise ValueError("Literal lexical audit does not reconstruct")
    rebuilt_split = build_split_audit(
        candidate_version=version,
        items=loaded.items,
        bindings=bindings,
        witnesses=witnesses,
    )
    if rebuilt_split != loaded.split_audit:
        raise ValueError("Literal split audit does not reconstruct")
    schema_counts = _count(binding.schema_identity.value for binding in bindings)
    level_counts = _count(binding.transfer_level.value for binding in bindings)
    family_counts = _count(binding.task_family.value for binding in bindings)
    mechanism_counts = _count(binding.source_mechanism_family for binding in bindings)
    provisional = LiteralValidationReport(
        candidate_version=version,
        purpose=purpose,
        semantic_group_count=len(bindings),
        source_item_count=len(loaded.items),
        schema_counts=schema_counts,
        level_counts=level_counts,
        family_counts=family_counts,
        mechanism_counts=mechanism_counts,
        m2_1_lifecycle_validation="not_evaluated_source_stage",
        human_validation_status=(
            "not_applicable_engineering" if manifest.engineering_only else "not_started"
        ),
        rights_status=("not_applicable_engineering" if manifest.engineering_only else "unresolved"),
        ethics_governance_status=(
            "not_applicable_engineering" if manifest.engineering_only else "unresolved"
        ),
        literal_validation_report_sha256="0" * 64,
    )
    expected = provisional.model_copy(
        update={"literal_validation_report_sha256": validation_report_hash(provisional)}
    )
    if expected != loaded.validation_report:
        raise ValueError("Literal validation report does not reconstruct")
    source_bundle = loaded.source_bundle
    expected_artifact_paths = {
        "source_manifest.json",
        "items.jsonl",
        f"{LITERAL_DIRECTORY}/{PARTITION_PLAN_FILE}",
        f"{LITERAL_DIRECTORY}/{TEMPLATE_REGISTRY_FILE}",
        f"{LITERAL_DIRECTORY}/{ITEM_BINDINGS_FILE}",
        f"{LITERAL_DIRECTORY}/{WITNESS_BUNDLE_FILE}",
        f"{LITERAL_DIRECTORY}/{LEXICAL_AUDIT_FILE}",
        f"{LITERAL_DIRECTORY}/{SPLIT_AUDIT_FILE}",
        f"{LITERAL_DIRECTORY}/{VALIDATION_REPORT_FILE}",
    }
    verify_artifact_records(
        loaded.root,
        source_bundle.artifacts,
        expected_paths=expected_artifact_paths,
    )
    operation = read_canonical_model(
        _literal_path(loaded.root, GENERATION_OPERATION_FILE),
        LiteralOperationRecord,
    )
    if operation_hash(operation) != operation.operation_sha256:
        raise ValueError("Literal generation-operation hash does not reconstruct")
    if operation.operation_sha256 != source_bundle.generation_operation_sha256:
        raise ValueError("Literal source bundle binds a different generation operation")
    if operation.artifacts != source_bundle.artifacts:
        raise ValueError("Literal generation operation and source artifact records differ")
    expected_source_hashes = {
        "m2_1_source_manifest_sha256": sha256_file(loaded.root / "source_manifest.json"),
        "m2_1_items_file_sha256": sha256_file(loaded.root / "items.jsonl"),
        "partition_plan_sha256": loaded.partition_plan.partition_plan_sha256,
        "template_registry_sha256": loaded.template_registry.template_registry_sha256,
        "item_binding_bundle_sha256": loaded.item_bindings.item_binding_bundle_sha256,
        "witness_bundle_sha256": loaded.witness_bundle.witness_bundle_sha256,
        "split_audit_sha256": loaded.split_audit.split_audit_sha256,
        "lexical_audit_sha256": loaded.lexical_audit.lexical_audit_sha256,
        "literal_validation_report_sha256": (
            loaded.validation_report.literal_validation_report_sha256
        ),
    }
    for field, expected_hash in expected_source_hashes.items():
        if getattr(source_bundle, field) != expected_hash:
            raise ValueError(f"Literal source bundle has a stale {field}")
    if source_bundle_hash(source_bundle) != source_bundle.literal_source_bundle_sha256:
        raise ValueError("Literal source-bundle hash does not reconstruct")
    return expected


def validate_literal_source(source_root: Path) -> LoadedLiteralSource:
    loaded = load_literal_source(source_root)
    validate_loaded_literal_source(loaded)
    return loaded


def review_content_records(
    loaded: LoadedLiteralSource,
) -> tuple[dict[str, object], ...]:
    """Return private logical review records without container or render identity."""

    items = {item.item_id: item for item in loaded.items}
    witnesses = {item.semantic_group_id: item for item in loaded.witness_bundle.witnesses}
    records: list[dict[str, object]] = []
    for binding in loaded.item_bindings.bindings:
        witness = witnesses[binding.semantic_group_id]
        left, right = (items[item_id] for item_id in binding.item_ids)
        records.append(
            {
                "path": f"item_review/{binding.semantic_group_id}",
                "semantic_group_id": binding.semantic_group_id,
                "item_ids": binding.item_ids,
                "schema_identity": binding.schema_identity,
                "transfer_level": binding.transfer_level,
                "task_family": binding.task_family,
                "prompt": left.model_visible.prompt,
                "instructions": left.model_visible.instructions,
                "option_forms": (
                    tuple(
                        option.model_dump(mode="json")
                        for option in left.model_visible.ordered_options
                    ),
                    tuple(
                        option.model_dump(mode="json")
                        for option in right.model_visible.ordered_options
                    ),
                ),
                "stable_correct_option_id": binding.stable_correct_option_id,
                "actual_outcome_code": witness.actual_outcome_code,
                "counterfactual_outcome_code": witness.counterfactual_outcome_code,
                "causal_factor": witness.declared_causal_factor,
                "lexical_cue_annotations": left.scientific_annotations.lexical_cue_annotations,
                "provenance": left.provenance,
                "human_validation": left.human_validation,
                "simulator_rationale": (
                    "Independent replay changed the declared causal factor and reproduced "
                    "the stable actual and counterfactual outcomes."
                ),
                "witness_sha256": witness.witness_sha256,
                "item_binding_sha256": binding.item_binding_sha256,
            }
        )
    records.append(
        {
            "path": "owner_review/pending",
            "record": pending_owner_review(loaded.source_manifest.benchmark_version),
        }
    )
    return tuple(records)


def pending_owner_review(candidate_version: str) -> LiteralPendingOwnerReview:
    return LiteralPendingOwnerReview(
        candidate_version=candidate_version,
        required_owner_bindings=(
            "literal_candidate_root_sha256",
            "literal_validation_report_sha256",
            "m2_1_candidate_bundle_root_sha256",
            "m2_1_candidate_manifest_file_sha256",
            "m2_1_source_snapshot_sha256",
            "pull_request_head_sha",
            "pull_request_number",
            "review_manifest_sha256",
            "witness_bundle_sha256",
        ),
    )


def canonical_record_sha256(value: Mapping[str, Any]) -> str:
    """Hash a non-domain artifact record for manifest file-integrity checks."""

    import hashlib

    return hashlib.sha256(canonical_logical_bytes(value)).hexdigest()
