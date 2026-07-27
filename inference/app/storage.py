"""Cloud Storage input download and result artifact upload helpers."""

from __future__ import annotations

import mimetypes
import os
import shutil
from collections.abc import Iterable
from pathlib import Path
from urllib.parse import unquote, urlparse

from google.cloud import storage as gcs


class StorageError(RuntimeError):
    """Raised when an inference storage operation cannot finish safely."""

    def __init__(self, *, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def parse_gs_uri(uri: str) -> tuple[str, str]:
    """Split a gs:// URI into its bucket name and object name."""

    if not isinstance(uri, str) or not uri.startswith("gs://"):
        raise StorageError(
            code="INVALID_STORAGE_URI",
            message="A valid gs:// storage URI is required.",
        )

    bucket_name, separator, object_name = uri[5:].partition("/")

    if (
        not separator
        or not bucket_name.strip()
        or not object_name.strip()
    ):
        raise StorageError(
            code="INVALID_STORAGE_URI",
            message=(
                "The Cloud Storage URI must include both "
                "a bucket and an object path."
            ),
        )

    return bucket_name, object_name


def _file_uri_to_path(uri: str) -> Path:
    """Convert an allowed file:// URI into a local filesystem path."""

    parsed = urlparse(uri)

    if parsed.scheme != "file":
        raise ValueError("A file:// URI is required.")

    if parsed.netloc not in ("", "localhost"):
        raise ValueError("Remote file:// hosts are not supported.")

    path_text = unquote(parsed.path)

    if (
        os.name == "nt"
        and len(path_text) >= 3
        and path_text[0] == "/"
        and path_text[2] == ":"
    ):
        path_text = path_text[1:]

    if not path_text:
        raise ValueError("The file:// URI does not contain a path.")

    return Path(path_text)


class ArtifactStorage:
    """Download inference inputs and upload generated artifacts."""

    def __init__(
        self,
        *,
        results_uri_prefix: str,
        allow_local_files: bool = False,
    ) -> None:
        self.results_uri_prefix = results_uri_prefix.rstrip("/")
        self.allow_local_files = allow_local_files
        self._client: gcs.Client | None = None

    def _get_client(self) -> gcs.Client:
        if self._client is None:
            self._client = gcs.Client()
        return self._client

    def download_input(
        self,
        input_uri: str,
        destination: Path,
    ) -> Path:
        """Download one input NIfTI file to a request workspace."""

        destination = Path(destination)

        try:
            destination.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            if input_uri.startswith("gs://"):
                bucket_name, object_name = parse_gs_uri(input_uri)
                blob = (
                    self._get_client()
                    .bucket(bucket_name)
                    .blob(object_name)
                )
                blob.download_to_filename(str(destination))

            elif input_uri.startswith("file://"):
                if not self.allow_local_files:
                    raise StorageError(
                        code="INPUT_DOWNLOAD_FAILED",
                        message="Local input files are disabled.",
                    )

                source = _file_uri_to_path(input_uri)

                if not source.is_file():
                    raise FileNotFoundError(source)

                if source.resolve() != destination.resolve():
                    shutil.copy2(source, destination)

            else:
                raise StorageError(
                    code="INPUT_DOWNLOAD_FAILED",
                    message=(
                        "The input URI must use the gs:// scheme."
                    ),
                )

        except StorageError as error:
            if error.code == "INPUT_DOWNLOAD_FAILED":
                raise

            raise StorageError(
                code="INPUT_DOWNLOAD_FAILED",
                message=(
                    "The input NIfTI file could not be downloaded."
                ),
            ) from error

        except Exception as error:
            raise StorageError(
                code="INPUT_DOWNLOAD_FAILED",
                message=(
                    "The input NIfTI file could not be downloaded."
                ),
            ) from error

        return destination

    @staticmethod
    def _validate_result_key(result_key: str) -> None:
        if (
            not result_key
            or result_key in {".", ".."}
            or "/" in result_key
            or "\\" in result_key
        ):
            raise StorageError(
                code="ARTIFACT_UPLOAD_FAILED",
                message="The result key is invalid.",
            )

    def upload_artifacts(
        self,
        paths: Iterable[Path],
        *,
        result_key: str,
    ) -> dict[str, str]:
        """Upload result files and return filename-to-URI mappings."""

        self._validate_result_key(result_key)
        source_paths = [Path(path) for path in paths]

        if not source_paths:
            raise StorageError(
                code="ARTIFACT_UPLOAD_FAILED",
                message="No result artifacts were provided.",
            )

        filenames = [path.name for path in source_paths]

        if len(filenames) != len(set(filenames)):
            raise StorageError(
                code="ARTIFACT_UPLOAD_FAILED",
                message="Result artifact filenames must be unique.",
            )

        try:
            for source_path in source_paths:
                if not source_path.is_file():
                    raise FileNotFoundError(source_path)

            if self.results_uri_prefix.startswith("gs://"):
                return self._upload_to_gcs(
                    source_paths,
                    result_key=result_key,
                )

            if self.results_uri_prefix.startswith("file://"):
                if not self.allow_local_files:
                    raise StorageError(
                        code="ARTIFACT_UPLOAD_FAILED",
                        message="Local result storage is disabled.",
                    )

                return self._upload_to_local_directory(
                    source_paths,
                    result_key=result_key,
                )

            raise StorageError(
                code="ARTIFACT_UPLOAD_FAILED",
                message=(
                    "RESULTS_URI_PREFIX must use the gs:// scheme."
                ),
            )

        except StorageError:
            raise

        except Exception as error:
            raise StorageError(
                code="ARTIFACT_UPLOAD_FAILED",
                message="Result artifacts could not be uploaded.",
            ) from error

    def _upload_to_gcs(
        self,
        source_paths: list[Path],
        *,
        result_key: str,
    ) -> dict[str, str]:
        placeholder_uri = (
            f"{self.results_uri_prefix}/placeholder"
        )
        bucket_name, placeholder_object = parse_gs_uri(
            placeholder_uri
        )
        base_object = placeholder_object.removesuffix(
            "/placeholder"
        )

        bucket = self._get_client().bucket(bucket_name)
        uploaded: dict[str, str] = {}

        for source_path in source_paths:
            object_name = "/".join(
                part
                for part in (
                    base_object.strip("/"),
                    result_key,
                    source_path.name,
                )
                if part
            )

            content_type, _ = mimetypes.guess_type(
                source_path.name
            )
            blob = bucket.blob(object_name)
            blob.upload_from_filename(
                str(source_path),
                content_type=(
                    content_type or "application/octet-stream"
                ),
            )

            uploaded[source_path.name] = (
                f"gs://{bucket_name}/{object_name}"
            )

        return uploaded

    def _upload_to_local_directory(
        self,
        source_paths: list[Path],
        *,
        result_key: str,
    ) -> dict[str, str]:
        base_directory = _file_uri_to_path(
            self.results_uri_prefix
        )
        result_directory = base_directory / result_key
        result_directory.mkdir(parents=True, exist_ok=True)

        uploaded: dict[str, str] = {}

        for source_path in source_paths:
            destination = result_directory / source_path.name

            if source_path.resolve() != destination.resolve():
                shutil.copy2(source_path, destination)

            uploaded[source_path.name] = (
                f"{self.results_uri_prefix}/"
                f"{result_key}/{source_path.name}"
            )

        return uploaded