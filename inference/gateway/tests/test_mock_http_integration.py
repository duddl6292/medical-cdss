"""Real HTTP tests from the FastAPI Gateway to development Mock MOSEC."""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from collections.abc import Iterator
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

import pytest
from fastapi.testclient import TestClient

from app import main
from app.clients import mosec_client

client = TestClient(main.app)


def _free_port() -> int:
    with socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM,
    ) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@pytest.fixture(scope="module")
def mock_mosec_url() -> Iterator[str]:
    """Start Mock MOSEC on an available local TCP port."""

    port = _free_port()
    url = f"http://127.0.0.1:{port}"

    repository_root = Path(__file__).resolve().parents[3]

    environment = os.environ.copy()
    environment["MOCK_TIMEOUT_SECONDS"] = "0.20"

    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "inference.mock_mosec.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--log-level",
            "error",
        ],
        cwd=repository_root,
        env=environment,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    deadline = time.monotonic() + 5.0

    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(
                "Mock MOSEC exited during test startup."
            )

        try:
            with urlopen(
                f"{url}/health",
                timeout=0.2,
            ) as response:
                if response.status == 200:
                    break
        except (OSError, URLError):
            time.sleep(0.02)
    else:
        process.terminate()
        raise RuntimeError(
            "Mock MOSEC did not become ready."
        )

    try:
        yield url
    finally:
        process.terminate()

        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=3)


def _request_payload(job_id: str) -> dict:
    return {
        "job_id": job_id,
        "case_id": "case-001",
        "input_uri": (
            "gs://uploads/case-001/input.nii.gz"
        ),
        "model_version": "bhsd-nnunet-v1.0.0",
        "parameters": {
            "threshold": 0.25,
            "min_component_size": 30,
        },
    }


@pytest.mark.parametrize(
    ("job_id", "status_code", "error_code"),
    [
        (
            "mock-http-500-001",
            502,
            "MOSEC_HTTP_ERROR",
        ),
        (
            "mock-invalid-json-001",
            502,
            "MOSEC_INVALID_JSON",
        ),
        (
            "mock-invalid-response-001",
            502,
            "MOSEC_INVALID_RESPONSE",
        ),
        (
            "mock-identity-mismatch-001",
            502,
            "MOSEC_IDENTITY_MISMATCH",
        ),
        (
            "mock-contract-violation-001",
            502,
            "MOSEC_CONTRACT_VIOLATION",
        ),
    ],
)
def test_gateway_maps_mock_mosec_http_failures(
    mock_mosec_url: str,
    monkeypatch,
    job_id: str,
    status_code: int,
    error_code: str,
) -> None:
    monkeypatch.setattr(
        mosec_client.settings,
        "mosec_url",
        mock_mosec_url,
    )

    monkeypatch.setattr(
        mosec_client.settings,
        "mosec_timeout_seconds",
        2.0,
    )

    response = client.post(
        "/api/v1/inference",
        json=_request_payload(job_id),
    )

    body = response.json()

    assert response.status_code == status_code
    assert body["status"] == "failed"
    assert body["job_id"] == job_id
    assert body["error"]["code"] == error_code


def test_gateway_maps_real_http_timeout(
    mock_mosec_url: str,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        mosec_client.settings,
        "mosec_url",
        mock_mosec_url,
    )

    monkeypatch.setattr(
        mosec_client.settings,
        "mosec_timeout_seconds",
        0.05,
    )

    response = client.post(
        "/api/v1/inference",
        json=_request_payload("mock-timeout-001"),
    )

    assert response.status_code == 504
    assert (
        response.json()["error"]["code"]
        == "MOSEC_TIMEOUT"
    )


def test_gateway_maps_real_connection_failure(
    monkeypatch,
) -> None:
    unavailable_url = (
        f"http://127.0.0.1:{_free_port()}"
    )

    monkeypatch.setattr(
        mosec_client.settings,
        "mosec_url",
        unavailable_url,
    )

    monkeypatch.setattr(
        mosec_client.settings,
        "mosec_timeout_seconds",
        0.2,
    )

    response = client.post(
        "/api/v1/inference",
        json=_request_payload(
            "job-unavailable-001"
        ),
    )

    assert response.status_code == 503
    assert (
        response.json()["error"]["code"]
        == "MOSEC_UNAVAILABLE"
    )