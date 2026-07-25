"""Thread-safe loading utilities for an nnU-Net Predictor."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from typing import Callable, Protocol


FoldIdentifier = int | str


class PredictorProtocol(Protocol):
    """Interface required from an nnU-Net-compatible Predictor."""

    def initialize_from_trained_model_folder(
        self,
        model_training_output_dir: str,
        use_folds: tuple[FoldIdentifier, ...],
        checkpoint_name: str,
    ) -> None:
        """Load model configuration, network and checkpoint weights."""


class ModelLoaderError(RuntimeError):
    """Raised when model configuration or loading fails."""

    def __init__(
        self,
        *,
        code: str,
        message: str,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True, slots=True)
class ModelLoaderConfig:
    """Configuration used to construct and initialize a Predictor."""

    model_training_output_dir: Path
    folds: tuple[FoldIdentifier, ...] = (0,)
    checkpoint_name: str = "checkpoint_best.pth"

    device: str = "cuda:0"
    tile_step_size: float = 0.5
    use_gaussian: bool = True
    use_mirroring: bool = True
    perform_everything_on_device: bool = True

    verbose: bool = False
    verbose_preprocessing: bool = False
    allow_tqdm: bool = False

    validate_model_files: bool = True

    def __post_init__(self) -> None:
        """Normalize the model path to a pathlib Path."""

        object.__setattr__(
            self,
            "model_training_output_dir",
            Path(self.model_training_output_dir),
        )


PredictorFactory = Callable[
    [ModelLoaderConfig],
    PredictorProtocol,
]


def create_nnunet_predictor(
    config: ModelLoaderConfig,
) -> PredictorProtocol:
    """Create the real nnU-Net Predictor.

    Heavy dependencies are imported only when this function is called.
    Therefore this module can be tested with a fake Predictor even when
    PyTorch or nnU-Net is not installed.
    """

    try:
        import torch
        from nnunetv2.inference.predict_from_raw_data import (
            nnUNetPredictor,
        )
    except ImportError as error:
        raise ModelLoaderError(
            code="MODEL_DEPENDENCY_MISSING",
            message=(
                "PyTorch or nnunetv2 is not installed. "
                "Install the model runtime dependencies before "
                "loading the real Predictor."
            ),
        ) from error

    device = torch.device(config.device)

    return nnUNetPredictor(
        tile_step_size=config.tile_step_size,
        use_gaussian=config.use_gaussian,
        use_mirroring=config.use_mirroring,
        perform_everything_on_device=(
            config.perform_everything_on_device
        ),
        device=device,
        verbose=config.verbose,
        verbose_preprocessing=(
            config.verbose_preprocessing
        ),
        allow_tqdm=config.allow_tqdm,
    )


class ModelLoader:
    """Load and retain exactly one Predictor instance."""

    def __init__(
        self,
        config: ModelLoaderConfig,
        *,
        predictor_factory: PredictorFactory = (
            create_nnunet_predictor
        ),
    ) -> None:
        self._config = config
        self._predictor_factory = predictor_factory
        self._predictor: PredictorProtocol | None = None
        self._load_lock = Lock()

    @property
    def config(self) -> ModelLoaderConfig:
        """Return the immutable loader configuration."""

        return self._config

    @property
    def is_loaded(self) -> bool:
        """Return whether model initialization has completed."""

        return self._predictor is not None

    def load(self) -> PredictorProtocol:
        """Load the model once and return the cached Predictor.

        Multiple calls return the same Predictor instance.
        The lock prevents simultaneous startup requests from loading
        duplicate model copies into GPU memory.
        """

        if self._predictor is not None:
            return self._predictor

        with self._load_lock:
            if self._predictor is not None:
                return self._predictor

            self._validate_configuration()

            if self._config.validate_model_files:
                self._validate_model_bundle()

            predictor = self._create_predictor()

            try:
                predictor.initialize_from_trained_model_folder(
                    str(
                        self._config.model_training_output_dir
                    ),
                    use_folds=self._config.folds,
                    checkpoint_name=(
                        self._config.checkpoint_name
                    ),
                )
            except Exception as error:
                raise ModelLoaderError(
                    code="MODEL_INITIALIZATION_FAILED",
                    message=(
                        "The Predictor could not initialize from "
                        "the trained model folder."
                    ),
                ) from error

            self._predictor = predictor
            return predictor

    def get_loaded_predictor(
        self,
    ) -> PredictorProtocol:
        """Return the Predictor after startup loading has completed."""

        if self._predictor is None:
            raise ModelLoaderError(
                code="MODEL_NOT_LOADED",
                message=(
                    "The model has not been loaded. "
                    "Call load() during application startup."
                ),
            )

        return self._predictor

    def _create_predictor(
        self,
    ) -> PredictorProtocol:
        """Create a Predictor using the injected factory."""

        try:
            predictor = self._predictor_factory(
                self._config
            )
        except ModelLoaderError:
            raise
        except Exception as error:
            raise ModelLoaderError(
                code="PREDICTOR_CREATION_FAILED",
                message=(
                    "The Predictor object could not be created."
                ),
            ) from error

        if predictor is None:
            raise ModelLoaderError(
                code="INVALID_PREDICTOR",
                message=(
                    "The Predictor factory returned None."
                ),
            )

        initialize_method = getattr(
            predictor,
            "initialize_from_trained_model_folder",
            None,
        )

        if not callable(initialize_method):
            raise ModelLoaderError(
                code="INVALID_PREDICTOR",
                message=(
                    "The Predictor does not provide "
                    "initialize_from_trained_model_folder()."
                ),
            )

        return predictor

    def _validate_configuration(self) -> None:
        """Validate values that control model loading."""

        config = self._config

        if not config.folds:
            raise ModelLoaderError(
                code="INVALID_MODEL_CONFIGURATION",
                message=(
                    "At least one model fold must be configured."
                ),
            )

        for fold in config.folds:
            valid_integer_fold = (
                isinstance(fold, int)
                and not isinstance(fold, bool)
                and fold >= 0
            )
            valid_all_fold = fold == "all"

            if not (
                valid_integer_fold
                or valid_all_fold
            ):
                raise ModelLoaderError(
                    code="INVALID_MODEL_CONFIGURATION",
                    message=(
                        "Each fold must be a non-negative integer "
                        "or the string 'all'."
                    ),
                )

        if len(set(config.folds)) != len(config.folds):
            raise ModelLoaderError(
                code="INVALID_MODEL_CONFIGURATION",
                message="Duplicate model folds are not allowed.",
            )

        if (
            not config.checkpoint_name
            or "/" in config.checkpoint_name
            or "\\" in config.checkpoint_name
        ):
            raise ModelLoaderError(
                code="INVALID_MODEL_CONFIGURATION",
                message=(
                    "checkpoint_name must be a file name, "
                    "not a path."
                ),
            )

        if (
            isinstance(config.tile_step_size, bool)
            or not isinstance(
                config.tile_step_size,
                (int, float),
            )
            or not 0.0 < config.tile_step_size <= 1.0
        ):
            raise ModelLoaderError(
                code="INVALID_MODEL_CONFIGURATION",
                message=(
                    "tile_step_size must be greater than zero "
                    "and less than or equal to one."
                ),
            )

        if not config.device.strip():
            raise ModelLoaderError(
                code="INVALID_MODEL_CONFIGURATION",
                message="The model device cannot be empty.",
            )

    def _validate_model_bundle(self) -> None:
        """Check the minimum nnU-Net model bundle structure."""

        model_dir = (
            self._config.model_training_output_dir
        )

        if not model_dir.exists():
            raise ModelLoaderError(
                code="MODEL_DIRECTORY_NOT_FOUND",
                message=(
                    "The trained model directory does not exist."
                ),
            )

        if not model_dir.is_dir():
            raise ModelLoaderError(
                code="INVALID_MODEL_DIRECTORY",
                message=(
                    "The trained model path is not a directory."
                ),
            )

        required_files = [
            model_dir / "dataset.json",
            model_dir / "plans.json",
        ]

        for fold in self._config.folds:
            required_files.append(
                model_dir
                / f"fold_{fold}"
                / self._config.checkpoint_name
            )

        missing_files = [
            path.name
            for path in required_files
            if not path.is_file()
        ]

        if missing_files:
            raise ModelLoaderError(
                code="MODEL_FILES_MISSING",
                message=(
                    "Required nnU-Net model files are missing: "
                    + ", ".join(missing_files)
                ),
            )