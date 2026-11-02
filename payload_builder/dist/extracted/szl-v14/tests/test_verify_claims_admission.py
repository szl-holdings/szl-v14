"""A claim report requires actual, well-formed claims before measuring."""
import json
from pathlib import Path

import pytest
import yaml

from szl_v14.lib.states import State, emit_json
from szl_v14.modules import verify_claims


def claim(**changes):
    return {"id": "repo-count", "claim": "Repository count", "expected": 1,
            "measure": {"kind": "github_repo_count"}, **changes}


def run(tmp_path, text):
    path = tmp_path / "claims.yaml"
    path.write_text(text)
    root = tmp_path / "snapshots"
    (root / "github").mkdir(parents=True, exist_ok=True)
    (root / "github/repos_cli.json").write_text(json.dumps([{"name": "known", "visibility": "PUBLIC"}]))
    return verify_claims.run(root, path)


@pytest.mark.parametrize("text", ["", "# no claims\n", "null", "[]"])
def test_empty_document_is_unknown_without_measurement(tmp_path, monkeypatch, text):
    monkeypatch.setattr(verify_claims, "_measure", lambda *args: pytest.fail("empty claims measured"))
    report = run(tmp_path, text)
    assert report.state == State.UNKNOWN
    assert report.findings[0].code == "NO_CLAIMS"


@pytest.mark.parametrize("document", [False, 0, "claims", {}, {"id": "mapping"},
    [None], [1], ["claim"], [False], [{}], [claim(id="")], [claim(id=[])],
    [claim(claim="")], [claim(claim=0)], [claim(measure=None)],
    [claim(measure=[])], [claim(measure={})], [claim(measure={"kind": 1})],
    [claim(expected=True)], [claim(expected="1")], [claim(expected=-1)],
    [claim(expected=float("nan"))], [claim(expected=float("inf"))],
    [claim(measure={"kind": "github_visibility_count"})],
    [claim(measure={"kind": "github_visibility_count", "visibility": []})],
    [claim(measure={"kind": "hf_repo_count", "repo_type": {}})],
    [claim(measure={"kind": "github_repo_present", "repo": "known"}, expected=1)],
    [claim(measure={"kind": "github_repo_present", "repo": []}, expected=True)],
    [claim(), claim()],
])
def test_malformed_claim_set_fails_before_any_measurement(tmp_path, monkeypatch, document):
    monkeypatch.setattr(verify_claims, "_measure", lambda *args: pytest.fail("invalid claim set measured"))
    report = run(tmp_path, yaml.safe_dump(document))
    assert report.state == State.FAIL
    assert report.findings[0].code == "INVALID_CLAIMS"
    json.loads(emit_json(report))


def test_missing_expected_and_invalid_later_claim_cannot_partially_pass(tmp_path, monkeypatch):
    incomplete = claim(id="second")
    del incomplete["expected"]
    monkeypatch.setattr(verify_claims, "_measure", lambda *args: pytest.fail("partially admitted claims"))
    assert run(tmp_path, yaml.safe_dump([claim(), incomplete])).state == State.FAIL


@pytest.mark.parametrize("text", ["[unterminated", "- id: one\n  measure: [unclosed"])
def test_yaml_syntax_error_is_a_report_not_a_traceback(tmp_path, text):
    report = run(tmp_path, text)
    assert report.state == State.FAIL
    assert report.findings[0].code == "INVALID_CLAIMS"


def test_missing_file_preserves_unknown(tmp_path):
    report = verify_claims.run(tmp_path, tmp_path / "absent.yaml")
    assert report.state == State.UNKNOWN
    assert report.findings[0].code == "NO_CLAIMS"


def test_unreadable_file_is_unknown(tmp_path):
    report = verify_claims.run(tmp_path, tmp_path)
    assert report.state == State.UNKNOWN
    assert report.findings[0].code == "CLAIMS_UNAVAILABLE"


def test_valid_pass_drift_and_future_measure_kind_preserve_states(tmp_path):
    good = run(tmp_path, yaml.safe_dump([claim()]))
    assert good.state == State.PASS and good.summary["pass"] == 1
    drift = run(tmp_path, yaml.safe_dump([claim(expected=2)]))
    assert drift.state == State.FAIL and drift.summary["claim_drift"] == 1
    future = run(tmp_path, yaml.safe_dump([claim(measure={"kind": "future_metric"})]))
    assert future.state == State.WARN and future.summary["unmeasurable"] == 1


def test_missing_snapshot_cannot_prove_repository_absence(tmp_path):
    path = tmp_path / "claims.yaml"
    path.write_text(yaml.safe_dump([claim(expected=False, measure={"kind": "github_repo_present", "repo": "absent"})]))
    report = verify_claims.run(tmp_path / "missing", path)
    assert report.state == State.WARN
    assert report.summary["unmeasurable"] == 1


def test_present_empty_snapshot_can_prove_repository_absence(tmp_path):
    path = tmp_path / "claims.yaml"
    path.write_text(yaml.safe_dump([claim(expected=False, measure={"kind": "github_repo_present", "repo": "absent"})]))
    (tmp_path / "github").mkdir()
    (tmp_path / "github/repos_cli.json").write_text("[]")
    report = verify_claims.run(tmp_path, path)
    assert report.state == State.PASS and report.summary["pass"] == 1


@pytest.mark.parametrize("visibility", ["public", "PuBlIc"])
@pytest.mark.parametrize("expected,state", [(1, State.PASS), (0, State.FAIL)])
def test_visibility_admission_and_measurement_use_the_same_case(tmp_path, visibility, expected, state):
    report = run(tmp_path, yaml.safe_dump([claim(
        measure={"kind": "github_visibility_count", "visibility": visibility}, expected=expected)]))
    assert report.state == state
    assert report.summary["results"][0]["measured"] == 1
