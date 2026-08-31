"""HTTP helpers. Secrets are never logged, never echoed, never in errors."""

from __future__ import annotations

import re
from typing import Any

import httpx

_BEARER = re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._\-]+")
_KEYVAL = re.compile(r"(?i)(token|secret|api[_-]?key|password|pat)([\"'\s:=]+)[^\s\"',}]+")


def _redact(text: str) -> str:
    text = _BEARER.sub(r"\1<redacted>", text)
    text = _KEYVAL.sub(lambda m: f"{m.group(1)}{m.group(2)}<redacted>", text)
    return text


def get_json(url: str, headers: dict[str, str] | None = None, timeout: float = 30.0) -> Any:
    """GET a URL and parse JSON. Errors are redacted before they surface."""
    try:
        resp = httpx.get(url, headers=headers or {}, timeout=timeout, follow_redirects=True)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:  # httpx errors may embed Authorization headers
        raise RuntimeError(_redact(f"{type(exc).__name__}: {exc}")) from None


def post_json(url: str, body: Any, headers: dict[str, str] | None = None, timeout: float = 30.0) -> Any:
    """POST JSON and parse the response. Errors are redacted."""
    try:
        resp = httpx.post(url, json=body, headers=headers or {}, timeout=timeout, follow_redirects=True)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        raise RuntimeError(_redact(f"{type(exc).__name__}: {exc}")) from None
