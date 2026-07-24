from fastapi import FastAPI, HTTPException, status

from app.clients.mosec_client import (
    MosecClientError,
    request_inference,
)
from app.config import settings
from app.schemas import (
    InferenceRequest,
    InferenceResponse,
)


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "inference-gateway",
    }


@app.post(
    "/api/v1/inference",
    response_model=InferenceResponse,
)
async def run_inference(
    request: InferenceRequest,
) -> InferenceResponse:
    try:
        result = await request_inference(request)

    except MosecClientError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    return InferenceResponse(
    job_id=request.job_id,
    case_id=request.case_id,
    status=result.get("status", "completed"),
    model_version=request.model_version,
    prediction=result.get("prediction"),
    timing=result.get("timing"),
    error=result.get("error"),
)