"""Tests for the thread-safe nnU-Net model loader."""

from pathlib import Path
from typing import Any

import pytest

from inference.app.model_loader import (
    ModelLoader,
    ModelLoaderConfig,
    ModelLoaderError,
)


class FakePredictor:
    """Fake Predictor used without nnU-Net, PyTorch, or a GPU."""

    def __init__(
        self,
        *,
        initialization_error: Exception | None = None,
    ) -> None:
        self.initialization_error = initialization_error
        self.initialize_calls: list[
            dict[str, Any]
        ] = []

    def initialize_from_trained_model_folder(
        self,
        model_training_output_dir: str,
        use_folds: tuple[int | str, ...],
        checkpoint_name: str,
    ) -> None:
        """Record the model initialization arguments."""

        self.initialize_calls.append(
            {
                "model_training_output_dir": (
                    model_training_output_dir
                ),
                "use_folds": use_folds,
                "checkpoint_name": checkpoint_name,
            }
        )

        if self.initialization_error is not None:
            raise self.initialization_error


def create_fake_model_bundle(
    base_directory: Path,
    *,
    checkpoint_name: str = "checkpoint_best.pth",
) -> Path:
    """Create the minimum fake nnU-Net model directory."""

    model_directory = (
        base_directory / "trained_model"
    )
    fold_directory = model_directory / "fold_0"

    fold_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    (model_directory / "dataset.json").write_text(
        "{}",
        encoding="utf-8",
    )
    (model_directory / "plans.json").write_text(
        "{}",
        encoding="utf-8",
    )
    (fold_directory / checkpoint_name).write_bytes(
        b"fake-checkpoint"
    )

    return model_directory


def test_loads_predictor_and_forwards_configuration(
    tmp_path: Path,
) -> None:
    """Create and initialize the Predictor with configured values."""

    model_directory = create_fake_model_bundle(
        tmp_path
    )
    predictor = FakePredictor()
    factory_calls: list[
        ModelLoaderConfig
    ] = []

    def predictor_factory(
        config: ModelLoaderConfig,
    ) -> FakePredictor:
        factory_calls.append(config)
        return predictor

    config = ModelLoaderConfig(
        model_training_output_dir=model_directory,
        folds=(0,),
        checkpoint_name="checkpoint_best.pth",
        device="cuda:0",
    )
    loader = ModelLoader(
        config,
        predictor_factory=predictor_factory,
    )

    loaded_predictor = loader.load()

    assert loaded_predictor is predictor
    assert loader.is_loaded is True
    assert loader.config is config
    assert factory_calls == [config]
    assert predictor.initialize_calls == [
        {
            "model_training_output_dir": str(
                model_directory
            ),
            "use_folds": (0,),
            "checkpoint_name": (
                "checkpoint_best.pth"
            ),
        }
    ]


def test_repeated_load_returns_cached_predictor(
    tmp_path: Path,
) -> None:
    """Do not create or initialize duplicate Predictor instances."""

    model_directory = create_fake_model_bundle(
        tmp_path
    )
    predictor = FakePredictor()
    factory_call_count = 0

    def predictor_factory(
        config: ModelLoaderConfig,
    ) -> FakePredictor:
        nonlocal factory_call_count
        factory_call_count += 1
        return predictor

    loader = ModelLoader(
        ModelLoaderConfig(
            model_training_output_dir=model_directory,
        ),
        predictor_factory=predictor_factory,
    )

    first_result = loader.load()
    second_result = loader.load()
    loaded_result = loader.get_loaded_predictor()

    assert first_result is predictor
    assert second_result is predictor
    assert loaded_result is predictor
    assert factory_call_count == 1
    assert len(predictor.initialize_calls) == 1


def test_get_loaded_predictor_fails_before_loading(
    tmp_path: Path,
) -> None:
    """Reject Predictor access before application startup loading."""

    loader = ModelLoader(
        ModelLoaderConfig(
            model_training_output_dir=(
                tmp_path / "model"
            ),
            validate_model_files=False,
        ),
        predictor_factory=lambda config: (
            FakePredictor()
        ),
    )

    with pytest.raises(
        ModelLoaderError,
    ) as error_info:
        loader.get_loaded_predictor()

    assert error_info.value.code == "MODEL_NOT_LOADED"
    assert loader.is_loaded is False


def test_missing_model_directory_is_rejected(
    tmp_path: Path,
) -> None:
    """Reject a configured model directory that does not exist."""

    loader = ModelLoader(
        ModelLoaderConfig(
            model_training_output_dir=(
                tmp_path / "missing-model"
            ),
        ),
        predictor_factory=lambda config: (
            FakePredictor()
        ),
    )

    with pytest.raises(
        ModelLoaderError,
    ) as error_info:
        loader.load()

    assert (
        error_info.value.code
        == "MODEL_DIRECTORY_NOT_FOUND"
    )


def test_model_path_must_be_directory(
    tmp_path: Path,
) -> None:
    """Reject a regular file used as the model directory."""

    model_file = tmp_path / "model-file"
    model_file.write_text(
        "not a directory",
        encoding="utf-8",
    )

    loader = ModelLoader(
        ModelLoaderConfig(
            model_training_output_dir=model_file,
        ),
        predictor_factory=lambda config: (
            FakePredictor()
        ),
    )

    with pytest.raises(
        ModelLoaderError,
    ) as error_info:
        loader.load()

    assert (
        error_info.value.code
        == "INVALID_MODEL_DIRECTORY"
    )


@pytest.mark.parametrize(
    "missing_relative_path",
    [
        Path("dataset.json"),
        Path("plans.json"),
        Path("fold_0") / "checkpoint_best.pth",
    ],
)
def test_missing_required_model_file_is_rejected(
    tmp_path: Path,
    missing_relative_path: Path,
) -> None:
    """Reject incomplete nnU-Net model bundles."""

    model_directory = create_fake_model_bundle(
        tmp_path
    )
    (
        model_directory / missing_relative_path
    ).unlink()

    loader = ModelLoader(
        ModelLoaderConfig(
            model_training_output_dir=model_directory,
        ),
        predictor_factory=lambda config: (
            FakePredictor()
        ),
    )

    with pytest.raises(
        ModelLoaderError,
    ) as error_info:
        loader.load()

    assert (
        error_info.value.code
        == "MODEL_FILES_MISSING"
    )


@pytest.mark.parametrize(
    "folds",
    [
        (),
        (-1,),
        (True,),
        ("0",),
        (0, 0),
    ],
)
def test_invalid_fold_configuration_is_rejected(
    tmp_path: Path,
    folds: tuple[Any, ...],
) -> None:
    """Reject empty, invalid, or duplicated fold identifiers."""

    loader = ModelLoader(
        ModelLoaderConfig(
            model_training_output_dir=(
                tmp_path / "model"
            ),
            folds=folds,
            validate_model_files=False,
        ),
        predictor_factory=lambda config: (
            FakePredictor()
        ),
    )

    with pytest.raises(
        ModelLoaderError,
    ) as error_info:
        loader.load()

    assert (
        error_info.value.code
        == "INVALID_MODEL_CONFIGURATION"
    )


@pytest.mark.parametrize(
    "checkpoint_name",
    [
        "",
        "fold_0/checkpoint_best.pth",
        "fold_0\\checkpoint_best.pth",
    ],
)
def test_invalid_checkpoint_name_is_rejected(
    tmp_path: Path,
    checkpoint_name: str,
) -> None:
    """Require a checkpoint file name instead of a path."""

    loader = ModelLoader(
        ModelLoaderConfig(
            model_training_output_dir=(
                tmp_path / "model"
            ),
            checkpoint_name=checkpoint_name,
            validate_model_files=False,
        ),
        predictor_factory=lambda config: (
            FakePredictor()
        ),
    )

    with pytest.raises(
        ModelLoaderError,
    ) as error_info:
        loader.load()

    assert (
        error_info.value.code
        == "INVALID_MODEL_CONFIGURATION"
    )


@pytest.mark.parametrize(
    "tile_step_size",
    [
        0.0,
        -0.1,
        1.1,
        True,
        "0.5",
    ],
)
def test_invalid_tile_step_size_is_rejected(
    tmp_path: Path,
    tile_step_size: Any,
) -> None:
    """Require a numeric tile step in the interval (0, 1]."""

    loader = ModelLoader(
        ModelLoaderConfig(
            model_training_output_dir=(
                tmp_path / "model"
            ),
            tile_step_size=tile_step_size,
            validate_model_files=False,
        ),
        predictor_factory=lambda config: (
            FakePredictor()
        ),
    )

    with pytest.raises(
        ModelLoaderError,
    ) as error_info:
        loader.load()

    assert (
        error_info.value.code
        == "INVALID_MODEL_CONFIGURATION"
    )


@pytest.mark.parametrize(
    "device",
    [
        "",
        "   ",
    ],
)
def test_empty_device_is_rejected(
    tmp_path: Path,
    device: str,
) -> None:
    """Reject an empty model device value."""

    loader = ModelLoader(
        ModelLoaderConfig(
            model_training_output_dir=(
                tmp_path / "model"
            ),
            device=device,
            validate_model_files=False,
        ),
        predictor_factory=lambda config: (
            FakePredictor()
        ),
    )

    with pytest.raises(
        ModelLoaderError,
    ) as error_info:
        loader.load()

    assert (
        error_info.value.code
        == "INVALID_MODEL_CONFIGURATION"
    )


def test_none_predictor_is_rejected(
    tmp_path: Path,
) -> None:
    """Reject a factory that returns no Predictor."""

    loader = ModelLoader(
        ModelLoaderConfig(
            model_training_output_dir=(
                tmp_path / "model"
            ),
            validate_model_files=False,
        ),
        predictor_factory=lambda config: None,
    )

    with pytest.raises(
        ModelLoaderError,
    ) as error_info:
        loader.load()

    assert error_info.value.code == "INVALID_PREDICTOR"


def test_predictor_without_initialize_method_is_rejected(
    tmp_path: Path,
) -> None:
    """Reject an incompatible Predictor object."""

    loader = ModelLoader(
        ModelLoaderConfig(
            model_training_output_dir=(
                tmp_path / "model"
            ),
            validate_model_files=False,
        ),
        predictor_factory=lambda config: object(),
    )

    with pytest.raises(
        ModelLoaderError,
    ) as error_info:
        loader.load()

    assert error_info.value.code == "INVALID_PREDICTOR"


def test_predictor_creation_failure_is_converted(
    tmp_path: Path,
) -> None:
    """Convert an unexpected factory error to a loader error."""

    def failing_factory(
        config: ModelLoaderConfig,
    ) -> FakePredictor:
        raise RuntimeError(
            "Predictor construction failed."
        )

    loader = ModelLoader(
        ModelLoaderConfig(
            model_training_output_dir=(
                tmp_path / "model"
            ),
            validate_model_files=False,
        ),
        predictor_factory=failing_factory,
    )

    with pytest.raises(
        ModelLoaderError,
    ) as error_info:
        loader.load()

    assert (
        error_info.value.code
        == "PREDICTOR_CREATION_FAILED"
    )


def test_existing_model_loader_error_is_preserved(
    tmp_path: Path,
) -> None:
    """Preserve deliberate errors raised by the Predictor factory."""

    expected_error = ModelLoaderError(
        code="CUSTOM_FACTORY_ERROR",
        message="Custom factory error.",
    )

    def failing_factory(
        config: ModelLoaderConfig,
    ) -> FakePredictor:
        raise expected_error

    loader = ModelLoader(
        ModelLoaderConfig(
            model_training_output_dir=(
                tmp_path / "model"
            ),
            validate_model_files=False,
        ),
        predictor_factory=failing_factory,
    )

    with pytest.raises(
        ModelLoaderError,
    ) as error_info:
        loader.load()

    assert error_info.value is expected_error
    assert (
        error_info.value.code
        == "CUSTOM_FACTORY_ERROR"
    )


def test_predictor_initialization_failure_is_converted(
    tmp_path: Path,
) -> None:
    """Convert model checkpoint initialization failures."""

    predictor = FakePredictor(
        initialization_error=RuntimeError(
            "Checkpoint is invalid."
        )
    )

    loader = ModelLoader(
        ModelLoaderConfig(
            model_training_output_dir=(
                tmp_path / "model"
            ),
            validate_model_files=False,
        ),
        predictor_factory=lambda config: predictor,
    )

    with pytest.raises(
        ModelLoaderError,
    ) as error_info:
        loader.load()

    assert (
        error_info.value.code
        == "MODEL_INITIALIZATION_FAILED"
    )
    assert loader.is_loaded is False