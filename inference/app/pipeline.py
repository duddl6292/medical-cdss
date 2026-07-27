"""End-to-end inference pipeline for the BHSD Exp05 3-slice 2.5D model.

The deployed nnU-Net model was trained with the following fixed input rule:

* NIfTI slice axis: 2 (Z)
* channel 0000: center slice - 1
* channel 0001: center slice
* channel 0002: center slice + 1
* boundary handling: edge replication
* target: center-slice mask

Only the final binary mask and a JSON result are persisted. Probability,
entropy and uncertainty volumes are intentionally outside the current scope.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Lock
from time import perf_counter
from typing import Any

import nibabel as nib
import numpy as np

from .measurements import (
    LesionMeasurements,
    calculate_lesion_measurements,
)
from .model_loader import ModelLoader
from .performance import (
    InferencePerformance,
    measure_inference_performance,
)
from .preprocessing import NiftiVolume, load_and_validate_nifti


SLICE_AXIS = 2
CONTEXT_OFFSETS = (-1, 0, 1)
CHANNEL_SUFFIXES = ("0000", "0001", "0002")
CHANNEL_ORDER = {
    "0000": "center_slice_minus_1",
    "0001": "center_slice",
    "0002": "center_slice_plus_1",
}
BOUNDARY_POLICY = "edge_replication"
TARGET_POLICY = "center_slice_mask"

EXPECTED_CHANNEL_NAMES = {
    "0": "CT",
    "1": "CT",
    "2": "CT",
}
EXPECTED_LABELS = {
    "background": 0,
    "hemorrhage": 1,
}
EXPECTED_FILE_ENDING = ".nii.gz"

DEFAULT_DISCLAIMER = (
    "AI 분석 결과이며 의료진의 최종 진단을 대체하지 않습니다."
)

# One nnUNetPredictor instance and one GPU must not be entered concurrently
# by multiple requests in the same process.
_PREDICTION_LOCK = Lock()


class InferencePipelineError(RuntimeError):
    """Raised when the end-to-end inference pipeline cannot finish safely."""

    def __init__(self, *, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True, slots=True)
class InferencePipelineConfig:
    """Deployed-model identity and output settings."""

    model_id: str
    model_version: str
    mask_filename: str = "mask.nii.gz"
    result_filename: str = "result.json"
    num_processes_preprocessing: int = 1
    num_processes_segmentation_export: int = 1
    disclaimer: str = DEFAULT_DISCLAIMER

    def __post_init__(self) -> None:
        if not self.model_id.strip():
            raise ValueError("model_id must not be empty.")

        if not self.model_version.strip():
            raise ValueError("model_version must not be empty.")

        if (
            Path(self.mask_filename).name != self.mask_filename
            or not self.mask_filename.lower().endswith(".nii.gz")
        ):
            raise ValueError(
                "mask_filename must be a .nii.gz file name, not a path."
            )

        if (
            Path(self.result_filename).name != self.result_filename
            or not self.result_filename.lower().endswith(".json")
        ):
            raise ValueError(
                "result_filename must be a .json file name, not a path."
            )

        if self.num_processes_preprocessing < 1:
            raise ValueError(
                "num_processes_preprocessing must be at least 1."
            )

        if self.num_processes_segmentation_export < 1:
            raise ValueError(
                "num_processes_segmentation_export must be at least 1."
            )


def _read_and_validate_dataset_json(
    model_loader: ModelLoader,
) -> dict[str, Any]:
    """Verify that the selected model is the expected Exp05 3-channel model."""

    dataset_path = (
        model_loader.config.model_training_output_dir / "dataset.json"
    )

    try:
        with dataset_path.open("r", encoding="utf-8") as file:
            dataset_json = json.load(file)
    except FileNotFoundError as error:
        raise InferencePipelineError(
            code="MODEL_DATASET_JSON_NOT_FOUND",
            message="dataset.json was not found in the trained model folder.",
        ) from error
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise InferencePipelineError(
            code="MODEL_DATASET_JSON_INVALID",
            message="dataset.json could not be read as valid UTF-8 JSON.",
        ) from error

    if not isinstance(dataset_json, dict):
        raise InferencePipelineError(
            code="MODEL_DATASET_JSON_INVALID",
            message="dataset.json must contain one JSON object.",
        )

    if dataset_json.get("channel_names") != EXPECTED_CHANNEL_NAMES:
        raise InferencePipelineError(
            code="MODEL_CHANNEL_CONTRACT_MISMATCH",
            message=(
                "The model must declare exactly three CT channels: "
                "0, 1 and 2."
            ),
        )

    if dataset_json.get("labels") != EXPECTED_LABELS:
        raise InferencePipelineError(
            code="MODEL_LABEL_CONTRACT_MISMATCH",
            message=(
                "The model labels must be background=0 and hemorrhage=1."
            ),
        )

    if dataset_json.get("file_ending") != EXPECTED_FILE_ENDING:
        raise InferencePipelineError(
            code="MODEL_FILE_ENDING_MISMATCH",
            message="The Exp05 model must use the .nii.gz file ending.",
        )

    return dataset_json


def _make_shifted_context(
    data: np.ndarray,
    *,
    offset: int,
) -> np.ndarray:
    """Shift an X-Y-Z CT along Z and replicate the nearest edge slice."""

    depth = data.shape[SLICE_AXIS]
    source_indices = np.clip(
        np.arange(depth, dtype=np.int64) + offset,
        0,
        depth - 1,
    )
    shifted = np.take(data, source_indices, axis=SLICE_AXIS)
    return np.asarray(shifted, dtype=np.float32)


def _save_float32_nifti(
    data: np.ndarray,
    path: Path,
    input_volume: NiftiVolume,
) -> None:
    """Save a context channel while preserving the input spatial geometry."""

    header = input_volume.header.copy()
    header.set_data_dtype(np.float32)
    header.set_slope_inter(1.0, 0.0)

    image = nib.Nifti1Image(
        np.ascontiguousarray(data, dtype=np.float32),
        input_volume.affine,
        header=header,
    )

    try:
        nib.save(image, str(path))
    except Exception as error:
        raise InferencePipelineError(
            code="CONTEXT_CHANNEL_WRITE_FAILED",
            message=f"The 2.5D context channel {path.name} could not be saved.",
        ) from error


def _create_context_channel_files(
    input_volume: NiftiVolume,
    directory: Path,
) -> list[Path]:
    """Create channel 0000/0001/0002 using the confirmed Exp05 rule."""

    channel_paths: list[Path] = []

    for suffix, offset in zip(
        CHANNEL_SUFFIXES,
        CONTEXT_OFFSETS,
        strict=True,
    ):
        channel_path = directory / f"case_{suffix}.nii.gz"
        channel_data = _make_shifted_context(
            input_volume.data,
            offset=offset,
        )
        _save_float32_nifti(
            channel_data,
            channel_path,
            input_volume,
        )
        channel_paths.append(channel_path)

    return channel_paths


def _run_nnunet_prediction(
    predictor: Any,
    channel_paths: list[Path],
    output_path_without_extension: Path,
    config: InferencePipelineConfig,
) -> None:
    """Run one file-based nnU-Net prediction without child processes."""

    predict_sequentially = getattr(
        predictor,
        "predict_from_files_sequential",
        None,
    )

    if callable(predict_sequentially):
        predict_sequentially(
            [[str(path) for path in channel_paths]],
            [str(output_path_without_extension)],
            save_probabilities=False,
            overwrite=True,
            folder_with_segs_from_prev_stage=None,
        )
        return

    predict_from_files = getattr(predictor, "predict_from_files", None)

    if not callable(predict_from_files):
        raise InferencePipelineError(
            code="INVALID_PREDICTOR",
            message="The loaded Predictor does not provide predict_from_files().",
        )

    predict_from_files(
        [[str(path) for path in channel_paths]],
        [str(output_path_without_extension)],
        save_probabilities=False,
        overwrite=True,
        num_processes_preprocessing=(
            config.num_processes_preprocessing
        ),
        num_processes_segmentation_export=(
            config.num_processes_segmentation_export
        ),
        folder_with_segs_from_prev_stage=None,
        num_parts=1,
        part_id=0,
    )


def _load_binary_mask(
    predicted_mask_path: Path,
    input_volume: NiftiVolume,
) -> tuple[np.ndarray, nib.Nifti1Image]:
    """Load and validate the segmentation exported by nnU-Net."""

    if not predicted_mask_path.is_file():
        raise InferencePipelineError(
            code="MASK_OUTPUT_NOT_CREATED",
            message="nnU-Net did not create the expected mask.nii.gz output.",
        )

    try:
        predicted_image = nib.load(str(predicted_mask_path))
        predicted_data = np.asarray(predicted_image.dataobj)
    except Exception as error:
        raise InferencePipelineError(
            code="MASK_OUTPUT_READ_FAILED",
            message="The predicted mask could not be read as NIfTI.",
        ) from error

    if predicted_data.shape != input_volume.shape:
        raise InferencePipelineError(
            code="MASK_SHAPE_MISMATCH",
            message=(
                "The predicted mask shape does not match the input CT shape. "
                f"Input: {input_volume.shape}; "
                f"mask: {predicted_data.shape}."
            ),
        )

    if not np.isfinite(predicted_data).all():
        raise InferencePipelineError(
            code="NON_FINITE_MASK_VALUES",
            message="The predicted mask contains NaN or infinite values.",
        )

    rounded_data = np.rint(predicted_data)

    if not np.allclose(
        predicted_data,
        rounded_data,
        rtol=0.0,
        atol=1e-6,
    ):
        raise InferencePipelineError(
            code="NON_INTEGER_MASK_VALUES",
            message="The predicted mask contains non-integer label values.",
        )

    labels = set(np.unique(rounded_data).astype(int).tolist())

    if not labels.issubset({0, 1}):
        raise InferencePipelineError(
            code="INVALID_MASK_LABELS",
            message=(
                "The predicted mask must contain only labels 0 and 1. "
                f"Received labels: {sorted(labels)}."
            ),
        )

    if not np.allclose(
        predicted_image.affine,
        input_volume.affine,
        rtol=1e-5,
        atol=1e-4,
    ):
        raise InferencePipelineError(
            code="MASK_AFFINE_MISMATCH",
            message=(
                "The predicted mask affine does not match the input CT affine."
            ),
        )

    return rounded_data.astype(np.uint8, copy=False), predicted_image


def _save_binary_mask_atomically(
    mask: np.ndarray,
    final_mask_path: Path,
    input_volume: NiftiVolume,
) -> None:
    """Persist a spatially aligned uint8 mask with an atomic replacement."""

    temporary_mask_path = final_mask_path.with_name(
        f".{final_mask_path.name.removesuffix('.nii.gz')}.tmp.nii.gz"
    )
    header = input_volume.header.copy()
    header.set_data_dtype(np.uint8)
    header.set_slope_inter(1.0, 0.0)

    output_image = nib.Nifti1Image(
        mask,
        input_volume.affine,
        header=header,
    )

    try:
        nib.save(output_image, str(temporary_mask_path))
        temporary_mask_path.replace(final_mask_path)
    except Exception as error:
        temporary_mask_path.unlink(missing_ok=True)
        raise InferencePipelineError(
            code="MASK_OUTPUT_WRITE_FAILED",
            message="The validated binary mask could not be saved.",
        ) from error


def _calculate_slice_summary(
    mask: np.ndarray,
    measurements: LesionMeasurements,
) -> dict[str, int | None]:
    """Return lesion range and largest-lesion slice as zero-based indices."""

    if not measurements.lesion_slice_indices:
        return {
            "lesion_slice_start": None,
            "lesion_slice_end": None,
            "max_lesion_slice": None,
            "max_lesion_slice_voxel_count": 0,
        }

    lesion_voxels_per_slice = np.count_nonzero(
        mask,
        axis=(0, 1),
    )
    max_lesion_slice = int(np.argmax(lesion_voxels_per_slice))

    return {
        "lesion_slice_start": measurements.lesion_slice_indices[0],
        "lesion_slice_end": measurements.lesion_slice_indices[-1],
        "max_lesion_slice": max_lesion_slice,
        "max_lesion_slice_voxel_count": int(
            lesion_voxels_per_slice[max_lesion_slice]
        ),
    }


def _build_summary(measurements: LesionMeasurements) -> str:
    """Create a deterministic, non-diagnostic result summary."""

    if not measurements.lesion_detected:
        return "AI 분할 결과 출혈 의심 영역이 감지되지 않았습니다."

    return (
        "AI가 출혈 의심 영역을 "
        f"{measurements.lesion_slice_count}개 슬라이스에서 분할했으며, "
        "계산된 병변 부피는 "
        f"{measurements.lesion_volume_ml:.2f} mL입니다."
    )


def _performance_to_dict(
    performance: InferencePerformance,
    *,
    context_preparation_time_ms: float,
) -> dict[str, float | bool | None | str]:
    """Return performance values with unambiguous measurement scopes."""

    payload: dict[str, float | bool | None | str] = (
        performance.to_dict()
    )
    payload["inference_time_seconds"] = (
        performance.inference_time_ms / 1000.0
    )
    payload["context_preparation_time_ms"] = (
        context_preparation_time_ms
    )
    payload["inference_timing_scope"] = (
        "nnunet_preprocessing_prediction_and_mask_export"
    )
    return payload


def _write_json_atomically(
    path: Path,
    payload: dict[str, Any],
) -> None:
    """Write UTF-8 JSON atomically and reject NaN or Infinity."""

    temporary_path = path.with_name(
        f".{path.name.removesuffix('.json')}.tmp.json"
    )

    try:
        with temporary_path.open(
            "w",
            encoding="utf-8",
            newline="\n",
        ) as file:
            json.dump(
                payload,
                file,
                ensure_ascii=False,
                indent=2,
                allow_nan=False,
            )
            file.write("\n")

        temporary_path.replace(path)
    except Exception as error:
        temporary_path.unlink(missing_ok=True)
        raise InferencePipelineError(
            code="RESULT_JSON_WRITE_FAILED",
            message="The inference result JSON could not be written.",
        ) from error


def _cuda_device_for_measurement(device_name: str) -> Any:
    """Return torch.device for CUDA measurement without a hard import."""

    if not device_name.lower().startswith("cuda"):
        return None

    try:
        import torch
    except ImportError:
        return None

    return torch.device(device_name)


def run_inference_pipeline(
    input_path: str | Path,
    output_dir: str | Path,
    *,
    model_loader: ModelLoader,
    config: InferencePipelineConfig,
) -> dict[str, Any]:
    """Create Exp05 context channels, binary mask, measurements and JSON.

    The returned dictionary is JSON-compatible and has the same content as
    ``result.json``. Uploaded CT files are never modified.
    """

    input_file = Path(input_path)
    output_directory = Path(output_dir)
    input_volume = load_and_validate_nifti(input_file)

    try:
        output_directory.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        raise InferencePipelineError(
            code="OUTPUT_DIRECTORY_CREATION_FAILED",
            message="The inference output directory could not be created.",
        ) from error

    if not output_directory.is_dir():
        raise InferencePipelineError(
            code="INVALID_OUTPUT_DIRECTORY",
            message="The inference output path is not a directory.",
        )

    _read_and_validate_dataset_json(model_loader)
    predictor = model_loader.load()

    final_mask_path = output_directory / config.mask_filename
    result_json_path = output_directory / config.result_filename

    with TemporaryDirectory(
        prefix=".nnunet_exp05_",
        dir=str(output_directory),
    ) as temporary_directory:
        temporary_path = Path(temporary_directory)

        context_start = perf_counter()
        channel_paths = _create_context_channel_files(
            input_volume,
            temporary_path,
        )
        context_preparation_time_ms = (
            perf_counter() - context_start
        ) * 1000.0

        output_path_without_extension = temporary_path / "prediction"
        predicted_mask_path = Path(
            f"{output_path_without_extension}{EXPECTED_FILE_ENDING}"
        )

        with _PREDICTION_LOCK:
            try:
                _, performance = measure_inference_performance(
                    _run_nnunet_prediction,
                    predictor,
                    channel_paths,
                    output_path_without_extension,
                    config,
                    cuda_device=_cuda_device_for_measurement(
                        model_loader.config.device
                    ),
                )
            except InferencePipelineError:
                raise
            except Exception as error:
                raise InferencePipelineError(
                    code="MODEL_PREDICTION_FAILED",
                    message="nnU-Net inference failed.",
                ) from error

        mask, _ = _load_binary_mask(
            predicted_mask_path,
            input_volume,
        )

    measurements = calculate_lesion_measurements(
        mask,
        input_volume.spacing,
        slice_axis=SLICE_AXIS,
    )
    measurement_payload = measurements.to_dict()
    measurement_payload.update(
        {
            "slice_axis": SLICE_AXIS,
            "slice_index_base": 0,
            **_calculate_slice_summary(mask, measurements),
        }
    )

    response: dict[str, Any] = {
        "status": "success",
        "input": {
            "filename": input_file.name,
            "shape": list(input_volume.shape),
            "spacing_mm": list(input_volume.spacing),
        },
        "model": {
            "model_id": config.model_id,
            "model_version": config.model_version,
            "folds": list(model_loader.config.folds),
            "checkpoint": model_loader.config.checkpoint_name,
            "nnunet_configuration": "2d",
            "input_mode": "2.5D_3Slice",
            "slice_axis": SLICE_AXIS,
            "context_offsets": list(CONTEXT_OFFSETS),
            "channel_order": CHANNEL_ORDER,
            "boundary_policy": BOUNDARY_POLICY,
            "target_policy": TARGET_POLICY,
            "segmentation_decision": "nnunet_default_label_conversion",
            "probability_output_saved": False,
            "entropy_output_saved": False,
            "uncertainty_output_saved": False,
        },
        "artifacts": {
            "mask_filename": final_mask_path.name,
            "result_filename": result_json_path.name,
        },
        "result": measurement_payload,
        "performance": _performance_to_dict(
            performance,
            context_preparation_time_ms=context_preparation_time_ms,
        ),
        "summary": _build_summary(measurements),
        "message": config.disclaimer,
    }

    _save_binary_mask_atomically(
        mask,
        final_mask_path,
        input_volume,
    )
    _write_json_atomically(result_json_path, response)

    return response
