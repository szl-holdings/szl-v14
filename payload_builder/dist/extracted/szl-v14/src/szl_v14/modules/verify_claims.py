"""verify-claims — re-measure published claims; mismatch -> CLAIM_DRIFT."""

from __future__ import annotations

from pathlib import Path

import yaml

from szl_v14.lib.estate import load_snapshots
from szl_v14.lib.states import Finding, Report, State

_CLAIMS_FILE = Path(__file__).resolve().parents[3] / "claims.yaml"


def _measure(claim: dict, snapshot_dir: Path):
    """Return measured value, or None when the claim is UNMEASURABLE here."""
    kind = claim.get("measure", {}).get("kind")
    snap = load_snapshots(snapshot_dir)
    if kind == "github_repo_count":
        return len(snap.github_repos) if snap.github_repos else None
    if kind == "github_visibility_count":
        vis = claim["measure"]["visibility"]
        return sum(1 for r in snap.github_repos if r.get("visibility") == vis) if snap.github_repos else None
    if kind == "hf_repo_count":
        rtype = claim["measure"]["repo_type"]
        return snap.hf_estate.get("counts", {}).get(rtype)
    if kind == "github_repo_present":
        return claim["measure"]["repo"] in {r.get("name") for r in snap.github_repos}
    return None


def run(snapshot_dir: Path, claims_path: Path | None = None) -> Report:
    claims_path = claims_path or _CLAIMS_FILE
    findings: list[Finding] = []
    results = []
    if not claims_path.exists():
        return Report(cmd="verify-claims", state=State.UNKNOWN,
                      findings=[Finding("MEDIUM", "NO_CLAIMS", f"claims file missing: {claims_path}")])

    claims = yaml.safe_load(claims_path.read_text()) or []
    for c in claims:
        measured = _measure(c, snapshot_dir)
        if measured is None:
            results.append({"id": c.get("id"), "state": "UNMEASURABLE", "claim": c.get("claim")})
            continue
        expected = c.get("expected")
        ok = measured == expected
        results.append({"id": c.get("id"), "claim": c.get("claim"), "expected": expected,
                        "measured": measured, "state": "PASS" if ok else "FAIL"})
        if not ok:
            findings.append(Finding("HIGH", "CLAIM_DRIFT",
                                    f"{c.get('id')}: published {expected!r} != measured {measured!r}",
                                    {"claim": c.get("claim"), "source": c.get("source")}))

    passed = sum(1 for r in results if r["state"] == "PASS")
    drifted = sum(1 for r in results if r["state"] == "FAIL")
    unmeasurable = sum(1 for r in results if r["state"] == "UNMEASURABLE")
    state = State.FAIL if drifted else (State.WARN if unmeasurable else State.PASS)
    return Report(cmd="verify-claims", state=state, findings=findings,
                  summary={"pass": passed, "claim_drift": drifted,
                           "unmeasurable": unmeasurable, "results": results})
