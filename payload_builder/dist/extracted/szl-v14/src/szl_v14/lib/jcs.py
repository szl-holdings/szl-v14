"""Canonical JSON per RFC 8785, via the real library. sort_keys is not JCS."""

from __future__ import annotations

import sys
from typing import Any

_INSTALL = "rfc8785 is not installed. Run: pip install rfc8785  (json.dumps with sorted keys is NOT JCS)"


def _lib():
    try:
        import rfc8785  # type: ignore
    except ImportError:
        sys.stderr.write(f"FATAL: {_INSTALL}\n")
        raise SystemExit(2)
    return rfc8785


def canonical(obj: Any) -> str:
    """Serialize obj to its RFC 8785 canonical form."""
    out = _lib().dumps(obj)
    return out.decode("utf-8") if isinstance(out, (bytes, bytearray)) else out


def jcs_digest(obj: Any) -> str:
    """SHA-256 of the canonical form."""
    from szl_v14.lib.digest import sha256_bytes

    return sha256_bytes(canonical(obj).encode("utf-8"))
