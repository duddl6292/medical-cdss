from typing import Any

import httpx

from app.config import settings
from app.schemas import InferenceRequest


class MosecClientError(RuntimeError):
    """MOSEC 호출 실패 시 사용하는 예외."""


async def request_inference(
    request: InferenceRequest,
) -> dict[str, Any]:
    url = f"{settings.mosec_url.rstrip('/')}/inference"

    payload = request.model_dump()

    try:
        async with httpx.AsyncClient(
            timeout=settings.mosec_timeout_seconds,
        ) as client:
            response = await client.post(
                url,
                json=payload,
            )
            response.raise_for_status()

    except httpx.TimeoutException as exc:
        raise MosecClientError(
            "MOSEC inference request timed out."
        ) from exc

    except httpx.HTTPStatusError as exc:
        raise MosecClientError(
            f"MOSEC returned HTTP {exc.response.status_code}."
        ) from exc

    except httpx.RequestError as exc:
        raise MosecClientError(
            "Could not connect to the MOSEC server."
        ) from exc

    try:
        result = response.json()
    except ValueError as exc:
        raise MosecClientError(
            "MOSEC returned an invalid JSON response."
        ) from exc

    if not isinstance(result, dict):
        raise MosecClientError(
            "MOSEC response must be a JSON object."
        )

    return result