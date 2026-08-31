"""remediate — findings JSON -> ORDERED plan. Credentials -> DNS -> origin-host -> code -> cosmetic."""

from __future__ import annotations

import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from szl_v14.lib.digest import sha256_file
from szl_v14.lib.states import Finding, Report, State

_TEMPLATE_DIR = Path(__file__).resolve().parents[3] / "templates"

_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}
_LANE = {"CF_TOKEN_BLOCKED": 0, "NO_HF_HUB": 0, "MISSING_BINARY": 0,
         "PAGES_ORANGE_CLOUD": 1, "IMPOSSIBLE_DNS": 1,
         "TUNNEL_1033": 2, "ESTATE_PARTIAL": 2,
         "FORBIDDEN_LINK": 3, "CLAIM_DRIFT": 3}


def run(findings_json: Path, out_dir: Path) -> Report:
    if not findings_json.exists():
        return Report(cmd="remediate", state=State.UNKNOWN,
                      findings=[Finding("MEDIUM", "NO_FINDINGS", f"missing: {findings_json}")])
    raw = json.loads(findings_json.read_text())
    items = raw if isinstance(raw, list) else raw.get("findings", [])
    items.sort(key=lambda f: (_ORDER.get(f.get("severity", "INFO"), 4),
                              _LANE.get(f.get("code", ""), 4)))

    plan = []
    for i, f in enumerate(items, 1):
        plan.append({"order": i, "severity": f.get("severity"), "code": f.get("code"),
                     "action": f.get("message"),
                     "verify": f.get("verify", "re-run the producing command; state must improve or stay honestly UNKNOWN")})

    out_dir.mkdir(parents=True, exist_ok=True)
    env = Environment(loader=FileSystemLoader(str(_TEMPLATE_DIR)),
                      autoescape=select_autoescape(disabled_extensions=("md", "j2")))
    path = out_dir / "REMEDIATION_PLAN.md"
    path.write_text(env.get_template("REPORT.j2").render(title="Remediation plan", plan=plan, items=plan))
    return Report(cmd="remediate", state=State.PASS,
                  outputs={str(path): sha256_file(path)},
                  summary={"items": len(plan)})
