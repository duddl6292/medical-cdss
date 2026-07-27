"""Pydantic copy of the internal MOSEC v1 JSON contract.

The Gateway and MOSEC run in separate containers, so each runtime validates
the same wire contract with its native validation library. Contract examples
and tests prevent these two definitions from drifting.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    model_validator,
)


SchemaVersion = Literal["1.0"]
InferenceStatus = Literal["completed", "failed"]

NonEmptyText = Annotated[str, StringConstraints(min_length=1)]
JobId = Annotated[
    str,
    StringConstraints(
        pattern=(
            r"^[0-9a-fA-F]{8}-"
            r"[0-9a-fA-F]{4}-"
            r"[1-5][0-9a-fA-F]{3}-"
            r"[89abAB][0-9a-fA-F]{3}-"
            r"[0-9a-fA-F]{12}$"
        )
    ),
]
GcsNiftiUri = Annotated[
    str,
    StringConstraints(pattern=r"^gs://[^/]+/.+\.nii\.gz$"),
]
GcsObjectUri = Annotated[
    str,
    StringConstraints(pattern=r"^gs://[^/]+/.+$"),
]
GcsJsonUri = Annotated[
    str,
    StringConstraints(pattern=r"^gs://[^/]+/.+\.json$"),
]
PositiveInt = Annotated[int, Field(gt=0, strict=True)]
NonNegativeInt = Annotated[int, Field(ge=0, strict=True)]
PositiveFloat = Annotated[float, Field(gt=0.0)]
NonNegativeFloat = Annotated[float, Field(ge=0.0)]
ErrorCode = Annotated[
    str,
    StringConstraints(pattern=r"^[A-Z][A-Z0-9_]{2,63}$"),
]
FoldIdentifier = NonNegativeInt | Literal["all"]


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class InferenceRequest(ContractModel):
    """One synchronous inference request from Django through the Gateway."""

    schema_version: SchemaVersion
    job_id: JobId
    case_id: PositiveInt
    input_uri: GcsNiftiUri
    model_version: NonEmptyText


class InputInfo(ContractModel):
    """Validated spatial metadata of the input CT."""

    shape: tuple[PositiveInt, PositiveInt, PositiveInt]
    spacing_mm: tuple[PositiveFloat, PositiveFloat, PositiveFloat]


class ModelInfo(ContractModel):
    """Identity and fixed inference behavior of the loaded model."""

    model_id: NonEmptyText
    model_version: NonEmptyText
    trainer_name: NonEmptyText
    architecture: NonEmptyText
    folds: list[FoldIdentifier]
    checkpoint: NonEmptyText
    nnunet_configuration: Literal["2d"]
    input_mode: Literal["2.5D_3Slice"]
    slice_axis: Literal[2]
    context_offsets: tuple[Literal[-1], Literal[0], Literal[1]]
    boundary_policy: Literal["edge_replication"]
    target_policy: Literal["center_slice_mask"]
    segmentation_decision: Literal["nnunet_default_label_conversion"]

    @model_validator(mode="after")
    def validate_folds(self) -> "ModelInfo":
        if not self.folds:
            raise ValueError("model.folds must contain at least one fold.")
        if len(set(self.folds)) != len(self.folds):
            raise ValueError("model.folds must not contain duplicates.")
        if "all" in self.folds and len(self.folds) != 1:
            raise ValueError(
                "model.folds='all' cannot be combined with numeric folds."
            )
        return self


class ArtifactInfo(ContractModel):
    """Cloud Storage objects created by one successful inference."""

    mask_uri: GcsNiftiUri
    result_json_uri: GcsJsonUri
    preview_uri: GcsObjectUri | None = None
    probability_uri: GcsNiftiUri | None = None
    entropy_uri: GcsNiftiUri | None = None
    uncertainty_uri: GcsNiftiUri | None = None


class LesionResult(ContractModel):
    """Non-diagnostic measurements calculated from the binary mask."""

    lesion_detected: bool
    lesion_voxel_count: NonNegativeInt
    voxel_volume_mm3: PositiveFloat
    lesion_volume_mm3: NonNegativeFloat
    lesion_volume_ml: NonNegativeFloat
    lesion_slice_count: NonNegativeInt
    lesion_slice_indices: list[NonNegativeInt]
    lesion_slice_start: NonNegativeInt | None
    lesion_slice_end: NonNegativeInt | None
    max_lesion_slice: NonNegativeInt | None
    max_lesion_slice_voxel_count: NonNegativeInt
    slice_axis: Literal[2]
    slice_index_base: Literal[0]

    @model_validator(mode="after")
    def validate_lesion_consistency(self) -> "LesionResult":
        if self.lesion_slice_count != len(self.lesion_slice_indices):
            raise ValueError(
                "result.lesion_slice_count must equal the number of "
                "result.lesion_slice_indices."
            )

        if self.lesion_detected:
            if self.lesion_voxel_count == 0:
                raise ValueError(
                    "A detected lesion must have at least one lesion voxel."
                )
            if not self.lesion_slice_indices:
                raise ValueError(
                    "A detected lesion must have at least one lesion slice."
                )
            if self.lesion_slice_start != self.lesion_slice_indices[0]:
                raise ValueError(
                    "result.lesion_slice_start must be the first lesion slice."
                )
            if self.lesion_slice_end != self.lesion_slice_indices[-1]:
                raise ValueError(
                    "result.lesion_slice_end must be the last lesion slice."
                )
            if self.max_lesion_slice not in self.lesion_slice_indices:
                raise ValueError(
                    "result.max_lesion_slice must be a lesion slice."
                )
            if self.max_lesion_slice_voxel_count == 0:
                raise ValueError(
                    "A detected lesion must have a positive maximum "
                    "slice voxel count."
                )
            return self

        if (
            self.lesion_voxel_count != 0
            or self.lesion_volume_mm3 != 0.0
            or self.lesion_volume_ml != 0.0
            or self.lesion_slice_count != 0
            or self.lesion_slice_indices
            or self.lesion_slice_start is not None
            or self.lesion_slice_end is not None
            or self.max_lesion_slice is not None
            or self.max_lesion_slice_voxel_count != 0
        ):
            raise ValueError(
                "A non-detected lesion must contain zero measurements and "
                "null slice summary fields."
            )
        return self


class PerformanceResult(ContractModel):
    """Measured wall-clock phase times and optional CUDA peak memory."""

    input_download_seconds: NonNegativeFloat
    context_preparation_seconds: NonNegativeFloat
    inference_seconds: NonNegativeFloat
    postprocessing_seconds: NonNegativeFloat
    output_upload_seconds: NonNegativeFloat
    total_seconds: NonNegativeFloat
    gpu_memory_measured: bool
    gpu_peak_memory_mb: NonNegativeFloat | None

    @model_validator(mode="after")
    def validate_gpu_memory(self) -> "PerformanceResult":
        if self.gpu_memory_measured and self.gpu_peak_memory_mb is None:
            raise ValueError(
                "performance.gpu_peak_memory_mb is required when GPU "
                "memory was measured."
            )
        if not self.gpu_memory_measured and self.gpu_peak_memory_mb is not None:
            raise ValueError(
                "performance.gpu_peak_memory_mb must be null when GPU "
                "memory was not measured."
            )
        return self


class InferenceError(ContractModel):
    """Safe, machine-readable failure information."""

    code: ErrorCode
    message: NonEmptyText
    retryable: bool


class InferenceResponse(ContractModel):
    """Synchronous MOSEC/Gateway response for completion or failure."""

    schema_version: SchemaVersion
    job_id: JobId
    case_id: PositiveInt
    status: InferenceStatus
    model_version: NonEmptyText
    input: InputInfo | None = None
    model: ModelInfo | None = None
    artifacts: ArtifactInfo | None = None
    result: LesionResult | None = None
    performance: PerformanceResult | None = None
    summary: NonEmptyText | None = None
    message: NonEmptyText | None = None
    error: InferenceError | None = None

    @model_validator(mode="after")
    def validate_status_payload(self) -> "InferenceResponse":
        success_payload = (
            self.input,
            self.model,
            self.artifacts,
            self.result,
            self.performance,
            self.summary,
            self.message,
        )

        if self.status == "completed":
            if any(value is None for value in success_payload):
                raise ValueError(
                    "A completed response requires input, model, artifacts, "
                    "result, performance, summary and message."
                )
            if self.error is not None:
                raise ValueError(
                    "A completed response must not contain an error."
                )
            if (
                self.model is not None
                and self.model.model_version != self.model_version
            ):
                raise ValueError(
                    "Top-level model_version must equal model.model_version."
                )
            return self

        if any(value is not None for value in success_payload):
            raise ValueError(
                "A failed response must not contain success-only fields."
            )
        if self.error is None:
            raise ValueError("A failed response requires an error.")
        return self
