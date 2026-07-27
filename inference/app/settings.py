"""Inference service settings."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import re


FoldIdentifier = int | str

DEFAULT_MODEL_RELATIVE_DIR = Path(
    "model"
) / "Dataset001_BHSD_25D" / (
    "nnUNetTrainerBHSD_Exp05_25DFinal__nnUNetPlans__2d"
)


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    return default if value is None else int(value)


def _get_float(name: str, default: float) -> float:
    value = os.getenv(name)
    return default if value is None else float(value)


def _get_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)

    if value is None:
        return default

    normalized = value.strip().lower()

    if normalized in {"1", "true", "yes", "on"}:
        return True

    if normalized in {"0", "false", "no", "off"}:
        return False

    raise ValueError(
        f"{name} must be one of: "
        "true, false, 1, 0, yes, no, on, off"
    )


def _get_folds(
    name: str,
    default: tuple[FoldIdentifier, ...],
) -> tuple[FoldIdentifier, ...]:
    value = os.getenv(name)

    if value is None:
        return default

    parsed: list[FoldIdentifier] = []

    for item in value.split(","):
        item = item.strip()

        if not item:
            raise ValueError(
                f"{name} must not contain an empty fold value"
            )

        if item.lower() == "all":
            parsed.append("all")
            continue

        try:
            parsed.append(int(item))
        except ValueError as error:
            raise ValueError(
                f"{name} must contain integers or 'all'"
            ) from error

    return tuple(parsed)


@dataclass(frozen=True)
class InferenceSettings:
    """Development defaults; production values are overridden by env vars."""

    max_nifti_bytes: int
    max_nifti_voxels: int
    probability_threshold: float
    min_component_voxels: int
    slice_axis: int

    results_uri_prefix: str
    allow_local_files: bool
    request_work_root: Path

    model_bucket: str
    model_object: str
    model_sha256: str
    model_cache_dir: Path
    model_dir: Path

    model_id: str
    model_version: str
    model_folds: tuple[FoldIdentifier, ...]
    model_checkpoint: str
    model_device: str
    model_tile_step_size: float
    model_use_mirroring: bool
    model_load_on_startup: bool

    @classmethod
    def from_env(cls) -> "InferenceSettings":
        model_cache_dir = Path(
            os.getenv("MODEL_CACHE_DIR", "/models")
        ).expanduser()

        default_model_dir = (
            model_cache_dir / DEFAULT_MODEL_RELATIVE_DIR
        )

        settings = cls(
            max_nifti_bytes=_get_int(
                "MAX_NIFTI_BYTES",
                512 * 1024 * 1024,
            ),
            max_nifti_voxels=_get_int(
                "MAX_NIFTI_VOXELS",
                100_000_000,
            ),
            probability_threshold=_get_float(
                "PROBABILITY_THRESHOLD",
                0.5,
            ),
            min_component_voxels=_get_int(
                "MIN_COMPONENT_VOXELS",
                10,
            ),
            slice_axis=_get_int(
                "SLICE_AXIS",
                2,
            ),
            results_uri_prefix=os.getenv(
                "RESULTS_URI_PREFIX",
                "",
            ).strip(),
            allow_local_files=_get_bool(
                "ALLOW_LOCAL_FILES",
                False,
            ),
            request_work_root=Path(
                os.getenv(
                    "REQUEST_WORK_ROOT",
                    "/tmp/medical-cdss-inference",
                )
            ).expanduser(),
            model_bucket=os.getenv(
                "MODEL_BUCKET",
                "",
            ).strip(),
            model_object=os.getenv(
                "MODEL_OBJECT",
                "",
            ).strip(),
            model_sha256=os.getenv(
                "MODEL_SHA256",
                "",
            ).strip().lower(),
            model_cache_dir=model_cache_dir,
            model_dir=Path(
                os.getenv(
                    "MODEL_DIR",
                    str(default_model_dir),
                )
            ).expanduser(),
            model_id=os.getenv(
                "MODEL_ID",
                "stroke-bhsd-nnunet-25d-exp05",
            ).strip(),
            model_version=os.getenv(
                "MODEL_VERSION",
                "1.0.0",
            ).strip(),
            model_folds=_get_folds(
                "MODEL_FOLDS",
                (0,),
            ),
            model_checkpoint=os.getenv(
                "MODEL_CHECKPOINT",
                "checkpoint_best.pth",
            ).strip(),
            model_device=os.getenv(
                "MODEL_DEVICE",
                "cuda",
            ).strip(),
            model_tile_step_size=_get_float(
                "MODEL_TILE_STEP_SIZE",
                0.5,
            ),
            model_use_mirroring=_get_bool(
                "MODEL_USE_MIRRORING",
                True,
            ),
            model_load_on_startup=_get_bool(
                "MODEL_LOAD_ON_STARTUP",
                True,
            ),
        )
        settings.validate()
        return settings

    def validate(self) -> None:
        if self.max_nifti_bytes <= 0:
            raise ValueError(
                "MAX_NIFTI_BYTES must be greater than 0"
            )

        if self.max_nifti_voxels <= 0:
            raise ValueError(
                "MAX_NIFTI_VOXELS must be greater than 0"
            )

        if not 0.0 <= self.probability_threshold <= 1.0:
            raise ValueError(
                "PROBABILITY_THRESHOLD must be between 0 and 1"
            )

        if self.min_component_voxels < 0:
            raise ValueError(
                "MIN_COMPONENT_VOXELS must be 0 or greater"
            )

        if self.slice_axis not in (0, 1, 2):
            raise ValueError(
                "SLICE_AXIS must be 0, 1, or 2"
            )

        if (
            self.results_uri_prefix.startswith("file://")
            and not self.allow_local_files
        ):
            raise ValueError(
                "ALLOW_LOCAL_FILES must be true when "
                "RESULTS_URI_PREFIX uses file://"
            )

        if not self.model_id:
            raise ValueError("MODEL_ID must not be empty")

        if not self.model_version:
            raise ValueError("MODEL_VERSION must not be empty")

        if not self.model_folds:
            raise ValueError(
                "MODEL_FOLDS must contain at least one fold"
            )

        for fold in self.model_folds:
            valid_integer = (
                isinstance(fold, int)
                and not isinstance(fold, bool)
                and fold >= 0
            )
            valid_all = fold == "all"

            if not valid_integer and not valid_all:
                raise ValueError(
                    "MODEL_FOLDS values must be "
                    "non-negative integers or 'all'"
                )

        if len(set(self.model_folds)) != len(self.model_folds):
            raise ValueError(
                "MODEL_FOLDS must not contain duplicates"
            )

        if (
            not self.model_checkpoint
            or "/" in self.model_checkpoint
            or "\\" in self.model_checkpoint
        ):
            raise ValueError(
                "MODEL_CHECKPOINT must be a file name"
            )

        if not self.model_device:
            raise ValueError("MODEL_DEVICE must not be empty")

        if not 0.0 < self.model_tile_step_size <= 1.0:
            raise ValueError(
                "MODEL_TILE_STEP_SIZE must be greater than 0 "
                "and less than or equal to 1"
            )

        cloud_model_values = (
            self.model_bucket,
            self.model_object,
            self.model_sha256,
        )

        if any(cloud_model_values) and not all(cloud_model_values):
            raise ValueError(
                "MODEL_BUCKET, MODEL_OBJECT and MODEL_SHA256 "
                "must be configured together"
            )

        if self.model_sha256 and re.fullmatch(
            r"[0-9a-f]{64}",
            self.model_sha256,
        ) is None:
            raise ValueError(
                "MODEL_SHA256 must be a 64-character "
                "SHA-256 hexadecimal value"
            )

        if self.model_object.startswith("/"):
            raise ValueError(
                "MODEL_OBJECT must not start with '/'"
            )


settings = InferenceSettings.from_env()