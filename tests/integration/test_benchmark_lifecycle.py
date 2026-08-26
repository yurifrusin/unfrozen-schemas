"""End-to-end offline M2.1 build, validate, approval, and freeze workflow."""

from __future__ import annotations

import json
import os
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import pytest
from typer.testing import CliRunner

import unfrozen_schemas.evaluation.benchmark_lifecycle as benchmark_lifecycle_module
from unfrozen_schemas.cli import app
from unfrozen_schemas.config import sha256_file
from unfrozen_schemas.evaluation.benchmark_hashing import (
    freeze_approval_hash,
    frozen_manifest_hash,
)
from unfrozen_schemas.evaluation.benchmark_lifecycle import (
    build_benchmark,
    create_engineering_freeze_approval,
    freeze_benchmark,
)
from unfrozen_schemas.evaluation.benchmark_models import (
    BenchmarkOperationError,
    BenchmarkOperationRecord,
    BenchmarkPurpose,
    CandidateManifest,
    FreezeApproval,
    FrozenManifest,
    ProductionPrerequisites,
)
from unfrozen_schemas.evaluation.benchmark_persistence import (
    read_canonical_model,
    write_canonical_json,
)
from unfrozen_schemas.evaluation.benchmark_validation import validate_benchmark_manifest


def test_complete_engineering_build_validate_and_write_once_freeze(
    tmp_path: Path, built_candidate: tuple[Path, CandidateManifest, Path]
) -> None:
    candidate_path, candidate, repository = built_candidate
    approval_path = tmp_path / "engineering-approval.json"
    approval = create_engineering_freeze_approval(
        candidate_manifest_path=candidate_path,
        output_path=approval_path,
        signer="engineering-validator-001",
        repository_root=repository,
    )
    assert approval.approval_class == "engineering_fixture"
    frozen_root = tmp_path / "frozen"
    result = freeze_benchmark(
        candidate_manifest_path=candidate_path,
        approval_path=approval_path,
        output_directory=frozen_root,
        repository_root=repository,
    )
    assert result.manifest_path is not None
    frozen = validate_benchmark_manifest(Path(result.manifest_path))
    assert isinstance(frozen, FrozenManifest)
    assert frozen.lifecycle_state.value == "FROZEN"
    assert frozen.candidate_bundle_root_sha256 == candidate.candidate_bundle_root_sha256
    with pytest.raises(BenchmarkOperationError, match="destination already exists"):
        freeze_benchmark(
            candidate_manifest_path=candidate_path,
            approval_path=approval_path,
            output_directory=frozen_root,
            repository_root=repository,
        )


def test_mutated_frozen_artifact_is_rejected(
    tmp_path: Path, built_candidate: tuple[Path, CandidateManifest, Path]
) -> None:
    candidate_path, _, repository = built_candidate
    approval_path = tmp_path / "approval.json"
    create_engineering_freeze_approval(
        candidate_manifest_path=candidate_path,
        output_path=approval_path,
        signer="engineering-validator-001",
        repository_root=repository,
    )
    frozen_root = tmp_path / "frozen"
    result = freeze_benchmark(
        candidate_manifest_path=candidate_path,
        approval_path=approval_path,
        output_directory=frozen_root,
        repository_root=repository,
    )
    assert result.manifest_path is not None
    item_path = frozen_root / "items.jsonl"
    item_path.chmod(0o644)
    item_path.write_bytes(item_path.read_bytes() + b" ")
    with pytest.raises(ValueError, match=r"Artifact (size|SHA-256) mismatch"):
        validate_benchmark_manifest(Path(result.manifest_path))


def _engineering_approval(
    tmp_path: Path,
    built_candidate: tuple[Path, CandidateManifest, Path],
) -> tuple[Path, Path, Path]:
    candidate_path, _, repository = built_candidate
    approval_path = tmp_path / "atomic-approval.json"
    create_engineering_freeze_approval(
        candidate_manifest_path=candidate_path,
        output_path=approval_path,
        signer="engineering-validator-001",
        repository_root=repository,
    )
    return candidate_path, approval_path, repository


def _refresh_frozen_artifact(frozen_manifest_path: Path, relative: str) -> None:
    manifest = read_canonical_model(frozen_manifest_path, FrozenManifest)
    artifact_path = frozen_manifest_path.parent / relative
    records = tuple(
        record.model_copy(
            update={
                "sha256": sha256_file(artifact_path),
                "size_bytes": artifact_path.stat().st_size,
            }
        )
        if record.path == relative
        else record
        for record in manifest.artifacts
    )
    provisional = manifest.model_copy(
        update={"artifacts": records, "frozen_manifest_sha256": "0" * 64}
    )
    changed = provisional.model_copy(
        update={"frozen_manifest_sha256": frozen_manifest_hash(provisional)}
    )
    write_canonical_json(frozen_manifest_path, changed)


def test_chmod_failure_is_advisory_and_keeps_valid_frozen_output(
    tmp_path: Path,
    built_candidate: tuple[Path, CandidateManifest, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidate_path, approval_path, repository = _engineering_approval(tmp_path, built_candidate)

    def fail_chmod(_path: Path, _mode: int) -> None:
        raise OSError("injected advisory chmod failure")

    monkeypatch.setattr(Path, "chmod", fail_chmod)
    output = tmp_path / "chmod-frozen"
    result = freeze_benchmark(
        candidate_manifest_path=candidate_path,
        approval_path=approval_path,
        output_directory=output,
        repository_root=repository,
    )
    assert result.manifest_path is not None
    assert isinstance(validate_benchmark_manifest(Path(result.manifest_path)), FrozenManifest)


@pytest.mark.parametrize(
    "injection_point",
    ("immediately_after_replace", "final_readback"),
)
def test_post_publication_failure_moves_output_to_invalid_quarantine(
    tmp_path: Path,
    built_candidate: tuple[Path, CandidateManifest, Path],
    monkeypatch: pytest.MonkeyPatch,
    injection_point: str,
) -> None:
    candidate_path, approval_path, repository = _engineering_approval(tmp_path, built_candidate)
    if injection_point == "immediately_after_replace":
        monkeypatch.setattr(
            benchmark_lifecycle_module,
            "_after_frozen_publication",
            lambda _output: (_ for _ in ()).throw(RuntimeError("injected after replace")),
        )
    else:
        monkeypatch.setattr(
            benchmark_lifecycle_module,
            "_read_back_published_freeze",
            lambda _manifest, _repository: (_ for _ in ()).throw(
                RuntimeError("injected final readback")
            ),
        )
    output = tmp_path / f"failed-{injection_point}"
    with pytest.raises(BenchmarkOperationError, match="injected") as raised:
        freeze_benchmark(
            candidate_manifest_path=candidate_path,
            approval_path=approval_path,
            output_directory=output,
            repository_root=repository,
        )
    assert str(raised.value).startswith("RuntimeError: injected")
    assert not output.exists()
    retained = list(tmp_path.glob(f".{output.name}.invalid-frozen-*"))
    assert len(retained) == 1
    assert (retained[0] / "frozen_manifest.json").is_file()


def test_quarantine_move_failure_removes_publication_without_masking_original_error(
    tmp_path: Path,
    built_candidate: tuple[Path, CandidateManifest, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidate_path, approval_path, repository = _engineering_approval(tmp_path, built_candidate)
    output = tmp_path / "quarantine-move-failure"
    real_replace = os.replace

    def selective_replace(source: str | Path, destination: str | Path) -> None:
        if Path(source) == output:
            raise OSError("injected quarantine replace failure")
        real_replace(source, destination)

    monkeypatch.setattr(os, "replace", selective_replace)
    monkeypatch.setattr(
        shutil,
        "move",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            OSError("injected quarantine move failure")
        ),
    )
    monkeypatch.setattr(
        benchmark_lifecycle_module,
        "_after_frozen_publication",
        lambda _output: (_ for _ in ()).throw(RuntimeError("primary published failure")),
    )
    with pytest.raises(BenchmarkOperationError) as raised:
        freeze_benchmark(
            candidate_manifest_path=candidate_path,
            approval_path=approval_path,
            output_directory=output,
            repository_root=repository,
        )
    assert str(raised.value).startswith("RuntimeError: primary published failure")
    assert not output.exists()
    assert not list(tmp_path.glob(f".{output.name}.invalid-frozen-*"))


def test_coordinated_freeze_operation_mutation_is_semantically_rejected(
    tmp_path: Path,
    built_candidate: tuple[Path, CandidateManifest, Path],
) -> None:
    candidate_path, approval_path, repository = _engineering_approval(tmp_path, built_candidate)
    output = tmp_path / "mutated-freeze-operation"
    result = freeze_benchmark(
        candidate_manifest_path=candidate_path,
        approval_path=approval_path,
        output_directory=output,
        repository_root=repository,
    )
    assert result.manifest_path is not None
    operation_path = output / "freeze_operation.json"
    operation_path.chmod(0o644)
    operation = read_canonical_model(operation_path, BenchmarkOperationRecord)
    changed = operation.model_copy(
        update={"input_hashes": {**operation.input_hashes, "unexpected": "f" * 64}}
    )
    write_canonical_json(operation_path, changed)
    frozen_manifest_path = Path(result.manifest_path)
    frozen_manifest_path.chmod(0o644)
    _refresh_frozen_artifact(frozen_manifest_path, "freeze_operation.json")
    with pytest.raises(ValueError, match="Freeze operation provenance"):
        validate_benchmark_manifest(frozen_manifest_path)


@pytest.mark.parametrize(
    "changed_field",
    ["candidate_manifest_sha256", "codex_spec_sha256", "git_commit"],
)
def test_stale_or_mismatched_approval_is_rejected(
    tmp_path: Path,
    built_candidate: tuple[Path, CandidateManifest, Path],
    changed_field: str,
) -> None:
    candidate_path, _, repository = built_candidate
    approval_path = tmp_path / "approval.json"
    approval = create_engineering_freeze_approval(
        candidate_manifest_path=candidate_path,
        output_path=approval_path,
        signer="engineering-validator-001",
        repository_root=repository,
    )
    replacement = "f" * (40 if changed_field == "git_commit" else 64)
    changed = approval.model_copy(update={changed_field: replacement, "approval_sha256": "0" * 64})
    changed = changed.model_copy(update={"approval_sha256": freeze_approval_hash(changed)})
    write_canonical_json(approval_path, changed)
    with pytest.raises(BenchmarkOperationError, match=f"Freeze approval mismatch: {changed_field}"):
        freeze_benchmark(
            candidate_manifest_path=candidate_path,
            approval_path=approval_path,
            output_directory=tmp_path / f"frozen-{changed_field}",
            repository_root=repository,
        )


def test_identical_source_rebuild_has_identical_logical_identities(
    tmp_path: Path,
    engineering_source: Path,
    clean_benchmark_repository: Path,
) -> None:
    first = build_benchmark(
        source_directory=engineering_source,
        output_directory=tmp_path / "candidate-a",
        version="engineering-benchmark-lifecycle-v1",
        purpose=BenchmarkPurpose.ENGINEERING,
        repository_root=clean_benchmark_repository,
    )
    second = build_benchmark(
        source_directory=engineering_source,
        output_directory=tmp_path / "candidate-b",
        version="engineering-benchmark-lifecycle-v1",
        purpose=BenchmarkPurpose.ENGINEERING,
        repository_root=clean_benchmark_repository,
    )
    assert first.candidate_bundle_root_sha256 == second.candidate_bundle_root_sha256
    assert first.private_answer_bundle_sha256 == second.private_answer_bundle_sha256
    assert first.public_metadata_bundle_sha256 == second.public_metadata_bundle_sha256
    assert first.manifest_path is not None and second.manifest_path is not None
    first_manifest = validate_benchmark_manifest(Path(first.manifest_path))
    second_manifest = validate_benchmark_manifest(Path(second.manifest_path))
    assert isinstance(first_manifest, CandidateManifest)
    assert isinstance(second_manifest, CandidateManifest)
    assert first_manifest.source_snapshot_sha256 == second_manifest.source_snapshot_sha256


def _production_source(tmp_path: Path, *, unresolved_rights: bool = False) -> Path:
    source = tmp_path / "production-source"
    source.mkdir(parents=True)
    fixture_root = Path("tests/fixtures/benchmark_lifecycle/source")
    item_lines = fixture_root.joinpath("items.jsonl").read_text(encoding="utf-8").splitlines()
    converted: list[dict[str, Any]] = []
    for index, line in enumerate(item_lines):
        item = cast(dict[str, Any], json.loads(line))
        item_id = f"outcome-neutral-{index + 1}"
        item.update(
            {
                "item_id": item_id,
                "purpose": "outcome",
                "identity_purpose": "outcome",
                "engineering_only": False,
                "scientific_eligible": True,
                "promotable": True,
            }
        )
        item["provenance"].update(
            {
                "origin_classification": "human_authored",
                "rights_status": "unresolved" if unresolved_rights else "cleared",
                "licence_reference": None if unresolved_rights else "rights-review:test-only",
                "ethics_status": "approved",
                "ethics_reference": "ethics:test-only",
                "created_from_source_record": item_id,
            }
        )
        item["human_validation"].update(
            {
                "validation_status": "passed",
                "protocol_version": "test-only-v1",
                "validator_count": 2,
                "agreement_metric": "unanimous",
                "agreement_value": 1.0,
                "adjudication_status": "resolved",
                "validator_population_description": "synthetic unit-test validators",
                "ethics_determination_reference": "ethics:test-only",
            }
        )
        item["private_answer"]["answer_provenance"] = "independent_human"
        converted.append(item)
    prereq = {
        field: str(index + 1) * 64
        for index, field in enumerate(ProductionPrerequisites.model_fields)
    }
    manifest = {
        "schema_version": "1",
        "manifest_kind": "benchmark_source",
        "lifecycle_state": "SOURCE",
        "source_format": "canonical-jsonl-v1",
        "benchmark_version": "v1_core",
        "purpose": "outcome",
        "engineering_only": False,
        "scientific_eligible": True,
        "promotable": True,
        "items_file": "items.jsonl",
        "expected_item_count": 2,
        "rights_determination_reference": "rights:test-only",
        "human_validation_reference": "human-validation:test-only",
        "ethics_determination_reference": "ethics:test-only",
        "production_prerequisites": prereq,
        "quarantine_scope": {
            "schema_version": "1",
            "mode": "canonical_root_scan",
            "canonical_roots": [
                "benchmarks/frozen",
                "benchmarks/private",
                "benchmarks/selection",
            ],
        },
    }
    source.joinpath("source_manifest.json").write_text(
        json.dumps(manifest), encoding="utf-8", newline="\n"
    )
    source.joinpath("items.jsonl").write_text(
        "".join(
            json.dumps(item, sort_keys=True, separators=(",", ":")) + "\n" for item in converted
        ),
        encoding="utf-8",
        newline="\n",
    )
    return source


def _renamed_selection_copy_source(tmp_path: Path) -> Path:
    source = _production_source(tmp_path)
    manifest_path = source / "source_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["benchmark_version"] = "selection-copy-test-v1"
    manifest["purpose"] = "selection"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8", newline="\n")
    converted: list[dict[str, Any]] = []
    for index, line in enumerate(
        source.joinpath("items.jsonl").read_text(encoding="utf-8").splitlines()
    ):
        item = cast(dict[str, Any], json.loads(line))
        item_id = f"selection-all-identities-renamed-{index + 1}"
        item["item_id"] = item_id
        item["purpose"] = "selection"
        item["identity_purpose"] = "selection"
        item["provenance"]["created_from_source_record"] = item_id
        item["model_visible"]["reverse_pair_id"] = "selection-renamed-pair"
        item["model_visible"]["variant_id"] = f"selection-renamed-variant-{index + 1}"
        option_mapping = {
            "opt-k7": "selection-option-k7",
            "opt-m4": "selection-option-m4",
        }
        for option in item["model_visible"]["ordered_options"]:
            option["option_id"] = option_mapping[option["option_id"]]
        item["model_visible"]["option_permutation"] = [
            option["option_id"] for option in item["model_visible"]["ordered_options"]
        ]
        item["private_answer"]["correct_option_id"] = option_mapping[
            item["private_answer"]["correct_option_id"]
        ]
        converted.append(item)
    source.joinpath("items.jsonl").write_text(
        "".join(
            json.dumps(item, sort_keys=True, separators=(",", ":")) + "\n" for item in converted
        ),
        encoding="utf-8",
        newline="\n",
    )
    return source


def _production_approval(candidate_path: Path, candidate: CandidateManifest) -> FreezeApproval:
    assert candidate.production_prerequisites is not None
    provisional = FreezeApproval(
        approval_class="production",
        benchmark_version=candidate.benchmark_version,
        benchmark_purpose=candidate.purpose,
        engineering_only=False,
        candidate_manifest_sha256=sha256_file(candidate_path),
        candidate_bundle_root_sha256=candidate.candidate_bundle_root_sha256,
        private_answer_bundle_sha256=candidate.private_answer_bundle_sha256,
        public_metadata_bundle_sha256=candidate.public_metadata_bundle_sha256,
        quarantine_scope_sha256=candidate.quarantine_scope_sha256,
        codex_spec_sha256=candidate.codex_spec_sha256,
        git_commit=candidate.git.commit,
        rights_determination_reference=candidate.rights_determination_reference,
        human_validation_reference=candidate.human_validation_reference,
        ethics_determination_reference=candidate.ethics_determination_reference,
        model_selection_approval_sha256=(
            candidate.production_prerequisites.model_selection_approval_sha256
        ),
        production_prerequisites=candidate.production_prerequisites,
        decision="APPROVED",
        signer="test-owner",
        timestamp=datetime(2026, 8, 25, tzinfo=UTC),
        rationale="Test-only prospective production approval structure.",
        approval_sha256="0" * 64,
    )
    return provisional.model_copy(update={"approval_sha256": freeze_approval_hash(provisional)})


def test_v1_core_freeze_is_refused_even_with_structural_prerequisite_placeholders(
    tmp_path: Path, clean_benchmark_repository: Path
) -> None:
    source = _production_source(tmp_path)
    build = build_benchmark(
        source_directory=source,
        output_directory=tmp_path / "v1-candidate",
        version="v1_core",
        purpose=BenchmarkPurpose.OUTCOME,
        repository_root=clean_benchmark_repository,
    )
    assert build.manifest_path is not None
    candidate_path = Path(build.manifest_path)
    candidate = validate_benchmark_manifest(
        candidate_path, repository_root=clean_benchmark_repository
    )
    assert isinstance(candidate, CandidateManifest)
    approval = _production_approval(candidate_path, candidate)
    approval_path = tmp_path / "v1-approval.json"
    write_canonical_json(approval_path, approval)
    with pytest.raises(BenchmarkOperationError, match="v1_core production freezing is not enabled"):
        freeze_benchmark(
            candidate_manifest_path=candidate_path,
            approval_path=approval_path,
            output_directory=tmp_path / "v1-frozen",
            repository_root=clean_benchmark_repository,
        )


def test_production_freeze_fails_first_on_unresolved_rights(
    tmp_path: Path, clean_benchmark_repository: Path
) -> None:
    source = _production_source(tmp_path, unresolved_rights=True)
    build = build_benchmark(
        source_directory=source,
        output_directory=tmp_path / "unresolved-candidate",
        version="v1_core",
        purpose=BenchmarkPurpose.OUTCOME,
        repository_root=clean_benchmark_repository,
    )
    assert build.manifest_path is not None
    candidate_path = Path(build.manifest_path)
    candidate = validate_benchmark_manifest(
        candidate_path, repository_root=clean_benchmark_repository
    )
    assert isinstance(candidate, CandidateManifest)
    approval_path = tmp_path / "unresolved-approval.json"
    write_canonical_json(approval_path, _production_approval(candidate_path, candidate))
    with pytest.raises(BenchmarkOperationError, match="resolved rights/licensing"):
        freeze_benchmark(
            candidate_manifest_path=candidate_path,
            approval_path=approval_path,
            output_directory=tmp_path / "unresolved-frozen",
            repository_root=clean_benchmark_repository,
        )


def test_non_engineering_build_fails_when_a_mandatory_quarantine_root_is_missing(
    tmp_path: Path,
    clean_benchmark_repository: Path,
) -> None:
    clean_benchmark_repository.joinpath("benchmarks/selection").rmdir()
    source = _production_source(tmp_path)
    with pytest.raises(BenchmarkOperationError, match="Quarantine root is missing"):
        build_benchmark(
            source_directory=source,
            output_directory=tmp_path / "missing-root-candidate",
            version="v1_core",
            purpose=BenchmarkPurpose.OUTCOME,
            repository_root=clean_benchmark_repository,
        )


def test_added_manifest_makes_candidate_and_approval_stale(
    tmp_path: Path,
    engineering_source: Path,
    clean_benchmark_repository: Path,
) -> None:
    source = _production_source(tmp_path)
    result = build_benchmark(
        source_directory=source,
        output_directory=tmp_path / "scoped-outcome-candidate",
        version="v1_core",
        purpose=BenchmarkPurpose.OUTCOME,
        repository_root=clean_benchmark_repository,
    )
    assert result.manifest_path is not None
    candidate_path = Path(result.manifest_path)
    candidate = validate_benchmark_manifest(
        candidate_path, repository_root=clean_benchmark_repository
    )
    assert isinstance(candidate, CandidateManifest)
    approval_path = tmp_path / "stale-production-approval.json"
    write_canonical_json(approval_path, _production_approval(candidate_path, candidate))
    build_benchmark(
        source_directory=engineering_source,
        output_directory=(
            clean_benchmark_repository / "benchmarks/private/late-engineering-manifest"
        ),
        version="engineering-benchmark-lifecycle-v1",
        purpose=BenchmarkPurpose.ENGINEERING,
        repository_root=clean_benchmark_repository,
    )
    with pytest.raises(ValueError, match="quarantine scope is stale"):
        validate_benchmark_manifest(candidate_path, repository_root=clean_benchmark_repository)
    with pytest.raises(BenchmarkOperationError, match="quarantine scope is stale"):
        freeze_benchmark(
            candidate_manifest_path=candidate_path,
            approval_path=approval_path,
            output_directory=tmp_path / "stale-frozen",
            repository_root=clean_benchmark_repository,
        )


def test_mandatory_scope_rejects_selection_copy_after_all_ids_are_renamed(
    tmp_path: Path,
    clean_benchmark_repository: Path,
) -> None:
    outcome_source = _production_source(tmp_path / "outcome")
    build_benchmark(
        source_directory=outcome_source,
        output_directory=(
            clean_benchmark_repository / "benchmarks/private/existing-outcome-candidate"
        ),
        version="v1_core",
        purpose=BenchmarkPurpose.OUTCOME,
        repository_root=clean_benchmark_repository,
    )
    selection_source = _renamed_selection_copy_source(tmp_path / "selection")
    with pytest.raises(BenchmarkOperationError, match="Exact displayed model input"):
        build_benchmark(
            source_directory=selection_source,
            output_directory=tmp_path / "prohibited-selection-copy",
            version="selection-copy-test-v1",
            purpose=BenchmarkPurpose.SELECTION,
            repository_root=clean_benchmark_repository,
        )


def test_cli_nonzero_and_no_network_required(
    tmp_path: Path,
    engineering_source: Path,
    clean_benchmark_repository: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def network_forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError(f"network access attempted: {args}, {kwargs}")

    import socket

    monkeypatch.setattr(socket, "create_connection", network_forbidden)
    build_benchmark(
        source_directory=engineering_source,
        output_directory=tmp_path / "offline-candidate",
        version="engineering-benchmark-lifecycle-v1",
        purpose=BenchmarkPurpose.ENGINEERING,
        repository_root=clean_benchmark_repository,
    )
    runner = CliRunner()
    result = runner.invoke(app, ["validate-benchmark"])
    assert result.exit_code != 0
    assert "exactly one" in result.output
