"""dns — validate targets, print plans, and (never mutate) print authorization packets."""

from __future__ import annotations

import json
from pathlib import Path

import yaml
from jsonschema import validate as js_validate

from szl_v14.lib.states import Finding, Report, State

_TARGETS = Path(__file__).resolve().parents[3] / "dns-targets.yaml"
_SCHEMA = Path(__file__).resolve().parents[3] / "schemas" / "dns_plan.schema.json"


def _load_targets(path: Path | None) -> dict:
    p = path or _TARGETS
    if not p.exists():
        raise FileNotFoundError(f"dns targets file missing: {p}")
    return yaml.safe_load(p.read_text())


def impossible_states(doc: dict) -> list[Finding]:
    """Reject impossible DNS states at compile/validate time, not at 2am."""
    findings: list[Finding] = []
    for z in doc.get("zones", []):
        apex_cnames = [r for r in z.get("records", [])
                       if r.get("type") == "CNAME" and r.get("name") in ("@", z.get("zone"))]
        if apex_cnames and not z.get("apex_cname_flattening", False):
            findings.append(Finding("CRITICAL", "IMPOSSIBLE_DNS",
                                    f"{z['zone']}: apex CNAME without confirmed flattening"))
        others = [r for r in z.get("records", [])
                  if r.get("name") == "@" and r.get("type") != "CNAME"]
        if apex_cnames and others:
            findings.append(Finding("CRITICAL", "IMPOSSIBLE_DNS",
                                    f"{z['zone']}: coexisting records at the CNAME label"))
        targets = {r.get("provider") for r in z.get("records", []) if r.get("provider")}
        if len(targets) > 1:
            findings.append(Finding("HIGH", "MIXED_CANONICAL",
                                    f"{z['zone']}: mixed provider targets {sorted(targets)}"))
        if not z.get("rollback_source"):
            findings.append(Finding("HIGH", "NO_ROLLBACK",
                                    f"{z['zone']}: no rollback source declared"))
        for r in z.get("records", []):
            if r.get("proxied") and str(r.get("content", "")).startswith("185.199."):
                findings.append(Finding("CRITICAL", "PAGES_ORANGE_CLOUD",
                                        f"{z['zone']}: proxied:true on a GitHub Pages IP breaks cert issuance"))
    return findings


def run_validate(targets: Path | None) -> Report:
    try:
        doc = _load_targets(targets)
    except FileNotFoundError as e:
        return Report(cmd="dns validate", state=State.FAIL,
                      findings=[Finding("HIGH", "MISSING_CONFIG", str(e))])
    if _SCHEMA.exists():
        schema = json.loads(_SCHEMA.read_text())
        try:
            js_validate(doc, schema)
        except Exception as e:
            return Report(cmd="dns validate", state=State.FAIL,
                          findings=[Finding("HIGH", "SCHEMA_MISMATCH", str(e)[:300])])
    findings = impossible_states(doc)
    state = State.FAIL if findings else State.PASS
    return Report(cmd="dns validate", state=state, findings=findings,
                  summary={"zones": [z["zone"] for z in doc.get("zones", [])]})


def run_plan(targets: Path | None) -> Report:
    v = run_validate(targets)
    if v.state == State.FAIL:
        v.cmd = "dns plan"
        return v
    doc = _load_targets(targets)
    plans = []
    for z in doc.get("zones", []):
        plans.append({
            "zone": z["zone"], "role": z.get("role", "UNKNOWN"),
            "prechecks": z.get("prechecks", []),
            "records": z.get("records", []),
            "rollback_source": z.get("rollback_source"),
            "rule": "snapshot the zone to the rollback_source BEFORE any write; one record set at a time; poll propagation between sets",
        })
    return Report(cmd="dns plan", state=State.PASS, findings=v.findings,
                  summary={"plans": plans})


def run_apply(targets: Path | None) -> Report:
    """Print the AUTHORIZATION PACKET and stop. Never mutates. R10."""
    plan = run_plan(targets)
    packet = {
        "state": "AWAITING_AUTHORIZATION",
        "warning": "this CLI never mutates; hand this packet to an operator",
        "prechecks_required": [
            "token verified active at /user/tokens/verify with Zone:DNS:Edit + Zone:Zone:Read scoped to target zones",
            "zone exported to rollback bundle on disk BEFORE any write",
            "one record set at a time with propagation polling between sets",
        ],
        "plans": plan.summary.get("plans", []),
    }
    return Report(cmd="dns apply", state=State.BLOCKED, findings=plan.findings,
                  summary=packet)
