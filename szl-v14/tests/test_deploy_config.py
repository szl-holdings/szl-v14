"""Read-only deployment inspection reports missing inputs without a crash."""
from szl_v14.lib.states import State
from szl_v14.modules import deploy, dns


def test_missing_explicit_targets_is_unknown(tmp_path):
    report = deploy.run(tmp_path / "absent.yaml", None)
    assert report.state == State.UNKNOWN
    assert report.findings[0].code == "MISSING_CONFIG"


def test_missing_default_targets_is_unknown(tmp_path, monkeypatch):
    monkeypatch.setattr(dns, "_TARGETS", tmp_path / "absent-default.yaml")
    report = deploy.run(None, None)
    assert report.state == State.UNKNOWN
    assert report.findings[0].code == "MISSING_CONFIG"


def test_valid_targets_are_loaded_once(monkeypatch):
    calls = []
    def load(path):
        calls.append(path)
        return {"zones": [{"zone": "example.test", "role": "demo", "target_summary": "offline"}]}
    monkeypatch.setattr(deploy, "_load_targets", load)
    report = deploy.run(None, None)
    assert calls == [None]
    assert report.state == State.PASS
    assert report.summary["deployments"] == [{"zone": "example.test", "role": "demo", "target": "offline", "notes": ""}]
