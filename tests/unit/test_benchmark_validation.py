"""Independent candidate validation, path safety, leakage, and failure provenance tests."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from unfrozen_schemas.cli import app
from unfrozen_schemas.config import sha256_file
from unfrozen_schemas.evaluation.benchmark_lifecycle import build_benchmark
from unfrozen_schemas.evaluation.benchmark_models import (
    BenchmarkOperationError,
    BenchmarkOperationRecord,
    BenchmarkPurpose,
    BuiltBenchmarkItem,
    CandidateManifest,
    PrivateAnswerRecord,
    QuarantineScope,
)
from unfrozen_schemas.evaluation.benchmark_persistence import (
    read_canonical_model,
    read_jsonl_models,
    resolve_safe_relative_path,
    validate_benchmark_version,
    write_canonical_json,
)
from unfrozen_schemas.evaluation.benchmark_validation import (
    assert_public_answer_isolation,
    audit_tracked_benchmark_paths,
    load_source_directory,
    validate_benchmark_manifest,
)


def _copy_candidate(source_manifest: Path, destination: Path) -> Path:
    shutil.copytree(source_manifest.parent, destination)
    return destination / "candidate_manifest.json"


def _refresh_candidate_artifact(manifest_path: Path, relative: str) -> None:
    manifest = read_canonical_model(manifest_path, CandidateManifest)
    artifact_path = manifest_path.parent / relative
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
    write_canonical_json(manifest_path, manifest.model_copy(update={"artifacts": records}))


@pytest.mark.parametrize(
    "declared",
    [
        "../items.jsonl",
        "C:/outside/items.jsonl",
        "C:\\outside\\items.jsonl",
        "/outside/items.jsonl",
        "nested\\items.jsonl",
        "nested//items.jsonl",
        "./items.jsonl",
    ],
)
def test_safe_relative_paths_reject_traversal_and_platform_absolute_forms(
    tmp_path: Path, declared: str
) -> None:
    with pytest.raises(ValueError, match="path"):
        resolve_safe_relative_path(tmp_path, declared, must_exist=False)


@pytest.mark.parametrize(
    "version",
    (
        "../escape",
        "nested/version",
        "nested\\version",
        "/absolute/version",
        "C:/absolute/version",
        "C:\\absolute\\version",
        ".",
        "..",
        "",
    ),
)
def test_cli_version_values_reject_traversal_and_absolute_forms(version: str) -> None:
    with pytest.raises(ValueError, match="Benchmark version"):
        validate_benchmark_version(version)
    result = CliRunner().invoke(app, ["validate-benchmark", "--version", version])
    assert result.exit_code != 0
    assert "Benchmark version" in result.output


def test_candidate_rejects_corrupted_item_artifact(
    tmp_path: Path, built_candidate: tuple[Path, CandidateManifest, Path]
) -> None:
    manifest_path = _copy_candidate(built_candidate[0], tmp_path / "corrupted-item")
    with (manifest_path.parent / "items.jsonl").open("ab") as handle:
        handle.write(b" ")
    with pytest.raises(ValueError, match=r"Artifact (size|SHA-256) mismatch"):
        validate_benchmark_manifest(manifest_path)


def test_candidate_rejects_corrupted_private_answer_bundle(
    tmp_path: Path, built_candidate: tuple[Path, CandidateManifest, Path]
) -> None:
    manifest_path = _copy_candidate(built_candidate[0], tmp_path / "corrupted-answer")
    answer_path = manifest_path.parent / "private_answers.jsonl"
    answer_path.write_bytes(answer_path.read_bytes().replace(b"K7", b"Q9", 1))
    with pytest.raises(ValueError, match="Artifact SHA-256 mismatch"):
        validate_benchmark_manifest(manifest_path)


def test_candidate_rejects_hash_mismatched_quarantine_scope(
    tmp_path: Path, built_candidate: tuple[Path, CandidateManifest, Path]
) -> None:
    manifest_path = _copy_candidate(built_candidate[0], tmp_path / "changed-quarantine-scope")
    scope_path = manifest_path.parent / "quarantine_scope.json"
    scope = read_canonical_model(scope_path, QuarantineScope)
    write_canonical_json(scope_path, scope.model_copy(update={"quarantine_scope_sha256": "f" * 64}))
    _refresh_candidate_artifact(manifest_path, "quarantine_scope.json")
    with pytest.raises(ValueError, match="Quarantine scope logical hash mismatch"):
        validate_benchmark_manifest(manifest_path)


def test_candidate_rejects_corrupted_manifest_lifecycle(
    tmp_path: Path, built_candidate: tuple[Path, CandidateManifest, Path]
) -> None:
    manifest_path = _copy_candidate(built_candidate[0], tmp_path / "corrupted-manifest")
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["lifecycle_state"] = "FROZEN"
    manifest_path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(Exception, match=r"lifecycle_state|canonical"):
        validate_benchmark_manifest(manifest_path)


def test_candidate_rejects_unsafe_declared_artifact_path(
    tmp_path: Path, built_candidate: tuple[Path, CandidateManifest, Path]
) -> None:
    manifest_path = _copy_candidate(built_candidate[0], tmp_path / "unsafe-path")
    manifest = read_canonical_model(manifest_path, CandidateManifest)
    changed_record = manifest.artifacts[0].model_copy(update={"path": "../outside.json"})
    changed = manifest.model_copy(update={"artifacts": (changed_record, *manifest.artifacts[1:])})
    write_canonical_json(manifest_path, changed)
    with pytest.raises(ValueError, match=r"Artifact set mismatch|traversal"):
        validate_benchmark_manifest(manifest_path)


def test_candidate_rejects_symlink_escape_when_supported(
    tmp_path: Path, built_candidate: tuple[Path, CandidateManifest, Path]
) -> None:
    manifest_path = _copy_candidate(built_candidate[0], tmp_path / "symlink-escape")
    item_path = manifest_path.parent / "items.jsonl"
    outside = tmp_path / "outside-items.jsonl"
    shutil.copyfile(item_path, outside)
    item_path.unlink()
    try:
        os.symlink(outside, item_path)
    except OSError as exc:
        pytest.skip(f"Symlink creation is unavailable: {exc}")
    with pytest.raises(ValueError, match="escapes"):
        validate_benchmark_manifest(manifest_path)


def test_public_leakage_scan_rejects_equivalent_field_and_secret_values(
    built_candidate: tuple[Path, CandidateManifest, Path],
) -> None:
    root = built_candidate[0].parent
    items = read_jsonl_models(root / "items.jsonl", BuiltBenchmarkItem, require_canonical=True)
    answers = read_jsonl_models(
        root / "private_answers.jsonl", PrivateAnswerRecord, require_canonical=True
    )
    with pytest.raises(ValueError, match="answer-equivalent"):
        assert_public_answer_isolation(({"gold-label": "redacted"},), answers, items)
    with pytest.raises(ValueError, match="private answer or item value"):
        assert_public_answer_isolation(
            ({"innocent_name": answers[0].correct_option_id},), answers, items
        )


def test_public_leakage_scan_covers_mapping_keys_lists_aliases_and_normalisation(
    built_candidate: tuple[Path, CandidateManifest, Path],
) -> None:
    root = built_candidate[0].parent
    items = read_jsonl_models(root / "items.jsonl", BuiltBenchmarkItem, require_canonical=True)
    answers = read_jsonl_models(
        root / "private_answers.jsonl", PrivateAnswerRecord, require_canonical=True
    )
    cases = (
        {answers[0].correct_option_id: 1},
        {"coverage": [items[0].model_visible.ordered_options[0].option_id]},
        {"nested": [{"values": [items[0].model_visible.prompt]}]},
        {"alias": f"prefix::{answers[0].answer_rationale}::suffix"},
        {"target-choice-id": "redacted"},
        {"alias": "  THE\r\n DISPLAYED   CODE IS k7.  "},
    )
    for value in cases:
        with pytest.raises(ValueError, match=r"answer-equivalent|private answer or item"):
            assert_public_answer_isolation((value,), answers, items)


def test_public_metadata_contains_no_per_item_answer_or_prompt_values(
    built_candidate: tuple[Path, CandidateManifest, Path],
) -> None:
    root = built_candidate[0].parent
    public_text = (root / "public_manifest.json").read_text(encoding="utf-8")
    coverage_text = (root / "coverage_summary.json").read_text(encoding="utf-8")
    private_answers = (root / "private_answers.jsonl").read_text(encoding="utf-8")
    assert "correct_option_id" in private_answers
    for prohibited in (
        "correct_option_id",
        "private_answer_record_sha256",
        "complete_private_item_record_sha256",
        "A card states code K7",
        "The displayed code is K7",
    ):
        assert prohibited not in public_text
        assert prohibited not in coverage_text


def test_candidate_overwrite_refusal_preserves_original_failure(
    built_candidate: tuple[Path, CandidateManifest, Path], engineering_source: Path
) -> None:
    manifest_path, _, repository = built_candidate
    with pytest.raises(BenchmarkOperationError) as raised:
        build_benchmark(
            source_directory=engineering_source,
            output_directory=manifest_path.parent,
            version="engineering-benchmark-lifecycle-v1",
            purpose=BenchmarkPurpose.ENGINEERING,
            repository_root=repository,
        )
    error = raised.value
    assert "FileExistsError" in str(error)
    assert error.failure_record_path is not None
    record = read_canonical_model(Path(error.failure_record_path), BenchmarkOperationRecord)
    assert record.status == "FAILED"
    assert record.failure_reason == str(error)
    assert record.lifecycle_state_after is None


def test_duplicate_item_ids_in_source_are_rejected(
    tmp_path: Path, engineering_source: Path
) -> None:
    source = tmp_path / "duplicate-source"
    shutil.copytree(engineering_source, source)
    lines = source.joinpath("items.jsonl").read_text(encoding="utf-8").splitlines()
    first = json.loads(lines[0])
    second = json.loads(lines[1])
    second["item_id"] = first["item_id"]
    second["provenance"]["created_from_source_record"] = first["item_id"]
    source.joinpath("items.jsonl").write_text(
        "\n".join(json.dumps(item) for item in (first, second)) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    with pytest.raises(ValueError, match="Duplicate stable item IDs"):
        load_source_directory(
            source,
            benchmark_version="engineering-benchmark-lifecycle-v1",
            purpose=BenchmarkPurpose.ENGINEERING,
        )


def test_operation_budget_reports_all_unused_scientific_resources_as_zero(
    built_candidate: tuple[Path, CandidateManifest, Path],
) -> None:
    operation = read_canonical_model(
        built_candidate[0].parent / "operation_record.json", BenchmarkOperationRecord
    )
    budget = operation.resource_budget
    for field in (
        "external_language_tokens",
        "self_generated_language_tokens",
        "sensor_observations",
        "sensor_bytes",
        "environment_steps",
        "optimisation_steps",
        "forward_passes",
        "backward_passes",
    ):
        assert getattr(budget, field) == 0
        assert budget.measurement_basis[field].status == "observed_zero"
    assert budget.measurement_basis["elapsed_compute_seconds"].status == "measured"
    assert "time.perf_counter" in budget.measurement_basis["elapsed_compute_seconds"].method
    assert budget.measurement_basis["stored_artifact_bytes"].status == "derived"


@pytest.mark.parametrize(
    "mutation",
    ("engineering_only", "git", "resolved_configuration", "input_hashes", "item_count"),
)
def test_coordinated_build_operation_mutation_remains_semantically_invalid(
    tmp_path: Path,
    built_candidate: tuple[Path, CandidateManifest, Path],
    mutation: str,
) -> None:
    manifest_path = _copy_candidate(built_candidate[0], tmp_path / f"operation-{mutation}")
    operation_path = manifest_path.parent / "operation_record.json"
    operation = read_canonical_model(operation_path, BenchmarkOperationRecord)
    if mutation == "engineering_only":
        changed = operation.model_copy(update={"engineering_only": False})
    elif mutation == "git":
        changed = operation.model_copy(
            update={"git": operation.git.model_copy(update={"dirty": not operation.git.dirty})}
        )
    elif mutation == "resolved_configuration":
        changed = operation.model_copy(
            update={
                "resolved_configuration": operation.resolved_configuration.model_copy(
                    update={"quarantine_scope_sha256": "f" * 64}
                )
            }
        )
    elif mutation == "input_hashes":
        changed = operation.model_copy(
            update={"input_hashes": {**operation.input_hashes, "unexpected": "f" * 64}}
        )
    else:
        changed = operation.model_copy(update={"item_count": operation.item_count + 1})
    write_canonical_json(operation_path, changed)
    _refresh_candidate_artifact(manifest_path, "operation_record.json")
    with pytest.raises(ValueError, match="Build operation provenance"):
        validate_benchmark_manifest(manifest_path)


def test_candidate_header_mutation_is_rejected_before_outer_metadata_can_mask_it(
    tmp_path: Path, built_candidate: tuple[Path, CandidateManifest, Path]
) -> None:
    manifest_path = _copy_candidate(built_candidate[0], tmp_path / "header-contradiction")
    manifest = read_canonical_model(manifest_path, CandidateManifest)
    write_canonical_json(
        manifest_path,
        manifest.model_copy(update={"scientific_eligible": not manifest.scientific_eligible}),
    )
    with pytest.raises(ValueError, match="Source snapshot header and candidate manifest mismatch"):
        validate_benchmark_manifest(manifest_path)


def test_standalone_resource_budget_requires_canonical_encoding(
    tmp_path: Path, built_candidate: tuple[Path, CandidateManifest, Path]
) -> None:
    manifest_path = _copy_candidate(built_candidate[0], tmp_path / "pretty-budget")
    budget_path = manifest_path.parent / "resource_budget.json"
    payload = json.loads(budget_path.read_text(encoding="utf-8"))
    budget_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8", newline="\n")
    _refresh_candidate_artifact(manifest_path, "resource_budget.json")
    with pytest.raises(ValueError, match="Non-canonical JSON encoding"):
        validate_benchmark_manifest(manifest_path)


def test_dry_run_writes_nothing(
    tmp_path: Path,
    engineering_source: Path,
    clean_benchmark_repository: Path,
) -> None:
    output = tmp_path / "dry-run-output"
    result = build_benchmark(
        source_directory=engineering_source,
        output_directory=output,
        version="engineering-benchmark-lifecycle-v1",
        purpose=BenchmarkPurpose.ENGINEERING,
        dry_run=True,
        repository_root=clean_benchmark_repository,
    )
    assert result.dry_run is True
    assert result.manifest_path is None
    assert not output.exists()
    assert not list(tmp_path.glob("*failure*"))


def test_gitignore_covers_representative_private_paths() -> None:
    paths = (
        "benchmarks/source/local-authoring/items.jsonl",
        "benchmarks/private/example/private_answers.jsonl",
        "benchmarks/frozen/example/items.jsonl",
        "benchmarks/selection/example/private_answers.jsonl",
    )
    for path in paths:
        completed = subprocess.run(
            ["git", "check-ignore", "-v", path], check=False, capture_output=True, text=True
        )
        assert completed.returncode == 0, path
        assert ".gitignore" in completed.stdout


@pytest.mark.parametrize(
    "unsafe_relative",
    (
        "private/demo/gold.json",
        "private/demo/answers.bin",
        "private/demo/questions.parquet",
        "private/demo/candidate-data.dat",
        "source/local/renamed-source-item.payload",
    ),
)
def test_git_audit_rejects_every_forced_tracked_unrecognised_file(
    tmp_path: Path, unsafe_relative: str
) -> None:
    repository = tmp_path / "audit-repository"
    for relative in (
        "benchmarks/README.md",
        "benchmarks/frozen/README.md",
        "benchmarks/private/README.md",
        "benchmarks/selection/README.md",
        "benchmarks/source/README.md",
    ):
        path = repository / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("safe\n", encoding="utf-8")
    unsafe = repository / "benchmarks" / unsafe_relative
    unsafe.parent.mkdir(parents=True)
    unsafe.write_text("synthetic\n", encoding="utf-8")
    subprocess.run(["git", "init"], cwd=repository, check=True, capture_output=True)
    subprocess.run(["git", "add", "-f", "."], cwd=repository, check=True)
    with pytest.raises(ValueError, match="README allowlist"):
        audit_tracked_benchmark_paths(repository)
