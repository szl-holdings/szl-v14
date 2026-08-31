"""doctor — environment triage. First section: BLOCKERS THAT OUTRANK ALL COSMETIC WORK."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from szl_v14.lib.estate import load_snapshots
from szl_v14.lib.states import Finding, Report, State

BLOCKER_HEADER = "BLOCKERS THAT OUTRANK ALL COSMETIC WORK"

_BINARIES = ["gh", "dig", "jq", "curl", "openssl"]


def run(snapshot_dir: Path) -> Report:
    findings: list[Finding] = []
    blockers: list[str] = []

    if sys.version_info < (3, 12):
        findings.append(Finding("CRITICAL", "PY_VERSION", f"python {sys.version.split()[0]} < 3.12"))

    try:
        import rfc8785  # noqa: F401
    except ImportError:
        findings.append(Finding("CRITICAL", "NO_RFC8785", "real JCS library missing; every digest claim is theater"))

    try:
        import importlib.metadata as md
        v = md.version("huggingface_hub")
        if int(v.split(".")[0]) < 1:
            findings.append(Finding("CRITICAL", "HF_HUB_VERSION", f"huggingface_hub {v} < 1.0 (bucket visibility)"))
    except Exception:
        findings.append(Finding("CRITICAL", "NO_HF_HUB", "huggingface_hub >= 1.0 missing — the only bucket-visible call"))

    for b in _BINARIES:
        if not shutil.which(b):
            findings.append(Finding("HIGH", "MISSING_BINARY", f"{b} not on PATH"))
    if not shutil.which("cosign"):
        findings.append(Finding("LOW", "NO_COSIGN", "cosign absent — signing path stays unsigned-honest until armed"))

    snap = load_snapshots(snapshot_dir)
    if not snap.github_repos:
        findings.append(Finding("CRITICAL", "NO_GH_SNAPSHOT", "github/repos_cli.json missing or empty"))
        blockers.append("GitHub estate snapshot missing")
    if not snap.hf_estate:
        findings.append(Finding("CRITICAL", "NO_HF_SNAPSHOT", "hf/hf_estate.json missing"))
        blockers.append("Hugging Face estate snapshot missing")
    cf = snap.cloudflare_status
    if cf.get("status") == "BLOCKED":
        msg = cf.get("diagnosis", "Cloudflare credential blocked")
        findings.append(Finding("HIGH", "CF_TOKEN_BLOCKED", msg,
                                {"error": cf.get("error"), "needed_scopes": cf.get("needed_scopes")}))
        blockers.append(f"Cloudflare: {msg}")
    if snap.estate_completeness not in ("VERIFIED", "VERIFIED (3 independent sources agree at 100)"):
        findings.append(Finding("MEDIUM", "ESTATE_NOT_VERIFIED",
                                f"estate completeness = {snap.estate_completeness}"))
    for missing in snap.unknown:
        findings.append(Finding("MEDIUM", "SNAPSHOT_MISSING", f"snapshot file missing: {missing}"))

    state = State.FAIL if any(f.severity == "CRITICAL" for f in findings) else (
        State.WARN if findings else State.PASS)
    return Report(cmd="doctor", state=state, findings=findings,
                  summary={"blockers_header": BLOCKER_HEADER, "blockers": blockers,
                           "estate_completeness": snap.estate_completeness})


def render_text(report: Report) -> str:
    lines = [BLOCKER_HEADER, "=" * len(BLOCKER_HEADER), ""]
    if report.summary["blockers"]:
        for b in report.summary["blockers"]:
            lines.append(f"  - {b}")
    else:
        lines.append("  (none)")
    lines.append("")
    lines.append(f"estate completeness: {report.summary['estate_completeness']}")
    lines.append(f"state: {report.state.value}")
    return "\n".join(lines)
