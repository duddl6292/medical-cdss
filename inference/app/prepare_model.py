"""Prepare the Exp05 model before the MOSEC server starts."""

from __future__ import annotations

import hashlib
import hmac
import logging
import shutil
import stat
from pathlib import Path, PurePosixPath
from tempfile import TemporaryDirectory
from zipfile import BadZipFile, ZipFile

from google.cloud import storage

from .settings import InferenceSettings, settings


LOGGER = logging.getLogger(__name__)


class ModelPreparationError(RuntimeError):
    """Raised when the model cannot be prepared safely."""


def _calculate_sha256(file_path: Path) -> str:
    digest = hashlib.sha256()

    with file_path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def _fold_directory(fold: int | str) -> str:
    return "fold_all" if fold == "all" else f"fold_{fold}"


def _missing_model_files(
    model_dir: Path,
    runtime_settings: InferenceSettings,
) -> list[Path]:
    required_files = [
        model_dir / "dataset.json",
        model_dir / "plans.json",
    ]

    for fold in runtime_settings.model_folds:
        required_files.append(
            model_dir
            / _fold_directory(fold)
            / runtime_settings.model_checkpoint
        )

    return [
        file_path
        for file_path in required_files
        if not file_path.is_file()
    ]


def _safe_extract_zip(
    archive_path: Path,
    destination: Path,
) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    destination_root = destination.resolve()

    try:
        with ZipFile(archive_path) as archive:
            for member in archive.infolist():
                normalized_name = member.filename.replace("\\", "/")
                relative_path = PurePosixPath(normalized_name)

                if (
                    relative_path.is_absolute()
                    or ".." in relative_path.parts
                ):
                    raise ModelPreparationError(
                        "The model ZIP contains an unsafe path: "
                        f"{member.filename}"
                    )

                file_type = (
                    member.external_attr >> 16
                ) & 0o170000

                if file_type == stat.S_IFLNK:
                    raise ModelPreparationError(
                        "The model ZIP must not contain symbolic links: "
                        f"{member.filename}"
                    )

                if member.flag_bits & 0x1:
                    raise ModelPreparationError(
                        "The model ZIP must not contain encrypted files: "
                        f"{member.filename}"
                    )

                target_path = (
                    destination
                    / Path(*relative_path.parts)
                ).resolve()

                if not target_path.is_relative_to(destination_root):
                    raise ModelPreparationError(
                        "The model ZIP contains a path outside "
                        "the extraction directory."
                    )

                if member.is_dir() or normalized_name.endswith("/"):
                    target_path.mkdir(parents=True, exist_ok=True)
                    continue

                target_path.parent.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                with archive.open(member) as source:
                    with target_path.open("wb") as target:
                        shutil.copyfileobj(source, target)

    except BadZipFile as error:
        raise ModelPreparationError(
            "The downloaded model artifact is not a valid ZIP file."
        ) from error


def _find_model_directory(
    extraction_root: Path,
    runtime_settings: InferenceSettings,
) -> Path:
    expected_name = runtime_settings.model_dir.name

    candidates = [
        path
        for path in extraction_root.rglob(expected_name)
        if (
            path.is_dir()
            and not _missing_model_files(
                path,
                runtime_settings,
            )
        )
    ]

    if len(candidates) != 1:
        raise ModelPreparationError(
            "Expected exactly one valid Exp05 model directory "
            f"named '{expected_name}', but found "
            f"{len(candidates)}."
        )

    return candidates[0]


def prepare_model(
    runtime_settings: InferenceSettings = settings,
) -> Path:
    """Download, verify and install the configured Exp05 model."""

    target_model_dir = runtime_settings.model_dir
    missing_files = _missing_model_files(
        target_model_dir,
        runtime_settings,
    )

    if not missing_files:
        LOGGER.info(
            "Exp05 model is already prepared at %s",
            target_model_dir,
        )
        return target_model_dir

    if target_model_dir.exists():
        missing_text = ", ".join(
            str(path)
            for path in missing_files
        )
        raise ModelPreparationError(
            "MODEL_DIR already exists but is incomplete. "
            f"Missing files: {missing_text}"
        )

    cloud_values = (
        runtime_settings.model_bucket,
        runtime_settings.model_object,
        runtime_settings.model_sha256,
    )

    if not all(cloud_values):
        raise ModelPreparationError(
            "MODEL_BUCKET, MODEL_OBJECT and MODEL_SHA256 "
            "must be configured before starting MOSEC."
        )

    runtime_settings.model_cache_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    with TemporaryDirectory(
        prefix=".exp05-model-",
        dir=runtime_settings.model_cache_dir,
    ) as temporary_directory:
        temporary_root = Path(temporary_directory)
        archive_path = temporary_root / "model.zip"
        extraction_root = temporary_root / "extracted"

        LOGGER.info(
            "Downloading gs://%s/%s",
            runtime_settings.model_bucket,
            runtime_settings.model_object,
        )

        try:
            client = storage.Client()
            bucket = client.bucket(
                runtime_settings.model_bucket
            )
            blob = bucket.blob(
                runtime_settings.model_object
            )
            blob.download_to_filename(str(archive_path))
        except Exception as error:
            raise ModelPreparationError(
                "Failed to download the Exp05 model "
                "from Cloud Storage."
            ) from error

        actual_sha256 = _calculate_sha256(archive_path)

        if not hmac.compare_digest(
            actual_sha256,
            runtime_settings.model_sha256,
        ):
            raise ModelPreparationError(
                "Downloaded model SHA-256 does not match. "
                f"Expected {runtime_settings.model_sha256}, "
                f"received {actual_sha256}."
            )

        LOGGER.info("Model SHA-256 verification completed.")

        _safe_extract_zip(
            archive_path,
            extraction_root,
        )

        extracted_model_dir = _find_model_directory(
            extraction_root,
            runtime_settings,
        )

        target_model_dir.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        extracted_model_dir.rename(target_model_dir)

        final_missing_files = _missing_model_files(
            target_model_dir,
            runtime_settings,
        )

        if final_missing_files:
            raise ModelPreparationError(
                "The installed Exp05 model failed final validation."
            )

    LOGGER.info(
        "Exp05 model prepared successfully at %s",
        target_model_dir,
    )

    return target_model_dir


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    model_dir = prepare_model()
    print(f"MODEL_READY={model_dir}")


if __name__ == "__main__":
    main()