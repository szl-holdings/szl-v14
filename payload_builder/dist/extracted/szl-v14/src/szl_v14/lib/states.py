"""Evidence states and findings.

PASS | WARN | FAIL | BLOCKED | UNKNOWN. UNKNOWN is never coerced to PASS.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Iterable


class State(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"
    UNKNOWN = "UNKNOWN"


def promote(state: State, target: State) -> State:
    """Promote an evidence state. UNKNOWN can never become PASS."""
    state, target = State(state), State(target)
    if state == State.UNKNOWN and target == State.PASS:
        raise ValueError("UNKNOWN is never coerced to PASS")
    return target


@dataclass
class Finding:
    severity: str  # CRITICAL | HIGH | MEDIUM | LOW | INFO
    code: str
    message: str
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass
class Report:
    cmd: str
    state: State
    findings: list[Finding] = field(default_factory=list)
    outputs: dict[str, str] = field(default_factory=dict)  # path -> sha256
    summary: dict[str, Any] = field(default_factory=dict)


def render_findings(findings: Iterable[Finding]) -> None:
    from rich.console import Console
    from rich.table import Table

    findings = list(findings)
    console = Console()
    if not findings:
        console.print("[green]no findings[/green]")
        return
    table = Table(title="Findings")
    for col in ("severity", "code", "message"):
        table.add_column(col)
    color = {"CRITICAL": "red", "HIGH": "red", "MEDIUM": "yellow",
             "LOW": "cyan", "INFO": "white"}
    for f in findings:
        table.add_row(f"[{color.get(f.severity, 'white')}]{f.severity}[/]",
                      f.code, f.message)
    console.print(table)


def worst_state(findings: Iterable[Finding]) -> State:
    ranking = {"CRITICAL": State.FAIL, "HIGH": State.FAIL,
               "MEDIUM": State.WARN, "LOW": State.WARN, "INFO": State.PASS}
    out = State.PASS
    for f in findings:
        s = ranking.get(f.severity, State.WARN)
        if s == State.FAIL:
            return State.FAIL
        if s == State.WARN:
            out = State.WARN
    return out


def to_jsonable(obj: Any) -> Any:
    if isinstance(obj, (State,)):
        return obj.value
    if isinstance(obj, (Finding, Report)):
        return to_jsonable(asdict(obj))
    if isinstance(obj, dict):
        return {k: to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_jsonable(v) for v in obj]
    return obj


def emit_json(report: Report) -> str:
    return json.dumps(to_jsonable(report), indent=2)
