"""Canonical serialization and SHA-256 identities for evidence artifacts."""

from __future__ import annotations

import hashlib
from typing import Any

import rfc8785


def canonical_json(value: Any) -> str:
    """Serialize an identity payload using RFC 8785 JSON Canonicalization."""
    return rfc8785.dumps(value).decode("utf-8")


def content_hash(value: Any) -> str:
    """Hash a canonical identity payload with SHA-256."""
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def bytes_hash(value: bytes) -> str:
    """Hash already-serialized artifact bytes with SHA-256."""
    return hashlib.sha256(value).hexdigest()
