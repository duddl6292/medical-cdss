"""Tests for lesion volume and slice measurements."""

import numpy as np
import pytest

from inference.app.measurements import (
    LesionMeasurementError,
    calculate_lesion_measurements,
)


def test_calculates_lesion_volume_and_slices() -> None:
    """Calculate volume and Z-axis slice indices correctly."""

    mask = np.zeros((4, 5, 6), dtype=np.uint8)

    mask[0, 0, 1] = 1
    mask[1, 2, 1] = 1
    mask[3, 4, 4] = 1

    result = calculate_lesion_measurements(
        mask=mask,
        spacing=(0.5, 0.5, 2.0),
    )

    assert result.lesion_detected is True
    assert result.lesion_voxel_count == 3
    assert result.voxel_volume_mm3 == pytest.approx(0.5)
    assert result.lesion_volume_mm3 == pytest.approx(1.5)
    assert result.lesion_volume_ml == pytest.approx(0.0015)
    assert result.lesion_slice_count == 2
    assert result.lesion_slice_indices == (1, 4)


def test_converts_result_to_json_compatible_dictionary() -> None:
    """Convert tuple slice indices to a JSON-compatible list."""

    mask = np.zeros((2, 2, 3), dtype=np.uint8)
    mask[0, 0, 2] = 1

    result = calculate_lesion_measurements(
        mask=mask,
        spacing=(1.0, 1.0, 1.0),
    )

    assert result.to_dict() == {
        "lesion_detected": True,
        "lesion_voxel_count": 1,
        "voxel_volume_mm3": 1.0,
        "lesion_volume_mm3": 1.0,
        "lesion_volume_ml": 0.001,
        "lesion_slice_count": 1,
        "lesion_slice_indices": [2],
    }


def test_empty_lesion_mask_returns_zero_measurements() -> None:
    """Return zero values when no lesion is detected."""

    mask = np.zeros((3, 4, 5), dtype=np.uint8)

    result = calculate_lesion_measurements(
        mask=mask,
        spacing=(0.5, 0.5, 1.0),
    )

    assert result.lesion_detected is False
    assert result.lesion_voxel_count == 0
    assert result.voxel_volume_mm3 == pytest.approx(0.25)
    assert result.lesion_volume_mm3 == pytest.approx(0.0)
    assert result.lesion_volume_ml == pytest.approx(0.0)
    assert result.lesion_slice_count == 0
    assert result.lesion_slice_indices == ()


def test_boolean_mask_is_accepted() -> None:
    """Accept a three-dimensional boolean lesion mask."""

    mask = np.zeros((2, 2, 2), dtype=bool)
    mask[1, 1, 1] = True

    result = calculate_lesion_measurements(
        mask=mask,
        spacing=(1.0, 1.0, 2.0),
    )

    assert result.lesion_detected is True
    assert result.lesion_voxel_count == 1
    assert result.lesion_volume_mm3 == pytest.approx(2.0)
    assert result.lesion_slice_indices == (1,)


@pytest.mark.parametrize(
    "shape",
    [
        (10, 10),
        (2, 2, 2, 2),
    ],
)
def test_non_3d_mask_is_rejected(
    shape: tuple[int, ...],
) -> None:
    """Reject masks that are not three-dimensional."""

    mask = np.zeros(shape, dtype=np.uint8)

    with pytest.raises(
        LesionMeasurementError,
    ) as error_info:
        calculate_lesion_measurements(
            mask=mask,
            spacing=(1.0, 1.0, 1.0),
        )

    assert error_info.value.code == "INVALID_MASK_DIMENSION"


def test_non_binary_mask_label_is_rejected() -> None:
    """Reject mask labels other than background 0 and lesion 1."""

    mask = np.zeros((3, 3, 3), dtype=np.uint8)
    mask[1, 1, 1] = 2

    with pytest.raises(
        LesionMeasurementError,
    ) as error_info:
        calculate_lesion_measurements(
            mask=mask,
            spacing=(1.0, 1.0, 1.0),
        )

    assert error_info.value.code == "INVALID_MASK_LABELS"


def test_non_finite_mask_value_is_rejected() -> None:
    """Reject NaN or infinite mask values."""

    mask = np.zeros((3, 3, 3), dtype=np.float64)
    mask[1, 1, 1] = np.nan

    with pytest.raises(
        LesionMeasurementError,
    ) as error_info:
        calculate_lesion_measurements(
            mask=mask,
            spacing=(1.0, 1.0, 1.0),
        )

    assert error_info.value.code == "NON_FINITE_MASK_VALUES"


@pytest.mark.parametrize(
    "spacing",
    [
        (1.0, 1.0),
        (1.0, 1.0, 1.0, 1.0),
        (1.0, 0.0, 1.0),
        (1.0, -1.0, 1.0),
        (1.0, np.nan, 1.0),
        ("x", "1", "2"),
    ],
)
def test_invalid_voxel_spacing_is_rejected(
    spacing: tuple[object, ...],
) -> None:
    """Reject incomplete, non-positive or non-numeric spacing."""

    mask = np.zeros((3, 3, 3), dtype=np.uint8)

    with pytest.raises(
        LesionMeasurementError,
    ) as error_info:
        calculate_lesion_measurements(
            mask=mask,
            spacing=spacing,
        )

    assert error_info.value.code == "INVALID_VOXEL_SPACING"


@pytest.mark.parametrize(
    "slice_axis",
    [
        -1,
        3,
        1.5,
        True,
    ],
)
def test_invalid_slice_axis_is_rejected(
    slice_axis: object,
) -> None:
    """Reject an invalid array axis for slice counting."""

    mask = np.zeros((3, 3, 3), dtype=np.uint8)

    with pytest.raises(
        LesionMeasurementError,
    ) as error_info:
        calculate_lesion_measurements(
            mask=mask,
            spacing=(1.0, 1.0, 1.0),
            slice_axis=slice_axis,
        )

    assert error_info.value.code == "INVALID_SLICE_AXIS"