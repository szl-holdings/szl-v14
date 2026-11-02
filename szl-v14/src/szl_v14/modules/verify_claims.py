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
        vis = claim["measure"]["visibility"].upper()
        return sum(1 for r in snap.github_repos
                   if isinstance(r.get("visibility"), str)
                   and r["visibility"].upper() == vis) if snap.github_repos else None
    if kind == "hf_repo_count":
        rtype = claim["measure"]["repo_type"]
        return snap.hf_estate.get("counts", {}).get(rtype)
    if kind == "github_repo_present":
        if "github/repos_cli.json" in snap.unknown:
            return None
        return claim["measure"]["repo"] in {r.get("name") for r in snap.github_repos}
    return None


def _invalid_claims(reason: str) -> Report:
    return Report(cmd="verify-claims", state=State.FAIL,
                  findings=[Finding("HIGH", "INVALID_CLAIMS", reason)])


def _valid_claim(claim: object) -> bool:
    if not isinstance(claim, dict):
        return False
    if any(not isinstance(claim.get(key), str) or not claim[key].strip()
           for key in ("id", "claim")) or "expected" not in claim:
        return False
    measure = claim.get("measure")
    if not isinstance(measure, dict):
        return False
    kind = measure.get("kind")
    if not isinstance(kind, str) or not kind.strip():
        return False
    if kind in {"github_repo_count", "github_visibility_count", "hf_repo_count"}:
        if type(claim["expected"]) is not int or claim["expected"] < 0:
            return False
    if kind == "github_visibility_count":
        visibility = measure.get("visibility")
        return isinstance(visibility, str) and visibility.upper() in {"PUBLIC", "PRIVATE", "INTERNAL"}
    if kind == "hf_repo_count":
        repo_type = measure.get("repo_type")
        return isinstance(repo_type, str) and repo_type in {"model", "dataset", "space"}
    if kind == "github_repo_present":
        repo = measure.get("repo")
        return type(claim["expected"]) is bool and isinstance(repo, str) and bool(repo.strip())
    # A future nonempty measurement kind remains UNMEASURABLE, never PASS.
    return True


def run(snapshot_dir: Path, claims_path: Path | None = None) -> Report:
    claims_path = claims_path or _CLAIMS_FILE
    findings: list[Finding] = []
    results = []
    if not claims_path.exists():
        return Report(cmd="verify-claims", state=State.UNKNOWN,
                      findings=[Finding("MEDIUM", "NO_CLAIMS", f"claims file missing: {claims_path}")])

    try:
        claims = yaml.safe_load(claims_path.read_text())
    except OSError:
        return Report(cmd="verify-claims", state=State.UNKNOWN,
                      findings=[Finding("MEDIUM", "CLAIMS_UNAVAILABLE", "claims file could not be read")])
    except (yaml.YAMLError, UnicodeError, ValueError, RecursionError):
        return _invalid_claims("claims file could not be parsed")
    if claims is None or (isinstance(claims, list) and not claims):
        return Report(cmd="verify-claims", state=State.UNKNOWN,
                      findings=[Finding("MEDIUM", "NO_CLAIMS", "claims file contains no claims")])
    if not isinstance(claims, list):
        return _invalid_claims("claims document must be a nonempty list")
    seen = set()
    for index, claim in enumerate(claims, start=1):
        if not _valid_claim(claim):
            return _invalid_claims(f"claim {index} has an invalid schema")
        if claim["id"] in seen:
            return _invalid_claims(f"claim {index} repeats a claim id")
        seen.add(claim["id"])
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
