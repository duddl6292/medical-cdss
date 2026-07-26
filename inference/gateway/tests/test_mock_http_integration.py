"""Real HTTP tests from the Gateway to development Mock MOSEC."""

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


CLIENT = TestClient(main.app)
SCENARIO_JOB_IDS = {
    "http_500": "00000000-0000-4000-8000-000000000500",
    "invalid_json": "00000000-0000-4000-8000-000000000501",
    "invalid_response": "00000000-0000-4000-8000-000000000502",
    "identity_mismatch": (
        "00000000-0000-4000-8000-000000000503"
    ),
    "contract_violation": (
        "00000000-0000-4000-8000-000000000504"
    ),
    "timeout": "00000000-0000-4000-8000-000000000505",
}


def _free_port() -> int:
    with socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM,
    ) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@pytest.fixture(scope="module")
def mock_mosec_url() -> Iterator[str]:
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
        "schema_version": "1.0",
        "job_id": job_id,
        "case_id": 1,
        "input_uri": "gs://uploads/case-001/input.nii.gz",
        "model_version": "bhsd-nnunet-v1.0.0",
    }


def test_gateway_calls_mock_over_real_http(
    mock_mosec_url: str,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        mosec_client.settings,
        "mosec_url",
        mock_mosec_url,
    )

    response = CLIENT.post(
        "/api/v1/inference",
        json=_request_payload(
            "00000000-0000-4000-8000-000000000001"
        ),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "completed"


@pytest.mark.parametrize(
    ("scenario", "status_code", "error_code"),
    [
        ("http_500", 502, "MOSEC_HTTP_ERROR"),
        ("invalid_json", 502, "MOSEC_INVALID_JSON"),
        ("invalid_response", 502, "MOSEC_INVALID_RESPONSE"),
        ("identity_mismatch", 502, "MOSEC_IDENTITY_MISMATCH"),
        (
            "contract_violation",
            502,
            "MOSEC_CONTRACT_VIOLATION",
        ),
    ],
)
def test_gateway_maps_mock_mosec_failures(
    mock_mosec_url: str,
    monkeypatch,
    scenario: str,
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

    response = CLIENT.post(
        "/api/v1/inference",
        json=_request_payload(SCENARIO_JOB_IDS[scenario]),
    )

    assert response.status_code == status_code
    assert response.json()["error"]["code"] == error_code


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

    response = CLIENT.post(
        "/api/v1/inference",
        json=_request_payload(SCENARIO_JOB_IDS["timeout"]),
    )

    assert response.status_code == 504
    assert response.json()["error"]["code"] == "MOSEC_TIMEOUT"


def test_gateway_maps_real_connection_failure(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        mosec_client.settings,
        "mosec_url",
        f"http://127.0.0.1:{_free_port()}",
    )
    monkeypatch.setattr(
        mosec_client.settings,
        "mosec_timeout_seconds",
        0.2,
    )

    response = CLIENT.post(
        "/api/v1/inference",
        json=_request_payload(
            "00000000-0000-4000-8000-000000000006"
        ),
    )

    assert response.status_code == 503
    assert (
        response.json()["error"]["code"]
        == "MOSEC_UNAVAILABLE"
    )
