"""FastAPI Gateway for the strict MOSEC inference contract v1."""

import logging

from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.clients.mosec_client import (
    MosecClientError,
    MosecHTTPError,
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


RETRYABLE_GATEWAY_ERRORS = {
    "MOSEC_TIMEOUT",
    "MOSEC_UNAVAILABLE",
    "MOSEC_HTTP_ERROR",
}


def _failed_response(
    request: InferenceRequest,
    *,
    status_code: int,
    error_code: str,
    message: str,
    retryable: bool = False,
) -> JSONResponse:
    """Return a Gateway-generated failure in the same strict v1 shape."""

    content = {
        "schema_version": "1.0",
        "job_id": request.job_id,
        "case_id": request.case_id,
        "status": "failed",
        "model_version": request.model_version,
        "input": None,
        "model": None,
        "artifacts": None,
        "result": None,
        "performance": None,
        "summary": None,
        "message": None,
        "error": {
            "code": error_code,
            "message": message,
            "retryable": retryable,
        },
    }

    validated = InferenceResponse.model_validate(content)
    return JSONResponse(
        status_code=status_code,
        content=validated.model_dump(mode="json"),
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
    except MosecClientError as exc:
        is_contract_rejection = (
            isinstance(exc, MosecHTTPError)
            and exc.upstream_status_code == 422
        )
        error_code = (
            "MOSEC_REQUEST_REJECTED"
            if is_contract_rejection
            else exc.error_code
        )
        status_code = (
            status.HTTP_422_UNPROCESSABLE_CONTENT
            if is_contract_rejection
            else exc.status_code
        )
        logger.warning(
            "MOSEC request failed: code=%s message=%s",
            error_code,
            str(exc),
        )
        return _failed_response(
            request,
            status_code=status_code,
            error_code=error_code,
            message=str(exc),
            retryable=(
                error_code in RETRYABLE_GATEWAY_ERRORS
                and not is_contract_rejection
            ),
        )

    try:
        response = InferenceResponse.model_validate(result)
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
                "MOSEC returned a response that violates contract v1."
            ),
        )

    if (
        response.job_id != request.job_id
        or response.case_id != request.case_id
    ):
        return _failed_response(
            request,
            status_code=status.HTTP_502_BAD_GATEWAY,
            error_code="MOSEC_IDENTITY_MISMATCH",
            message=(
                "MOSEC response identity does not match the request."
            ),
        )

    if response.model_version != request.model_version:
        return _failed_response(
            request,
            status_code=status.HTTP_502_BAD_GATEWAY,
            error_code="MOSEC_MODEL_VERSION_MISMATCH",
            message=(
                "MOSEC response model version does not match the request."
            ),
        )

    return response
