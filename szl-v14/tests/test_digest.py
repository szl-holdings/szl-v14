from szl_v14.lib.digest import sha256_file, sha256_bytes, digest_map

# known sha256 vector over real bytes
ABC = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def test_sha256_bytes_known_vector():
    assert sha256_bytes(b"abc") == ABC


def test_sha256_file_hashes_bytes_not_name(tmp_path):
    p = tmp_path / "SZLHOLDINGS"  # a name that must NOT be hashed
    p.write_bytes(b"abc")
    assert sha256_file(p) == ABC
    # and the name itself hashes to something different
    assert sha256_file(p) != sha256_bytes(b"SZLHOLDINGS")


def test_digest_map_relative(tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "f.txt").write_bytes(b"abc")
    m = digest_map(tmp_path)
    assert m == {"a/f.txt": ABC}
