"""Django-to-Gateway inference orchestration.

Django owns the persisted job lifecycle. It calls only the FastAPI Gateway;
MOSEC and PostgreSQL never communicate directly.
"""

from __future__ import annotations

from time import perf_counter
from typing import Any

import httpx
from django.conf import settings
from django.db import transaction
from google.auth.transport.requests import Request
from google.oauth2 import id_token

from cases.models import Case

from .models import Prediction, PredictionResult


class PredictionDispatchError(RuntimeError):
    """Safe error returned when the Gateway request cannot be completed."""

    def __init__(
        self,
        *,
        code: str,
        message: str,
        retryable: bool,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = retryable


def _input_gs_uri(case: Case) -> str:
    bucket_name = settings.GS_BUCKET_NAME
    object_name = case.ct_file.name.lstrip("/")

    if not bucket_name or not object_name:
        raise PredictionDispatchError(
            code="INPUT_STORAGE_NOT_CONFIGURED",
            message=(
                "Cloud Storage must be configured before inference starts."
            ),
            retryable=False,
        )

    return f"gs://{bucket_name}/{object_name}"


def _gateway_payload(prediction: Prediction) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "job_id": str(prediction.job_id),
        "case_id": prediction.case.ct_id,
        "input_uri": _input_gs_uri(prediction.case),
        "model_version": settings.MODEL_VERSION,
    }


def _gateway_headers() -> dict[str, str]:
    audience = settings.INFERENCE_GATEWAY_AUDIENCE
    if not audience:
        return {}

    token = id_token.fetch_id_token(Request(), audience)
    return {"Authorization": f"Bearer {token}"}


def _request_gateway(prediction: Prediction) -> dict[str, Any]:
    try:
        response = httpx.post(
            settings.INFERENCE_GATEWAY_URL,
            json=_gateway_payload(prediction),
            headers=_gateway_headers(),
            timeout=settings.INFERENCE_TIMEOUT_SECONDS,
            trust_env=False,
        )
    except httpx.TimeoutException as error:
        raise PredictionDispatchError(
            code="GATEWAY_TIMEOUT",
            message="The inference Gateway request timed out.",
            retryable=True,
        ) from error
    except httpx.RequestError as error:
        raise PredictionDispatchError(
            code="GATEWAY_UNAVAILABLE",
            message="The inference Gateway is unavailable.",
            retryable=True,
        ) from error

    try:
        payload = response.json()
    except ValueError as error:
        raise PredictionDispatchError(
            code="GATEWAY_INVALID_JSON",
            message="The inference Gateway returned invalid JSON.",
            retryable=False,
        ) from error

    if not isinstance(payload, dict):
        raise PredictionDispatchError(
            code="GATEWAY_INVALID_RESPONSE",
            message="The inference Gateway returned an invalid response.",
            retryable=False,
        )

    if (
        payload.get("job_id") != str(prediction.job_id)
        or payload.get("case_id") != prediction.case.ct_id
    ):
        raise PredictionDispatchError(
            code="GATEWAY_IDENTITY_MISMATCH",
            message="The Gateway response does not match the prediction job.",
            retryable=False,
        )

    if payload.get("status") == "failed":
        failure = payload.get("error")
        if not isinstance(failure, dict):
            failure = {}
        raise PredictionDispatchError(
            code=str(failure.get("code") or "INFERENCE_FAILED"),
            message=str(
                failure.get("message")
                or "The inference service reported a failure."
            ),
            retryable=bool(failure.get("retryable", False)),
        )

    if response.is_error or payload.get("status") != "completed":
        raise PredictionDispatchError(
            code="GATEWAY_INVALID_RESPONSE",
            message="The inference Gateway returned an invalid response.",
            retryable=response.status_code >= 500,
        )

    return payload


def _complete_prediction(
    prediction: Prediction,
    payload: dict[str, Any],
    *,
    elapsed_seconds: float,
) -> None:
    model = payload["model"]
    artifacts = payload["artifacts"]
    result = payload["result"]
    performance = payload["performance"]

    with transaction.atomic():
        PredictionResult.objects.update_or_create(
            prediction=prediction,
            defaults={
                "model_id": model["model_id"],
                "model_version": model["model_version"],
                "folds": model["folds"],
                "checkpoint": model["checkpoint"],
                "mask_path": artifacts["mask_uri"],
                "result_json_uri": artifacts["result_json_uri"],
                "preview_uri": artifacts.get("preview_uri") or "",
                "probability_uri": (
                    artifacts.get("probability_uri") or ""
                ),
                "entropy_uri": artifacts.get("entropy_uri") or "",
                "uncertainty_uri": (
                    artifacts.get("uncertainty_uri") or ""
                ),
                "lesion_volume_ml": result["lesion_volume_ml"],
                "lesion_slice_count": result["lesion_slice_count"],
                "lesion_slice_start": result["lesion_slice_start"],
                "lesion_slice_end": result["lesion_slice_end"],
                "max_lesion_slice": result["max_lesion_slice"],
                "inference_time_seconds": (
                    performance["inference_seconds"]
                ),
                "gpu_peak_memory_mb": (
                    performance["gpu_peak_memory_mb"]
                ),
                "message": payload["message"],
            },
        )
        prediction.status = Prediction.Status.COMPLETED
        prediction.progress = 100
        prediction.elapsed_time = elapsed_seconds
        prediction.error_code = ""
        prediction.error_message = ""
        prediction.save(
            update_fields=[
                "status",
                "progress",
                "elapsed_time",
                "error_code",
                "error_message",
                "updated_at",
            ]
        )


def dispatch_prediction(prediction: Prediction) -> dict[str, Any]:
    """Run one synchronous v1 inference and persist its final state."""

    prediction.status = Prediction.Status.PROCESSING
    prediction.progress = 10
    prediction.error_code = ""
    prediction.error_message = ""
    prediction.save(
        update_fields=[
            "status",
            "progress",
            "error_code",
            "error_message",
            "updated_at",
        ]
    )

    started = perf_counter()
    try:
        payload = _request_gateway(prediction)
        elapsed_seconds = perf_counter() - started
        _complete_prediction(
            prediction,
            payload,
            elapsed_seconds=elapsed_seconds,
        )
        return payload
    except PredictionDispatchError as error:
        prediction.status = Prediction.Status.FAILED
        prediction.progress = 0
        prediction.elapsed_time = perf_counter() - started
        prediction.error_code = error.code
        prediction.error_message = error.message
        prediction.save(
            update_fields=[
                "status",
                "progress",
                "elapsed_time",
                "error_code",
                "error_message",
                "updated_at",
            ]
        )
        raise
