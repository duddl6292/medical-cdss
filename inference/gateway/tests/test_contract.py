import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.schemas import InferenceRequest, InferenceResponse


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
CONTRACTS_DIR = REPOSITORY_ROOT / "contracts"


def _load_json(name: str) -> dict:
    with (CONTRACTS_DIR / name).open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def test_examples_match_gateway_schema() -> None:
    request = InferenceRequest.model_validate(
        _load_json("inference-request.example.json")
    )
    response = InferenceResponse.model_validate(
        _load_json("inference-response.example.json")
    )

    assert request.schema_version == "1.0"
    assert request.case_id == 1
    assert response.status == "completed"


def test_gateway_rejects_legacy_parameters() -> None:
    payload = _load_json("inference-request.example.json")
    payload["parameters"] = {
        "threshold": 0.25,
        "min_component_size": 30,
    }

    with pytest.raises(ValidationError):
        InferenceRequest.model_validate(payload)


def test_gateway_rejects_string_case_id() -> None:
    payload = _load_json("inference-request.example.json")
    payload["case_id"] = "1"

    with pytest.raises(ValidationError):
        InferenceRequest.model_validate(payload)
