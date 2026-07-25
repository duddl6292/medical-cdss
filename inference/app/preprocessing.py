"""NIfTI loading and input validation."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import nibabel as nib
import numpy as np
from numpy.typing import NDArray

from .settings import settings


class NiftiValidationError(ValueError):
    """Raised when an uploaded NIfTI volume is invalid."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class NiftiVolume:
    """Validated three-dimensional NIfTI volume."""

    data: NDArray[np.float32]
    affine: NDArray[np.float64]
    header: Any
    shape: tuple[int, int, int]
    spacing: tuple[float, float, float]


def is_nifti_filename(filename: str) -> bool:
    """Return True only for .nii and .nii.gz filenames."""

    lower_name = filename.lower()
    return lower_name.endswith(".nii") or lower_name.endswith(".nii.gz")


def load_and_validate_nifti(
    file_path: str | Path,
    *,
    max_bytes: int | None = None,
    max_voxels: int | None = None,
) -> NiftiVolume:
    """Load a NIfTI file and validate its basic medical-image structure."""

    path = Path(file_path)
    byte_limit = max_bytes or settings.max_nifti_bytes
    voxel_limit = max_voxels or settings.max_nifti_voxels

    if not path.is_file():
        raise NiftiValidationError(
            "NIFTI_FILE_NOT_FOUND",
            "NIfTI file was not found.",
        )

    if not is_nifti_filename(path.name):
        raise NiftiValidationError(
            "INVALID_NIFTI_EXTENSION",
            "Only .nii and .nii.gz files are allowed.",
        )

    file_size = path.stat().st_size

    if file_size == 0:
        raise NiftiValidationError(
            "EMPTY_NIFTI_FILE",
            "The uploaded NIfTI file is empty.",
        )

    if file_size > byte_limit:
        raise NiftiValidationError(
            "NIFTI_FILE_TOO_LARGE",
            "The uploaded NIfTI file exceeds the configured size limit.",
        )

    try:
        image = nib.load(str(path))
    except Exception as exc:
        raise NiftiValidationError(
            "INVALID_NIFTI_FILE",
            "The file could not be read as a valid NIfTI image.",
        ) from exc

    shape = tuple(int(value) for value in image.shape)

    if len(shape) != 3:
        raise NiftiValidationError(
            "INVALID_NIFTI_DIMENSION",
            "A three-dimensional NIfTI volume is required.",
        )

    if any(size <= 0 for size in shape):
        raise NiftiValidationError(
            "INVALID_NIFTI_SHAPE",
            "The NIfTI volume contains an invalid dimension size.",
        )

    voxel_count = int(np.prod(shape, dtype=np.int64))

    if voxel_count > voxel_limit:
        raise NiftiValidationError(
            "NIFTI_VOXEL_LIMIT_EXCEEDED",
            "The NIfTI volume exceeds the configured voxel limit.",
        )

    affine = np.asarray(image.affine, dtype=np.float64)

    if affine.shape != (4, 4) or not np.all(np.isfinite(affine)):
        raise NiftiValidationError(
            "INVALID_NIFTI_AFFINE",
            "The NIfTI affine matrix is invalid.",
        )

    zooms = image.header.get_zooms()

    if len(zooms) < 3:
        raise NiftiValidationError(
            "INVALID_NIFTI_SPACING",
            "The NIfTI header does not contain 3D voxel spacing.",
        )

    spacing = tuple(float(value) for value in zooms[:3])

    if any(not np.isfinite(value) or value <= 0 for value in spacing):
        raise NiftiValidationError(
            "INVALID_NIFTI_SPACING",
            "NIfTI voxel spacing must contain positive finite values.",
        )

    try:
        data = np.asarray(image.dataobj, dtype=np.float32)
    except Exception as exc:
        raise NiftiValidationError(
            "NIFTI_DATA_READ_FAILED",
            "The NIfTI voxel data could not be read.",
        ) from exc

    if data.shape != shape:
        raise NiftiValidationError(
            "NIFTI_SHAPE_MISMATCH",
            "The NIfTI header and voxel data shapes do not match.",
        )

    if not np.all(np.isfinite(data)):
        raise NiftiValidationError(
            "NON_FINITE_NIFTI_VALUES",
            "The NIfTI volume contains NaN or infinite values.",
        )

    return NiftiVolume(
        data=data,
        affine=affine,
        header=image.header.copy(),
        shape=shape,
        spacing=spacing,
    )