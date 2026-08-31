"""DSSE envelopes with honest unsigned naming.

An artifact without a signature is named ``*.unsigned.json`` and carries
``signatures: []``. An empty signature list is never described as signed.
"""

from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any


def envelope(payload: bytes, payload_type: str = "application/vnd.in-toto+json") -> dict[str, Any]:
    """Build a DSSE envelope. Always honestly unsigned at creation time."""
    return {
        "payloadType": payload_type,
        "payload": base64.b64encode(payload).decode("ascii"),
        "signatures": [],
    }


def write_unsigned(env: dict[str, Any], path: str | Path) -> Path:
    """Write an unsigned envelope, enforcing the naming contract."""
    path = Path(path)
    if not path.name.endswith(".unsigned.json"):
        raise ValueError(f"unsigned envelopes must be named *.unsigned.json (got {path.name})")
    if env.get("signatures") != []:
        raise ValueError("envelope claims signatures but file is named unsigned")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(env, indent=2) + "\n")
    return path


def verify_unsigned(path: str | Path) -> dict[str, Any]:
    """Load an envelope and assert name/signature honesty. Raises on violation."""
    path = Path(path)
    env = json.loads(path.read_text())
    sigs = env.get("signatures", None)
    if path.name.endswith(".unsigned.json"):
        if sigs not in ([], None):
            raise ValueError("envelope claims signatures but file is named unsigned")
    else:
        if sigs == []:
            raise ValueError("envelope has no signatures but is not named *.unsigned.json")
    return env
