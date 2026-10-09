from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from scripts.model_role_embedding import (
    EmbeddingRuntimeError,
    HuggingFaceSentenceTransformerEmbedder,
)


def test_embedding_identity_digest_changes_with_any_pinned_file() -> None:
    embedder = HuggingFaceSentenceTransformerEmbedder.__new__(
        HuggingFaceSentenceTransformerEmbedder
    )
    embedder.model_id = "google/embeddinggemma-2"
    embedder.revision = "a" * 40
    embedder.files_sha256 = {
        "model.safetensors": "b" * 64,
        "tokenizer.json": "c" * 64,
        "modules.json": "d" * 64,
    }
    embedder.environment_lock_sha256 = "e" * 64
    first = embedder.identity_sha256
    embedder.files_sha256["modules.json"] = "f" * 64
    assert embedder.identity_sha256 != first


def test_embedding_identity_rejects_incomplete_or_unpinned_checkpoint() -> None:
    embedder = HuggingFaceSentenceTransformerEmbedder.__new__(
        HuggingFaceSentenceTransformerEmbedder
    )
    embedder.model_id = "google/embeddinggemma-2"
    embedder.revision = "main"
    embedder.files_sha256 = {"model.safetensors": "b" * 64}
    embedder.dimension = 768
    embedder.environment_lock_sha256 = "e" * 64

    with pytest.raises(EmbeddingRuntimeError, match="pinned 40-character"):
        embedder._validate_inputs()

    embedder.revision = "a" * 40
    with pytest.raises(EmbeddingRuntimeError, match="hashes are incomplete"):
        embedder._validate_inputs()


def test_checkpoint_file_hash_requires_exact_bytes(tmp_path: Path) -> None:
    checkpoint = tmp_path / "modules.json"
    checkpoint.write_bytes(b"pinned checkpoint file")
    expected = hashlib.sha256(checkpoint.read_bytes()).hexdigest()

    HuggingFaceSentenceTransformerEmbedder._check_file_hash(checkpoint, expected)
    with pytest.raises(EmbeddingRuntimeError, match="SHA-256 mismatch"):
        HuggingFaceSentenceTransformerEmbedder._check_file_hash(checkpoint, "0" * 64)
