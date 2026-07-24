from typing import Any

from pydantic import BaseModel, Field


class InferenceRequest(BaseModel):
    job_id: str = Field(min_length=1)
    input_uri: str = Field(min_length=1)
    model_version: str = Field(min_length=1)

    threshold: float = Field(default=0.25, ge=0.0, le=1.0)
    min_component_size: int = Field(default=30, ge=0)


class InferenceResponse(BaseModel):
    job_id: str
    status: str
    model_version: str
    result: dict[str, Any]