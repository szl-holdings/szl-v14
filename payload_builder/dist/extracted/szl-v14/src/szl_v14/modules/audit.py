"""audit — one audit file per repo from a Jinja template + REPOSITORY_MATRIX.csv.

Fields not probed are UNKNOWN. Never guessed, never carried forward.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from szl_v14.lib.digest import sha256_file
from szl_v14.lib.estate import load_snapshots
from szl_v14.lib.states import Finding, Report, State

FORBIDDEN_DOMAIN = re.compile(r"(?<!-)a11oy\.com")

_TEMPLATE_DIR = Path(__file__).resolve().parents[3] / "templates"

MATRIX_FIELDS = ["name", "visibility", "archived", "default_branch", "language",
                 "license", "pushed_at", "open_prs", "has_pages", "forbidden_refs", "state"]


def _repo_view(r: dict, enrichment: dict | None) -> dict:
    e = enrichment or {}
    text = " ".join(str(r.get(k) or "") for k in ("description", "url")) + " " + str(e.get("homepage") or "")
    return {
        "name": r.get("name", "UNKNOWN"),
        "visibility": r.get("visibility", "UNKNOWN"),
        "archived": r.get("isArchived", "UNKNOWN"),
        "default_branch": (r.get("defaultBranchRef") or {}).get("name", "UNKNOWN"),
        "language": (r.get("primaryLanguage") or {}).get("name", "UNKNOWN"),
        "license": (r.get("licenseInfo") or {}).get("spdxId", "UNKNOWN"),
        "pushed_at": (r.get("pushedAt") or "UNKNOWN")[:10],
        "description": r.get("description") or "UNKNOWN",
        "url": r.get("url", "UNKNOWN"),
        "open_prs": e.get("open_prs", "UNKNOWN"),
        "has_pages": e.get("has_pages", "UNKNOWN"),
        "homepage": e.get("homepage", "UNKNOWN"),
        "topics": [t.get("name") for t in (r.get("repositoryTopics") or [])] or "UNKNOWN",
        "forbidden_refs": len(FORBIDDEN_DOMAIN.findall(text)),
        "state": "FAIL" if FORBIDDEN_DOMAIN.findall(text) else "PASS",
    }


def run(snapshot_dir: Path, out_dir: Path) -> Report:
    snap = load_snapshots(snapshot_dir)
    findings: list[Finding] = []
    audits = out_dir / "audits" / "repos"
    audits.mkdir(parents=True, exist_ok=True)

    enrichment: dict[str, dict] = {}
    edir = snapshot_dir / "github" / "enrichment"
    if edir.is_dir():
        import json as _json
        for f in edir.glob("*.json"):
            try:
                d = _json.loads(f.read_text())
                if d.get("name"):
                    enrichment[d["name"]] = d
            except Exception:
                pass
    else:
        findings.append(Finding("INFO", "NO_ENRICHMENT", "no per-repo enrichment; deep fields are UNKNOWN"))

    env = Environment(loader=FileSystemLoader(str(_TEMPLATE_DIR)),
                      autoescape=select_autoescape(disabled_extensions=("md", "j2")))
    tpl = env.get_template("REPO_AUDIT.j2")

    rows: list[dict] = []
    outputs: dict[str, str] = {}
    for r in sorted(snap.github_repos, key=lambda x: x.get("name", "")):
        view = _repo_view(r, enrichment.get(r.get("name")))
        if view["forbidden_refs"]:
            findings.append(Finding("CRITICAL", "FORBIDDEN_LINK",
                                    f"{view['name']}: forbidden domain reference in metadata"))
        path = audits / f"{view['name']}.md"
        path.write_text(tpl.render(repo=view))
        outputs[str(path)] = sha256_file(path)
        rows.append(view)

    matrix = out_dir / "REPOSITORY_MATRIX.csv"
    with open(matrix, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=MATRIX_FIELDS)
        w.writeheader()
        for v in rows:
            w.writerow({k: v.get(k, "UNKNOWN") for k in MATRIX_FIELDS})
    outputs[str(matrix)] = sha256_file(matrix)

    state = State.FAIL if any(f.severity == "CRITICAL" for f in findings) else (
        State.WARN if findings else State.PASS)
    return Report(cmd="audit", state=state, findings=findings, outputs=outputs,
                  summary={"repos_audited": len(rows),
                           "forbidden_refs": sum(v["forbidden_refs"] for v in rows)})
