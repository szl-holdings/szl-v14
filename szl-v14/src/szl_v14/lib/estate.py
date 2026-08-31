"""Load estate snapshots. A missing file is UNKNOWN, never a guess, never a crash."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class EstateSnapshot:
    root: Path
    github_repos: list[dict[str, Any]] = field(default_factory=list)   # repos_cli.json
    github_enumeration: dict[str, Any] = field(default_factory=dict)   # enumeration.json
    hf_estate: dict[str, Any] = field(default_factory=dict)            # hf_estate.json
    cloudflare_status: dict[str, Any] = field(default_factory=dict)    # status.json
    unknown: list[str] = field(default_factory=list)                   # snapshot names that were missing

    @property
    def estate_completeness(self) -> str:
        return self.github_enumeration.get("estate_completeness", "UNKNOWN")


def _load(root: Path, rel: str, unknown: list[str]) -> Any:
    p = root / rel
    if not p.exists():
        unknown.append(rel)
        return None
    try:
        return json.loads(p.read_text())
    except Exception:
        unknown.append(rel)
        return None


def load_snapshots(root: str | Path) -> EstateSnapshot:
    root = Path(root)
    unknown: list[str] = []
    return EstateSnapshot(
        root=root,
        github_repos=_load(root, "github/repos_cli.json", unknown) or [],
        github_enumeration=_load(root, "github/enumeration.json", unknown) or {},
        hf_estate=_load(root, "hf/hf_estate.json", unknown) or {},
        cloudflare_status=_load(root, "cloudflare/status.json", unknown) or {},
        unknown=unknown,
    )
