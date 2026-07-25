"""Unit tests for NIfTI input validation."""

from pathlib import Path

import nibabel as nib
import numpy as np
import pytest

from inference.app.preprocessing import (
    NiftiValidationError,
    load_and_validate_nifti,
)


def save_fake_nifti(
    path: Path,
    data: np.ndarray,
    spacing: tuple[float, float, float] = (0.5, 0.5, 5.0),
) -> Path:
    """Create and save a fake NIfTI image for testing."""

    affine = np.diag(
        [
            spacing[0],
            spacing[1],
            spacing[2],
            1.0,
        ]
    ).astype(np.float64)

    image = nib.Nifti1Image(data, affine)

    if data.ndim == 2:
        image.header.set_zooms(spacing[:2])
    elif data.ndim == 3:
        image.header.set_zooms(spacing)
    elif data.ndim == 4:
        image.header.set_zooms((*spacing, 1.0))

    nib.save(image, str(path))
    return path


def assert_validation_error(
    expected_code: str,
    file_path: Path,
    **kwargs,
) -> None:
    """Assert that NIfTI validation fails with the expected error code."""

    with pytest.raises(NiftiValidationError) as exc_info:
        load_and_validate_nifti(file_path, **kwargs)

    assert exc_info.value.code == expected_code


def test_valid_3d_nifti_passes(tmp_path: Path) -> None:
    """A valid three-dimensional NIfTI file must pass validation."""

    data = np.arange(
        4 * 5 * 6,
        dtype=np.float32,
    ).reshape(4, 5, 6)

    file_path = save_fake_nifti(
        tmp_path / "valid_ct.nii.gz",
        data,
        spacing=(0.5, 0.5, 5.0),
    )

    volume = load_and_validate_nifti(file_path)

    assert volume.shape == (4, 5, 6)
    assert volume.spacing == pytest.approx((0.5, 0.5, 5.0))
    assert volume.data.dtype == np.float32
    assert volume.affine.shape == (4, 4)
    np.testing.assert_allclose(volume.data, data)


def test_invalid_extension_is_rejected(tmp_path: Path) -> None:
    """A file without a .nii or .nii.gz extension must be rejected."""

    file_path = tmp_path / "not_nifti.txt"
    file_path.write_text("fake medical image", encoding="utf-8")

    assert_validation_error(
        "INVALID_NIFTI_EXTENSION",
        file_path,
    )


@pytest.mark.parametrize(
    ("shape", "filename"),
    [
        ((8, 8), "two_dimensional.nii.gz"),
        ((8, 8, 4, 2), "four_dimensional.nii.gz"),
    ],
)
def test_non_3d_nifti_is_rejected(
    tmp_path: Path,
    shape: tuple[int, ...],
    filename: str,
) -> None:
    """Two-dimensional and four-dimensional NIfTI files must be rejected."""

    data = np.zeros(shape, dtype=np.float32)
    file_path = save_fake_nifti(tmp_path / filename, data)

    assert_validation_error(
        "INVALID_NIFTI_DIMENSION",
        file_path,
    )


def test_nan_value_is_rejected(tmp_path: Path) -> None:
    """A NIfTI volume containing NaN must be rejected."""

    data = np.zeros((8, 8, 4), dtype=np.float32)
    data[2, 3, 1] = np.nan

    file_path = save_fake_nifti(
        tmp_path / "contains_nan.nii.gz",
        data,
    )

    assert_validation_error(
        "NON_FINITE_NIFTI_VALUES",
        file_path,
    )


def test_voxel_limit_is_enforced(tmp_path: Path) -> None:
    """A volume exceeding the configured voxel count must be rejected."""

    data = np.zeros((4, 4, 4), dtype=np.float32)
    file_path = save_fake_nifti(
        tmp_path / "too_many_voxels.nii.gz",
        data,
    )

    assert_validation_error(
        "NIFTI_VOXEL_LIMIT_EXCEEDED",
        file_path,
        max_voxels=63,
    )


def test_corrupted_nifti_is_rejected(tmp_path: Path) -> None:
    """A corrupted file with a NIfTI extension must be rejected."""

    file_path = tmp_path / "corrupted.nii.gz"
    file_path.write_bytes(b"this is not a nifti file")

    assert_validation_error(
        "INVALID_NIFTI_FILE",
        file_path,
    )


def test_empty_nifti_is_rejected(tmp_path: Path) -> None:
    """An empty NIfTI file must be rejected."""

    file_path = tmp_path / "empty.nii.gz"
    file_path.touch()

    assert_validation_error(
        "EMPTY_NIFTI_FILE",
        file_path,
    )


def test_missing_nifti_is_rejected(tmp_path: Path) -> None:
    """A nonexistent NIfTI file must be rejected."""

    file_path = tmp_path / "missing.nii.gz"

    assert_validation_error(
        "NIFTI_FILE_NOT_FOUND",
        file_path,
    )