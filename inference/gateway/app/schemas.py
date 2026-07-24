from typing import Literal

from pydantic import BaseModel, Field


class InferenceParameters(BaseModel):
    threshold: float = Field(default=0.25, ge=0.0, le=1.0)
    min_component_size: int = Field(default=30, ge=0)


class InferenceRequest(BaseModel):
    job_id: str = Field(min_length=1)
    case_id: str = Field(min_length=1)
    input_uri: str = Field(min_length=1)
    model_version: str = Field(min_length=1)
    parameters: InferenceParameters = Field(
        default_factory=InferenceParameters
    )


class PredictionResult(BaseModel):
    mask_uri: str | None = None
    preview_uri: str | None = None
    lesion_voxels: int = Field(ge=0)
    lesion_volume_ml: float = Field(ge=0.0)
    shape: list[int] = Field(min_length=3, max_length=3)
    spacing: list[float] = Field(min_length=3, max_length=3)
    preview_slice_index: int = Field(ge=0)


class TimingResult(BaseModel):
    preprocessing_seconds: float = Field(ge=0.0)
    inference_seconds: float = Field(ge=0.0)
    postprocessing_seconds: float = Field(ge=0.0)
    total_seconds: float = Field(ge=0.0)


class InferenceError(BaseModel):
    code: str
    message: str


class InferenceResponse(BaseModel):
    job_id: str
    case_id: str
    status: Literal["queued", "running", "completed", "failed"]
    model_version: str
    prediction: PredictionResult | None = None
    timing: TimingResult | None = None
    error: InferenceError | None = None