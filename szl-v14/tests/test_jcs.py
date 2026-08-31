import json

from szl_v14.lib.jcs import canonical, jcs_digest


def test_canonical_orders_keys_and_strips_whitespace():
    obj = {"b": [1, 2], "a": "x"}
    assert canonical(obj) == '{"a":"x","b":[1,2]}'


def test_whitespace_equivalent_docs_have_identical_digest():
    """The real-JCS proof: formatting-only differences produce zero drift."""
    a = {"z": 1, "a": [True, None]}
    b = json.loads('{ "a" : [ true , null ] , "z" : 1 }')
    assert canonical(a) == canonical(b)
    assert jcs_digest(a) == jcs_digest(b)


def test_unicode_and_numbers_are_rfc8785():
    # RFC 8785 serializes non-ASCII unescaped and integers without decoration
    assert canonical({"é": 1}) == '{"é":1}'
