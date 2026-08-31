"""deploy — inspect-only deployment state. No mutation anywhere."""

from __future__ import annotations

from pathlib import Path

from szl_v14.modules.dns import _load_targets
from szl_v14.lib.states import Finding, Report, State


def run(targets: Path | None, probe_file: Path | None) -> Report:
    findings: list[Finding] = []
    doc = _load_targets(targets) if (targets or True) else {}
    rows = []
    try:
        doc = _load_targets(targets)
    except FileNotFoundError as e:
        return Report(cmd="deploy", state=State.UNKNOWN,
                      findings=[Finding("MEDIUM", "MISSING_CONFIG", str(e))])

    for z in doc.get("zones", []):
        rows.append({"zone": z["zone"], "role": z.get("role", "UNKNOWN"),
                     "target": z.get("target_summary", "UNKNOWN"),
                     "notes": z.get("notes", "")})
    findings.append(Finding(
        "INFO", "HSTS_PRELOAD",
        ".dev is HSTS-preloaded: order is DNS -> cert -> curl-verify -> announce; "
        "linking szl.dev before a valid cert exists is a hard browser failure"))
    findings.append(Finding(
        "INFO", "ACCESS_403_OK",
        "never remove Cloudflare Access to turn a 403 into a 200; 403 means Access is working"))
    return Report(cmd="deploy", state=State.PASS, findings=findings,
                  summary={"deployments": rows})
