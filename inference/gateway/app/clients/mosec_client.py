from typing import Any

import anyio
import httpx
from google.auth.transport.requests import Request
from google.oauth2 import id_token

from app.config import settings
from app.schemas import InferenceRequest


class MosecClientError(RuntimeError):
    """MOSEC 호출 실패 시 사용하는 기본 예외."""

    error_code = "MOSEC_CLIENT_ERROR"
    status_code = 502


class MosecTimeoutError(MosecClientError):
    """MOSEC 응답 시간이 제한을 초과한 경우."""

    error_code = "MOSEC_TIMEOUT"
    status_code = 504


class MosecUnavailableError(MosecClientError):
    """MOSEC 서버에 연결할 수 없는 경우."""

    error_code = "MOSEC_UNAVAILABLE"
    status_code = 503


class MosecHTTPError(MosecClientError):
    """MOSEC가 4xx 또는 5xx 상태를 반환한 경우."""

    error_code = "MOSEC_HTTP_ERROR"
    status_code = 502

    def __init__(
        self,
        message: str,
        *,
        upstream_status_code: int,
    ) -> None:
        super().__init__(message)
        self.upstream_status_code = upstream_status_code


class MosecInvalidJSONError(MosecClientError):
    """MOSEC 응답을 JSON으로 해석할 수 없는 경우."""

    error_code = "MOSEC_INVALID_JSON"
    status_code = 502


class MosecInvalidResponseError(MosecClientError):
    """MOSEC JSON 응답 형식이 올바르지 않은 경우."""

    error_code = "MOSEC_INVALID_RESPONSE"
    status_code = 502


def _fetch_id_token(audience: str) -> str:
    return id_token.fetch_id_token(Request(), audience)


async def _authorization_headers() -> dict[str, str]:
    audience = settings.mosec_audience.strip()
    if not audience:
        return {}

    token = await anyio.to_thread.run_sync(
        _fetch_id_token,
        audience,
    )
    return {"Authorization": f"Bearer {token}"}


async def request_inference(
    request: InferenceRequest,
) -> dict[str, Any]:
    """MOSEC 추론 서버에 비동기 추론 요청을 전송합니다."""

    url = f"{settings.mosec_url.rstrip('/')}/inference"
    payload = request.model_dump()

    try:
        async with httpx.AsyncClient(
            timeout=settings.mosec_timeout_seconds,
            trust_env=False,
        ) as client:
            response = await client.post(
                url,
                json=payload,
                headers=await _authorization_headers(),
            )

            response.raise_for_status()

    # 서버에 연결을 시도했지만 연결 시간이 초과된 경우
    except httpx.ConnectTimeout as exc:
        raise MosecUnavailableError(
            "Could not connect to the MOSEC server."
        ) from exc

    # 연결 후 응답 수신·전송 등의 시간이 초과된 경우
    except httpx.TimeoutException as exc:
        raise MosecTimeoutError(
            "MOSEC inference request timed out."
        ) from exc

    # MOSEC가 4xx 또는 5xx HTTP 상태를 반환한 경우
    except httpx.HTTPStatusError as exc:
        raise MosecHTTPError(
            f"MOSEC returned HTTP "
            f"{exc.response.status_code}.",
            upstream_status_code=exc.response.status_code,
        ) from exc

    # 연결 거부, DNS 오류, 네트워크 오류 등의 경우
    except httpx.RequestError as exc:
        raise MosecUnavailableError(
            "Could not connect to the MOSEC server."
        ) from exc

    # MOSEC URL 자체가 올바르지 않은 경우
    except httpx.InvalidURL as exc:
        raise MosecUnavailableError(
            "The configured MOSEC URL is invalid."
        ) from exc

    try:
        result = response.json()

    except ValueError as exc:
        raise MosecInvalidJSONError(
            "MOSEC returned an invalid JSON response."
        ) from exc

    if not isinstance(result, dict):
        raise MosecInvalidResponseError(
            "MOSEC response must be a JSON object."
        )

    return result
