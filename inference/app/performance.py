"""Utilities for measuring model inference performance."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Any, Callable, Protocol, TypeVar


MEBIBYTE_IN_BYTES = 1024 * 1024

InferenceResult = TypeVar("InferenceResult")


class CudaMemoryBackend(Protocol):
    """Required CUDA operations for GPU memory measurement."""

    def is_available(self) -> bool:
        """Return whether a CUDA device is available."""

    def current_device(self) -> Any:
        """Return the currently selected CUDA device."""

    def synchronize(
        self,
        device: Any = None,
    ) -> None:
        """Wait for queued CUDA operations to finish."""

    def reset_peak_memory_stats(
        self,
        device: Any = None,
    ) -> None:
        """Reset peak GPU memory statistics."""

    def max_memory_allocated(
        self,
        device: Any = None,
    ) -> int:
        """Return peak allocated GPU memory in bytes."""


@dataclass(frozen=True)
class InferencePerformance:
    """Performance measurements for one successful inference."""

    inference_time_ms: float
    gpu_memory_measured: bool
    gpu_peak_memory_mb: float | None

    def to_dict(self) -> dict[str, float | bool | None]:
        """Convert the measurements to a JSON-compatible dictionary."""

        return {
            "inference_time_ms": self.inference_time_ms,
            "gpu_memory_measured": self.gpu_memory_measured,
            "gpu_peak_memory_mb": self.gpu_peak_memory_mb,
        }


def _load_torch_cuda_backend() -> CudaMemoryBackend | None:
    """Load torch.cuda when PyTorch is installed."""

    try:
        import torch
    except ImportError:
        return None

    return torch.cuda


def measure_inference_performance(
    inference_function: Callable[..., InferenceResult],
    *args: Any,
    cuda_backend: CudaMemoryBackend | None = None,
    cuda_device: Any = None,
    **kwargs: Any,
) -> tuple[InferenceResult, InferencePerformance]:
    """Run an inference function and measure its execution performance.

    CUDA operations run asynchronously. Synchronization is therefore
    performed immediately before and after inference so that elapsed
    time includes the actual completion of GPU computation.

    Args:
        inference_function:
            Callable that performs one model inference.
        *args:
            Positional arguments passed to the inference function.
        cuda_backend:
            Optional CUDA measurement backend. When omitted, torch.cuda
            is used if PyTorch is installed.
        cuda_device:
            CUDA device to measure. When omitted, the current CUDA
            device is used.
        **kwargs:
            Keyword arguments passed to the inference function.

    Returns:
        A tuple containing the inference result and performance data.

    Raises:
        Any exception raised by the inference function is propagated.
    """

    backend = (
        cuda_backend
        if cuda_backend is not None
        else _load_torch_cuda_backend()
    )

    gpu_memory_measured = bool(
        backend is not None
        and backend.is_available()
    )

    selected_device = cuda_device

    if gpu_memory_measured:
        if selected_device is None:
            selected_device = backend.current_device()

        backend.synchronize(selected_device)
        backend.reset_peak_memory_stats(selected_device)

    start_time = perf_counter()

    inference_result = inference_function(
        *args,
        **kwargs,
    )

    if gpu_memory_measured:
        backend.synchronize(selected_device)

    end_time = perf_counter()

    inference_time_ms = (
        end_time - start_time
    ) * 1000.0

    gpu_peak_memory_mb: float | None = None

    if gpu_memory_measured:
        peak_memory_bytes = backend.max_memory_allocated(
            selected_device
        )
        gpu_peak_memory_mb = (
            float(peak_memory_bytes)
            / MEBIBYTE_IN_BYTES
        )

    performance = InferencePerformance(
        inference_time_ms=inference_time_ms,
        gpu_memory_measured=gpu_memory_measured,
        gpu_peak_memory_mb=gpu_peak_memory_mb,
    )

    return inference_result, performance