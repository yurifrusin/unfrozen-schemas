"""Resource-accounting models for Milestone 0 and later extension."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

ResourceField = Literal[
    "external_language_tokens",
    "self_generated_language_tokens",
    "sensor_observations",
    "sensor_bytes",
    "environment_steps",
    "optimisation_steps",
    "forward_passes",
    "backward_passes",
    "elapsed_compute_seconds",
    "peak_memory_bytes",
    "stored_artifact_count",
    "stored_artifact_bytes",
]

RESOURCE_FIELDS: tuple[ResourceField, ...] = (
    "external_language_tokens",
    "self_generated_language_tokens",
    "sensor_observations",
    "sensor_bytes",
    "environment_steps",
    "optimisation_steps",
    "forward_passes",
    "backward_passes",
    "elapsed_compute_seconds",
    "peak_memory_bytes",
    "stored_artifact_count",
    "stored_artifact_bytes",
)

MeasurementStatus = Literal["measured", "derived", "observed_zero", "unavailable"]


class ResourceMeasurementBasis(BaseModel):
    """How one resource value was obtained, including why it may be unavailable."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    status: MeasurementStatus
    method: str = Field(min_length=1)
    reason: str | None = None

    @model_validator(mode="after")
    def validate_unavailable_reason(self) -> ResourceMeasurementBasis:
        if self.status == "unavailable" and not self.reason:
            raise ValueError("An unavailable resource measurement requires a reason")
        return self


class ResourceBudget(BaseModel):
    """Separately accounted resources for one run or checkpoint interval."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["2"] = "2"
    run_id: str = Field(min_length=1)
    interval_kind: Literal["run", "checkpoint"]
    interval_start: datetime
    interval_end: datetime | None
    external_language_tokens: int | None = Field(ge=0)
    self_generated_language_tokens: int | None = Field(ge=0)
    sensor_observations: int | None = Field(ge=0)
    sensor_bytes: int | None = Field(ge=0)
    environment_steps: int | None = Field(ge=0)
    optimisation_steps: int | None = Field(ge=0)
    forward_passes: int | None = Field(ge=0)
    backward_passes: int | None = Field(ge=0)
    elapsed_compute_seconds: float | None = Field(ge=0.0)
    peak_memory_bytes: int | None = Field(ge=0)
    stored_artifact_count: int | None = Field(ge=0)
    stored_artifact_bytes: int | None = Field(ge=0)
    measurement_basis: dict[ResourceField, ResourceMeasurementBasis]
    stored_artifact_scope: Literal[
        "hash-stable run files excluding the self-referential provenance manifest"
    ] = "hash-stable run files excluding the self-referential provenance manifest"

    @model_validator(mode="after")
    def validate_interval_and_measurements(self) -> ResourceBudget:
        if self.interval_start.tzinfo is None or self.interval_start.utcoffset() is None:
            raise ValueError("Resource-budget interval_start must be timezone-aware")
        if self.interval_end is not None:
            if self.interval_end.tzinfo is None or self.interval_end.utcoffset() is None:
                raise ValueError("Resource-budget interval_end must be timezone-aware")
            if self.interval_end < self.interval_start:
                raise ValueError("Resource-budget interval_end cannot precede interval_start")

        expected_fields = set(RESOURCE_FIELDS)
        observed_fields = set(self.measurement_basis)
        if observed_fields != expected_fields:
            missing = sorted(expected_fields - observed_fields)
            unexpected = sorted(observed_fields - expected_fields)
            raise ValueError(
                "Resource measurement metadata must cover every resource field exactly once; "
                f"missing={missing}, unexpected={unexpected}"
            )

        for field_name in RESOURCE_FIELDS:
            value = getattr(self, field_name)
            basis = self.measurement_basis[field_name]
            if basis.status == "observed_zero" and value != 0:
                raise ValueError(f"Observed-zero resource {field_name} must equal zero")
            if basis.status == "unavailable" and value is not None:
                raise ValueError(f"Unavailable resource {field_name} must be null")
            if basis.status in {"measured", "derived"} and value is None:
                raise ValueError(f"{basis.status.title()} resource {field_name} cannot be null")
        return self
