from szl_v14.modules.dns import impossible_states


def _zone(**kw):
    base = {"zone": "example.net", "records": [], "rollback_source": "rb.json"}
    base.update(kw)
    return base


def test_apex_cname_without_flattening_is_rejected():
    doc = {"zones": [_zone(records=[{"type": "CNAME", "name": "@", "content": "hf.space."}])]}
    codes = [f.code for f in impossible_states(doc)]
    assert "IMPOSSIBLE_DNS" in codes


def test_apex_cname_with_flattening_passes():
    doc = {"zones": [_zone(apex_cname_flattening=True,
                           records=[{"type": "CNAME", "name": "@", "content": "hf.space."}])]}
    assert impossible_states(doc) == []


def test_proxied_pages_ip_is_rejected():
    doc = {"zones": [_zone(records=[{"type": "A", "name": "@", "content": "185.199.108.153",
                                     "proxied": True}])]}
    codes = [f.code for f in impossible_states(doc)]
    assert "PAGES_ORANGE_CLOUD" in codes


def test_unproxied_pages_ip_plus_rollback_passes():
    doc = {"zones": [_zone(records=[{"type": "A", "name": "@", "content": "185.199.108.153",
                                     "proxied": False}])]}
    assert impossible_states(doc) == []


def test_missing_rollback_source_flagged():
    z = _zone()
    del z["rollback_source"]
    doc = {"zones": [z]}
    assert "NO_ROLLBACK" in [f.code for f in impossible_states(doc)]
