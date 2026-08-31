"""Command receipts — the ONLY place timestamps are allowed."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from szl_v14.lib.digest import sha256_file
from szl_v14.lib.jcs import canonical, jcs_digest


@dataclass
class Receipt:
    cmd: str
    args_digest: str
    inputs: dict[str, str] = field(default_factory=dict)   # path -> sha256
    outputs: dict[str, str] = field(default_factory=dict)  # path -> sha256
    state: str = "UNKNOWN"
    timestamp_utc: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def write(
    root: str | Path,
    cmd: str,
    args: dict[str, Any],
    inputs: dict[str, str] | None = None,
    outputs: dict[str, str] | None = None,
    state: str = "UNKNOWN",
    extra_inputs: list[str | Path] | None = None,
) -> Path:
    """Write receipts/<cmd>-<ts>.json under root and return its path."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    ins = dict(inputs or {})
    for p in extra_inputs or []:
        p = Path(p)
        if p.exists():
            ins[str(p)] = sha256_file(p)
    rcpt = Receipt(
        cmd=cmd,
        args_digest=jcs_digest(args),
        inputs=ins,
        outputs=outputs or {},
        state=state,
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
    )
    outdir = Path(root) / "receipts"
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / f"{cmd.replace(' ', '_')}-{ts}.json"
    path.write_text(canonical(rcpt.to_dict()) + "\n")
    return path
