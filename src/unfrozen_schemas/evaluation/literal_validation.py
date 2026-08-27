"""Independent M2.2 literal-source and composite-candidate validation."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from itertools import pairwise
from pathlib import Path
from typing import Any, Literal

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
from unfrozen_schemas.evaluation.literal_contracts import (
    intervention_contract,
    mechanism_kind_signature,
    narrative_facts,
    render_literal_prompt,
    structural_signatures,
    target_mechanism,
)
from unfrozen_schemas.evaluation.literal_hashing import (
    authoring_snapshot_hash,
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
    LiteralAuditStatus,
    LiteralAuthoringManifest,
    LiteralItemBinding,
    LiteralItemBindingBundle,
    LiteralLexicalAudit,
    LiteralLexicalCategory,
    LiteralLexicalCategorySummary,
    LiteralLexicalFinding,
    LiteralOperationRecord,
    LiteralPartition,
    LiteralPartitionPlan,
    LiteralPendingOwnerReview,
    LiteralScenarioSpec,
    LiteralSourceBundleManifest,
    LiteralSplitAudit,
    LiteralTaskFamily,
    LiteralTemplate,
    LiteralTemplateRegistryManifest,
    LiteralTransferLevel,
    LiteralValidationReport,
    LiteralWitnessBundle,
    LiteralWitnessRecord,
)

LITERAL_DIRECTORY = ".literal"
AUTHORING_SNAPSHOT_FILE = "authoring_snapshot.json"
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
CANDIDATE_MATERIALIZATION_OPERATION_FILE = "candidate_materialization_operation_record.json"
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
    (
        "evaluation-status-language",
        re.compile(r"\b(?:held-out|novel|mechanism-transfer|transfer item)\b", re.I),
    ),
)

_CAUSAL_TERM_ALLOWLIST: tuple[str, ...] = (
    "aligned",
    "blocked",
    "changing",
    "closed",
    "cut",
    "disabled",
    "downward",
    "elevated",
    "enabled",
    "enough",
    "falls",
    "fully",
    "load-bearing",
    "movement",
    "moves",
    "not",
    "observed",
    "open",
    "removed",
    "removing",
    "small",
    "stays",
    "taut",
    "too",
    "unchanged",
    "wide",
)

_PHYSICAL_MECHANISM_TERMS: frozenset[str] = frozenset(
    {
        "anchor",
        "aperture",
        "boundary",
        "contact",
        "container",
        "bearing",
        "non-load",
        "opening",
        "perimeter",
        "platform",
        "side-touching",
        "support",
        "tether",
        "touches",
    }
)

_DIRECTION_ORIENTATION_TERMS: frozenset[str] = frozenset(
    {"bottom", "inside", "inward", "left", "outside", "outward", "right", "top"}
)

_TASK_META_TERMS: frozenset[str] = frozenset(
    {
        "a",
        "after",
        "alternative",
        "and",
        "another",
        "anything",
        "apply",
        "as",
        "at",
        "actual",
        "before",
        "begins",
        "but",
        "causal",
        "consequence",
        "consider",
        "control",
        "described",
        "exactly",
        "following",
        "for",
        "has",
        "happens",
        "in",
        "is",
        "its",
        "next",
        "no",
        "now",
        "object",
        "of",
        "one",
        "on",
        "or",
        "occurs",
        "otherwise",
        "outcome",
        "pattern",
        "physical",
        "reference",
        "same",
        "setup",
        "setups",
        "stated",
        "step",
        "s",
        "that",
        "the",
        "then",
        "there",
        "this",
        "to",
        "two",
        "under",
        "what",
        "when",
        "which",
        "with",
        "without",
    }
)


@dataclass(frozen=True, slots=True)
class LoadedLiteralSource:
    root: Path
    source_manifest: SourceManifest
    authoring_snapshot: LiteralAuthoringManifest
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


def _sentence_ngrams(value: str) -> Counter[str]:
    """Return unigrams/bigrams without crossing punctuation or line boundaries."""

    normalised = unicodedata.normalize(
        "NFC", value.replace("\r\n", "\n").replace("\r", "\n")
    ).casefold()
    result: Counter[str] = Counter()
    for sentence in re.split(r"(?:[.!?]+|\n+)", normalised):
        tokens = _tokens(sentence)
        result.update(tokens)
        result.update(f"{first} {second}" for first, second in pairwise(tokens))
    return result


def _lexical_category(value: str) -> LiteralLexicalCategory:
    parts = set(value.split())
    if parts & _DIRECTION_ORIENTATION_TERMS:
        return LiteralLexicalCategory.NUISANCE_DIRECTION_ORIENTATION_VOCABULARY
    content = parts - _TASK_META_TERMS
    if content & _PHYSICAL_MECHANISM_TERMS:
        return LiteralLexicalCategory.PHYSICAL_MECHANISM_CORRELATION
    if content and content <= set(_CAUSAL_TERM_ALLOWLIST):
        return LiteralLexicalCategory.NECESSARY_CAUSAL_CONDITION_VOCABULARY
    if not content:
        return LiteralLexicalCategory.TASK_META_VOCABULARY
    return LiteralLexicalCategory.RENDERER_GRAMMATICAL_CONSTRUCTION_CUE


def _association_disposition(
    category: LiteralLexicalCategory, semantic_group_support: int
) -> LiteralAuditStatus:
    if semantic_group_support < 2 or category is LiteralLexicalCategory.TASK_META_VOCABULARY:
        return LiteralAuditStatus.PASS
    if category in {
        LiteralLexicalCategory.NECESSARY_CAUSAL_CONDITION_VOCABULARY,
        LiteralLexicalCategory.PHYSICAL_MECHANISM_CORRELATION,
    }:
        return LiteralAuditStatus.OWNER_REVIEW_REQUIRED
    if category in {
        LiteralLexicalCategory.NUISANCE_DIRECTION_ORIENTATION_VOCABULARY,
        LiteralLexicalCategory.RENDERER_GRAMMATICAL_CONSTRUCTION_CUE,
        LiteralLexicalCategory.AUDIT_BOUNDARY_ARTIFACT,
    }:
        return LiteralAuditStatus.FAIL
    return LiteralAuditStatus.PASS


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
    binding_by_group = {binding.semantic_group_id: binding for binding in bindings}
    findings: list[LiteralLexicalFinding] = []
    answer_position_counts: Counter[str] = Counter()
    prompt_by_group: dict[str, str] = {}
    association_counts: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    association_groups: dict[tuple[str, str], set[str]] = defaultdict(set)
    prompt_lengths: dict[str, list[int]] = defaultdict(list)
    option_lengths_by_class: dict[str, list[int]] = defaultdict(list)
    distractor_lengths_by_class: dict[str, list[int]] = defaultdict(list)
    option_styles: dict[str, Counter[str]] = defaultdict(Counter)
    option_pair_differences: Counter[str] = Counter()

    def add_finding(
        *,
        category: LiteralLexicalCategory,
        finding_kind: str,
        scope: str,
        value: str,
        disposition: LiteralAuditStatus,
        semantic_group_ids: Iterable[str],
        item_ids: Iterable[str],
        answer_class_counts: Mapping[str, int],
        occurrence_support: int,
    ) -> None:
        groups = tuple(sorted(set(semantic_group_ids)))
        addressed_items = tuple(sorted(set(item_ids)))
        counts = dict(sorted(answer_class_counts.items()))
        membership = {
            "semantic_group_ids": groups,
            "item_ids": addressed_items,
        }
        membership_sha256 = hashlib.sha256(canonical_logical_bytes(membership)).hexdigest()
        identity = {
            "category_version": "literal-lexical-category-v2",
            "category": category.value,
            "finding_kind": finding_kind,
            "scope": scope,
            "value": value,
            "occurrence_support": occurrence_support,
            "answer_class_counts": counts,
            "membership_sha256": membership_sha256,
        }
        finding_id = "cue-" + hashlib.sha256(canonical_logical_bytes(identity)).hexdigest()[:24]
        findings.append(
            LiteralLexicalFinding(
                finding_id=finding_id,
                category=category,
                finding_kind=finding_kind,
                scope=scope,
                value=value,
                occurrence_support=occurrence_support,
                semantic_group_support=len(groups),
                answer_class_counts=counts,
                semantic_group_ids=groups,
                item_ids=addressed_items,
                membership_sha256=membership_sha256,
                disposition=disposition,
            )
        )

    def style(value: str) -> str:
        stripped = value.strip()
        modality = next(
            (
                item
                for item in ("may", "might", "must", "will", "would", "could", "should")
                if re.search(rf"\b{item}\b", stripped, flags=re.IGNORECASE)
            ),
            "none",
        )
        terminal = stripped[-1] if stripped[-1] in ".!?" else "none"
        return (
            f"capitalised-{stripped[:1].isupper()}|terminal-{terminal}|"
            f"modality-{modality}|sentences-{len(re.findall(r'[.!?]', stripped))}"
        )

    def summary(values: Sequence[int]) -> dict[str, int]:
        return {
            "count": len(values),
            "minimum": min(values),
            "maximum": max(values),
            "total": sum(values),
        }

    for binding in bindings:
        left = item_by_id[binding.item_ids[0]]
        right = item_by_id[binding.item_ids[1]]
        if left.model_visible.prompt != right.model_visible.prompt:
            raise ValueError(f"Reverse group {binding.semantic_group_id} changes its prompt")
        prompt_by_group[binding.semantic_group_id] = _normalise_text(left.model_visible.prompt)
        prompt_lengths[binding.stable_correct_option_id].append(
            len(_tokens(left.model_visible.prompt))
        )
        left_lengths = {
            option.option_id: len(_tokens(option.text))
            for option in left.model_visible.ordered_options
        }
        correct_length = left_lengths[binding.stable_correct_option_id]
        distractor_length = next(
            length
            for option_id, length in left_lengths.items()
            if option_id != binding.stable_correct_option_id
        )
        option_lengths_by_class[binding.stable_correct_option_id].append(correct_length)
        distractor_lengths_by_class[binding.stable_correct_option_id].append(distractor_length)
        option_pair_differences[str(abs(correct_length - distractor_length))] += 1
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
                    add_finding(
                        category=LiteralLexicalCategory.NUISANCE_IDENTIFIER_VOCABULARY,
                        finding_kind=kind,
                        scope=item.item_id,
                        value=match.group(0),
                        disposition=LiteralAuditStatus.FAIL,
                        semantic_group_ids=(binding.semantic_group_id,),
                        item_ids=(item.item_id,),
                        answer_class_counts={binding.stable_correct_option_id: 1},
                        occurrence_support=1,
                    )
            normalised_prompt = _normalise_text(item.model_visible.prompt)
            if any(
                _normalise_text(option.text) in normalised_prompt
                for option in item.model_visible.ordered_options
            ):
                add_finding(
                    category=LiteralLexicalCategory.RENDERER_GRAMMATICAL_CONSTRUCTION_CUE,
                    finding_kind="prompt-states-option-consequence",
                    scope=item.item_id,
                    value="option text appears in prompt",
                    disposition=LiteralAuditStatus.FAIL,
                    semantic_group_ids=(binding.semantic_group_id,),
                    item_ids=(item.item_id,),
                    answer_class_counts={binding.stable_correct_option_id: 1},
                    occurrence_support=1,
                )
            pair_lengths = [
                len(_tokens(option.text)) for option in item.model_visible.ordered_options
            ]
            if max(pair_lengths) - min(pair_lengths) > 1:
                add_finding(
                    category=LiteralLexicalCategory.RENDERER_GRAMMATICAL_CONSTRUCTION_CUE,
                    finding_kind="option-length-imbalance",
                    scope=item.item_id,
                    value=str(pair_lengths),
                    disposition=LiteralAuditStatus.FAIL,
                    semantic_group_ids=(binding.semantic_group_id,),
                    item_ids=(item.item_id,),
                    answer_class_counts={binding.stable_correct_option_id: 1},
                    occurrence_support=1,
                )
            observed_styles = {style(option.text) for option in item.model_visible.ordered_options}
            if len(observed_styles) != 1:
                add_finding(
                    category=LiteralLexicalCategory.RENDERER_GRAMMATICAL_CONSTRUCTION_CUE,
                    finding_kind="option-style-imbalance",
                    scope=item.item_id,
                    value="grammaticality-specificity-or-modality-style-differs",
                    disposition=LiteralAuditStatus.FAIL,
                    semantic_group_ids=(binding.semantic_group_id,),
                    item_ids=(item.item_id,),
                    answer_class_counts={binding.stable_correct_option_id: 1},
                    occurrence_support=1,
                )
            if any(
                not option.text.startswith("The object ")
                for option in item.model_visible.ordered_options
            ):
                add_finding(
                    category=LiteralLexicalCategory.NUISANCE_IDENTIFIER_VOCABULARY,
                    finding_kind="option-object-reference-mismatch",
                    scope=item.item_id,
                    value="options must use the neutral object referent",
                    disposition=LiteralAuditStatus.FAIL,
                    semantic_group_ids=(binding.semantic_group_id,),
                    item_ids=(item.item_id,),
                    answer_class_counts={binding.stable_correct_option_id: 1},
                    occurrence_support=1,
                )
        correct_option = next(
            option
            for option in left.model_visible.ordered_options
            if option.option_id == binding.stable_correct_option_id
        )
        option_styles[binding.stable_correct_option_id][style(correct_option.text)] += 1
        ngrams = _sentence_ngrams(left.model_visible.prompt)
        for token, count in ngrams.items():
            key = (binding.task_family.value, token)
            association_counts[key][binding.stable_correct_option_id] += count
            association_groups[key].add(binding.semantic_group_id)

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
            if prompt_by_group[left_id] == prompt_by_group[right_id]:
                continue
            left_tokens = token_sets[left_id]
            right_tokens = token_sets[right_id]
            union = left_tokens | right_tokens
            if union and len(left_tokens & right_tokens) / len(union) >= 0.92:
                near_pairs.append((left_id, right_id))

    for (family, token), counts in sorted(association_counts.items()):
        if len(counts) != 1:
            continue
        association_group_ids = association_groups[(family, token)]
        category = _lexical_category(token)
        disposition = _association_disposition(category, len(association_group_ids))
        add_finding(
            category=category,
            finding_kind="family-lexical-association",
            scope=family,
            value=token,
            disposition=disposition,
            semantic_group_ids=association_group_ids,
            item_ids=(
                item_id
                for group in association_group_ids
                for item_id in next(
                    binding.item_ids for binding in bindings if binding.semantic_group_id == group
                )
            ),
            answer_class_counts=counts,
            occurrence_support=sum(counts.values()),
        )

    template_counts = _answer_counts(bindings, "prompt_template_id")
    action_counts = _answer_counts(bindings, "action_word")
    mechanism_counts = _answer_counts(bindings, "source_mechanism")
    target_mechanism_counts = _answer_counts(bindings, "target_mechanism")
    for label, answer_groups in (
        ("template", template_counts),
        ("action-word", action_counts),
        ("source-mechanism", mechanism_counts),
        ("target-mechanism", target_mechanism_counts),
    ):
        for group, answer_counts in answer_groups.items():
            if len(answer_counts) < 2:
                member_bindings = [
                    binding
                    for binding in bindings
                    if {
                        "template": binding.prompt_template_id,
                        "action-word": binding.action_word,
                        "source-mechanism": binding.source_mechanism.value,
                        "target-mechanism": binding.target_mechanism.value,
                    }[label]
                    == group
                ]
                category = (
                    LiteralLexicalCategory.PHYSICAL_MECHANISM_CORRELATION
                    if label in {"source-mechanism", "target-mechanism"}
                    else LiteralLexicalCategory.NECESSARY_CAUSAL_CONDITION_VOCABULARY
                    if label == "action-word"
                    else LiteralLexicalCategory.RENDERER_GRAMMATICAL_CONSTRUCTION_CUE
                )
                add_finding(
                    category=category,
                    finding_kind=f"{label}-single-answer-class",
                    scope=group,
                    value=next(iter(answer_counts)),
                    disposition=_association_disposition(category, len(member_bindings)),
                    semantic_group_ids=(b.semantic_group_id for b in member_bindings),
                    item_ids=(item_id for b in member_bindings for item_id in b.item_ids),
                    answer_class_counts=answer_counts,
                    occurrence_support=sum(answer_counts.values()),
                )
    for left_id, right_id in near_pairs:
        pair_bindings = tuple(
            binding for binding in bindings if binding.semantic_group_id in {left_id, right_id}
        )
        add_finding(
            category=LiteralLexicalCategory.DUPLICATE_MATCHED_WORDING,
            finding_kind="near-prompt-duplicate",
            scope="semantic-groups",
            value=f"{left_id}|{right_id}",
            disposition=LiteralAuditStatus.OWNER_REVIEW_REQUIRED,
            semantic_group_ids=(left_id, right_id),
            item_ids=(item_id for binding in pair_bindings for item_id in binding.item_ids),
            answer_class_counts=Counter(
                binding.stable_correct_option_id for binding in pair_bindings
            ),
            occurrence_support=2,
        )
    for left_id, right_id in duplicate_groups:
        duplicate_bindings = (binding_by_group[left_id], binding_by_group[right_id])
        causal_scenarios = {
            binding.structural_signatures.causal_scenario_sha256 for binding in duplicate_bindings
        }
        matched_strata = {binding.matched_stratum_id for binding in duplicate_bindings}
        declared_variant = (
            len(causal_scenarios) == 1 and len(matched_strata) == 1 and None not in matched_strata
        )
        add_finding(
            category=LiteralLexicalCategory.DUPLICATE_MATCHED_WORDING,
            finding_kind="exact-prompt-duplicate",
            scope="semantic-groups",
            value=f"{left_id}|{right_id}",
            disposition=(
                LiteralAuditStatus.OWNER_REVIEW_REQUIRED
                if declared_variant
                else LiteralAuditStatus.FAIL
            ),
            semantic_group_ids=(left_id, right_id),
            item_ids=(item_id for binding in duplicate_bindings for item_id in binding.item_ids),
            answer_class_counts=Counter(
                binding.stable_correct_option_id for binding in duplicate_bindings
            ),
            occurrence_support=2,
        )
    opposing_classes = (
        ("movement-succeeds", "movement-blocked"),
        ("object-falls", "object-stays"),
    )
    for left_class, right_class in opposing_classes:
        if (
            left_class in option_lengths_by_class
            and right_class in option_lengths_by_class
            and not set(option_lengths_by_class[left_class])
            & set(option_lengths_by_class[right_class])
        ):
            raise ValueError(
                "Correct-option whitespace length deterministically separates answer classes"
            )
    failures = [finding for finding in findings if finding.disposition is LiteralAuditStatus.FAIL]
    if failures:
        first = failures[0]
        raise ValueError(
            f"Literal lexical audit failed: {first.finding_kind} at {first.scope}: {first.value}"
        )
    owner_findings = [
        finding
        for finding in findings
        if finding.disposition is LiteralAuditStatus.OWNER_REVIEW_REQUIRED
    ]
    findings_tuple = tuple(sorted(findings, key=lambda finding: finding.finding_id))
    category_summaries: list[LiteralLexicalCategorySummary] = []
    for category in LiteralLexicalCategory:
        finding_ids = tuple(
            finding.finding_id for finding in findings_tuple if finding.category is category
        )
        owner_required = any(
            finding.category is category
            and finding.disposition is LiteralAuditStatus.OWNER_REVIEW_REQUIRED
            for finding in findings_tuple
        )
        category_hash = hashlib.sha256(
            canonical_logical_bytes(
                {
                    "category_version": "literal-lexical-category-v2",
                    "category": category.value,
                    "finding_ids": finding_ids,
                }
            )
        ).hexdigest()
        category_summaries.append(
            LiteralLexicalCategorySummary(
                category=category,
                finding_ids=finding_ids,
                finding_count=len(finding_ids),
                owner_disposition_required=owner_required,
                category_membership_sha256=category_hash,
            )
        )
    provisional = LiteralLexicalAudit(
        candidate_version=candidate_version,
        causal_term_allowlist=_CAUSAL_TERM_ALLOWLIST,
        semantic_group_count=len(bindings),
        source_item_count=len(items),
        answer_position_counts=dict(sorted(answer_position_counts.items())),
        template_answer_counts=template_counts,
        action_word_answer_counts=action_counts,
        source_mechanism_answer_counts=mechanism_counts,
        target_mechanism_answer_counts=target_mechanism_counts,
        prompt_length_by_answer_class={
            key: summary(value) for key, value in sorted(prompt_lengths.items())
        },
        option_length_by_answer_class={
            key: summary(value) for key, value in sorted(option_lengths_by_class.items())
        },
        distractor_option_length_by_answer_class={
            key: summary(value) for key, value in sorted(distractor_lengths_by_class.items())
        },
        option_style_by_answer_class={
            key: dict(sorted(value.items())) for key, value in sorted(option_styles.items())
        },
        option_pair_length_difference_counts=dict(sorted(option_pair_differences.items())),
        exact_duplicate_group_count=len(duplicate_groups),
        near_duplicate_group_pairs=tuple(near_pairs),
        findings=findings_tuple,
        category_summaries=tuple(category_summaries),
        unresolved_owner_review_finding_count=len(owner_findings),
        status=(
            LiteralAuditStatus.OWNER_REVIEW_REQUIRED if owner_findings else LiteralAuditStatus.PASS
        ),
        lexical_audit_sha256="0" * 64,
    )
    return provisional.model_copy(update={"lexical_audit_sha256": lexical_audit_hash(provisional)})


def build_split_audit(
    *,
    candidate_version: str,
    items: Sequence[SourceItemRecord],
    bindings: Sequence[LiteralItemBinding],
    witnesses: Sequence[LiteralWitnessRecord],
    partition_plan: LiteralPartitionPlan,
) -> LiteralSplitAudit:
    item_by_id = {item.item_id: item for item in items}
    binding_by_group = {item.semantic_group_id: item for item in bindings}
    prompt_groups: dict[str, list[LiteralItemBinding]] = defaultdict(list)
    for binding in bindings:
        prompt = _normalise_text(item_by_id[binding.item_ids[0]].model_visible.prompt)
        prompt_groups[prompt].append(binding)
    duplicates = sum(len(members) - 1 for members in prompt_groups.values() if len(members) > 1)
    for members in prompt_groups.values():
        if len(members) < 2:
            continue
        causal_scenarios = {
            member.structural_signatures.causal_scenario_sha256 for member in members
        }
        matched_strata = {member.matched_stratum_id for member in members}
        if len(causal_scenarios) != 1 or len(matched_strata) != 1 or None in matched_strata:
            raise ValueError(
                "Exact prompt duplicates must be declared variants of one causal scenario"
            )
    l2_dimensions = {
        binding.semantic_group_id: binding.structural_novelty_dimensions
        for binding in bindings
        if binding.transfer_level is LiteralTransferLevel.L2
    }
    if len({item.semantic_group_id for item in bindings}) != len(bindings):
        raise ValueError("Literal split reuses a semantic-group identity")
    witness_by_group = {item.semantic_group_id: item for item in witnesses}
    if len(witness_by_group) != len(witnesses):
        raise ValueError("Literal split reuses a witness semantic-group identity")
    l1 = [item for item in bindings if item.transfer_level is LiteralTransferLevel.L1]
    l2 = [item for item in bindings if item.transfer_level is LiteralTransferLevel.L2]
    l1_witnesses = [witness_by_group[item.semantic_group_id] for item in l1]
    l2_witnesses = [witness_by_group[item.semantic_group_id] for item in l2]

    def exact_hashes(records: Sequence[LiteralWitnessRecord], first: str, second: str) -> set[str]:
        return {
            value
            for record in records
            for value in (getattr(record, first), getattr(record, second))
        }

    exact_partitions = {
        "state": (
            exact_hashes(l1_witnesses, "initial_state_hash", "counterfactual_initial_state_hash"),
            exact_hashes(l2_witnesses, "initial_state_hash", "counterfactual_initial_state_hash"),
        ),
        "observation": (
            exact_hashes(
                l1_witnesses,
                "initial_observation_hash",
                "counterfactual_initial_observation_hash",
            ),
            exact_hashes(
                l2_witnesses,
                "initial_observation_hash",
                "counterfactual_initial_observation_hash",
            ),
        ),
        "action": (
            exact_hashes(
                l1_witnesses, "action_sequence_hash", "counterfactual_action_sequence_hash"
            ),
            exact_hashes(
                l2_witnesses, "action_sequence_hash", "counterfactual_action_sequence_hash"
            ),
        ),
        "group": (
            {item.semantic_group_id for item in l1},
            {item.semantic_group_id for item in l2},
        ),
        "witness": (
            {item.witness_sha256 for item in l1_witnesses},
            {item.witness_sha256 for item in l2_witnesses},
        ),
    }
    for label, (l1_hashes, l2_hashes) in exact_partitions.items():
        if l1_hashes & l2_hashes:
            raise ValueError(f"L1/L2 exact {label} identities are not disjoint")
    l1_templates = {item.prompt_template_id for item in l1}
    l1_configurations = {item.structural_signatures.configuration_sha256 for item in l1}
    complete_l1_mechanisms = {item.structural_signatures.target_mechanism_sha256 for item in l1}
    if complete_l1_mechanisms != set(partition_plan.prohibited_l1_source_mechanism_signatures):
        raise ValueError("Partition plan does not bind the complete L1 mechanism-source set")
    expected_prohibited = complete_l1_mechanisms | set(
        partition_plan.prospective_adaptation_source_mechanism_signatures
    )
    if expected_prohibited != set(partition_plan.prohibited_mechanism_transfer_target_signatures):
        raise ValueError("Partition plan omits a prohibited mechanism-transfer source signature")
    complete_l1_mechanism_kinds = {
        item.structural_signatures.target_mechanism_kind_sha256 for item in l1
    }
    if complete_l1_mechanism_kinds != set(
        partition_plan.prohibited_l1_source_mechanism_kind_signatures
    ):
        raise ValueError("Partition plan does not bind the complete L1 mechanism-kind set")
    expected_prohibited_kinds = complete_l1_mechanism_kinds | set(
        partition_plan.prospective_adaptation_source_mechanism_kind_signatures
    )
    if expected_prohibited_kinds != set(
        partition_plan.prohibited_mechanism_transfer_target_kind_signatures
    ):
        raise ValueError("Partition plan omits a prohibited mechanism-transfer source kind")
    for binding in l2:
        if binding.partition is LiteralPartition.L2_NOVEL_TEMPLATE:
            if binding.prompt_template_id in l1_templates:
                raise ValueError("Novel-template L2 template was not withheld from L1")
        elif (
            binding.partition is LiteralPartition.L2_NOVEL_CONFIGURATION
            and binding.structural_signatures.configuration_sha256 in l1_configurations
        ):
            raise ValueError("Novel-configuration L2 signature is present in L1")
        if binding.task_family is LiteralTaskFamily.PHYSICAL_ANALOGY:
            assert binding.analogy_reference_group_id is not None
            reference = binding_by_group.get(binding.analogy_reference_group_id)
            if reference is None or reference.transfer_level is not LiteralTransferLevel.L1:
                raise ValueError("Physical analogy lacks its declared L1 reference")
            if (
                binding.source_mechanism is not reference.target_mechanism
                or binding.structural_signatures.source_mechanism_sha256
                != reference.structural_signatures.target_mechanism_sha256
                or binding.structural_signatures.source_mechanism_kind_sha256
                != reference.structural_signatures.target_mechanism_kind_sha256
            ):
                raise ValueError("Physical analogy source identity is not its L1 reference")
            if (
                binding.target_mechanism is not target_mechanism(binding.scenario_case)
                or binding.structural_signatures.target_mechanism_sha256 in expected_prohibited
            ):
                raise ValueError(
                    "Mechanism-transfer target is represented in prohibited source material"
                )
            expected_target_kind = mechanism_kind_signature(binding.target_mechanism)
            if binding.structural_signatures.target_mechanism_kind_sha256 != expected_target_kind:
                raise ValueError("Mechanism-transfer target kind identity does not reconstruct")
            if expected_target_kind in expected_prohibited_kinds:
                raise ValueError(
                    "Mechanism-transfer target kind is represented in prohibited "
                    "mechanism-kind source material"
                )
            if (
                binding.structural_signatures.source_mechanism_kind_sha256
                == binding.structural_signatures.target_mechanism_kind_sha256
            ):
                raise ValueError(
                    "Physical analogy lacks a distinct source-to-target mechanism-kind mapping"
                )

    causal_groups: dict[str, list[LiteralItemBinding]] = defaultdict(list)
    structural_groups: dict[str, list[LiteralItemBinding]] = defaultdict(list)
    for binding in bindings:
        causal_groups[binding.structural_signatures.causal_scenario_sha256].append(binding)
        structural_groups[binding.structural_signatures.structural_stratum_sha256].append(binding)
    for signature, members in causal_groups.items():
        if len(members) == 1:
            continue
        strata = {item.matched_stratum_id for item in members}
        if len(strata) != 1 or None in strata:
            raise ValueError(
                f"Repeated structural signature {signature} lacks one declared matched stratum"
            )
    matched_variants = sum(
        max(0, len({member.task_family for member in members}) - 1)
        for members in causal_groups.values()
    )
    cosmetic_variants = sum(
        len(members) - len({member.task_family for member in members})
        for members in causal_groups.values()
    )

    provisional = LiteralSplitAudit(
        candidate_version=candidate_version,
        semantic_group_count=len(bindings),
        question_group_count=len(bindings),
        causal_scenario_count=len(causal_groups),
        independent_structural_stratum_count=len(structural_groups),
        matched_variant_count=matched_variants,
        cosmetic_variant_count=cosmetic_variants,
        l1_group_count=sum(
            binding.transfer_level is LiteralTransferLevel.L1 for binding in bindings
        ),
        l2_group_count=sum(
            binding.transfer_level is LiteralTransferLevel.L2 for binding in bindings
        ),
        unique_state_hash_count=len(
            exact_hashes(witnesses, "initial_state_hash", "counterfactual_initial_state_hash")
        ),
        unique_observation_hash_count=len(
            exact_hashes(
                witnesses,
                "initial_observation_hash",
                "counterfactual_initial_observation_hash",
            )
        ),
        unique_action_hash_count=len(
            exact_hashes(
                witnesses,
                "action_sequence_hash",
                "counterfactual_action_sequence_hash",
            )
        ),
        unique_group_count=len(binding_by_group),
        unique_witness_hash_count=len({item.witness_sha256 for item in witnesses}),
        l2_structural_novelty_dimensions=dict(sorted(l2_dimensions.items())),
        causal_scenario_groups={
            signature: tuple(sorted(item.semantic_group_id for item in members))
            for signature, members in sorted(causal_groups.items())
        },
        structural_signature_strata={
            signature: tuple(sorted(item.semantic_group_id for item in members))
            for signature, members in sorted(structural_groups.items())
        },
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


def verify_witness(
    witness: LiteralWitnessRecord,
    spec: LiteralScenarioSpec,
    template: LiteralTemplate,
    *,
    analogy_source: LiteralWitnessRecord | None = None,
) -> None:
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
    contract = intervention_contract(spec.scenario_case)
    if witness.intervention_contract != contract:
        raise ValueError(f"Intervention contract mismatch: {witness.semantic_group_id}")
    if spec.intervention_kind is not contract.intervention_kind:
        raise ValueError(f"Declared intervention kind mismatch: {witness.semantic_group_id}")
    if initial_differences != witness.observed_initial_difference_paths:
        raise ValueError(f"Undeclared initial-state difference: {witness.semantic_group_id}")
    if action_differences != witness.observed_action_difference_paths:
        raise ValueError(f"Undeclared action difference: {witness.semantic_group_id}")
    if initial_differences != contract.allowed_initial_difference_paths:
        raise ValueError(
            "Initial-state differences exceed the prospective contract: "
            f"{witness.semantic_group_id}"
        )
    if action_differences != contract.allowed_action_difference_paths:
        raise ValueError(
            f"Action differences exceed the prospective contract: {witness.semantic_group_id}"
        )
    if len(witness.actual_actions) != contract.allowed_horizon:
        raise ValueError(f"Witness exceeds the prospective horizon: {witness.semantic_group_id}")
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
    if (
        actual is not contract.expected_actual_outcome
        or counterfactual is not contract.expected_counterfactual_outcome
    ):
        raise ValueError(f"Prospective outcome contract mismatch: {witness.semantic_group_id}")
    expected_facts = narrative_facts(
        spec,
        witness.initial_privileged_state,
        witness.counterfactual_initial_privileged_state,
        witness.actual_actions,
        witness.counterfactual_actions,
        analogy_source=analogy_source,
    )
    if witness.narrative_facts != expected_facts:
        raise ValueError(f"Typed narrative facts do not reconstruct: {witness.semantic_group_id}")
    expected_signatures = structural_signatures(
        spec,
        template,
        witness.initial_privileged_state,
        witness.counterfactual_initial_privileged_state,
        witness.actual_actions,
        witness.counterfactual_actions,
        actual,
        counterfactual,
        analogy_source=analogy_source,
    )
    if witness.structural_signatures != expected_signatures:
        raise ValueError(f"Structural signatures do not reconstruct: {witness.semantic_group_id}")
    expected_metadata = (
        spec.semantic_group_id,
        spec.schema_identity,
        spec.transfer_level,
        spec.task_family,
        (
            analogy_source.target_mechanism
            if analogy_source is not None
            else target_mechanism(spec.scenario_case)
        ),
        target_mechanism(spec.scenario_case),
        spec.prompt_template_id,
        spec.partition,
        spec.scenario_case,
        spec.intervention_kind,
        spec.structural_novelty_dimensions,
        spec.matched_stratum_id,
        spec.analogy_reference_group_id,
    )
    observed_metadata = (
        witness.semantic_group_id,
        witness.schema_identity,
        witness.transfer_level,
        witness.task_family,
        witness.source_mechanism,
        witness.target_mechanism,
        witness.prompt_template_id,
        witness.partition,
        witness.scenario_case,
        witness.intervention_kind,
        witness.structural_novelty_dimensions,
        witness.matched_stratum_id,
        witness.analogy_reference_group_id,
    )
    if observed_metadata != expected_metadata:
        raise ValueError(f"Witness authoring metadata mismatch: {witness.semantic_group_id}")
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
        authoring_snapshot=read_canonical_model(
            _literal_path(root, AUTHORING_SNAPSHOT_FILE), LiteralAuthoringManifest
        ),
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


def validate_literal_root_location(
    loaded: LoadedLiteralSource,
    *,
    observed_root: Path,
    root_kind: Literal["source", "review"],
) -> None:
    """Require outcome artifacts to occupy their tracked canonical root."""

    if loaded.source_manifest.engineering_only:
        return
    from unfrozen_schemas.config import find_repository_root

    repository = find_repository_root(Path.cwd()).resolve()
    key = f"{root_kind}_root"
    configured_value = loaded.source_bundle.resolved_configuration.get(key)
    if not isinstance(configured_value, str) or not configured_value:
        raise ValueError(f"Outcome literal configuration is missing {key}")
    configured_path = Path(configured_value)
    if configured_path.is_absolute():
        raise ValueError(f"Outcome literal configured {key} must be repository-relative")
    expected = (repository / configured_path).resolve()
    if not expected.is_relative_to(repository):
        raise ValueError(f"Outcome literal configured {key} escapes the repository")
    observed = observed_root.resolve()
    if observed != expected:
        raise ValueError(
            f"Outcome literal {key} is outside its configured canonical location: "
            f"expected {expected}; observed {observed}"
        )


def _verify_template_registry(
    registry: LiteralTemplateRegistryManifest, templates: Sequence[LiteralTemplate]
) -> None:
    expected = {template.template_id: template_hash(template) for template in templates}
    if registry.template_content_hashes != dict(sorted(expected.items())):
        raise ValueError("Literal template registry content hashes do not reconstruct")
    if template_registry_hash(registry) != registry.template_registry_sha256:
        raise ValueError("Literal template registry hash does not reconstruct")


def _validate_loaded_literal_source_content(
    loaded: LoadedLiteralSource,
) -> LiteralValidationReport:
    """Reconstruct the complete source from its retained authoring snapshot."""

    manifest = loaded.source_manifest
    version = manifest.benchmark_version
    purpose = manifest.purpose.value
    if version != loaded.partition_plan.candidate_version:
        raise ValueError("M2.1 and M2.2 source versions differ")
    if loaded.authoring_snapshot.candidate_version != version:
        raise ValueError("Retained authoring snapshot has the wrong candidate version")
    _source_manifest, source_snapshot = load_source_directory(
        loaded.root, benchmark_version=version, purpose=manifest.purpose
    )
    if source_snapshot.items != loaded.items:
        raise ValueError("M2.1 source snapshot and M2.2 source items differ")
    validate_reverse_pairs(loaded.items)
    bindings = loaded.item_bindings.bindings
    witnesses = loaded.witness_bundle.witnesses
    scenarios = loaded.authoring_snapshot.scenarios
    templates = loaded.authoring_snapshot.templates
    if not (
        len(loaded.items) == 2 * len(bindings) and len(bindings) == len(witnesses) == len(scenarios)
    ):
        raise ValueError("Literal source requires exactly two items and one witness per group")
    if tuple(sorted(binding.semantic_group_id for binding in bindings)) != tuple(
        binding.semantic_group_id for binding in bindings
    ):
        raise ValueError("Literal item bindings are not canonically ordered")
    if tuple(sorted(witness.semantic_group_id for witness in witnesses)) != tuple(
        witness.semantic_group_id for witness in witnesses
    ):
        raise ValueError("Literal witnesses are not canonically ordered")
    expected_groups = tuple(sorted(item.semantic_group_id for item in scenarios))
    observed_binding_groups = tuple(item.semantic_group_id for item in bindings)
    observed_witness_groups = tuple(item.semantic_group_id for item in witnesses)
    if observed_binding_groups != expected_groups or observed_witness_groups != expected_groups:
        raise ValueError("Authoring, binding, and witness semantic-group sets differ")
    partition_groups = tuple(
        sorted(
            (
                *loaded.partition_plan.l1_held_out_group_ids,
                *loaded.partition_plan.l2_novel_template_group_ids,
                *loaded.partition_plan.l2_novel_configuration_group_ids,
                *loaded.partition_plan.l2_mechanism_transfer_group_ids,
            )
        )
    )
    if partition_groups != expected_groups:
        raise ValueError("Partition plan does not contain the complete authoring group set")
    witness_by_group = {item.semantic_group_id: item for item in witnesses}
    scenario_by_group = {item.semantic_group_id: item for item in scenarios}
    template_by_id = {item.template_id: item for item in templates}
    outcome_text_by_id = {
        item.text_id: item for item in loaded.authoring_snapshot.outcome_text_registry
    }
    items_by_id = {item.item_id: item for item in loaded.items}
    all_bound_item_ids: list[str] = []
    for binding in bindings:
        if item_binding_hash(binding) != binding.item_binding_sha256:
            raise ValueError(f"Item-binding hash mismatch: {binding.semantic_group_id}")
        witness = witness_by_group.get(binding.semantic_group_id)
        if witness is None or witness.witness_sha256 != binding.witness_sha256:
            raise ValueError(f"Item binding has no matching witness: {binding.semantic_group_id}")
        spec = scenario_by_group[binding.semantic_group_id]
        template = template_by_id[spec.prompt_template_id]
        analogy_source = (
            witness_by_group[spec.analogy_reference_group_id]
            if spec.analogy_reference_group_id is not None
            else None
        )
        verify_witness(witness, spec, template, analogy_source=analogy_source)
        expected_binding_fields = (
            witness.item_ids,
            spec.outcome_text_record_ids,
            spec.schema_identity,
            spec.transfer_level,
            spec.task_family,
            witness.source_mechanism,
            witness.target_mechanism,
            spec.prompt_template_id,
            spec.partition,
            spec.scenario_case,
            spec.intervention_kind,
            witness.actual_actions[0].kind.value.casefold().replace("_", "-"),
            spec.structural_novelty_dimensions,
            witness.structural_signatures,
            spec.matched_stratum_id,
            spec.analogy_reference_group_id,
            witness.stable_correct_option_id,
        )
        observed_binding_fields = (
            binding.item_ids,
            binding.outcome_text_record_ids,
            binding.schema_identity,
            binding.transfer_level,
            binding.task_family,
            binding.source_mechanism,
            binding.target_mechanism,
            binding.prompt_template_id,
            binding.partition,
            binding.scenario_case,
            binding.intervention_kind,
            binding.action_word,
            binding.structural_novelty_dimensions,
            binding.structural_signatures,
            binding.matched_stratum_id,
            binding.analogy_reference_group_id,
            binding.stable_correct_option_id,
        )
        if observed_binding_fields != expected_binding_fields:
            raise ValueError(f"Witness and item binding disagree: {binding.semantic_group_id}")
        all_bound_item_ids.extend(binding.item_ids)
        pair = tuple(items_by_id[item_id] for item_id in binding.item_ids)
        expected_prompt = render_literal_prompt(template, witness.narrative_facts)
        expected_options = {
            outcome_text_by_id[text_id].outcome_code.value: outcome_text_by_id[text_id].text
            for text_id in spec.outcome_text_record_ids
        }
        for index, item in enumerate(pair):
            expected_order = binding.option_permutations[index]
            if (
                item.task_family_slug != binding.task_family.value
                or item.transfer_level
                != (1 if binding.transfer_level is LiteralTransferLevel.L1 else 2)
                or item.source_mechanism_family != binding.source_mechanism.value
                or item.prompt_template_id != binding.prompt_template_id
                or item.partition_id != binding.partition.value
                or item.model_visible.prompt != expected_prompt
                or item.model_visible.instructions != witness.narrative_facts.instructions
                or item.model_visible.variant_id != binding.variant_ids[index]
                or item.model_visible.option_permutation != expected_order
                or tuple(option.option_id for option in item.model_visible.ordered_options)
                != expected_order
                or {option.option_id: option.text for option in item.model_visible.ordered_options}
                != {option_id: expected_options[option_id] for option_id in expected_order}
                or item.scientific_annotations.required_causal_factors
                != (witness.intervention_contract.causal_factor.value,)
                or item.scientific_annotations.source_mechanism_family
                != binding.source_mechanism.value
            ):
                raise ValueError(
                    f"Typed narrative/source item mismatch: {binding.semantic_group_id}"
                )
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
        correct_text_record = next(
            (
                outcome_text_by_id[text_id]
                for text_id in spec.outcome_text_record_ids
                if outcome_text_by_id[text_id].outcome_code.value
                == witness.stable_correct_option_id
            ),
            None,
        )
        if (
            correct_text_record is None
            or correct_text_record.outcome_code is not witness.actual_outcome_code
        ):
            raise ValueError(
                "Stable correct option does not express simulator outcome: "
                f"{binding.semantic_group_id}"
            )

    if len(all_bound_item_ids) != len(set(all_bound_item_ids)) or set(all_bound_item_ids) != set(
        items_by_id
    ):
        raise ValueError("Literal source has an orphaned or reused source item")

    if partition_plan_hash(loaded.partition_plan) != loaded.partition_plan.partition_plan_sha256:
        raise ValueError("Literal partition-plan hash does not reconstruct")
    if (
        item_binding_bundle_hash(loaded.item_bindings)
        != loaded.item_bindings.item_binding_bundle_sha256
    ):
        raise ValueError("Literal item-binding bundle hash does not reconstruct")
    if witness_bundle_hash(loaded.witness_bundle) != loaded.witness_bundle.witness_bundle_sha256:
        raise ValueError("Literal witness-bundle hash does not reconstruct")
    _verify_template_registry(loaded.template_registry, templates)
    from unfrozen_schemas.evaluation.literal_generation import _partition_plan

    if _partition_plan(loaded.authoring_snapshot, witnesses) != loaded.partition_plan:
        raise ValueError("Literal partition plan does not reconstruct from authoring and witnesses")
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
        partition_plan=loaded.partition_plan,
    )
    if rebuilt_split != loaded.split_audit:
        raise ValueError("Literal split audit does not reconstruct")
    schema_counts = _count(binding.schema_identity.value for binding in bindings)
    level_counts = _count(binding.transfer_level.value for binding in bindings)
    family_counts = _count(binding.task_family.value for binding in bindings)
    source_mechanism_counts = _count(binding.source_mechanism.value for binding in bindings)
    target_mechanism_counts = _count(binding.target_mechanism.value for binding in bindings)
    provisional = LiteralValidationReport(
        candidate_version=version,
        purpose=purpose,
        semantic_group_count=len(bindings),
        question_group_count=rebuilt_split.question_group_count,
        causal_scenario_count=rebuilt_split.causal_scenario_count,
        independent_structural_stratum_count=(rebuilt_split.independent_structural_stratum_count),
        matched_variant_count=rebuilt_split.matched_variant_count,
        cosmetic_variant_count=rebuilt_split.cosmetic_variant_count,
        source_item_count=len(loaded.items),
        schema_counts=schema_counts,
        level_counts=level_counts,
        family_counts=family_counts,
        source_mechanism_counts=source_mechanism_counts,
        target_mechanism_counts=target_mechanism_counts,
        lexical_cue_audit=(
            "OWNER_REVIEW_REQUIRED"
            if loaded.lexical_audit.status is LiteralAuditStatus.OWNER_REVIEW_REQUIRED
            else "PASS"
        ),
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
        f"{LITERAL_DIRECTORY}/{AUTHORING_SNAPSHOT_FILE}",
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
    if operation.operation_sha256 != source_bundle.source_generation_operation_sha256:
        raise ValueError("Literal source bundle binds a different generation operation")
    if operation.artifacts != source_bundle.artifacts:
        raise ValueError("Literal generation operation and source artifact records differ")
    expected_source_hashes = {
        "authoring_snapshot_file_sha256": sha256_file(
            _literal_path(loaded.root, AUTHORING_SNAPSHOT_FILE)
        ),
        "authoring_snapshot_sha256": authoring_snapshot_hash(loaded.authoring_snapshot),
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
    if operation.operation_kind != "generate_literal_source" or operation.status != "COMPLETED":
        raise ValueError("Literal source operation kind/status is invalid")
    expected_input_hashes = {
        "authoring_input_file_sha256": source_bundle.authoring_input_file_sha256,
        "tracked_configuration_file_sha256": source_bundle.tracked_configuration_file_sha256,
    }
    expected_output_hashes = {
        "literal_source_bundle_sha256": source_bundle.literal_source_bundle_sha256
    }
    if (
        operation.engineering_only != manifest.engineering_only
        or operation.scientific_result is not False
        or operation.git != source_bundle.git
        or operation.codex_spec_sha256 != source_bundle.codex_spec_sha256
        or operation.resolved_configuration != source_bundle.resolved_configuration
        or operation.input_hashes != expected_input_hashes
        or operation.output_hashes != expected_output_hashes
        or operation.item_count != len(loaded.items)
        or operation.semantic_group_count != len(bindings)
        or operation.schema_counts != schema_counts
        or operation.level_counts != level_counts
        or operation.family_counts != family_counts
    ):
        raise ValueError("Literal source-generation operation provenance is inconsistent")
    from unfrozen_schemas.evaluation.literal_generation import _resource_budget

    expected_budget = _resource_budget(
        operation_id=operation.operation_id,
        started_at=operation.started_at,
        ended_at=operation.ended_at,
        elapsed=operation.resource_budget.elapsed_compute_seconds or 0.0,
        peak_memory=operation.resource_budget.peak_memory_bytes,
        witnesses=witnesses,
        artifact_count=len(operation.artifacts),
        artifact_bytes=sum(item.size_bytes for item in operation.artifacts),
    )
    if operation.resource_budget != expected_budget:
        raise ValueError("Literal source ResourceBudget does not reconstruct")
    from unfrozen_schemas.config import find_repository_root
    from unfrozen_schemas.literal_config import load_literal_config
    from unfrozen_schemas.provenance import (
        capture_git_state,
        collect_package_versions,
        collect_platform_information,
    )

    repository = find_repository_root(Path.cwd())
    if (
        operation.package_versions != collect_package_versions()
        or operation.platform != collect_platform_information()
    ):
        raise ValueError("Literal source package/platform provenance is stale")
    if sha256_file(repository / "CODEX_SPEC.md") != source_bundle.codex_spec_sha256:
        raise ValueError("Literal source CODEX_SPEC identity is stale")
    if not manifest.engineering_only:
        current_git = capture_git_state(repository)
        if current_git.dirty or current_git.commit != source_bundle.git.commit:
            raise ValueError("Outcome literal source does not match the current clean Git head")
    config_relative = str(source_bundle.resolved_configuration.get("source_config_path", ""))
    config_path = (repository / config_relative).resolve()
    if (
        not config_path.is_file()
        or sha256_file(config_path) != source_bundle.tracked_configuration_file_sha256
    ):
        raise ValueError("Tracked literal configuration is missing or changed")
    configured = load_literal_config(config_path)
    if configured.resolved.model_dump(mode="json") != source_bundle.resolved_configuration:
        raise ValueError("Tracked and retained resolved literal configurations differ")
    if (
        not configured.authoring_manifest.is_file()
        or sha256_file(configured.authoring_manifest) != source_bundle.authoring_input_file_sha256
    ):
        raise ValueError("Literal authoring input file is missing or changed")
    from unfrozen_schemas.evaluation.literal_generation import _coverage

    _coverage(configured, bindings)
    return expected


def validate_loaded_literal_source(
    loaded: LoadedLiteralSource,
) -> LiteralValidationReport:
    """Validate source content and the canonical outcome-source location."""

    report = _validate_loaded_literal_source_content(loaded)
    validate_literal_root_location(
        loaded,
        observed_root=loaded.root,
        root_kind="source",
    )
    return report


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
                "partition": binding.partition,
                "scenario_case": binding.scenario_case,
                "source_mechanism": binding.source_mechanism,
                "target_mechanism": binding.target_mechanism,
                "structural_novelty_dimensions": binding.structural_novelty_dimensions,
                "structural_signatures": binding.structural_signatures,
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
                "intervention_contract": witness.intervention_contract,
                "observed_initial_difference_paths": (witness.observed_initial_difference_paths),
                "observed_action_difference_paths": witness.observed_action_difference_paths,
                "narrative_facts": witness.narrative_facts,
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
        required_owner_bindings=tuple(
            sorted(
                {
                    "authoring_snapshot_file_sha256",
                    "authoring_snapshot_sha256",
                    "candidate_materialization_operation_sha256",
                    "literal_candidate_root_sha256",
                    "literal_validation_report_sha256",
                    "m2_1_candidate_bundle_root_sha256",
                    "m2_1_candidate_manifest_file_sha256",
                    "m2_1_source_snapshot_sha256",
                    "pull_request_head_sha",
                    "pull_request_number",
                    "review_manifest_file_sha256",
                    "review_manifest_sha256",
                    "review_operation_sha256",
                    "source_generation_operation_sha256",
                    "witness_bundle_sha256",
                }
            )
        ),
    )


def canonical_record_sha256(value: Mapping[str, Any]) -> str:
    """Hash a non-domain artifact record for manifest file-integrity checks."""

    import hashlib

    return hashlib.sha256(canonical_logical_bytes(value)).hexdigest()
