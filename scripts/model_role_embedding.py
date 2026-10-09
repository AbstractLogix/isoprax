"""Pinned Hugging Face embedding backend for the model-role research runner."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import platform
import re
from pathlib import Path
from typing import Any


class EmbeddingRuntimeError(RuntimeError):
    """Raised when the pinned embedding runtime cannot be verified or loaded."""


class HuggingFaceSentenceTransformerEmbedder:
    """Load one exact SentenceTransformers checkpoint on CPU."""

    def __init__(
        self,
        model_id: str,
        revision: str,
        files_sha256: dict[str, str],
        dimension: int,
        environment_lock_path: Path,
        environment_lock_sha256: str,
    ) -> None:
        self.model_id = model_id
        self.revision = revision
        self.files_sha256 = dict(files_sha256)
        self.dimension = dimension
        self.environment_lock_path = Path(environment_lock_path)
        self.environment_lock_sha256 = environment_lock_sha256
        self._validate_inputs()
        self._validate_environment()

        try:
            import numpy as np
            import torch
            from huggingface_hub import snapshot_download
            from sentence_transformers import SentenceTransformer

            torch.set_num_threads(1)
            torch.use_deterministic_algorithms(True)
            self.snapshot_path = Path(
                snapshot_download(
                    repo_id=self.model_id,
                    revision=self.revision,
                    allow_patterns=sorted(self.files_sha256),
                )
            )
            for name, digest in sorted(self.files_sha256.items()):
                self._check_file_hash(self.snapshot_path / name, digest)
            self.model = SentenceTransformer(
                str(self.snapshot_path),
                model_kwargs={"torch_dtype": torch.float32},
                config_kwargs={"vision_config": None, "audio_config": None},
                device="cpu",
            )
            self.model.to("cpu")
            parameter = next(self.model.parameters(), None)
            if (
                parameter is None
                or parameter.device.type != "cpu"
                or parameter.dtype != torch.float32
            ):
                raise EmbeddingRuntimeError(
                    "SentenceTransformers model is not loaded on CPU in float32"
                )
            self._numpy = np
            self._torch = torch
        except EmbeddingRuntimeError:
            raise
        except Exception as exc:
            raise EmbeddingRuntimeError(
                f"cannot load pinned SentenceTransformers checkpoint: {exc}"
            ) from exc

    def _validate_inputs(self) -> None:
        if re.fullmatch(r"[0-9a-f]{40}", self.revision) is None:
            raise EmbeddingRuntimeError("revision must be a pinned 40-character commit")
        if not self.model_id or self.dimension < 1:
            raise EmbeddingRuntimeError("model identity and dimension are required")
        required_files = {"model.safetensors", "tokenizer.json", "modules.json"}
        if not required_files.issubset(self.files_sha256):
            raise EmbeddingRuntimeError("checkpoint file hashes are incomplete")
        for filename, value in self.files_sha256.items():
            path = Path(filename)
            if (
                path.is_absolute()
                or ".." in path.parts
                or not path.parts
                or re.fullmatch(r"[0-9a-f]{64}", value) is None
            ):
                raise EmbeddingRuntimeError(f"invalid checkpoint file hash: {filename}")
        for label, value in (("requirements lock", self.environment_lock_sha256),):
            if re.fullmatch(r"[0-9a-f]{64}", value) is None:
                raise EmbeddingRuntimeError(f"invalid {label} SHA-256")

    def _validate_environment(self) -> None:
        try:
            lock_bytes = self.environment_lock_path.read_bytes()
        except OSError as exc:
            raise EmbeddingRuntimeError(
                f"cannot read requirements lock: {exc}"
            ) from exc
        actual_hash = hashlib.sha256(lock_bytes).hexdigest()
        if actual_hash != self.environment_lock_sha256:
            raise EmbeddingRuntimeError(
                f"requirements lock SHA-256 mismatch: {actual_hash}"
            )

        for raw_line in lock_bytes.decode("utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            match = re.fullmatch(r"([A-Za-z0-9_.-]+)==([^\s]+)", line)
            if match is None:
                raise EmbeddingRuntimeError(
                    f"unsupported requirements lock entry: {line}"
                )
            package, expected_version = match.groups()
            try:
                installed_version = importlib.metadata.version(package)
            except importlib.metadata.PackageNotFoundError as exc:
                raise EmbeddingRuntimeError(
                    f"locked package is missing: {package}"
                ) from exc
            if installed_version != expected_version:
                raise EmbeddingRuntimeError(
                    f"locked package version mismatch for {package}: "
                    f"expected {expected_version}, got {installed_version}"
                )

    @staticmethod
    def _check_file_hash(path: Path, expected_hash: str) -> None:
        try:
            actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError as exc:
            raise EmbeddingRuntimeError(f"cannot read checkpoint file {path}") from exc
        if actual_hash != expected_hash:
            raise EmbeddingRuntimeError(
                f"checkpoint SHA-256 mismatch for {path.name}: {actual_hash}"
            )

    def runtime_metadata(self) -> dict[str, Any]:
        return {
            "backend": "sentence-transformers-cpu",
            "model_id": self.model_id,
            "revision": self.revision,
            "identity_sha256": self.identity_sha256,
            "checkpoint_files_sha256": self.files_sha256,
            "requirements_lock_sha256": self.environment_lock_sha256,
            "python": platform.python_version(),
            "platform": platform.platform(),
            "torch": str(self._torch.__version__),
            "transformers": importlib.metadata.version("transformers"),
            "sentence_transformers": importlib.metadata.version(
                "sentence-transformers"
            ),
            "huggingface_hub": importlib.metadata.version("huggingface-hub"),
            "pillow": importlib.metadata.version("pillow"),
            "torchvision": importlib.metadata.version("torchvision"),
            "device": "cpu",
            "dtype": "float32",
            "threads": self._torch.get_num_threads(),
            "dimension": self.dimension,
            "normalize_embeddings": False,
            "normalization_note": (
                "No additional SentenceTransformers normalization was requested. "
                "The preflight observed unit-norm vectors from the loaded pipeline. "
                "This does not establish equivalence to Ollama outputs."
            ),
        }

    @property
    def identity_sha256(self) -> str:
        identity = {
            "backend": "sentence-transformers-cpu",
            "model_id": self.model_id,
            "revision": self.revision,
            "checkpoint_files_sha256": self.files_sha256,
            "requirements_lock_sha256": self.environment_lock_sha256,
        }
        canonical = json.dumps(identity, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def embed(self, inputs: list[str]) -> list[list[float]]:
        if not inputs or any(not isinstance(value, str) for value in inputs):
            raise ValueError("inputs must be a non-empty list of strings")
        try:
            embeddings = self._numpy.asarray(
                self.model.encode(
                    inputs,
                    batch_size=min(len(inputs), 32),
                    convert_to_numpy=True,
                    normalize_embeddings=False,
                    show_progress_bar=False,
                ),
                dtype=self._numpy.float32,
            )
        except Exception as exc:
            raise EmbeddingRuntimeError(f"embedding inference failed: {exc}") from exc
        if embeddings.shape != (len(inputs), self.dimension):
            raise ValueError(
                f"expected {len(inputs)} by {self.dimension} embeddings, "
                f"got {embeddings.shape}"
            )
        if not self._numpy.isfinite(embeddings).all():
            raise ValueError("embedding output contains non-finite values")
        return [[float(value) for value in row] for row in embeddings]
