"""Validated JSON contract for the internal MOSEC inference endpoint."""

from __future__ import annotations

from typing import Annotated, Any, Literal

import msgspec


SCHEMA_VERSION = "1.0"

SchemaVersion = Literal["1.0"]
InferenceStatus = Literal["completed", "failed"]
FoldIdentifier = int | Literal["all"]

NonEmptyText = Annotated[str, msgspec.Meta(min_length=1)]
JobId = Annotated[
    str,
    msgspec.Meta(
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
    msgspec.Meta(pattern=r"^gs://[^/]+/.+\.nii\.gz$"),
]
GcsObjectUri = Annotated[
    str,
    msgspec.Meta(pattern=r"^gs://[^/]+/.+$"),
]
GcsJsonUri = Annotated[
    str,
    msgspec.Meta(pattern=r"^gs://[^/]+/.+\.json$"),
]
PositiveInt = Annotated[int, msgspec.Meta(gt=0)]
NonNegativeInt = Annotated[int, msgspec.Meta(ge=0)]
PositiveFloat = Annotated[float, msgspec.Meta(gt=0.0)]
NonNegativeFloat = Annotated[float, msgspec.Meta(ge=0.0)]
ErrorCode = Annotated[
    str,
    msgspec.Meta(pattern=r"^[A-Z][A-Z0-9_]{2,63}$"),
]


class InferenceRequest(
    msgspec.Struct,
    forbid_unknown_fields=True,
    kw_only=True,
):
    """One synchronous inference request from Gateway to MOSEC."""

    schema_version: SchemaVersion
    job_id: JobId
    case_id: PositiveInt
    input_uri: GcsNiftiUri
    model_version: NonEmptyText


class InputInfo(
    msgspec.Struct,
    forbid_unknown_fields=True,
    kw_only=True,
):
    """Validated spatial metadata of the input CT."""

    shape: tuple[PositiveInt, PositiveInt, PositiveInt]
    spacing_mm: tuple[PositiveFloat, PositiveFloat, PositiveFloat]


class ModelInfo(
    msgspec.Struct,
    forbid_unknown_fields=True,
    kw_only=True,
):
    """Identity of the model that produced the mask."""

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

    def __post_init__(self) -> None:
        if not self.folds:
            raise ValueError("model.folds must contain at least one fold.")
        if len(set(self.folds)) != len(self.folds):
            raise ValueError("model.folds must not contain duplicates.")
        if "all" in self.folds and len(self.folds) != 1:
            raise ValueError(
                "model.folds='all' cannot be combined with numeric folds."
            )
        for fold in self.folds:
            if isinstance(fold, int) and (
                isinstance(fold, bool) or fold < 0
            ):
                raise ValueError(
                    "Numeric model folds must be non-negative integers."
                )


class ArtifactInfo(
    msgspec.Struct,
    forbid_unknown_fields=True,
    kw_only=True,
):
    """Cloud Storage objects created by one successful inference."""

    mask_uri: GcsNiftiUri
    result_json_uri: GcsJsonUri
    preview_uri: GcsObjectUri | None = None
    probability_uri: GcsNiftiUri | None = None
    entropy_uri: GcsNiftiUri | None = None
    uncertainty_uri: GcsNiftiUri | None = None


class LesionResult(
    msgspec.Struct,
    forbid_unknown_fields=True,
    kw_only=True,
):
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

    def __post_init__(self) -> None:
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
            return

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


class PerformanceResult(
    msgspec.Struct,
    forbid_unknown_fields=True,
    kw_only=True,
):
    """Measured wall-clock phase times and optional CUDA peak memory."""

    input_download_seconds: NonNegativeFloat
    context_preparation_seconds: NonNegativeFloat
    inference_seconds: NonNegativeFloat
    postprocessing_seconds: NonNegativeFloat
    output_upload_seconds: NonNegativeFloat
    total_seconds: NonNegativeFloat
    gpu_memory_measured: bool
    gpu_peak_memory_mb: NonNegativeFloat | None

    def __post_init__(self) -> None:
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


class InferenceError(
    msgspec.Struct,
    forbid_unknown_fields=True,
    kw_only=True,
):
    """Safe, machine-readable failure information."""

    code: ErrorCode
    message: NonEmptyText
    retryable: bool


class InferenceResponse(
    msgspec.Struct,
    forbid_unknown_fields=True,
    kw_only=True,
):
    """Synchronous MOSEC response for either completion or failure."""

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

    def __post_init__(self) -> None:
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
            if self.model is not None:
                if self.model.model_version != self.model_version:
                    raise ValueError(
                        "Top-level model_version must equal "
                        "model.model_version."
                    )
            return

        if any(value is not None for value in success_payload):
            raise ValueError(
                "A failed response must not contain success-only fields."
            )
        if self.error is None:
            raise ValueError("A failed response requires an error.")


def validate_inference_request(data: object) -> InferenceRequest:
    """Convert MOSEC's decoded JSON object into a validated request."""

    return msgspec.convert(
        data,
        type=InferenceRequest,
        strict=True,
    )


def validate_inference_response(data: object) -> InferenceResponse:
    """Convert a built response object into the strict v1 response type."""

    return msgspec.convert(
        data,
        type=InferenceResponse,
        strict=True,
    )


def to_json_object(value: msgspec.Struct) -> dict[str, Any]:
    """Return plain JSON-compatible builtins for MOSEC's JSON encoder."""

    result = msgspec.to_builtins(value)
    if not isinstance(result, dict):
        raise TypeError("The inference contract root must be a JSON object.")
    return result
