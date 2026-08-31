import pytest

from szl_v14.lib.dsse import envelope, write_unsigned, verify_unsigned


def test_envelope_is_honestly_unsigned():
    env = envelope(b"payload")
    assert env["signatures"] == []
    assert env["payloadType"]


def test_write_unsigned_enforces_naming(tmp_path):
    env = envelope(b"x")
    with pytest.raises(ValueError):
        write_unsigned(env, tmp_path / "payload.json")  # wrong name -> error
    p = write_unsigned(env, tmp_path / "payload.unsigned.json")
    assert verify_unsigned(p)["signatures"] == []


def test_named_unsigned_but_claims_signatures_fails(tmp_path):
    env = envelope(b"x")
    env["signatures"] = [{"sig": "abc"}]
    with pytest.raises(ValueError):
        write_unsigned(env, tmp_path / "payload.unsigned.json")


def test_verify_rejects_empty_sigs_without_unsigned_name(tmp_path):
    env = envelope(b"x")
    p = tmp_path / "payload.json"
    p.write_text(__import__("json").dumps(env))
    with pytest.raises(ValueError):
        verify_unsigned(p)
