"""Lesion measurement utilities for a three-dimensional binary mask."""

from dataclasses import dataclass
from typing import Any, Sequence

import numpy as np


BACKGROUND_LABEL = 0
LESION_LABEL = 1
DEFAULT_SLICE_AXIS = 2
MM3_PER_ML = 1000.0


class LesionMeasurementError(ValueError):
    """Raised when lesion measurements cannot be calculated safely."""

    def __init__(
        self,
        code: str,
        message: str,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class LesionMeasurements:
    """Calculated lesion measurements for one patient volume."""

    lesion_detected: bool
    lesion_voxel_count: int
    voxel_volume_mm3: float
    lesion_volume_mm3: float
    lesion_volume_ml: float
    lesion_slice_count: int
    lesion_slice_indices: tuple[int, ...]

    def to_dict(self) -> dict[str, Any]:
        """Convert the measurement result to a JSON-compatible dictionary."""

        return {
            "lesion_detected": self.lesion_detected,
            "lesion_voxel_count": self.lesion_voxel_count,
            "voxel_volume_mm3": self.voxel_volume_mm3,
            "lesion_volume_mm3": self.lesion_volume_mm3,
            "lesion_volume_ml": self.lesion_volume_ml,
            "lesion_slice_count": self.lesion_slice_count,
            "lesion_slice_indices": list(
                self.lesion_slice_indices
            ),
        }


def _validate_mask(
    mask: np.ndarray,
) -> np.ndarray:
    """Validate and return a three-dimensional binary lesion mask."""

    mask_array = np.asarray(mask)

    if mask_array.ndim != 3:
        raise LesionMeasurementError(
            code="INVALID_MASK_DIMENSION",
            message=(
                "The lesion mask must be three-dimensional. "
                f"Received shape: {mask_array.shape}"
            ),
        )

    if mask_array.size == 0:
        raise LesionMeasurementError(
            code="EMPTY_MASK",
            message="The lesion mask must not be empty.",
        )

    is_numeric = np.issubdtype(
        mask_array.dtype,
        np.number,
    )
    is_boolean = np.issubdtype(
        mask_array.dtype,
        np.bool_,
    )

    if not is_numeric and not is_boolean:
        raise LesionMeasurementError(
            code="INVALID_MASK_TYPE",
            message=(
                "The lesion mask must contain numeric or boolean values. "
                f"Received dtype: {mask_array.dtype}"
            ),
        )

    if not np.isfinite(mask_array).all():
        raise LesionMeasurementError(
            code="NON_FINITE_MASK_VALUES",
            message="The lesion mask contains NaN or infinite values.",
        )

    valid_labels = np.isin(
        mask_array,
        [BACKGROUND_LABEL, LESION_LABEL],
    )

    if not valid_labels.all():
        invalid_labels = np.unique(
            mask_array[~valid_labels]
        ).tolist()

        raise LesionMeasurementError(
            code="INVALID_MASK_LABELS",
            message=(
                "The lesion mask must contain only labels 0 and 1. "
                f"Invalid labels: {invalid_labels}"
            ),
        )

    return mask_array == LESION_LABEL


def _validate_spacing(
    spacing: Sequence[float],
) -> tuple[float, float, float]:
    """Validate three-dimensional voxel spacing in millimetres."""

    try:
        spacing_array = np.asarray(
            spacing,
            dtype=np.float64,
        )
    except (TypeError, ValueError) as error:
        raise LesionMeasurementError(
            code="INVALID_VOXEL_SPACING",
            message="Voxel spacing must contain three numeric values.",
        ) from error

    if spacing_array.shape != (3,):
        raise LesionMeasurementError(
            code="INVALID_VOXEL_SPACING",
            message=(
                "Voxel spacing must contain exactly three values. "
                f"Received: {spacing_array.tolist()}"
            ),
        )

    if not np.isfinite(spacing_array).all():
        raise LesionMeasurementError(
            code="INVALID_VOXEL_SPACING",
            message="Voxel spacing contains NaN or infinite values.",
        )

    if np.any(spacing_array <= 0):
        raise LesionMeasurementError(
            code="INVALID_VOXEL_SPACING",
            message=(
                "Every voxel spacing value must be greater than zero. "
                f"Received: {spacing_array.tolist()}"
            ),
        )

    return (
        float(spacing_array[0]),
        float(spacing_array[1]),
        float(spacing_array[2]),
    )


def calculate_lesion_measurements(
    mask: np.ndarray,
    spacing: Sequence[float],
    *,
    slice_axis: int = DEFAULT_SLICE_AXIS,
) -> LesionMeasurements:
    """Calculate lesion volume and occupied axial-slice information.

    Args:
        mask:
            Three-dimensional binary mask with labels
            0 for background and 1 for lesion.
        spacing:
            Voxel spacing in millimetres in X, Y and Z order.
        slice_axis:
            Array axis representing the slice direction.
            The default is axis 2 for an X-Y-Z NIfTI volume.

    Returns:
        Lesion volume, voxel count and lesion-slice information.

    Raises:
        LesionMeasurementError:
            If the mask, spacing or slice axis is invalid.
    """

    if (
        isinstance(slice_axis, bool)
        or not isinstance(slice_axis, int)
        or slice_axis not in (0, 1, 2)
    ):
        raise LesionMeasurementError(
            code="INVALID_SLICE_AXIS",
            message=(
                "The slice axis must be one of 0, 1 or 2. "
                f"Received: {slice_axis}"
            ),
        )

    binary_mask = _validate_mask(mask)
    validated_spacing = _validate_spacing(spacing)

    lesion_voxel_count = int(
        np.count_nonzero(binary_mask)
    )

    voxel_volume_mm3 = float(
        np.prod(
            np.asarray(
                validated_spacing,
                dtype=np.float64,
            )
        )
    )

    lesion_volume_mm3 = (
        lesion_voxel_count * voxel_volume_mm3
    )
    lesion_volume_ml = (
        lesion_volume_mm3 / MM3_PER_ML
    )

    non_slice_axes = tuple(
        axis
        for axis in range(binary_mask.ndim)
        if axis != slice_axis
    )

    occupied_slices = np.any(
        binary_mask,
        axis=non_slice_axes,
    )

    lesion_slice_indices = tuple(
        int(index)
        for index in np.flatnonzero(
            occupied_slices
        )
    )

    return LesionMeasurements(
        lesion_detected=lesion_voxel_count > 0,
        lesion_voxel_count=lesion_voxel_count,
        voxel_volume_mm3=voxel_volume_mm3,
        lesion_volume_mm3=lesion_volume_mm3,
        lesion_volume_ml=lesion_volume_ml,
        lesion_slice_count=len(lesion_slice_indices),
        lesion_slice_indices=lesion_slice_indices,
    )