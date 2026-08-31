"""export — bundle a directory: digest manifest (schema-validated), DSSE unsigned envelope, receipt.

Every export gets a manifest; every manifest gets a digest; every bundle records
inputs and outputs. The manifest itself is validated against export_bundle.schema.json.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from jsonschema import validate as js_validate

from szl_v14.lib.digest import digest_map, sha256_file
from szl_v14.lib.dsse import envelope, write_unsigned
from szl_v14.lib.jcs import canonical
from szl_v14.lib.states import Finding, Report, State

FORBIDDEN_DOMAIN = re.compile(r"(?<!-)a11oy\.com")
_SCHEMA = Path(__file__).resolve().parents[3] / "schemas" / "export_bundle.schema.json"


def run(target_dir: Path, out_dir: Path, bundle_name: str = "bundle") -> Report:
    if not target_dir.is_dir():
        return Report(cmd="export", state=State.FAIL,
                      findings=[Finding("HIGH", "MISSING_INPUT", f"no such directory: {target_dir}")])

    files = digest_map(target_dir)
    findings: list[Finding] = []
    for rel in files:
        content = (target_dir / rel).read_text(errors="ignore")
        if FORBIDDEN_DOMAIN.search(content):
            findings.append(Finding("CRITICAL", "FORBIDDEN_LINK",
                                    f"forbidden domain reference in bundle member {rel}"))

    manifest = {"bundle": bundle_name,
                "format": "szl/v14-export-bundle",
                "subjects": [{"name": k, "digest": {"sha256": v}} for k, v in files.items()]}
    if _SCHEMA.exists():
        schema = json.loads(_SCHEMA.read_text())
        try:
            js_validate(manifest, schema)
        except Exception as e:
            return Report(cmd="export", state=State.FAIL,
                          findings=[Finding("HIGH", "SCHEMA_MISMATCH", f"bundle manifest invalid: {str(e)[:300]}")])

    out_dir.mkdir(parents=True, exist_ok=True)
    mpath = out_dir / "manifest.json"
    mpath.write_text(canonical(manifest) + "\n")
    env = envelope(canonical(manifest).encode("utf-8"), payload_type="application/vnd.szl.bundle-manifest+json")
    epath = write_unsigned(env, out_dir / "manifest.unsigned.json")

    outputs = {str(mpath): sha256_file(mpath), str(epath): sha256_file(epath)}
    state = State.FAIL if any(f.severity == "CRITICAL" for f in findings) else State.PASS
    return Report(cmd="export", state=state, findings=findings, outputs=outputs,
                  summary={"files": len(files), "bundle": bundle_name,
                           "manifest_digest": outputs[str(mpath)]})
