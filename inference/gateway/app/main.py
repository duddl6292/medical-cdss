import logging

from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.clients.mosec_client import (
    MosecClientError,
    request_inference,
)
from app.config import settings
from app.schemas import (
    InferenceRequest,
    InferenceResponse,
)


logger = logging.getLogger(__name__)


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
)


def _failed_response(
    request: InferenceRequest,
    *,
    status_code: int,
    error_code: str,
    message: str,
) -> JSONResponse:
    """
    Gateway 오류 응답을 공통 형식으로 생성합니다.

    HTTPException의 detail 필드를 사용하지 않으므로,
    오류 정보가 detail 내부에 중첩되지 않습니다.
    """

    content = {
        "job_id": request.job_id,
        "case_id": request.case_id,
        "status": "failed",
        "model_version": request.model_version,
        "prediction": None,
        "timing": None,
        "error": {
            "code": error_code,
            "message": message,
        },
    }

    return JSONResponse(
        status_code=status_code,
        content=content,
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
) -> InferenceResponse | JSONResponse:
    try:
        result = await request_inference(request)

    # MOSEC Client에서 분류한 오류를 Gateway 오류 형식으로 변환
    except MosecClientError as exc:
        logger.warning(
            "MOSEC request failed: code=%s message=%s",
            exc.error_code,
            str(exc),
        )

        return _failed_response(
            request,
            status_code=exc.status_code,
            error_code=exc.error_code,
            message=str(exc),
        )

    # MOSEC 응답이 현재 요청에 대한 결과인지 확인
    if (
        result.get("job_id") != request.job_id
        or result.get("case_id") != request.case_id
    ):
        return _failed_response(
            request,
            status_code=status.HTTP_502_BAD_GATEWAY,
            error_code="MOSEC_IDENTITY_MISMATCH",
            message=(
                "MOSEC response identity does not match "
                "the request."
            ),
        )

    response_payload = {
        "job_id": result["job_id"],
        "case_id": result["case_id"],
        "status": result.get(
            "status",
            "completed",
        ),
        "model_version": result.get(
            "model_version",
            request.model_version,
        ),
        "prediction": result.get("prediction"),
        "timing": result.get("timing"),
        "error": result.get("error"),
    }

    # 외부 서비스의 응답을 Gateway 응답 계약으로 검증
    try:
        return InferenceResponse.model_validate(
            response_payload,
        )

    except ValidationError as exc:
        logger.warning(
            "MOSEC response contract validation failed: %s",
            exc.errors(include_input=False),
        )

        return _failed_response(
            request,
            status_code=status.HTTP_502_BAD_GATEWAY,
            error_code="MOSEC_CONTRACT_VIOLATION",
            message=(
                "MOSEC returned a response that violates "
                "the contract."
            ),
        )