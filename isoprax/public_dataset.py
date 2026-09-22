"""Small deterministic helpers shared by offline public-dataset verifiers."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Iterable

_HASH_CHUNK_SIZE = 1024 * 1024


def sha256_path(path: str | Path) -> str:
    """Hash an explicitly supplied local file without network or mutation."""

    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(_HASH_CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def unique_errors(errors: Iterable[str]) -> tuple[str, ...]:
    """Preserve first occurrence while making repeated row errors auditable."""

    return tuple(dict.fromkeys(errors))
