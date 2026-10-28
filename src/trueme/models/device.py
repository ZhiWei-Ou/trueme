"""Explicit ONNX provider initialization and observable execution fallback."""

import contextlib
import sys
from pathlib import Path

from trueme.errors import DeviceError, ModelError, ProcessingError

CPU = "CPUExecutionProvider"
CUDA = "CUDAExecutionProvider"


class ModelSession:
    def __init__(self, path: Path, requested: str):
        if requested not in {"auto", "cpu", "cuda"}:
            raise DeviceError("Device must be auto, cpu, or cuda.")
        try:
            import onnxruntime as ort
        except (ImportError, OSError) as exc:
            raise ModelError(
                "Install exactly one ONNX Runtime distribution: "
                "use make setup DEVICE=cpu or DEVICE=gpu."
            ) from exc
        from onnxruntime.capi import onnxruntime_pybind11_state as state

        self._failures = (
            RuntimeError,
            ValueError,
            OSError,
            state.Fail,
            state.InvalidArgument,
            state.InvalidGraph,
            state.NoSuchFile,
            state.NotImplemented,
            state.RuntimeException,
            state.EPFail,
        )
        self._ort = ort
        self.path = path
        self.requested = requested
        self.fallback_reason = None
        available = ort.get_available_providers()
        if requested == "cpu":
            self.session = self._cpu()
        elif CUDA not in available:
            if requested == "cuda":
                raise DeviceError(
                    "CUDAExecutionProvider is unavailable. Install the GPU environment "
                    "and compatible CUDA/cuDNN libraries."
                )
            self.fallback_reason = "CUDAExecutionProvider is unavailable; using CPU."
            self.session = self._cpu()
        else:
            try:
                self.session = self._create([CUDA, CPU])
                if CUDA not in self.session.get_providers():
                    raise DeviceError(
                        "CUDA provider did not initialize (check CUDA/cuDNN libraries)."
                    )
            except (*self._failures, DeviceError) as exc:
                if requested == "cuda":
                    raise DeviceError(
                        "CUDA session initialization failed; check the GPU setup in docs/models.md."
                    ) from exc
                self.fallback_reason = "CUDA session initialization failed; using CPU."
                self.session = self._cpu()

    def _create(self, providers):
        options = self._ort.SessionOptions()
        # Avoid oversubscribing the host for these small, sequential models.
        options.intra_op_num_threads = 2
        options.inter_op_num_threads = 1
        options.log_severity_level = 3
        with contextlib.redirect_stdout(sys.stderr):
            session = self._ort.InferenceSession(
                str(self.path), sess_options=options, providers=providers
            )
        session.disable_fallback()
        return session

    def _cpu(self):
        try:
            return self._create([CPU])
        except self._failures as exc:
            raise ModelError(
                f"CPU initialization failed for {self.path.name}; "
                "verify the runtime and model installation."
            ) from exc

    def run(self, tensor, output_names=None):
        feed = {self.session.get_inputs()[0].name: tensor}
        try:
            return self.session.run(output_names, feed)
        except self._failures as exc:
            if CUDA in self.session.get_providers():
                if self.requested == "cuda":
                    raise DeviceError(
                        "CUDA execution failed; explicit CUDA does not fall back to CPU."
                    ) from exc
                self.fallback_reason = "CUDA execution failed; repeated this inference on CPU."
                self.session = self._cpu()
                try:
                    return self.session.run(output_names, feed)
                except self._failures as cpu_exc:
                    raise ProcessingError("Model execution also failed on CPU.") from cpu_exc
            raise ProcessingError("Model execution failed on CPU.") from exc

    def info(self) -> dict:
        return {
            "configured_providers": self.session.get_providers(),
            "fallback_reason": self.fallback_reason,
        }
