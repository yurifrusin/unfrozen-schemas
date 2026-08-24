"""Resource-accounting models for Milestone 0 and later extension."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ResourceBudget(BaseModel):
    """Separately accounted resources for one run or checkpoint."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["1"] = "1"
    run_id: str = Field(min_length=1)
    external_language_tokens: int = Field(default=0, ge=0)
    self_generated_language_tokens: int = Field(default=0, ge=0)
    sensor_observations: int = Field(default=0, ge=0)
    sensor_bytes: int = Field(default=0, ge=0)
    environment_steps: int = Field(default=0, ge=0)
    optimisation_steps: int = Field(default=0, ge=0)
    forward_passes: int = Field(default=0, ge=0)
    backward_passes: int = Field(default=0, ge=0)
    elapsed_compute_seconds: float = Field(default=0.0, ge=0.0)
    peak_memory_bytes: int = Field(default=0, ge=0)
    stored_artifact_count: int = Field(default=0, ge=0)
    stored_artifact_bytes: int = Field(default=0, ge=0)
    stored_artifact_scope: Literal[
        "hash-stable run files excluding the self-referential provenance manifest"
    ] = "hash-stable run files excluding the self-referential provenance manifest"
