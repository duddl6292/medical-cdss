"""Contract tests for the internal MOSEC JSON schema."""

from __future__ import annotations

import json
from pathlib import Path

import msgspec
import pytest

from inference.app.schemas import (
    InferenceResponse,
    validate_inference_request,
    validate_inference_response,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CONTRACTS_DIR = REPOSITORY_ROOT / "contracts"


def _load_json(name: str) -> dict:
    with (CONTRACTS_DIR / name).open("r", encoding="utf-8") as file:
        return json.load(file)


def test_request_example_matches_worker_schema() -> None:
    request = validate_inference_request(
        _load_json("inference-request.example.json")
    )

    assert request.schema_version == "1.0"
    assert request.case_id == 1


def test_completed_response_example_matches_worker_schema() -> None:
    response = validate_inference_response(
        _load_json("inference-response.example.json")
    )

    assert isinstance(response, InferenceResponse)
    assert response.status == "completed"
    assert response.error is None
    assert (
        response.model is not None
        and response.model.trainer_name
        == "nnUNetTrainerBHSD_Exp05_25DFinal"
    )


def test_request_rejects_ignored_postprocessing_parameters() -> None:
    payload = _load_json("inference-request.example.json")
    payload["parameters"] = {
        "threshold": 0.25,
        "min_component_size": 30,
    }

    with pytest.raises(msgspec.ValidationError):
        validate_inference_request(payload)


def test_request_rejects_non_gcs_nifti_input() -> None:
    payload = _load_json("inference-request.example.json")
    payload["input_uri"] = "C:/patient/image.nii.gz"

    with pytest.raises(msgspec.ValidationError):
        validate_inference_request(payload)


def test_completed_response_requires_success_payload() -> None:
    payload = _load_json("inference-response.example.json")
    payload["artifacts"] = None

    with pytest.raises(msgspec.ValidationError):
        validate_inference_response(payload)


def test_failed_response_requires_error_and_null_success_fields() -> None:
    payload = {
        "schema_version": "1.0",
        "job_id": "550e8400-e29b-41d4-a716-446655440000",
        "case_id": 1,
        "status": "failed",
        "model_version": "1.0.0",
        "input": None,
        "model": None,
        "artifacts": None,
        "result": None,
        "performance": None,
        "summary": None,
        "message": None,
        "error": {
            "code": "INVALID_NIFTI_DIMENSION",
            "message": (
                "The input NIfTI volume must be three-dimensional."
            ),
            "retryable": False,
        },
    }

    response = validate_inference_response(payload)

    assert response.status == "failed"
    assert response.error is not None
    assert response.error.retryable is False


def test_failed_response_rejects_success_payload() -> None:
    payload = _load_json("inference-response.example.json")
    payload["status"] = "failed"
    payload["error"] = {
        "code": "MODEL_PREDICTION_FAILED",
        "message": "nnU-Net inference failed.",
        "retryable": True,
    }

    with pytest.raises(msgspec.ValidationError):
        validate_inference_response(payload)


def test_model_rejects_mixed_all_and_numeric_folds() -> None:
    payload = _load_json("inference-response.example.json")
    payload["model"]["folds"] = ["all", 0]

    with pytest.raises(msgspec.ValidationError):
        validate_inference_response(payload)


def test_model_requires_latest_dev_trainer_identity() -> None:
    payload = _load_json("inference-response.example.json")
    del payload["model"]["trainer_name"]

    with pytest.raises(msgspec.ValidationError):
        validate_inference_response(payload)
