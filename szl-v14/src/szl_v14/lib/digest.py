"""Byte digests over actual file contents. Never a name. Never a string."""

from __future__ import annotations

import hashlib
from pathlib import Path

CHUNK = 1 << 20  # 1 MiB


def sha256_file(path: str | Path, chunk: int = CHUNK) -> str:
    """SHA-256 of a file's actual bytes, read in chunks."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    """SHA-256 of an in-memory byte string."""
    return hashlib.sha256(data).hexdigest()


def digest_map(root: str | Path, chunk: int = CHUNK) -> dict[str, str]:
    """{relative_posix_path: sha256} for every file under root, sorted."""
    root = Path(root)
    return {
        p.relative_to(root).as_posix(): sha256_file(p, chunk)
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }
