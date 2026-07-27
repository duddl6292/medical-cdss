import json
from copy import deepcopy
from pathlib import Path

from fastapi.testclient import TestClient

from app import main
from app.clients.mosec_client import MosecHTTPError


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
CONTRACTS_DIR = REPOSITORY_ROOT / "contracts"
CLIENT = TestClient(main.app)


def _load_json(name: str) -> dict:
    with (CONTRACTS_DIR / name).open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def test_gateway_returns_validated_mosec_response(
    monkeypatch,
) -> None:
    completed = _load_json("inference-response.example.json")

    async def fake_request_inference(_request):
        return deepcopy(completed)

    monkeypatch.setattr(
        main,
        "request_inference",
        fake_request_inference,
    )
    response = CLIENT.post(
        "/api/v1/inference",
        json=_load_json("inference-request.example.json"),
    )

    assert response.status_code == 200
    assert response.json() == completed


def test_gateway_rejects_mosec_identity_mismatch(
    monkeypatch,
) -> None:
    completed = _load_json("inference-response.example.json")
    completed["case_id"] = 2

    async def fake_request_inference(_request):
        return deepcopy(completed)

    monkeypatch.setattr(
        main,
        "request_inference",
        fake_request_inference,
    )
    response = CLIENT.post(
        "/api/v1/inference",
        json=_load_json("inference-request.example.json"),
    )

    assert response.status_code == 502
    assert (
        response.json()["error"]["code"]
        == "MOSEC_IDENTITY_MISMATCH"
    )


def test_gateway_rejects_model_version_mismatch(
    monkeypatch,
) -> None:
    completed = _load_json("inference-response.example.json")
    completed["model_version"] = "2.0.0"
    completed["model"]["model_version"] = "2.0.0"

    async def fake_request_inference(_request):
        return deepcopy(completed)

    monkeypatch.setattr(
        main,
        "request_inference",
        fake_request_inference,
    )
    response = CLIENT.post(
        "/api/v1/inference",
        json=_load_json("inference-request.example.json"),
    )

    assert response.status_code == 502
    assert (
        response.json()["error"]["code"]
        == "MOSEC_MODEL_VERSION_MISMATCH"
    )


def test_gateway_rejects_legacy_request() -> None:
    payload = _load_json("inference-request.example.json")
    payload["parameters"] = {"threshold": 0.25}

    response = CLIENT.post("/api/v1/inference", json=payload)

    assert response.status_code == 422


def test_gateway_preserves_mosec_contract_rejection(
    monkeypatch,
) -> None:
    async def fake_request_inference(_request):
        raise MosecHTTPError(
            "MOSEC returned HTTP 422.",
            upstream_status_code=422,
        )

    monkeypatch.setattr(
        main,
        "request_inference",
        fake_request_inference,
    )

    response = CLIENT.post(
        "/api/v1/inference",
        json=_load_json("inference-request.example.json"),
    )

    assert response.status_code == 422
    assert response.json()["status"] == "failed"
    assert response.json()["error"] == {
        "code": "MOSEC_REQUEST_REJECTED",
        "message": "MOSEC returned HTTP 422.",
        "retryable": False,
    }
