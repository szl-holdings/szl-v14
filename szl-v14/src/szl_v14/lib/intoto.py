"""in-toto Statement v1 construction with real byte digests."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from szl_v14.lib.digest import sha256_file

_STATEMENT_TYPE = "https://in-toto.io/Statement/v1"


def statement(
    subjects: Iterable[tuple[str, str | Path]],
    predicate_type: str,
    predicate: dict[str, Any],
) -> dict[str, Any]:
    """Build an in-toto Statement v1.

    subjects: iterable of (name, path); the digest is over the file's bytes.
    """
    return {
        "_type": _STATEMENT_TYPE,
        "subject": [
            {"name": name, "digest": {"sha256": sha256_file(path)}}
            for name, path in subjects
        ],
        "predicateType": predicate_type,
        "predicate": predicate,
    }
