"""End-to-end offline M2.1 build, validate, approval, and freeze workflow."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import pytest
from typer.testing import CliRunner

from unfrozen_schemas.cli import app
from unfrozen_schemas.config import sha256_file
from unfrozen_schemas.evaluation.benchmark_hashing import freeze_approval_hash
from unfrozen_schemas.evaluation.benchmark_lifecycle import (
    build_benchmark,
    create_engineering_freeze_approval,
    freeze_benchmark,
)
from unfrozen_schemas.evaluation.benchmark_models import (
    BenchmarkOperationError,
    BenchmarkPurpose,
    CandidateManifest,
    FreezeApproval,
    FrozenManifest,
    ProductionPrerequisites,
)
from unfrozen_schemas.evaluation.benchmark_persistence import write_canonical_json
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
    source.mkdir()
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
    candidate = validate_benchmark_manifest(candidate_path)
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
    candidate = validate_benchmark_manifest(candidate_path)
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
