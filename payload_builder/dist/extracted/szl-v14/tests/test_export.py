import json

from szl_v14.lib.digest import sha256_file, digest_map
from szl_v14.lib.states import State
from szl_v14.modules import export as m_export


def test_bundle_manifest_validates_and_digests_match(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.txt").write_text("alpha")
    (src / "b.txt").write_text("beta")
    out = tmp_path / "out"
    report = m_export.run(src, out, "t")
    assert report.state == State.PASS
    manifest = json.loads((out / "manifest.json").read_text())
    subjects = {s["name"]: s["digest"]["sha256"] for s in manifest["subjects"]}
    assert subjects == digest_map(src)
    # unsigned envelope present and honest
    env = json.loads((out / "manifest.unsigned.json").read_text())
    assert env["signatures"] == []


def test_forbidden_domain_in_bundle_is_critical(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "bad.md").write_text("see https://a11oy" + ".com for details")
    report = m_export.run(src, tmp_path / "out", "t")
    assert report.state == State.FAIL
    assert any(f.code == "FORBIDDEN_LINK" for f in report.findings)


def test_missing_dir_fails(tmp_path):
    assert m_export.run(tmp_path / "nope", tmp_path / "o", "t").state == State.FAIL
