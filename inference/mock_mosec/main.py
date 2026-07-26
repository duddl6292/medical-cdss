"""Runnable development-only substitute for the MOSEC HTTP contract."""

from __future__ import annotations

import asyncio
import os

from fastapi import FastAPI
from fastapi.responses import JSONResponse, PlainTextResponse, Response

from inference.gateway.app.schemas import (
    InferenceRequest,
    InferenceResponse,
)

app = FastAPI(
    title="Medical CDSS Mock MOSEC",
    version="0.1.0",
)

_SCENARIO_PREFIXES = {
    "mock-timeout": "timeout",
    "mock-http-500": "http_500",
    "mock-invalid-json": "invalid_json",
    "mock-invalid-response": "invalid_response",
    "mock-identity-mismatch": "identity_mismatch",
    "mock-contract-violation": "contract_violation",
}


def _artifact_uri(
    request: InferenceRequest,
    filename: str,
) -> str:
    prefix = os.getenv(
        "MOCK_RESULTS_URI_PREFIX",
        "gs://mock-medical-cdss/results",
    ).rstrip("/")
    return (
        f"{prefix}/{request.case_id}/{request.job_id}/{filename}"
    )


def _scenario(job_id: str) -> str | None:
    """Select a development-only failure from a reserved job-id prefix."""

    for prefix, scenario in _SCENARIO_PREFIXES.items():
        if job_id == prefix or job_id.startswith(f"{prefix}-"):
            return scenario
    return None


def _timeout_seconds() -> float:
    try:
        value = float(os.getenv("MOCK_TIMEOUT_SECONDS", "2"))
    except ValueError:
        return 2.0
    return max(0.01, min(value, 120.0))


def _completed_response(
    request: InferenceRequest,
) -> InferenceResponse:
    return InferenceResponse(
        job_id=request.job_id,
        case_id=request.case_id,
        status="completed",
        model_version=request.model_version,
        prediction={
            "mask_uri": _artifact_uri(
                request,
                "mask.nii.gz",
            ),
            "probability_uri": _artifact_uri(
                request,
                "probability.nii.gz",
            ),
            "entropy_uri": _artifact_uri(
                request,
                "entropy.nii.gz",
            ),
            "uncertainty_uri": _artifact_uri(
                request,
                "uncertainty.nii.gz",
            ),
            "result_uri": _artifact_uri(
                request,
                "result.json",
            ),
            "preview_uri": None,
            "lesion_voxels": 0,
            "lesion_volume_ml": 0.0,
            "lesion_slice_count": 0,
            "lesion_slice_indices": [],
            "bounding_box": None,
            "shape": [512, 512, 32],
            "spacing": [0.5, 0.5, 5.0],
            "preview_slice_index": 16,
        },
        timing={
            "preprocessing_seconds": 0.01,
            "inference_seconds": 0.01,
            "postprocessing_seconds": 0.01,
            "total_seconds": 0.03,
            "gpu_memory_measured": False,
            "gpu_peak_memory_mb": None,
        },
        postprocessing={
            "probability_threshold": (
                request.parameters.threshold
            ),
            "min_component_voxels": (
                request.parameters.min_component_size
            ),
            "connectivity": 26,
            "component_count_before": 0,
            "component_count_after": 0,
            "removed_component_count": 0,
            "removed_voxel_count": 0,
        },
        xai={
            "probability_definition": (
                "mock probability; no model inference was run"
            ),
            "entropy_definition": (
                "mock entropy; no model inference was run"
            ),
            "uncertainty_definition": (
                "mock uncertainty; no model inference was run"
            ),
            "value_range": [0.0, 1.0],
            "limitation": (
                "Development-only response. It contains no medical result."
            ),
        },
        error=None,
    )


@app.get("/health")
@app.get("/openapi")
async def health() -> dict[str, str | bool]:
    """Match the readiness path exposed by the real MOSEC runtime."""

    return {
        "status": "ready",
        "service": "mock-mosec",
        "mock": True,
    }


@app.post(
    "/inference",
    response_model=InferenceResponse,
)
async def inference(
    request: InferenceRequest,
) -> InferenceResponse | Response:
    """Return a deterministic contract-valid response without inference."""

    scenario = _scenario(request.job_id)

    if scenario == "timeout":
        await asyncio.sleep(_timeout_seconds())
    elif scenario == "http_500":
        return JSONResponse(
            status_code=500,
            content={
                "error": "Forced Mock MOSEC HTTP failure.",
            },
        )
    elif scenario == "invalid_json":
        return PlainTextResponse(
            "forced-invalid-json",
            status_code=200,
        )
    elif scenario == "invalid_response":
        return JSONResponse(
            status_code=200,
            content=["not", "a", "JSON", "object"],
        )

    response = _completed_response(request)

    if scenario == "identity_mismatch":
        return response.model_copy(
            update={"job_id": "different-job"},
        )
    if scenario == "contract_violation":
        payload = response.model_dump(mode="json")
        payload["prediction"]["lesion_voxels"] = -1
        return JSONResponse(
            status_code=200,
            content=payload,
        )

    return response