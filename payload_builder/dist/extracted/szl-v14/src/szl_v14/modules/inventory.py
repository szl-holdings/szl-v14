"""inventory — build repos.yaml from snapshots. Sources disagree -> PARTIAL."""

from __future__ import annotations

from pathlib import Path

import yaml

from szl_v14.lib.digest import sha256_file
from szl_v14.lib.estate import load_snapshots
from szl_v14.lib.states import Finding, Report, State


def run(snapshot_dir: Path, out_dir: Path) -> Report:
    snap = load_snapshots(snapshot_dir)
    findings: list[Finding] = []

    enum = snap.github_enumeration
    srcs = enum.get("sources", {})
    counts = [v for v in srcs.values() if isinstance(v, int)]
    if len(set(counts)) > 1:
        findings.append(Finding("HIGH", "SOURCE_DISAGREE",
                                f"enumeration sources disagree: {srcs}"))
        completeness = "PARTIAL"
    elif not counts:
        completeness = "UNKNOWN"
        findings.append(Finding("MEDIUM", "NO_ENUM", "no enumeration evidence"))
    else:
        completeness = enum.get("estate_completeness", "PARTIAL")
        if completeness != "VERIFIED" and not completeness.startswith("VERIFIED"):
            findings.append(Finding("MEDIUM", "ESTATE_PARTIAL", completeness))

    repos = []
    for r in snap.github_repos:
        repos.append({
            "name": r.get("name"),
            "visibility": r.get("visibility"),
            "archived": r.get("isArchived"),
            "default_branch": (r.get("defaultBranchRef") or {}).get("name"),
            "language": (r.get("primaryLanguage") or {}).get("name"),
            "pushed_at": r.get("pushedAt"),
            "license": (r.get("licenseInfo") or {}).get("spdxId"),
            "description": r.get("description"),
            "url": r.get("url"),
        })

    hf = snap.hf_estate
    doc = {
        "schema": "szl/v14-inventory",
        "estate_completeness": completeness,
        "github": {"org": "szl-holdings", "count": len(repos),
                   "sources": srcs, "repos": repos},
        "huggingface": {"org": "SZLHOLDINGS",
                        "counts": hf.get("counts", {}),
                        "names": hf.get("names", {})},
        "cloudflare": {"status": snap.cloudflare_status.get("status", "UNKNOWN"),
                       "error": snap.cloudflare_status.get("error")},
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "repos.yaml"
    path.write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True))
    state = State.WARN if findings else State.PASS
    return Report(cmd="inventory", state=state, findings=findings,
                  outputs={str(path): sha256_file(path)},
                  summary={"github_repos": len(repos), "hf": hf.get("counts", {}),
                           "estate_completeness": completeness})
