"""Deterministic build, validation, approval, and write-once freeze operations."""

from __future__ import annotations

import os
import shutil
import stat
import time
import tracemalloc
import uuid
from contextlib import suppress
from datetime import datetime
from pathlib import Path
from typing import Literal

from unfrozen_schemas.budgets import (
    RESOURCE_FIELDS,
    ResourceBudget,
    ResourceField,
    ResourceMeasurementBasis,
)
from unfrozen_schemas.config import find_repository_root, sha256_file
from unfrozen_schemas.evaluation.benchmark_hashing import (
    bundle_hashes,
    derive_built_records,
    freeze_approval_hash,
    frozen_manifest_hash,
    public_metadata_bundle_hash,
)
from unfrozen_schemas.evaluation.benchmark_models import (
    ENGINEERING_VERSION,
    BenchmarkOperationError,
    BenchmarkOperationRecord,
    BenchmarkOperationResult,
    BenchmarkPurpose,
    CandidateManifest,
    FreezeApproval,
    FrozenManifest,
    ImmutableReceipt,
    LifecycleState,
    QuarantineScope,
    ResolvedBenchmarkConfig,
    ValidationReport,
)
from unfrozen_schemas.evaluation.benchmark_persistence import (
    make_artifact_records,
    read_canonical_model,
    resolve_candidate_version_path,
    resolve_frozen_version_path,
    write_canonical_json,
    write_canonical_jsonl,
)
from unfrozen_schemas.evaluation.benchmark_validation import (
    CANDIDATE_ARTIFACT_PATHS,
    CANDIDATE_BUDGET_PATHS,
    CANDIDATE_MANIFEST_FILENAME,
    FROZEN_BUDGET_PATHS,
    FROZEN_MANIFEST_FILENAME,
    VALIDATION_CHECKS,
    _load_candidate_payload,
    _load_frozen_payload,
    coverage_summary,
    create_quarantine_scope,
    ensure_lifecycle_transition,
    load_source_directory,
    public_manifest,
    validate_benchmark_manifest,
    validate_quarantine_scope_content,
    verify_freeze_approval,
)
from unfrozen_schemas.provenance import (
    GitState,
    capture_git_state,
    collect_package_versions,
    collect_platform_information,
    create_run_id,
    utc_now,
)


def _resolved_config(
    version: str,
    purpose: BenchmarkPurpose,
    quarantine_scope_sha256: str | None = None,
) -> ResolvedBenchmarkConfig:
    return ResolvedBenchmarkConfig(
        benchmark_version=version,
        purpose=purpose,
        quarantine_scope_sha256=quarantine_scope_sha256,
    )


def _basis(
    status: Literal["measured", "derived", "observed_zero", "unavailable"],
    method: str,
    reason: str | None = None,
) -> ResourceMeasurementBasis:
    return ResourceMeasurementBasis(status=status, method=method, reason=reason)


def _measurement_basis(peak_available: bool) -> dict[ResourceField, ResourceMeasurementBasis]:
    result: dict[ResourceField, ResourceMeasurementBasis] = {}
    for field in RESOURCE_FIELDS:
        if field in {
            "external_language_tokens",
            "self_generated_language_tokens",
            "sensor_observations",
            "sensor_bytes",
            "environment_steps",
            "optimisation_steps",
            "forward_passes",
            "backward_passes",
        }:
            result[field] = _basis(
                "observed_zero", "M2.1 benchmark lifecycle code-path observation"
            )
        elif field in {"stored_artifact_count", "stored_artifact_bytes"}:
            result[field] = _basis("derived", "sum of retained hash-stable operation files")
        elif field == "elapsed_compute_seconds":
            result[field] = _basis("measured", "time.perf_counter monotonic elapsed time")
        elif field == "peak_memory_bytes":
            result[field] = (
                _basis("measured", "tracemalloc peak traced Python allocations")
                if peak_available
                else _basis(
                    "unavailable",
                    "tracemalloc peak traced Python allocations",
                    "tracemalloc was unavailable for this operation",
                )
            )
        else:
            raise AssertionError(field)
    return result


def _budget(
    *,
    operation_id: str,
    started_at: datetime,
    ended_at: datetime,
    elapsed: float,
    peak_memory: int | None,
    artifact_count: int,
    artifact_bytes: int,
) -> ResourceBudget:
    return ResourceBudget(
        run_id=operation_id,
        interval_kind="run",
        interval_start=started_at,
        interval_end=ended_at,
        external_language_tokens=0,
        self_generated_language_tokens=0,
        sensor_observations=0,
        sensor_bytes=0,
        environment_steps=0,
        optimisation_steps=0,
        forward_passes=0,
        backward_passes=0,
        elapsed_compute_seconds=elapsed,
        peak_memory_bytes=peak_memory,
        stored_artifact_count=artifact_count,
        stored_artifact_bytes=artifact_bytes,
        measurement_basis=_measurement_basis(peak_memory is not None),
    )


def _stabilize_budget(
    *,
    budget_path: Path,
    stable_paths_without_budget: list[Path],
    operation_id: str,
    started_at: datetime,
    ended_at: datetime,
    elapsed: float,
    peak_memory: int | None,
) -> ResourceBudget:
    candidate = _budget(
        operation_id=operation_id,
        started_at=started_at,
        ended_at=ended_at,
        elapsed=elapsed,
        peak_memory=peak_memory,
        artifact_count=len(stable_paths_without_budget) + 1,
        artifact_bytes=sum(path.stat().st_size for path in stable_paths_without_budget),
    )
    for _ in range(16):
        write_canonical_json(budget_path, candidate)
        observed_bytes = sum(path.stat().st_size for path in stable_paths_without_budget)
        observed_bytes += budget_path.stat().st_size
        if observed_bytes == candidate.stored_artifact_bytes:
            return candidate
        candidate = candidate.model_copy(update={"stored_artifact_bytes": observed_bytes})
    raise RuntimeError("Benchmark resource-budget file size did not reach a stable value")


def _peak_and_restore(tracing_started_here: bool, tracing_was_active: bool) -> int | None:
    peak: int | None = None
    if tracemalloc.is_tracing():
        peak = tracemalloc.get_traced_memory()[1]
        if tracing_started_here:
            tracemalloc.stop()
    if tracing_was_active and not tracemalloc.is_tracing():
        tracemalloc.start()
    return peak


def _safe_remove_staging(staging: Path, parent: Path) -> None:
    if not staging.exists():
        return
    resolved_parent = parent.resolve()
    resolved_staging = staging.resolve()
    if resolved_staging.parent != resolved_parent or ".staging-" not in resolved_staging.name:
        raise RuntimeError(f"Refusing to remove unexpected staging directory: {staging}")
    shutil.rmtree(resolved_staging)


def _failure_record(
    *,
    output: Path,
    operation_id: str,
    operation_kind: Literal["build_benchmark", "freeze_benchmark"],
    version: str,
    purpose: BenchmarkPurpose,
    repository_root: Path,
    git: GitState,
    spec_hash: str,
    started_at: datetime,
    start_tick: float,
    peak_memory: int | None,
    failure_reason: str,
    item_count: int,
    input_hashes: dict[str, str],
    lifecycle_before: LifecycleState,
    quarantine_scope_sha256: str | None,
) -> str | None:
    try:
        ended_at = utc_now()
        operation = BenchmarkOperationRecord(
            operation_id=operation_id,
            operation_kind=operation_kind,
            engineering_only=purpose is BenchmarkPurpose.ENGINEERING,
            git=git,
            codex_spec_sha256=spec_hash,
            quarantine_scope_sha256=quarantine_scope_sha256,
            resolved_configuration=_resolved_config(version, purpose, quarantine_scope_sha256),
            input_hashes=dict(sorted(input_hashes.items())),
            lifecycle_state_before=lifecycle_before,
            lifecycle_state_after=None,
            benchmark_version=version,
            purpose=purpose,
            item_count=item_count,
            artifacts=(),
            package_versions=collect_package_versions(),
            platform=collect_platform_information(),
            started_at=started_at,
            ended_at=ended_at,
            status="FAILED",
            failure_reason=failure_reason,
            resource_budget=_budget(
                operation_id=operation_id,
                started_at=started_at,
                ended_at=ended_at,
                elapsed=time.perf_counter() - start_tick,
                peak_memory=peak_memory,
                artifact_count=0,
                artifact_bytes=0,
            ),
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        path = output.parent / f"{output.name}.{operation_kind}-failure-{operation_id}.json"
        write_canonical_json(path, operation)
        read_canonical_model(path, BenchmarkOperationRecord)
        return str(path)
    except Exception:
        return None


def build_benchmark(
    *,
    source_directory: Path,
    output_directory: Path,
    version: str,
    purpose: BenchmarkPurpose,
    dry_run: bool = False,
    repository_root: Path | None = None,
) -> BenchmarkOperationResult:
    """Build one deterministic PRIVATE candidate without overwriting any destination."""

    ensure_lifecycle_transition(LifecycleState.SOURCE, LifecycleState.PRIVATE)
    repository = (
        find_repository_root(Path.cwd()) if repository_root is None else repository_root.resolve()
    )
    operation_id = create_run_id("benchmark-build")
    started_at = utc_now()
    start_tick = time.perf_counter()
    tracing_was_active = tracemalloc.is_tracing()
    tracing_started_here = not tracing_was_active
    if tracing_started_here:
        tracemalloc.start()
    output = output_directory.resolve()
    staging = output.parent / f".{output.name}.staging-{uuid.uuid4().hex}"
    git = capture_git_state(repository)
    spec_hash = sha256_file(repository / "CODEX_SPEC.md")
    item_count = 0
    input_hashes: dict[str, str] = {}
    quarantine_scope: QuarantineScope | None = None
    published_quarantine: Path | None = None
    publication_cleanup_error: str | None = None
    published = False
    try:
        if purpose is not BenchmarkPurpose.ENGINEERING:
            expected_output = resolve_candidate_version_path(repository, version, purpose)
            if output != expected_output:
                raise ValueError(
                    "Non-engineering build destination must be the exact canonical "
                    f"purpose-specific directory: {expected_output}"
                )
        if output.exists():
            raise FileExistsError(f"PRIVATE candidate destination already exists: {output}")
        _, snapshot = load_source_directory(
            source_directory, benchmark_version=version, purpose=purpose
        )
        item_count = len(snapshot.items)
        quarantine_scope = create_quarantine_scope(
            snapshot.header.quarantine_scope,
            repository,
        )
        input_hashes = {
            "quarantine_scope_sha256": quarantine_scope.quarantine_scope_sha256,
            "source_snapshot_sha256": snapshot.source_snapshot_sha256,
        }
        records = tuple(derive_built_records(item) for item in snapshot.items)
        items = tuple(pair[0] for pair in records)
        answers = tuple(pair[1] for pair in records)
        validate_quarantine_scope_content(purpose, items, quarantine_scope)
        hashes = bundle_hashes(
            benchmark_version=version,
            purpose=purpose.value,
            source_snapshot_sha256=snapshot.source_snapshot_sha256,
            quarantine_scope_sha256=quarantine_scope.quarantine_scope_sha256,
            items=items,
            answers=answers,
        )
        coverage = coverage_summary(
            version=version,
            purpose=purpose,
            items=items,
            engineering_only=snapshot.header.engineering_only,
            scientific_eligible=snapshot.header.scientific_eligible,
        )
        public = public_manifest(
            version=version,
            purpose=purpose,
            items=items,
            engineering_only=snapshot.header.engineering_only,
            scientific_eligible=snapshot.header.scientific_eligible,
            promotable=snapshot.header.promotable,
            source_snapshot_sha256=snapshot.source_snapshot_sha256,
            quarantine_scope_sha256=quarantine_scope.quarantine_scope_sha256,
            hashes=hashes,
        )
        public_hash = public_metadata_bundle_hash(public, coverage)
        if dry_run:
            _peak_and_restore(tracing_started_here, tracing_was_active)
            return BenchmarkOperationResult(
                operation_id=operation_id,
                dry_run=True,
                benchmark_version=version,
                purpose=purpose,
                manifest_path=None,
                candidate_bundle_root_sha256=hashes["candidate_bundle_root_sha256"],
                private_answer_bundle_sha256=hashes["private_answer_bundle_sha256"],
                public_metadata_bundle_sha256=public_hash,
            )
        output.parent.mkdir(parents=True, exist_ok=True)
        staging.mkdir(parents=False, exist_ok=False)
        config = _resolved_config(version, purpose, quarantine_scope.quarantine_scope_sha256)
        paths = {
            "source_snapshot.json": staging / "source_snapshot.json",
            "items.jsonl": staging / "items.jsonl",
            "private_answers.jsonl": staging / "private_answers.jsonl",
            "public_manifest.json": staging / "public_manifest.json",
            "coverage_summary.json": staging / "coverage_summary.json",
            "resolved_benchmark_config.json": staging / "resolved_benchmark_config.json",
            "validation_report.json": staging / "validation_report.json",
            "resource_budget.json": staging / "resource_budget.json",
            "operation_record.json": staging / "operation_record.json",
            "quarantine_scope.json": staging / "quarantine_scope.json",
        }
        write_canonical_json(paths["source_snapshot.json"], snapshot)
        write_canonical_jsonl(paths["items.jsonl"], list(items))
        write_canonical_jsonl(paths["private_answers.jsonl"], list(answers))
        write_canonical_json(paths["public_manifest.json"], public)
        write_canonical_json(paths["coverage_summary.json"], coverage)
        write_canonical_json(paths["resolved_benchmark_config.json"], config)
        write_canonical_json(paths["quarantine_scope.json"], quarantine_scope)
        write_canonical_json(
            paths["validation_report.json"],
            ValidationReport(
                benchmark_version=version,
                lifecycle_state=LifecycleState.PRIVATE,
                purpose=purpose,
                item_count=len(items),
                checks=VALIDATION_CHECKS,
            ),
        )
        ended_at = utc_now()
        peak = _peak_and_restore(tracing_started_here, tracing_was_active)
        stable_without_budget = [
            path
            for name, path in paths.items()
            if name in CANDIDATE_BUDGET_PATHS - {"resource_budget.json"}
        ]
        budget = _stabilize_budget(
            budget_path=paths["resource_budget.json"],
            stable_paths_without_budget=stable_without_budget,
            operation_id=operation_id,
            started_at=started_at,
            ended_at=ended_at,
            elapsed=time.perf_counter() - start_tick,
            peak_memory=peak,
        )
        operation_artifacts = make_artifact_records(
            staging, [paths[name] for name in sorted(CANDIDATE_BUDGET_PATHS)]
        )
        operation = BenchmarkOperationRecord(
            operation_id=operation_id,
            operation_kind="build_benchmark",
            engineering_only=snapshot.header.engineering_only,
            git=git,
            codex_spec_sha256=spec_hash,
            quarantine_scope_sha256=quarantine_scope.quarantine_scope_sha256,
            resolved_configuration=config,
            input_hashes=input_hashes,
            lifecycle_state_before=LifecycleState.SOURCE,
            lifecycle_state_after=LifecycleState.PRIVATE,
            benchmark_version=version,
            purpose=purpose,
            item_count=len(items),
            artifacts=operation_artifacts,
            package_versions=collect_package_versions(),
            platform=collect_platform_information(),
            started_at=started_at,
            ended_at=ended_at,
            status="COMPLETED",
            failure_reason=None,
            resource_budget=budget,
        )
        write_canonical_json(paths["operation_record.json"], operation)
        candidate = CandidateManifest(
            benchmark_version=version,
            purpose=purpose,
            engineering_only=snapshot.header.engineering_only,
            scientific_eligible=snapshot.header.scientific_eligible,
            promotable=snapshot.header.promotable,
            source_snapshot_sha256=snapshot.source_snapshot_sha256,
            public_metadata_bundle_sha256=public_hash,
            quarantine_scope_sha256=quarantine_scope.quarantine_scope_sha256,
            codex_spec_sha256=spec_hash,
            git=git,
            item_count=len(items),
            item_ids=tuple(item.item_id for item in items),
            production_prerequisites=snapshot.header.production_prerequisites,
            rights_determination_reference=snapshot.header.rights_determination_reference,
            human_validation_reference=snapshot.header.human_validation_reference,
            ethics_determination_reference=snapshot.header.ethics_determination_reference,
            artifacts=make_artifact_records(
                staging, [paths[name] for name in sorted(CANDIDATE_ARTIFACT_PATHS)]
            ),
            **hashes,
        )
        manifest_path = staging / CANDIDATE_MANIFEST_FILENAME
        write_canonical_json(manifest_path, candidate)
        _load_candidate_payload(
            manifest_path,
            repository_root=repository,
            revalidate_quarantine=False,
            enforce_storage_location=False,
        )
        os.replace(staging, output)
        published = True
        _after_candidate_publication(output)
        published_manifest = output / CANDIDATE_MANIFEST_FILENAME
        _read_back_published_candidate(published_manifest, repository)
        return BenchmarkOperationResult(
            operation_id=operation_id,
            dry_run=False,
            benchmark_version=version,
            purpose=purpose,
            manifest_path=str(published_manifest),
            candidate_bundle_root_sha256=hashes["candidate_bundle_root_sha256"],
            private_answer_bundle_sha256=hashes["private_answer_bundle_sha256"],
            public_metadata_bundle_sha256=public_hash,
        )
    except Exception as exc:
        peak = _peak_and_restore(tracing_started_here, tracing_was_active)
        original_reason = f"{type(exc).__name__}: {exc}"
        if published and output.exists():
            try:
                published_quarantine = _quarantine_failed_publication(
                    output,
                    operation_id,
                    invalid_kind="private",
                )
            except Exception as cleanup_exc:
                publication_cleanup_error = f"{type(cleanup_exc).__name__}: {cleanup_exc}"
        with suppress(Exception):
            _safe_remove_staging(staging, output.parent)
        reason = original_reason
        failure_path = None
        if not dry_run:
            failure_path = _failure_record(
                output=output,
                operation_id=operation_id,
                operation_kind="build_benchmark",
                version=version,
                purpose=purpose,
                repository_root=repository,
                git=git,
                spec_hash=spec_hash,
                started_at=started_at,
                start_tick=start_tick,
                peak_memory=peak,
                failure_reason=reason,
                item_count=item_count,
                input_hashes=input_hashes,
                lifecycle_before=LifecycleState.SOURCE,
                quarantine_scope_sha256=(
                    quarantine_scope.quarantine_scope_sha256
                    if quarantine_scope is not None
                    else None
                ),
            )
        if published_quarantine is not None:
            reason += f"; invalid publication quarantined at {published_quarantine.name}"
        elif published and not output.exists():
            reason += "; invalid publication removed after quarantine move failure"
        if publication_cleanup_error is not None:
            reason += f"; secondary publication cleanup failure: {publication_cleanup_error}"
        raise BenchmarkOperationError(reason, failure_record_path=failure_path) from exc


def create_engineering_freeze_approval(
    *,
    candidate_manifest_path: Path,
    output_path: Path,
    signer: str,
    rationale: str = "Engineering-only M2.1 lifecycle verification; not scientific approval.",
    repository_root: Path | None = None,
) -> FreezeApproval:
    """Create an exact-hash engineering approval that cannot authorise production data."""

    repository = (
        find_repository_root(Path.cwd()) if repository_root is None else repository_root.resolve()
    )
    candidate = validate_benchmark_manifest(candidate_manifest_path, repository_root=repository)
    if not isinstance(candidate, CandidateManifest):
        raise ValueError("Engineering approval requires a PRIVATE candidate manifest")
    if candidate.benchmark_version != ENGINEERING_VERSION or not candidate.engineering_only:
        raise ValueError("Only the declared engineering lifecycle fixture may use this command")
    current_git = capture_git_state(repository)
    current_spec_hash = sha256_file(repository / "CODEX_SPEC.md")
    if current_git.dirty:
        raise ValueError("Engineering freeze approval requires a clean working tree")
    if current_git != candidate.git:
        raise ValueError("Current clean Git state does not match the candidate build")
    if current_spec_hash != candidate.codex_spec_sha256:
        raise ValueError("Current CODEX_SPEC.md hash does not match the candidate build")
    if output_path.exists():
        raise FileExistsError(f"Freeze approval destination already exists: {output_path}")
    provisional = FreezeApproval(
        approval_class="engineering_fixture",
        benchmark_version=candidate.benchmark_version,
        benchmark_purpose=candidate.purpose,
        engineering_only=True,
        candidate_manifest_sha256=sha256_file(candidate_manifest_path),
        candidate_bundle_root_sha256=candidate.candidate_bundle_root_sha256,
        private_answer_bundle_sha256=candidate.private_answer_bundle_sha256,
        public_metadata_bundle_sha256=candidate.public_metadata_bundle_sha256,
        quarantine_scope_sha256=candidate.quarantine_scope_sha256,
        codex_spec_sha256=candidate.codex_spec_sha256,
        git_commit=candidate.git.commit,
        rights_determination_reference=candidate.rights_determination_reference,
        human_validation_reference=candidate.human_validation_reference,
        ethics_determination_reference=candidate.ethics_determination_reference,
        decision="APPROVED",
        signer=signer,
        timestamp=utc_now(),
        rationale=rationale,
        approval_sha256="0" * 64,
    )
    approval = provisional.model_copy(update={"approval_sha256": freeze_approval_hash(provisional)})
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.parent / f".{output_path.name}.staging-{uuid.uuid4().hex}"
    write_canonical_json(temporary, approval)
    os.replace(temporary, output_path)
    restored = read_canonical_model(output_path, FreezeApproval)
    if freeze_approval_hash(restored) != restored.approval_sha256:
        raise RuntimeError("Persisted engineering freeze approval failed hash verification")
    return restored


def _after_candidate_publication(_output: Path) -> None:
    """Injection seam for the first instruction after PRIVATE publication."""


def _read_back_published_candidate(manifest_path: Path, repository_root: Path) -> None:
    validate_benchmark_manifest(manifest_path, repository_root=repository_root)


def _after_frozen_publication(_output: Path) -> None:
    """Injection seam for the first instruction after atomic publication."""


def _read_back_published_freeze(manifest_path: Path, repository_root: Path) -> None:
    validate_benchmark_manifest(manifest_path, repository_root=repository_root)


def _make_tree_writable(root: Path) -> None:
    for path in (root, *root.rglob("*")):
        with suppress(OSError):
            path.chmod(path.stat().st_mode | stat.S_IWUSR)


def _quarantine_failed_publication(
    output: Path,
    operation_id: str,
    *,
    invalid_kind: Literal["private", "frozen"],
) -> Path | None:
    """Move a published failure to a type-specific invalid name or remove it."""

    if not output.exists():
        return None
    quarantine = output.parent / f".{output.name}.invalid-{invalid_kind}-{operation_id}"
    if quarantine.exists():
        raise RuntimeError(f"Invalid-publication quarantine already exists: {quarantine}")
    try:
        os.replace(output, quarantine)
        return quarantine
    except Exception as replace_exc:
        try:
            shutil.move(str(output), str(quarantine))
            return quarantine
        except Exception as move_exc:
            try:
                _make_tree_writable(output)
                shutil.rmtree(output)
                return None
            except Exception as remove_exc:
                raise RuntimeError(
                    f"Unable to quarantine or remove failed {invalid_kind.upper()} publication; "
                    f"replace={replace_exc}; move={move_exc}; remove={remove_exc}"
                ) from remove_exc


def _apply_read_only_advisory(output: Path) -> tuple[str, ...]:
    """Apply advisory permissions without changing scientific operation success."""

    failures: list[str] = []
    for path in output.rglob("*"):
        if path.is_file():
            try:
                path.chmod(path.stat().st_mode & ~stat.S_IWUSR & ~stat.S_IWGRP & ~stat.S_IWOTH)
            except Exception as exc:
                failures.append(f"{path.name}: {exc}")
    return tuple(failures)


def freeze_benchmark(
    *,
    candidate_manifest_path: Path,
    approval_path: Path,
    output_directory: Path,
    dry_run: bool = False,
    repository_root: Path | None = None,
) -> BenchmarkOperationResult:
    """Publish one validated PRIVATE candidate as a write-once FROZEN version."""

    ensure_lifecycle_transition(LifecycleState.PRIVATE, LifecycleState.FROZEN)
    repository = (
        find_repository_root(Path.cwd()) if repository_root is None else repository_root.resolve()
    )
    operation_id = create_run_id("benchmark-freeze")
    started_at = utc_now()
    start_tick = time.perf_counter()
    tracing_was_active = tracemalloc.is_tracing()
    tracing_started_here = not tracing_was_active
    if tracing_started_here:
        tracemalloc.start()
    output = output_directory.resolve()
    staging = output.parent / f".{output.name}.staging-{uuid.uuid4().hex}"
    git = capture_git_state(repository)
    spec_hash = sha256_file(repository / "CODEX_SPEC.md")
    version = "unknown"
    purpose = BenchmarkPurpose.ENGINEERING
    item_count = 0
    input_hashes: dict[str, str] = {}
    published_quarantine: Path | None = None
    publication_cleanup_error: str | None = None
    published = False
    quarantine_scope_sha256: str | None = None
    try:
        if output.exists():
            raise FileExistsError(f"FROZEN benchmark destination already exists: {output}")
        candidate = validate_benchmark_manifest(candidate_manifest_path, repository_root=repository)
        if not isinstance(candidate, CandidateManifest):
            raise ValueError("freeze-benchmark requires a PRIVATE candidate manifest")
        version = candidate.benchmark_version
        purpose = candidate.purpose
        item_count = candidate.item_count
        quarantine_scope_sha256 = candidate.quarantine_scope_sha256
        if not candidate.engineering_only:
            expected_output = resolve_frozen_version_path(repository, version, purpose)
            if output != expected_output:
                raise ValueError(
                    "Non-engineering frozen destination must be the exact canonical directory: "
                    f"{expected_output}"
                )
        approval = read_canonical_model(approval_path, FreezeApproval)

        _, items, _ = _load_candidate_payload(candidate_manifest_path, repository_root=repository)
        verify_freeze_approval(candidate_manifest_path, candidate, items, approval)
        input_hashes = {
            "candidate_manifest_sha256": sha256_file(candidate_manifest_path),
            "candidate_bundle_root_sha256": candidate.candidate_bundle_root_sha256,
            "freeze_approval_sha256": approval.approval_sha256,
            "quarantine_scope_sha256": candidate.quarantine_scope_sha256,
        }
        if git != candidate.git or spec_hash != candidate.codex_spec_sha256:
            raise ValueError(
                "Current Git/specification state does not match the approved candidate"
            )
        if dry_run:
            _peak_and_restore(tracing_started_here, tracing_was_active)
            return BenchmarkOperationResult(
                operation_id=operation_id,
                dry_run=True,
                benchmark_version=version,
                purpose=purpose,
                manifest_path=None,
                candidate_bundle_root_sha256=candidate.candidate_bundle_root_sha256,
                private_answer_bundle_sha256=candidate.private_answer_bundle_sha256,
                public_metadata_bundle_sha256=candidate.public_metadata_bundle_sha256,
            )
        candidate_root = candidate_manifest_path.parent.resolve()
        if output == candidate_root or output.is_relative_to(candidate_root):
            raise ValueError("Frozen destination must be separate from the PRIVATE candidate")
        output.parent.mkdir(parents=True, exist_ok=True)
        staging.mkdir(parents=False, exist_ok=False)
        for relative in sorted(CANDIDATE_ARTIFACT_PATHS | {CANDIDATE_MANIFEST_FILENAME}):
            shutil.copyfile(candidate_root / relative, staging / relative)
        write_canonical_json(staging / "freeze_approval.json", approval)
        receipt = ImmutableReceipt(
            benchmark_version=version,
            purpose=purpose,
            candidate_manifest_sha256=sha256_file(candidate_manifest_path),
            candidate_bundle_root_sha256=candidate.candidate_bundle_root_sha256,
            freeze_approval_sha256=approval.approval_sha256,
            quarantine_scope_sha256=candidate.quarantine_scope_sha256,
        )
        write_canonical_json(staging / "immutable_receipt.json", receipt)
        freeze_budget_path = staging / "freeze_resource_budget.json"
        ended_at = utc_now()
        peak = _peak_and_restore(tracing_started_here, tracing_was_active)
        stable_without_budget = [
            staging / relative
            for relative in sorted(FROZEN_BUDGET_PATHS - {"freeze_resource_budget.json"})
        ]
        budget = _stabilize_budget(
            budget_path=freeze_budget_path,
            stable_paths_without_budget=stable_without_budget,
            operation_id=operation_id,
            started_at=started_at,
            ended_at=ended_at,
            elapsed=time.perf_counter() - start_tick,
            peak_memory=peak,
        )
        operation = BenchmarkOperationRecord(
            operation_id=operation_id,
            operation_kind="freeze_benchmark",
            engineering_only=candidate.engineering_only,
            git=git,
            codex_spec_sha256=spec_hash,
            quarantine_scope_sha256=candidate.quarantine_scope_sha256,
            resolved_configuration=_resolved_config(
                version, purpose, candidate.quarantine_scope_sha256
            ),
            input_hashes=input_hashes,
            lifecycle_state_before=LifecycleState.PRIVATE,
            lifecycle_state_after=LifecycleState.FROZEN,
            benchmark_version=version,
            purpose=purpose,
            item_count=item_count,
            artifacts=make_artifact_records(
                staging, [staging / relative for relative in sorted(FROZEN_BUDGET_PATHS)]
            ),
            package_versions=collect_package_versions(),
            platform=collect_platform_information(),
            started_at=started_at,
            ended_at=ended_at,
            status="COMPLETED",
            failure_reason=None,
            resource_budget=budget,
        )
        write_canonical_json(staging / "freeze_operation.json", operation)
        provisional = FrozenManifest(
            benchmark_version=version,
            purpose=purpose,
            engineering_only=candidate.engineering_only,
            scientific_eligible=candidate.scientific_eligible,
            promotable=candidate.promotable,
            item_count=candidate.item_count,
            candidate_manifest_sha256=sha256_file(candidate_manifest_path),
            candidate_bundle_root_sha256=candidate.candidate_bundle_root_sha256,
            private_answer_bundle_sha256=candidate.private_answer_bundle_sha256,
            public_metadata_bundle_sha256=candidate.public_metadata_bundle_sha256,
            quarantine_scope_sha256=candidate.quarantine_scope_sha256,
            freeze_approval_sha256=approval.approval_sha256,
            codex_spec_sha256=candidate.codex_spec_sha256,
            git_commit=candidate.git.commit,
            artifacts=make_artifact_records(
                staging,
                [
                    staging / relative
                    for relative in sorted(
                        CANDIDATE_ARTIFACT_PATHS
                        | {
                            CANDIDATE_MANIFEST_FILENAME,
                            "freeze_approval.json",
                            "freeze_operation.json",
                            "freeze_resource_budget.json",
                            "immutable_receipt.json",
                        }
                    )
                ],
            ),
            frozen_manifest_sha256="0" * 64,
        )
        frozen = provisional.model_copy(
            update={"frozen_manifest_sha256": frozen_manifest_hash(provisional)}
        )
        staging_manifest = staging / FROZEN_MANIFEST_FILENAME
        write_canonical_json(staging_manifest, frozen)
        final_candidate, final_items, _ = _load_candidate_payload(
            candidate_manifest_path,
            repository_root=repository,
            transient_staging_roots=(staging,),
        )
        if final_candidate != candidate:
            raise ValueError("PRIVATE candidate changed during freeze construction")
        verify_freeze_approval(candidate_manifest_path, candidate, final_items, approval)
        _load_frozen_payload(
            staging_manifest,
            repository_root=repository,
            revalidate_quarantine=False,
            enforce_storage_location=False,
        )
        os.replace(staging, output)
        published = True
        _after_frozen_publication(output)
        published_manifest = output / FROZEN_MANIFEST_FILENAME
        _read_back_published_freeze(published_manifest, repository)
        _apply_read_only_advisory(output)
        return BenchmarkOperationResult(
            operation_id=operation_id,
            dry_run=False,
            benchmark_version=version,
            purpose=purpose,
            manifest_path=str(published_manifest),
            candidate_bundle_root_sha256=candidate.candidate_bundle_root_sha256,
            private_answer_bundle_sha256=candidate.private_answer_bundle_sha256,
            public_metadata_bundle_sha256=candidate.public_metadata_bundle_sha256,
        )
    except Exception as exc:
        peak = _peak_and_restore(tracing_started_here, tracing_was_active)
        original_reason = f"{type(exc).__name__}: {exc}"
        if published and output.exists():
            try:
                published_quarantine = _quarantine_failed_publication(
                    output,
                    operation_id,
                    invalid_kind="frozen",
                )
            except Exception as cleanup_exc:
                publication_cleanup_error = f"{type(cleanup_exc).__name__}: {cleanup_exc}"
        with suppress(Exception):
            _safe_remove_staging(staging, output.parent)
        reason = original_reason
        failure_path = None
        if not dry_run:
            failure_path = _failure_record(
                output=output,
                operation_id=operation_id,
                operation_kind="freeze_benchmark",
                version=version,
                purpose=purpose,
                repository_root=repository,
                git=git,
                spec_hash=spec_hash,
                started_at=started_at,
                start_tick=start_tick,
                peak_memory=peak,
                failure_reason=reason,
                item_count=item_count,
                input_hashes=input_hashes,
                lifecycle_before=LifecycleState.PRIVATE,
                quarantine_scope_sha256=quarantine_scope_sha256,
            )
        if published_quarantine is not None:
            reason += f"; invalid publication quarantined at {published_quarantine.name}"
        elif published and not output.exists():
            reason += "; invalid publication removed after quarantine move failure"
        if publication_cleanup_error is not None:
            reason += f"; secondary publication cleanup failure: {publication_cleanup_error}"
        raise BenchmarkOperationError(reason, failure_record_path=failure_path) from exc
