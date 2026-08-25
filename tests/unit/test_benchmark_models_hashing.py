"""Strict M2.1 item contracts, purpose quarantine, revisions, and logical hashes."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, cast

import pytest
from pydantic import ValidationError

from unfrozen_schemas.evaluation.benchmark_hashing import (
    annotation_metadata_hash,
    bundle_hashes,
    canonical_logical_bytes,
    derive_built_records,
    make_source_snapshot,
    model_visible_item_hash,
    private_answer_record_hash,
)
from unfrozen_schemas.evaluation.benchmark_models import (
    BenchmarkPurpose,
    LifecycleState,
    SourceItemRecord,
    SourceManifest,
    SourceSnapshotHeader,
)
from unfrozen_schemas.evaluation.benchmark_validation import (
    ensure_lifecycle_transition,
    validate_cross_purpose_records,
    validate_reverse_pairs,
)


def _source_dict(index: int = 0) -> dict[str, Any]:
    lines = (
        Path("tests/fixtures/benchmark_lifecycle/source/items.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    )
    return cast(dict[str, Any], json.loads(lines[index]))


def _item(index: int = 0) -> SourceItemRecord:
    return SourceItemRecord.model_validate(_source_dict(index))


def test_source_item_is_strict_and_rejects_unknown_fields() -> None:
    data = _source_dict()
    data["unexpected"] = True
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        SourceItemRecord.model_validate(data)


@pytest.mark.parametrize("missing", ["provenance", "human_validation"])
def test_source_item_requires_rights_and_human_validation_contracts(missing: str) -> None:
    data = _source_dict()
    del data[missing]
    with pytest.raises(ValidationError, match=missing):
        SourceItemRecord.model_validate(data)


@pytest.mark.parametrize(
    ("section", "missing"),
    [
        ("provenance", "rights_status"),
        ("provenance", "ethics_status"),
        ("human_validation", "validation_status"),
    ],
)
def test_source_item_rejects_missing_governance_fields(section: str, missing: str) -> None:
    data = _source_dict()
    del data[section][missing]
    with pytest.raises(ValidationError, match=missing):
        SourceItemRecord.model_validate(data)


def test_purpose_is_immutable_for_stable_item_identity() -> None:
    data = _source_dict()
    data["purpose"] = "outcome"
    with pytest.raises(ValidationError, match="purpose is immutable"):
        SourceItemRecord.model_validate(data)


def test_engineering_item_cannot_be_promoted_to_scientific() -> None:
    data = _source_dict()
    data["scientific_eligible"] = True
    data["promotable"] = True
    with pytest.raises(ValidationError, match="not promotable"):
        SourceItemRecord.model_validate(data)


def test_evaluated_model_is_not_valid_answer_provenance() -> None:
    data = _source_dict()
    cast_answer = data["private_answer"]
    assert isinstance(cast_answer, dict)
    cast_answer["answer_provenance"] = "evaluated_model"
    with pytest.raises(ValidationError, match="answer_provenance"):
        SourceItemRecord.model_validate(data)


def test_duplicate_option_ids_are_rejected() -> None:
    data = _source_dict()
    visible = data["model_visible"]
    assert isinstance(visible, dict)
    options = visible["ordered_options"]
    assert isinstance(options, list)
    options[1]["option_id"] = options[0]["option_id"]
    visible["option_permutation"] = [options[0]["option_id"], options[0]["option_id"]]
    with pytest.raises(ValidationError, match="option IDs must be unique"):
        SourceItemRecord.model_validate(data)


def test_duplicate_normalised_option_text_is_rejected() -> None:
    data = _source_dict()
    visible = data["model_visible"]
    assert isinstance(visible, dict)
    options = visible["ordered_options"]
    assert isinstance(options, list)
    options[1]["text"] = " k7 "
    with pytest.raises(ValidationError, match="option text"):
        SourceItemRecord.model_validate(data)


def test_invalid_correct_option_reference_is_rejected() -> None:
    data = _source_dict()
    answer = data["private_answer"]
    assert isinstance(answer, dict)
    answer["correct_option_id"] = "opt-absent"
    with pytest.raises(ValidationError, match="correct option"):
        SourceItemRecord.model_validate(data)


def test_invalid_option_permutation_is_rejected() -> None:
    data = _source_dict()
    visible = data["model_visible"]
    assert isinstance(visible, dict)
    visible["option_permutation"] = ["opt-m4", "opt-k7"]
    with pytest.raises(ValidationError, match="option_permutation"):
        SourceItemRecord.model_validate(data)


def test_malformed_reverse_pair_is_rejected() -> None:
    with pytest.raises(ValueError, match="exactly two"):
        validate_reverse_pairs((_item(0),))


def test_reverse_pair_requires_exact_reverse_permutation() -> None:
    left = _item(0)
    right_data = _source_dict(1)
    visible = right_data["model_visible"]
    assert isinstance(visible, dict)
    visible["ordered_options"] = deepcopy(_source_dict(0)["model_visible"]["ordered_options"])
    visible["option_permutation"] = ["opt-k7", "opt-m4"]
    right = SourceItemRecord.model_validate(right_data)
    with pytest.raises(ValueError, match="invalid option permutation"):
        validate_reverse_pairs((left, right))


def test_model_input_hash_changes_only_with_visible_content() -> None:
    item = _item()
    changed_data = item.model_dump(mode="json")
    changed_data["model_visible"]["prompt"] += " Extra."
    changed = SourceItemRecord.model_validate(changed_data)
    assert model_visible_item_hash(item) != model_visible_item_hash(changed)
    assert private_answer_record_hash(item) == private_answer_record_hash(changed)


def test_answer_hash_and_complete_hash_change_with_answer() -> None:
    item = _item()
    changed_data = item.model_dump(mode="json")
    changed_data["private_answer"]["answer_rationale"] = "Independent changed rationale."
    changed = SourceItemRecord.model_validate(changed_data)
    built, _ = derive_built_records(item)
    changed_built, _ = derive_built_records(changed)
    assert private_answer_record_hash(item) != private_answer_record_hash(changed)
    assert (
        built.complete_private_item_record_sha256
        != changed_built.complete_private_item_record_sha256
    )
    assert model_visible_item_hash(item) == model_visible_item_hash(changed)


def test_metadata_hash_changes_without_changing_model_input_hash() -> None:
    item = _item()
    changed_data = item.model_dump(mode="json")
    changed_data["scientific_annotations"]["composition_depth"] = 1
    changed = SourceItemRecord.model_validate(changed_data)
    assert annotation_metadata_hash(item) != annotation_metadata_hash(changed)
    assert model_visible_item_hash(item) == model_visible_item_hash(changed)


def test_line_endings_and_mapping_insertion_order_do_not_change_identity() -> None:
    item = _item()
    changed_data = item.model_dump(mode="json")
    changed_data["model_visible"]["prompt"] = changed_data["model_visible"]["prompt"].replace(
        ". ", ".\r\n"
    )
    lf_data = deepcopy(changed_data)
    lf_data["model_visible"]["prompt"] = lf_data["model_visible"]["prompt"].replace("\r\n", "\n")
    crlf = SourceItemRecord.model_validate(changed_data)
    lf = SourceItemRecord.model_validate(lf_data)
    assert model_visible_item_hash(crlf) == model_visible_item_hash(lf)
    assert canonical_logical_bytes({"b": 2, "a": 1}) == canonical_logical_bytes({"a": 1, "b": 2})


def test_source_item_order_does_not_change_snapshot_or_bundle_hashes() -> None:
    items = (_item(0), _item(1))
    header = SourceSnapshotHeader(
        benchmark_version="engineering-benchmark-lifecycle-v1",
        purpose=BenchmarkPurpose.ENGINEERING,
        engineering_only=True,
        scientific_eligible=False,
        promotable=False,
        item_count=2,
        rights_determination_reference="not-applicable:engineering-fixture",
        human_validation_reference="not-applicable:engineering-fixture",
        ethics_determination_reference="not-applicable:engineering-fixture",
        production_prerequisites=None,
    )
    left = make_source_snapshot(header, items)
    right = make_source_snapshot(header, tuple(reversed(items)))
    assert left.source_snapshot_sha256 == right.source_snapshot_sha256
    left_records = tuple(derive_built_records(item) for item in left.items)
    right_records = tuple(derive_built_records(item) for item in reversed(right.items))
    left_hashes = bundle_hashes(
        benchmark_version=header.benchmark_version,
        purpose=header.purpose.value,
        source_snapshot_sha256=left.source_snapshot_sha256,
        items=tuple(record[0] for record in left_records),
        answers=tuple(record[1] for record in left_records),
    )
    right_hashes = bundle_hashes(
        benchmark_version=header.benchmark_version,
        purpose=header.purpose.value,
        source_snapshot_sha256=right.source_snapshot_sha256,
        items=tuple(record[0] for record in right_records),
        answers=tuple(record[1] for record in right_records),
    )
    assert left_hashes == right_hashes


def test_revision_retains_item_id_but_changes_revision_sensitive_hashes() -> None:
    original = _item()
    changed_data = original.model_dump(mode="json")
    changed_data["item_revision"] = 2
    changed_data["provenance"]["created_from_source_revision"] = 2
    revised = SourceItemRecord.model_validate(changed_data)
    assert original.item_id == revised.item_id
    assert original.item_revision != revised.item_revision
    assert model_visible_item_hash(original) != model_visible_item_hash(revised)


@pytest.mark.parametrize(
    ("version", "purpose"),
    [("v1_core", "engineering"), ("selection_probe_v1", "engineering")],
)
def test_reserved_versions_are_rejected_for_engineering(version: str, purpose: str) -> None:
    data = json.loads(
        Path("tests/fixtures/benchmark_lifecycle/source/source_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    data["benchmark_version"] = version
    data["purpose"] = purpose
    with pytest.raises(ValidationError, match="reserved"):
        SourceManifest.model_validate(data)


@pytest.mark.parametrize(
    ("before", "after"),
    [
        (LifecycleState.SOURCE, LifecycleState.FROZEN),
        (LifecycleState.FROZEN, LifecycleState.PRIVATE),
        (LifecycleState.FROZEN, LifecycleState.SOURCE),
        (LifecycleState.PRIVATE, LifecycleState.SOURCE),
    ],
)
def test_illegal_lifecycle_transitions_fail(before: LifecycleState, after: LifecycleState) -> None:
    with pytest.raises(ValueError, match="Illegal benchmark lifecycle transition"):
        ensure_lifecycle_transition(before, after)


def test_cross_purpose_duplicate_id_and_content_are_rejected() -> None:
    engineering, _ = derive_built_records(_item())
    outcome_data = _source_dict()
    outcome_data.update(
        {
            "item_id": "outcome-copy-a",
            "purpose": "outcome",
            "identity_purpose": "outcome",
            "engineering_only": False,
            "scientific_eligible": True,
            "promotable": True,
        }
    )
    outcome_data["provenance"]["created_from_source_record"] = "outcome-copy-a"
    outcome_data["provenance"]["origin_classification"] = "human_authored"
    outcome_data["private_answer"]["answer_provenance"] = "independent_human"
    outcome, _ = derive_built_records(SourceItemRecord.model_validate(outcome_data))
    with pytest.raises(ValueError, match="Equivalent model-visible content"):
        validate_cross_purpose_records(
            {
                BenchmarkPurpose.ENGINEERING: (engineering,),
                BenchmarkPurpose.OUTCOME: (outcome,),
            }
        )


def test_selection_item_cannot_be_relabelled_as_outcome() -> None:
    data = _source_dict()
    data.update(
        {
            "item_id": "selection-neutral-a",
            "purpose": "outcome",
            "identity_purpose": "selection",
            "engineering_only": False,
            "scientific_eligible": True,
            "promotable": True,
        }
    )
    data["provenance"]["created_from_source_record"] = "selection-neutral-a"
    data["provenance"]["origin_classification"] = "human_authored"
    data["private_answer"]["answer_provenance"] = "independent_human"
    with pytest.raises(ValidationError, match="purpose is immutable"):
        SourceItemRecord.model_validate(data)
