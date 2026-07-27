"""MOSEC worker for the strict v1 Exp05 inference contract.

This module owns request orchestration only:

1. validate the strict v1 request;
2. download one NIfTI CT from Cloud Storage;
3. call ``run_inference_pipeline``;
4. upload ``mask.nii.gz``;
5. replace the pipeline-internal JSON with the strict v1 response;
6. upload the final ``result.json``;
7. return the same strict v1 response to the FastAPI Gateway.

PostgreSQL persistence is intentionally not performed here. Django owns the
database and persists the response returned through the Gateway.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter
from typing import Any

import msgspec
from mosec import Worker
from mosec.errors import ValidationError as MosecValidationError

from .measurements import LesionMeasurementError
from .model_loader import (
    ModelLoader,
    ModelLoaderConfig,
    ModelLoaderError,
)
from .pipeline import (
    InferencePipelineConfig,
    InferencePipelineError,
    run_inference_pipeline,
)
from .preprocessing import NiftiValidationError
from .schemas import (
    InferenceRequest,
    to_json_object,
    validate_inference_request,
    validate_inference_response,
)
from .settings import InferenceSettings, settings
from .storage import ArtifactStorage, StorageError, parse_gs_uri


LOGGER = logging.getLogger(__name__)

SCHEMA_VERSION = "1.0"
TRAINER_NAME = "nnUNetTrainerBHSD_Exp05_25DFinal"
ARCHITECTURE = "PlainConvUNet"

PipelineRunner = Callable[..., dict[str, Any]]

RETRYABLE_ERROR_CODES = frozenset(
    {
        "INPUT_DOWNLOAD_FAILED",
        "ARTIFACT_UPLOAD_FAILED",
        "MODEL_PREDICTION_FAILED",
        "INFERENCE_INTERNAL_ERROR",
    }
)


class WorkerOrchestrationError(RuntimeError):
    """Raised when Worker-level response orchestration cannot finish safely."""

    def __init__(self, *, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class InferenceService:
    """Testable service used by one single-GPU MOSEC Worker process."""

    def __init__(
        self,
        *,
        runtime_settings: InferenceSettings = settings,
        model_loader: ModelLoader | None = None,
        artifact_storage: ArtifactStorage | None = None,
        pipeline_runner: PipelineRunner = run_inference_pipeline,
    ) -> None:
        self.settings = runtime_settings
        self.model_loader = (
            model_loader
            if model_loader is not None
            else self._create_model_loader()
        )
        self.storage = (
            artifact_storage
            if artifact_storage is not None
            else ArtifactStorage(
                results_uri_prefix=(
                    self.settings.results_uri_prefix
                ),
                allow_local_files=(
                    self.settings.allow_local_files
                ),
            )
        )
        self.pipeline_runner = pipeline_runner
        self.pipeline_config = InferencePipelineConfig(
            model_id=self.settings.model_id,
            model_version=self.settings.model_version,
        )

        # Each MOSEC Worker process owns one cached Predictor. Loading during
        # startup prevents the first clinical request from paying model-load
        # latency. ModelLoader.load() remains idempotent when pipeline.py calls
        # it again.
        if self.settings.model_load_on_startup:
            self.model_loader.load()

    def _create_model_loader(self) -> ModelLoader:
        use_cuda = self.settings.model_device.lower().startswith(
            "cuda"
        )
        return ModelLoader(
            ModelLoaderConfig(
                model_training_output_dir=(
                    self.settings.model_dir
                ),
                folds=self.settings.model_folds,
                checkpoint_name=(
                    self.settings.model_checkpoint
                ),
                device=self.settings.model_device,
                tile_step_size=(
                    self.settings.model_tile_step_size
                ),
                use_mirroring=(
                    self.settings.model_use_mirroring
                ),
                perform_everything_on_device=use_cuda,
            )
        )

    @staticmethod
    def _validate_request(payload: Any) -> InferenceRequest:
        """Validate a decoded JSON object or raise MOSEC HTTP 422."""

        try:
            return validate_inference_request(payload)
        except (msgspec.ValidationError, TypeError, ValueError) as error:
            LOGGER.warning(
                "Rejected a request that violates MOSEC contract v1."
            )
            raise MosecValidationError(
                "Request does not conform to MOSEC inference contract v1."
            ) from error

    def _failed_response(
        self,
        request: InferenceRequest,
        *,
        code: str,
        message: str,
        retryable: bool | None = None,
    ) -> dict[str, Any]:
        """Build and validate one strict v1 failed response."""

        response_payload = {
            "schema_version": SCHEMA_VERSION,
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
                "code": code,
                "message": message,
                "retryable": (
                    code in RETRYABLE_ERROR_CODES
                    if retryable is None
                    else retryable
                ),
            },
        }
        validated = validate_inference_response(
            response_payload
        )
        return to_json_object(validated)

    def _result_object_uri(
        self,
        *,
        result_key: str,
        filename: str,
    ) -> str:
        """Return the deterministic strict-v1 Cloud Storage result URI."""

        prefix = self.settings.results_uri_prefix.rstrip("/")

        if not prefix.startswith("gs://"):
            raise WorkerOrchestrationError(
                code="INVALID_RESULTS_URI_PREFIX",
                message=(
                    "Strict contract v1 requires a gs:// "
                    "RESULTS_URI_PREFIX."
                ),
            )

        bucket_name, placeholder_object = parse_gs_uri(
            f"{prefix}/placeholder"
        )
        base_object = placeholder_object.removesuffix(
            "/placeholder"
        )
        object_name = "/".join(
            part
            for part in (
                base_object.strip("/"),
                result_key,
                filename,
            )
            if part
        )
        return f"gs://{bucket_name}/{object_name}"

    @staticmethod
    def _require_pipeline_mapping(
        result: Any,
        field_name: str,
    ) -> dict[str, Any]:
        """Return one required pipeline mapping with a safe error."""

        if not isinstance(result, dict):
            raise WorkerOrchestrationError(
                code="INVALID_PIPELINE_RESULT",
                message=(
                    "The inference pipeline returned an invalid result."
                ),
            )

        value = result.get(field_name)
        if not isinstance(value, dict):
            raise WorkerOrchestrationError(
                code="INVALID_PIPELINE_RESULT",
                message=(
                    "The inference pipeline result is missing "
                    f"the {field_name} object."
                ),
            )
        return value

    def _model_payload(
        self,
        pipeline_result: dict[str, Any],
    ) -> dict[str, Any]:
        """Select only strict-v1 model fields from the pipeline result."""

        model = self._require_pipeline_mapping(
            pipeline_result,
            "model",
        )

        if (
            model.get("model_id") != self.settings.model_id
            or model.get("model_version")
            != self.settings.model_version
        ):
            raise WorkerOrchestrationError(
                code="PIPELINE_MODEL_IDENTITY_MISMATCH",
                message=(
                    "The inference pipeline model identity does not "
                    "match the loaded MOSEC model."
                ),
            )

        return {
            "model_id": model["model_id"],
            "model_version": model["model_version"],
            "trainer_name": TRAINER_NAME,
            "architecture": ARCHITECTURE,
            "folds": model["folds"],
            "checkpoint": model["checkpoint"],
            "nnunet_configuration": model[
                "nnunet_configuration"
            ],
            "input_mode": model["input_mode"],
            "slice_axis": model["slice_axis"],
            "context_offsets": model["context_offsets"],
            "boundary_policy": model["boundary_policy"],
            "target_policy": model["target_policy"],
            "segmentation_decision": model[
                "segmentation_decision"
            ],
        }

    @staticmethod
    def _performance_payload(
        pipeline_result: dict[str, Any],
        *,
        input_download_seconds: float,
        pipeline_seconds: float,
        mask_upload_seconds: float,
    ) -> dict[str, Any]:
        """Convert pipeline timings into the strict v1 phase structure.

        ``output_upload_seconds`` measures the binary mask upload. The
        metadata JSON upload is intentionally excluded because result.json
        contains this value itself; including its own upload duration would
        make the persisted document self-referential.
        """

        performance = InferenceService._require_pipeline_mapping(
            pipeline_result,
            "performance",
        )

        context_seconds = float(
            performance["context_preparation_time_ms"]
        ) / 1000.0
        inference_seconds = float(
            performance["inference_time_seconds"]
        )
        postprocessing_seconds = max(
            0.0,
            pipeline_seconds
            - context_seconds
            - inference_seconds,
        )

        total_seconds = (
            input_download_seconds
            + context_seconds
            + inference_seconds
            + postprocessing_seconds
            + mask_upload_seconds
        )

        gpu_peak_memory = performance[
            "gpu_peak_memory_mb"
        ]

        return {
            "input_download_seconds": float(
                input_download_seconds
            ),
            "context_preparation_seconds": context_seconds,
            "inference_seconds": inference_seconds,
            "postprocessing_seconds": postprocessing_seconds,
            "output_upload_seconds": float(
                mask_upload_seconds
            ),
            "total_seconds": total_seconds,
            "gpu_memory_measured": bool(
                performance["gpu_memory_measured"]
            ),
            "gpu_peak_memory_mb": (
                None
                if gpu_peak_memory is None
                else float(gpu_peak_memory)
            ),
        }

    def _completed_response(
        self,
        request: InferenceRequest,
        pipeline_result: dict[str, Any],
        *,
        mask_uri: str,
        result_json_uri: str,
        input_download_seconds: float,
        pipeline_seconds: float,
        mask_upload_seconds: float,
    ) -> dict[str, Any]:
        """Build and validate the complete strict v1 success response."""

        input_metadata = self._require_pipeline_mapping(
            pipeline_result,
            "input",
        )
        lesion_result = self._require_pipeline_mapping(
            pipeline_result,
            "result",
        )

        response_payload = {
            "schema_version": SCHEMA_VERSION,
            "job_id": request.job_id,
            "case_id": request.case_id,
            "status": "completed",
            "model_version": request.model_version,
            "input": {
                "shape": input_metadata["shape"],
                "spacing_mm": input_metadata["spacing_mm"],
            },
            "model": self._model_payload(
                pipeline_result
            ),
            "artifacts": {
                "mask_uri": mask_uri,
                "result_json_uri": result_json_uri,
                "preview_uri": None,
                "probability_uri": None,
                "entropy_uri": None,
                "uncertainty_uri": None,
            },
            "result": lesion_result,
            "performance": self._performance_payload(
                pipeline_result,
                input_download_seconds=(
                    input_download_seconds
                ),
                pipeline_seconds=pipeline_seconds,
                mask_upload_seconds=mask_upload_seconds,
            ),
            "summary": pipeline_result["summary"],
            "message": pipeline_result["message"],
            "error": None,
        }

        validated = validate_inference_response(
            response_payload
        )
        return to_json_object(validated)

    @staticmethod
    def _write_result_json(
        path: Path,
        response: dict[str, Any],
    ) -> None:
        """Atomically replace pipeline JSON with the final strict response."""

        temporary_path = path.with_name(
            f".{path.name.removesuffix('.json')}.worker.tmp.json"
        )

        try:
            with temporary_path.open(
                "w",
                encoding="utf-8",
                newline="\n",
            ) as file:
                json.dump(
                    response,
                    file,
                    ensure_ascii=False,
                    indent=2,
                    allow_nan=False,
                )
                file.write("\n")
            temporary_path.replace(path)
        except Exception as error:
            temporary_path.unlink(missing_ok=True)
            raise WorkerOrchestrationError(
                code="RESULT_JSON_WRITE_FAILED",
                message=(
                    "The final inference result JSON could not "
                    "be written."
                ),
            ) from error

    def _run_request(
        self,
        request: InferenceRequest,
    ) -> dict[str, Any]:
        """Download, infer, publish, and return one completed response."""

        if request.model_version != self.settings.model_version:
            raise WorkerOrchestrationError(
                code="UNSUPPORTED_MODEL_VERSION",
                message=(
                    "The requested model_version is not loaded "
                    "by this MOSEC service."
                ),
            )

        self.settings.request_work_root.mkdir(
            parents=True,
            exist_ok=True,
        )

        with TemporaryDirectory(
            prefix=f"{request.job_id}_",
            dir=str(self.settings.request_work_root),
        ) as request_directory:
            request_path = Path(request_directory)
            input_path = request_path / "input.nii.gz"
            output_directory = request_path / "outputs"

            download_started = perf_counter()
            self.storage.download_input(
                request.input_uri,
                input_path,
            )
            input_download_seconds = (
                perf_counter() - download_started
            )

            pipeline_started = perf_counter()
            pipeline_result = self.pipeline_runner(
                input_path,
                output_directory,
                model_loader=self.model_loader,
                config=self.pipeline_config,
            )
            pipeline_seconds = (
                perf_counter() - pipeline_started
            )

            artifacts = self._require_pipeline_mapping(
                pipeline_result,
                "artifacts",
            )
            mask_filename = artifacts.get("mask_filename")
            result_filename = artifacts.get("result_filename")

            if (
                not isinstance(mask_filename, str)
                or Path(mask_filename).name != mask_filename
                or not isinstance(result_filename, str)
                or Path(result_filename).name
                != result_filename
            ):
                raise WorkerOrchestrationError(
                    code="INVALID_PIPELINE_ARTIFACTS",
                    message=(
                        "The inference pipeline returned invalid "
                        "artifact file names."
                    ),
                )

            mask_path = output_directory / mask_filename
            result_json_path = (
                output_directory / result_filename
            )
            result_key = request.job_id

            expected_mask_uri = self._result_object_uri(
                result_key=result_key,
                filename=mask_filename,
            )
            result_json_uri = self._result_object_uri(
                result_key=result_key,
                filename=result_filename,
            )

            mask_upload_started = perf_counter()
            uploaded_mask = self.storage.upload_artifacts(
                [mask_path],
                result_key=result_key,
            )
            mask_upload_seconds = (
                perf_counter() - mask_upload_started
            )
            mask_uri = uploaded_mask.get(mask_filename)

            if mask_uri != expected_mask_uri:
                raise WorkerOrchestrationError(
                    code="ARTIFACT_URI_MISMATCH",
                    message=(
                        "The uploaded mask URI does not match the "
                        "configured result destination."
                    ),
                )

            completed_response = self._completed_response(
                request,
                pipeline_result,
                mask_uri=mask_uri,
                result_json_uri=result_json_uri,
                input_download_seconds=(
                    input_download_seconds
                ),
                pipeline_seconds=pipeline_seconds,
                mask_upload_seconds=mask_upload_seconds,
            )

            self._write_result_json(
                result_json_path,
                completed_response,
            )
            uploaded_result = self.storage.upload_artifacts(
                [result_json_path],
                result_key=result_key,
            )

            if uploaded_result.get(result_filename) != result_json_uri:
                raise WorkerOrchestrationError(
                    code="ARTIFACT_URI_MISMATCH",
                    message=(
                        "The uploaded result JSON URI does not match "
                        "the configured result destination."
                    ),
                )

            return completed_response

    def handle(self, payload: Any) -> dict[str, Any]:
        """Validate and process one request from the FastAPI Gateway."""

        # Invalid identifiers cannot be represented honestly in the strict
        # response schema. Raise MOSEC ValidationError so MOSEC returns HTTP
        # 422. The Gateway already applies the same validation before calling
        # this internal endpoint.
        request = self._validate_request(payload)

        try:
            return self._run_request(request)
        except (
            StorageError,
            NiftiValidationError,
            ModelLoaderError,
            InferencePipelineError,
            LesionMeasurementError,
            WorkerOrchestrationError,
        ) as error:
            LOGGER.exception(
                "MOSEC inference failed: code=%s",
                error.code,
            )
            return self._failed_response(
                request,
                code=error.code,
                message=error.message,
            )
        except Exception:
            LOGGER.exception(
                "Unhandled MOSEC inference request failure."
            )
            return self._failed_response(
                request,
                code="INFERENCE_INTERNAL_ERROR",
                message=(
                    "The inference service encountered an "
                    "unexpected internal error."
                ),
                retryable=True,
            )


class MosecInferenceWorker(Worker):
    """One MOSEC process owning one cached Exp05 nnU-Net Predictor."""

    def __init__(self) -> None:
        super().__init__()
        self.service = InferenceService()

    def forward(self, data: Any) -> dict[str, Any]:
        """Run one non-batched JSON request."""

        return self.service.handle(data)
