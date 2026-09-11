"""Canonical serialization and SHA-256 identities for evidence artifacts."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_json(value: Any) -> str:
    """Serialize an identity payload deterministically across all reducers."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def content_hash(value: Any) -> str:
    """Hash a canonical identity payload with SHA-256."""
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def bytes_hash(value: bytes) -> str:
    """Hash already-serialized artifact bytes with SHA-256."""
    return hashlib.sha256(value).hexdigest()
