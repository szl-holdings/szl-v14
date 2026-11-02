#!/usr/bin/env python3
"""payload_builder — the thing that builds the payload.

Sections are the source. dist/ is derived. Never hand-edit dist/.

Verbs:
  generate  Scaffold missing section stubs from manifest.toml. Idempotent.
  compile   Hard gates: order, must_contain tokens, forbidden + banned-claims lint.
  extract   Write <!-- extract: path mode=755 --> fences to dist/extracted/.
  export    Assemble payload + manifest.json + DSSE unsigned envelope +
            in-toto statement + timestamped build receipt.
  verify    Re-digest, honesty assertions, forbidden-domain grep. Exit 1 on failure.
  all       compile -> extract -> export. No destructive apply exists.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import sys
import tomllib
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MANIFEST_PATH = ROOT / "manifest.toml"
DIST = ROOT / "dist"
EXTRACTED = DIST / "extracted"
RECEIPTS = DIST / "receipts"
LINT_FORBIDDEN = ROOT / "lint" / "forbidden.txt"
LINT_BANNED = ROOT / "lint" / "banned_claims.txt"

EXTRACT_TAG = re.compile(r"<!--\s*extract:\s*(\S+?)(?:\s+mode=(\d+))?\s*-->")
# Variable-length fences: content containing ``` is wrapped in longer runs.
FENCE = re.compile(r"(`{3,})[^\n]*\n(.*?)\n?\1(?!`)", re.S)
FORBIDDEN_DOMAIN = re.compile(r"(?<!-)a11oy\.com")  # prose must defang: a11oy[.]com


def fail(msg: str, code: int = 1) -> "None":
    print(f"COMPILE-FAIL: {msg}", file=sys.stderr)
    sys.exit(code)


def sha256_file(path: Path) -> str:
    """Digest ACTUAL FILE BYTES. Never a name. Never an .encode() of a string."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_manifest() -> dict:
    if not MANIFEST_PATH.exists():
        fail("manifest.toml missing")
    return tomllib.loads(MANIFEST_PATH.read_text())


def sections(man: dict) -> list[dict]:
    return man.get("sections", [])


def load_lint(path: Path) -> list[re.Pattern]:
    if not path.exists():
        fail(f"lint file missing: {path}")
    pats = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            pats.append(re.compile(line, re.I if "banned" in path.name else 0))
    return pats


# ---------------------------------------------------------------- generate
def cmd_generate(man: dict) -> None:
    created = 0
    for sec in sections(man):
        p = ROOT / sec["path"]
        if p.exists():
            continue  # idempotent: never overwrite real content
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(f"# SECTION: {sec['id']}\n\n(stub — replace with real content)\n")
        created += 1
        print(f"scaffolded stub: {sec['path']}  (STUB — not real content)")
    (ROOT / "lint").mkdir(exist_ok=True)
    print(f"generate: {created} stub(s) created, {len(sections(man)) - created} section(s) already present")


# ------------------------------------------------------------------ compile
def cmd_compile(man: dict) -> None:
    secs = sections(man)
    if not secs:
        fail("no sections in manifest.toml")

    # Every declared section must exist.
    for sec in secs:
        if not (ROOT / sec["path"]).exists():
            fail(f"declared section missing on disk: {sec['path']} (run: python build.py generate)")

    # Gate: require_dns_first — DNS/credential repair precedes training/chip work.
    gates = man.get("gates", {})
    if gates.get("require_dns_first"):
        idx_dns = next((i for i, s in enumerate(secs) if s["id"] == "phase_neg1_dns"), None)
        if idx_dns is None:
            fail("require_dns_first is set but no section has id 'phase_neg1_dns'")
        before_kinds = gates.get("dns_first_before", ["khipu", "train"])
        for i, s in enumerate(secs):
            if i < idx_dns and any(k in s["id"] for k in before_kinds):
                fail(f"section '{s['id']}' appears before 'phase_neg1_dns' — DNS-first ordering violated")

    # Per-section token assertions — the constraints most likely dropped in a casual edit.
    for sec in secs:
        body = (ROOT / sec["path"]).read_text()
        for token in sec.get("must_contain", []):
            if token not in body:
                fail(f"section '{sec['id']}' missing required token: {token!r}")

    # Compile-fail promotion: extract tags must be wired, not orphaned.
    for sec in secs:
        body = (ROOT / sec["path"]).read_text()
        if EXTRACT_TAG.search(body) and not FENCE.search(body, EXTRACT_TAG.search(body).end()):
            fail(f"section '{sec['id']}' contains an extract tag with no following code fence")

    # Forbidden antipatterns: the recurring defects, as regexes.
    for pat in load_lint(LINT_FORBIDDEN):
        for sec in secs:
            body = (ROOT / sec["path"]).read_text()
            m = pat.search(body)
            if m:
                fail(f"forbidden pattern /{pat.pattern}/ matched in {sec['path']}: {m.group(0)[:80]!r}")

    # Banned claim-language.
    for pat in load_lint(LINT_BANNED):
        for sec in secs:
            body = (ROOT / sec["path"]).read_text()
            m = pat.search(body)
            if m:
                fail(f"banned claim /{pat.pattern}/ in {sec['path']}: {m.group(0)!r}")

    print(f"compile: OK — {len(secs)} sections, all gates green")


# ------------------------------------------------------------------ extract
def iter_extract_fences(man: dict):
    for sec in sections(man):
        body = (ROOT / sec["path"]).read_text()
        pos = 0
        while True:
            tag = EXTRACT_TAG.search(body, pos)
            if not tag:
                break
            fence = FENCE.search(body, tag.end())
            if not fence or body[tag.end():fence.start()].strip():
                fail(f"extract tag in {sec['path']} at offset {tag.start()} is not immediately followed by a code fence")
            yield sec, tag.group(1), tag.group(2) or "644", fence.group(2)
            pos = fence.end()


def cmd_extract(man: dict) -> None:
    EXTRACTED.mkdir(parents=True, exist_ok=True)
    seen: set[str] = set()
    count = 0
    for sec, rel, mode, content in iter_extract_fences(man):
        rp = Path(rel)
        if ".." in rp.parts or rp.is_absolute():
            fail(f"extract path escape attempt in {sec['path']}: {rel!r}")
        if rel in seen:
            fail(f"duplicate extract target: {rel!r} (second occurrence in {sec['path']})")
        seen.add(rel)
        dest = EXTRACTED / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        # Canonical form: exactly one trailing newline. Sources are normalized
        # the same way, so extract is byte-lossless vs the source tree.
        dest.write_text(content.rstrip("\n") + "\n")
        os.chmod(dest, int(mode, 8))
        count += 1
    print(f"extract: {count} file(s) written to dist/extracted/")


# ------------------------------------------------------------------- export
def jcs(obj) -> str:
    """Canonical JSON per RFC 8785 via the real library. Not sort_keys."""
    try:
        import rfc8785
    except ImportError:
        fail("rfc8785 not installed (pip install rfc8785). json.dumps(sort_keys=True) is not JCS.")
    out = rfc8785.dumps(obj)
    return out.decode("utf-8") if isinstance(out, bytes) else out


def write_json(path: Path, obj) -> None:
    path.write_bytes(jcs(obj).encode("utf-8"))


def builder_publication_eligible(man: dict) -> bool:
    """Return the builder's fixed authorization value after strict admission."""
    gates = man.get("gates", {})
    if type(gates) is not dict:
        fail("gates must be a TOML table")
    value = gates.get("publication_eligible", False)
    if value is not False:
        fail("publication_eligible must be the literal boolean false at the builder layer")
    return False


def build_payload(man: dict) -> bytes:
    name = man["payload"]["name"]
    lines = [f"# {name}", ""]
    if man["payload"].get("embed_build_time_in_body"):
        fail("embed_build_time_in_body=true destroys reproducibility; build time belongs only in the receipt")
    for sec in sections(man):
        body = (ROOT / sec["path"]).read_text()
        sec_digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
        # Inline per-section digest: diff two payload versions and know instantly which section changed.
        lines.append(f"<!-- section:{sec['id']} sha256:{sec_digest} -->")
        lines.append(body.rstrip())
        lines.append("\n---\n")
    return ("\n".join(lines)).encode("utf-8")


def cmd_export(man: dict) -> None:
    DIST.mkdir(exist_ok=True)
    RECEIPTS.mkdir(exist_ok=True)
    payload = build_payload(man)
    out = DIST / Path(man["payload"]["out"]).name
    out.write_bytes(payload)

    self_artifacts = {out.name, "manifest.json", "statement.intoto.json", "payload.unsigned.json"}
    subjects = [{"name": str(p.relative_to(DIST)), "digest": {"sha256": sha256_file(p)}}
                for p in sorted(DIST.rglob("*"))
                if p.is_file() and "receipts" not in p.parts and p.name not in self_artifacts]
    subjects.insert(0, {"name": out.name, "digest": {"sha256": sha256_file(out)}})

    manifest = {
        "payload": man["payload"]["name"],
        "version": man["payload"]["version"],
        "publication_eligible": builder_publication_eligible(man),
        "sections": [{"id": s["id"], "path": s["path"],
                      "sha256": hashlib.sha256((ROOT / s["path"]).read_bytes()).hexdigest()}
                     for s in sections(man)],
        "subjects": subjects,
    }
    write_json(DIST / "manifest.json", manifest)

    # in-toto Statement v1 over the payload and every extracted file.
    statement = {
        "_type": "https://in-toto.io/Statement/v1",
        "subject": subjects,
        "predicateType": "https://szl.dev/predicates/payload-build/v1",
        "predicate": {
            "builder": {"id": "payload_builder/build.py"},
            "invocation": {"parameters": {"command": "all"}},
            "publication_eligible": manifest["publication_eligible"],
        },
    }
    write_json(DIST / "statement.intoto.json", statement)

    # DSSE envelope, honestly unsigned: b64 payload, signatures: [].
    env = {
        "payloadType": "application/vnd.in-toto+json",
        "payload": base64.b64encode(jcs(statement).encode("utf-8")).decode("ascii"),
        "signatures": [],
    }
    write_json(DIST / "payload.unsigned.json", env)

    # Time lives ONLY here. Receipts are events; artifacts are deterministic.
    rcpt = {
        "event": "build",
        "cmd": "export",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "outputs": {s["name"]: s["digest"]["sha256"] for s in subjects},
    }
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    write_json(RECEIPTS / f"build-{ts}.json", rcpt)
    print(f"export: {out} ({sha256_file(out)[:16]}…) + manifest + in-toto + payload.unsigned.json + receipt")


# ------------------------------------------------------------------- verify
def cmd_verify(man: dict) -> None:
    out = DIST / Path(man["payload"]["out"]).name
    for p in (out, DIST / "manifest.json", DIST / "payload.unsigned.json", DIST / "statement.intoto.json"):
        if not p.exists():
            fail(f"missing dist artifact: {p.name} (run: python build.py all)")

    # Digest re-check against the manifest.
    manifest = json.loads((DIST / "manifest.json").read_text())
    for s in manifest["subjects"]:
        target = DIST / s["name"]
        if not target.exists():
            fail(f"manifest subject missing: {s['name']}")
        actual = sha256_file(target)
        if actual != s["digest"]["sha256"]:
            fail(f"digest mismatch: {s['name']} manifest={s['digest']['sha256'][:16]}… actual={actual[:16]}…")

    # Signing honesty: the envelope must not claim signatures while named unsigned.
    env = json.loads((DIST / "payload.unsigned.json").read_text())
    if env.get("signatures") != []:
        fail("envelope claims signatures but file is named unsigned")
    if not (DIST / "payload.unsigned.json").name.endswith(".unsigned.json"):
        fail("unsigned envelope mislabeled")

    # publication_eligible must remain false at the builder layer; the control
    # plane computes it from 14 inputs; nothing here may assert it.
    if manifest.get("publication_eligible") is not False:
        fail("publication_eligible is not False")

    # Forbidden-domain grep over every dist artifact.
    for p in DIST.rglob("*"):
        if p.is_file() and FORBIDDEN_DOMAIN.search(p.read_text(errors="ignore")):
            fail(f"forbidden domain reference in dist artifact: {p.relative_to(DIST)}")

    print("verify: OK — digests match, unsigned naming honest, forbidden domain absent, eligibility not asserted")


VERBS = {"generate": cmd_generate, "compile": cmd_compile, "extract": cmd_extract,
         "export": cmd_export, "verify": cmd_verify}


def cmd_all(man: dict) -> None:
    cmd_compile(man)
    cmd_extract(man)
    cmd_export(man)
    print("all: build complete (no destructive apply exists) — run: python build.py verify && make idempotent")


VERBS["all"] = cmd_all


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in VERBS:
        print(f"usage: python build.py [{'|'.join(VERBS)}]", file=sys.stderr)
        sys.exit(2)
    VERBS[sys.argv[1]](load_manifest())


if __name__ == "__main__":
    main()

