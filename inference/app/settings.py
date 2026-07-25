"""Inference service settings."""

from dataclasses import dataclass
import os


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    return default if value is None else int(value)


def _get_float(name: str, default: float) -> float:
    value = os.getenv(name)
    return default if value is None else float(value)


@dataclass(frozen=True)
class InferenceSettings:
    """Development defaults; production values can be overridden by env vars."""

    max_nifti_bytes: int
    max_nifti_voxels: int
    probability_threshold: float
    min_component_voxels: int
    slice_axis: int

    @classmethod
    def from_env(cls) -> "InferenceSettings":
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
        )
        settings.validate()
        return settings

    def validate(self) -> None:
        if self.max_nifti_bytes <= 0:
            raise ValueError("MAX_NIFTI_BYTES must be greater than 0")

        if self.max_nifti_voxels <= 0:
            raise ValueError("MAX_NIFTI_VOXELS must be greater than 0")

        if not 0.0 <= self.probability_threshold <= 1.0:
            raise ValueError(
                "PROBABILITY_THRESHOLD must be between 0 and 1"
            )

        if self.min_component_voxels < 0:
            raise ValueError(
                "MIN_COMPONENT_VOXELS must be 0 or greater"
            )

        if self.slice_axis not in (0, 1, 2):
            raise ValueError("SLICE_AXIS must be 0, 1, or 2")


settings = InferenceSettings.from_env()