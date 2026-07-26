"""Development-only strict v1 substitute for the MOSEC service."""

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
    version="1.0.0",
)

SCENARIO_JOB_IDS = {
    "00000000-0000-4000-8000-000000000500": "http_500",
    "00000000-0000-4000-8000-000000000501": "invalid_json",
    "00000000-0000-4000-8000-000000000502": "invalid_response",
    "00000000-0000-4000-8000-000000000503": "identity_mismatch",
    "00000000-0000-4000-8000-000000000504": "contract_violation",
    "00000000-0000-4000-8000-000000000505": "timeout",
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
        schema_version="1.0",
        job_id=request.job_id,
        case_id=request.case_id,
        status="completed",
        model_version=request.model_version,
        input={
            "shape": [512, 512, 32],
            "spacing_mm": [0.5, 0.5, 5.0],
        },
        model={
            "model_id": "mock-exp05-model",
            "model_version": request.model_version,
            "trainer_name": "nnUNetTrainerBHSD_Exp05_25DFinal",
            "architecture": "PlainConvUNet",
            "folds": [0],
            "checkpoint": "checkpoint_best.pth",
            "nnunet_configuration": "2d",
            "input_mode": "2.5D_3Slice",
            "slice_axis": 2,
            "context_offsets": [-1, 0, 1],
            "boundary_policy": "edge_replication",
            "target_policy": "center_slice_mask",
            "segmentation_decision": (
                "nnunet_default_label_conversion"
            ),
        },
        artifacts={
            "mask_uri": _artifact_uri(
                request,
                "mask.nii.gz",
            ),
            "result_json_uri": _artifact_uri(
                request,
                "result.json",
            ),
            "preview_uri": None,
            "probability_uri": None,
            "entropy_uri": None,
            "uncertainty_uri": None,
        },
        result={
            "lesion_detected": False,
            "lesion_voxel_count": 0,
            "voxel_volume_mm3": 1.25,
            "lesion_volume_mm3": 0.0,
            "lesion_volume_ml": 0.0,
            "lesion_slice_count": 0,
            "lesion_slice_indices": [],
            "lesion_slice_start": None,
            "lesion_slice_end": None,
            "max_lesion_slice": None,
            "max_lesion_slice_voxel_count": 0,
            "slice_axis": 2,
            "slice_index_base": 0,
        },
        performance={
            "input_download_seconds": 0.01,
            "context_preparation_seconds": 0.01,
            "inference_seconds": 0.01,
            "postprocessing_seconds": 0.01,
            "output_upload_seconds": 0.01,
            "total_seconds": 0.05,
            "gpu_memory_measured": False,
            "gpu_peak_memory_mb": None,
        },
        summary=(
            "개발용 Mock 응답이며 실제 의료 영상 추론을 "
            "수행하지 않았습니다."
        ),
        message=(
            "AI 분석 결과이며 의료진의 최종 진단을 "
            "대체하지 않습니다."
        ),
        error=None,
    )


@app.get("/health")
@app.get("/openapi")
async def health() -> dict[str, str | bool]:
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
    scenario = SCENARIO_JOB_IDS.get(request.job_id)

    if scenario == "timeout":
        await asyncio.sleep(_timeout_seconds())
    elif scenario == "http_500":
        return JSONResponse(
            status_code=500,
            content={"error": "Forced Mock MOSEC HTTP failure."},
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
            update={
                "job_id": (
                    "00000000-0000-4000-8000-000000000599"
                )
            },
        )
    if scenario == "contract_violation":
        payload = response.model_dump(mode="json")
        payload["result"]["lesion_voxel_count"] = -1
        return JSONResponse(status_code=200, content=payload)

    return response
