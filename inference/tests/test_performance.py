"""Tests for model inference performance measurements."""

from typing import Any

import pytest

from inference.app.performance import (
    InferencePerformance,
    measure_inference_performance,
)


MEBIBYTE_IN_BYTES = 1024 * 1024


class FakeCudaBackend:
    """Fake CUDA backend for testing without a physical GPU."""

    def __init__(
        self,
        *,
        available: bool,
        peak_memory_bytes: int = 0,
    ) -> None:
        self.available = available
        self.peak_memory_bytes = peak_memory_bytes
        self.calls: list[tuple[str, Any]] = []

    def is_available(self) -> bool:
        self.calls.append(("is_available", None))
        return self.available

    def current_device(self) -> str:
        self.calls.append(("current_device", None))
        return "cuda:0"

    def synchronize(
        self,
        device: Any = None,
    ) -> None:
        self.calls.append(("synchronize", device))

    def reset_peak_memory_stats(
        self,
        device: Any = None,
    ) -> None:
        self.calls.append(("reset_peak_memory_stats", device))

    def max_memory_allocated(
        self,
        device: Any = None,
    ) -> int:
        self.calls.append(("max_memory_allocated", device))
        return self.peak_memory_bytes


def test_runs_inference_and_forwards_arguments() -> None:
    """Pass positional and keyword arguments to the inference function."""

    backend = FakeCudaBackend(available=False)

    def inference_function(
        value: int,
        *,
        multiplier: int,
    ) -> int:
        return value * multiplier

    result, performance = measure_inference_performance(
        inference_function,
        4,
        multiplier=3,
        cuda_backend=backend,
    )

    assert result == 12
    assert performance.inference_time_ms >= 0.0
    assert performance.gpu_memory_measured is False
    assert performance.gpu_peak_memory_mb is None


def test_converts_performance_to_json_compatible_dictionary() -> None:
    """Convert performance measurements to a JSON-compatible dictionary."""

    performance = InferencePerformance(
        inference_time_ms=125.5,
        gpu_memory_measured=True,
        gpu_peak_memory_mb=2048.0,
    )

    assert performance.to_dict() == {
        "inference_time_ms": 125.5,
        "gpu_memory_measured": True,
        "gpu_peak_memory_mb": 2048.0,
    }


def test_measures_peak_gpu_memory() -> None:
    """Synchronize CUDA and convert peak bytes to MiB."""

    backend = FakeCudaBackend(
        available=True,
        peak_memory_bytes=8 * MEBIBYTE_IN_BYTES,
    )

    def inference_function() -> str:
        backend.calls.append(("inference", None))
        return "mask-result"

    result, performance = measure_inference_performance(
        inference_function,
        cuda_backend=backend,
    )

    assert result == "mask-result"
    assert performance.inference_time_ms >= 0.0
    assert performance.gpu_memory_measured is True
    assert performance.gpu_peak_memory_mb == pytest.approx(8.0)

    assert backend.calls == [
        ("is_available", None),
        ("current_device", None),
        ("synchronize", "cuda:0"),
        ("reset_peak_memory_stats", "cuda:0"),
        ("inference", None),
        ("synchronize", "cuda:0"),
        ("max_memory_allocated", "cuda:0"),
    ]


def test_uses_explicit_cuda_device() -> None:
    """Use the requested CUDA device instead of the current device."""

    backend = FakeCudaBackend(
        available=True,
        peak_memory_bytes=2 * MEBIBYTE_IN_BYTES,
    )

    result, performance = measure_inference_performance(
        lambda: 100,
        cuda_backend=backend,
        cuda_device="cuda:1",
    )

    assert result == 100
    assert performance.gpu_peak_memory_mb == pytest.approx(2.0)
    assert ("current_device", None) not in backend.calls
    assert ("synchronize", "cuda:1") in backend.calls
    assert ("reset_peak_memory_stats", "cuda:1") in backend.calls
    assert ("max_memory_allocated", "cuda:1") in backend.calls


def test_unavailable_cuda_does_not_measure_gpu_memory() -> None:
    """Skip CUDA memory operations when no GPU is available."""

    backend = FakeCudaBackend(available=False)

    _, performance = measure_inference_performance(
        lambda: "completed",
        cuda_backend=backend,
    )

    assert performance.gpu_memory_measured is False
    assert performance.gpu_peak_memory_mb is None
    assert backend.calls == [
        ("is_available", None),
    ]


def test_inference_exception_is_propagated() -> None:
    """Do not hide errors raised during model inference."""

    backend = FakeCudaBackend(available=False)

    def failing_inference() -> None:
        raise RuntimeError("Inference failed.")

    with pytest.raises(
        RuntimeError,
        match="Inference failed.",
    ):
        measure_inference_performance(
            failing_inference,
            cuda_backend=backend,
        )