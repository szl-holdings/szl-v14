# §90 Control plane — szl-v14 (machine-wrapped source of truth)

Every file below is written to `dist/extracted/` by `build.py extract`.
Edit here, not in `dist/`. Regenerate only when the tree changes shape.

## `szl-v14/README.md`

<!-- extract: szl-v14/README.md -->
````markdown
# szl-v14 — SZL Holdings estate control plane

Audit the GitHub / Hugging Face / Cloudflare estate from snapshots, plan DNS
repair, build provenance, and export digest-bearing evidence bundles.
**Read-only by construction**: every mutating verb prints an authorization
packet and stops with state `AWAITING_AUTHORIZATION`.

## Install

```bash
pip install -e .
```

## Commands

| Command | Purpose |
|---|---|
| `szl-v14 doctor` | Environment triage; first section is `BLOCKERS THAT OUTRANK ALL COSMETIC WORK`; exit 2 on any FATAL |
| `szl-v14 inventory --snapshot-dir <dir>` | Build `repos.yaml` from estate snapshots; two-source agreement check; PARTIAL on disagreement |
| `szl-v14 audit --snapshot-dir <dir>` | One audit file per repo from `REPO_AUDIT.j2` + `REPOSITORY_MATRIX.csv`; unprobed fields are UNKNOWN |
| `szl-v14 verify-claims --snapshot-dir <dir>` | Re-measure `claims.yaml`; mismatches become CLAIM_DRIFT findings |
| `szl-v14 dns plan` / `dns validate` / `dns apply` | Plan and validate `dns-targets.yaml`; `apply` prints the AUTHORIZATION PACKET and stops |
| `szl-v14 deploy` | Inspect-only deployment state table |
| `szl-v14 provenance <dir>` | in-toto Statement v1 + DSSE `*.unsigned.json` envelope over a directory |
| `szl-v14 mcp` | Drift fixtures: canonical-equivalence must show zero drift; refusal-then-leak nets −3.0 |
| `szl-v14 remediate <findings.json>` | Ordered remediation plan (credentials → DNS → origin-host → code → cosmetic) |
| `szl-v14 export <dir>` | Bundle: `manifest.json` (schema-validated), `manifest.unsigned.json`, receipt |

Every command supports `--json` and writes a receipt. Exit codes: 0 ok,
2 FAIL/CRITICAL finding, 3 misuse. BLOCKED and UNKNOWN print prominently and
are never coerced to PASS.

## Doctrine

Digests are over actual file bytes. Canonical JSON is real RFC 8785.
Unsigned artifacts are named `*.unsigned.json` and carry `signatures: []`.
No timestamps inside artifact bodies — time lives only in receipts.
The forbidden domain (`a11oy[.]com`) fails any command it appears in.
````

## `szl-v14/claims.yaml`

<!-- extract: szl-v14/claims.yaml -->
```yaml
# Published claims, re-measured against live snapshots. Mismatch -> CLAIM_DRIFT.
- id: gh-repo-count
  claim: GitHub org repository count
  source: estate enumeration 2026-08-31 (3-source agreement)
  expected: 100
  measure: {kind: github_repo_count}
- id: gh-public-count
  claim: GitHub org public repository count
  source: estate enumeration 2026-08-31
  expected: 95
  measure: {kind: github_visibility_count, visibility: PUBLIC}
- id: hf-model-count
  claim: Hugging Face model count
  source: hub_repo_search author=SZLHOLDINGS 2026-08-31
  expected: 44
  measure: {kind: hf_repo_count, repo_type: model}
- id: hf-dataset-count
  claim: Hugging Face dataset count
  source: hub_repo_search author=SZLHOLDINGS 2026-08-31
  expected: 38
  measure: {kind: hf_repo_count, repo_type: dataset}
- id: hf-space-count
  claim: Hugging Face space count
  source: hub_repo_search author=SZLHOLDINGS 2026-08-31
  expected: 47
  measure: {kind: hf_repo_count, repo_type: space}
- id: khipu-sda-core-exists
  claim: khipu-sda-core exists (the KHIPU line is not greenfield)
  source: estate enumeration 2026-08-31
  expected: true
  measure: {kind: github_repo_present, repo: khipu-sda-core}
```

## `szl-v14/dns-targets.yaml`

<!-- extract: szl-v14/dns-targets.yaml -->
```yaml
# Canonical DNS plan for the SZL estate. The command center is a-11-oy.com;
# the public proof origin is a11oy.net. The forbidden domain appears nowhere.
zones:
  - zone: a11oy.net
    role: public proof origin
    apex_cname_flattening: false
    rollback_source: artifacts/dns/a11oy.net.rollback.json
    target_summary: GitHub Pages (4 apex A + www CNAME)
    notes: proxied=false while GitHub provisions the certificate; if proxying is ever wanted, set Full (strict) BEFORE enabling it
    prechecks:
      - zone exported to rollback source before any write
      - token verified active at /user/tokens/verify
    records:
      - {type: A, name: "@", content: "185.199.108.153", provider: github_pages, proxied: false, ttl: 300}
      - {type: A, name: "@", content: "185.199.109.153", provider: github_pages, proxied: false, ttl: 300}
      - {type: A, name: "@", content: "185.199.110.153", provider: github_pages, proxied: false, ttl: 300}
      - {type: A, name: "@", content: "185.199.111.153", provider: github_pages, proxied: false, ttl: 300}
      - {type: CNAME, name: "www", content: "szl-holdings.github.io.", provider: github_pages, proxied: false, ttl: 300}
  - zone: a-11-oy.com
    role: command center
    apex_cname_flattening: true
    rollback_source: artifacts/dns/a-11-oy.com.rollback.json
    target_summary: Hugging Face Spaces custom domain (hf.space)
    notes: Spaces custom domains require PRO/Team/Enterprise; SZLHOLDINGS org is Team plan (verified) — precheck PASS. Cloudflare flattens apex CNAME natively.
    prechecks:
      - HF plan tier verified PRO/Team/Enterprise before any DNS work
      - no coexisting A/AAAA/CNAME at the label
    records:
      - {type: CNAME, name: "@", content: "hf.space.", provider: hf_spaces, proxied: false, ttl: 300}
  - zone: szl.dev
    role: developer surface
    apex_cname_flattening: false
    rollback_source: artifacts/dns/szl.dev.rollback.json
    target_summary: triage only — registrar/delegation first
    notes: .dev is HSTS-preloaded; order DNS -> cert -> curl-verify -> announce; run whois -> dig +trace NS -> SOA before any record work
    prechecks:
      - whois szl.dev
      - dig +trace NS szl.dev
      - dig SOA szl.dev
    records: []
```

## `szl-v14/pyproject.toml`

<!-- extract: szl-v14/pyproject.toml -->
```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "szl-v14"
version = "14.0.0"
description = "SZL Holdings estate control plane: audit, DNS planning, provenance, evidence export. Read-only; mutating verbs print authorization packets and stop."
requires-python = ">=3.12"
dependencies = [
    "typer>=0.12",
    "rich>=13.7",
    "pydantic>=2.6",
    "httpx>=0.27",
    "jinja2>=3.1",
    "pyyaml>=6.0",
    "jsonschema>=4.21",
    "rfc8785>=0.1.2",
]

[project.optional-dependencies]
dev = ["pytest>=8.0"]

[project.scripts]
szl-v14 = "szl_v14.cli:app"

[tool.setuptools.packages.find]
where = ["src"]

[tool.setuptools.package-data]
szl_v14 = ["py.typed"]
```

## `szl-v14/schemas/dns_plan.schema.json`

<!-- extract: szl-v14/schemas/dns_plan.schema.json -->
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://szl.dev/schemas/dns_plan.schema.json",
  "title": "SZL v14 DNS targets",
  "type": "object",
  "required": ["zones"],
  "properties": {
    "zones": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["zone", "records"],
        "properties": {
          "zone": {"type": "string"},
          "role": {"type": "string"},
          "apex_cname_flattening": {"type": "boolean"},
          "rollback_source": {"type": "string"},
          "prechecks": {"type": "array", "items": {"type": "string"}},
          "target_summary": {"type": "string"},
          "notes": {"type": "string"},
          "records": {
            "type": "array",
            "items": {
              "type": "object",
              "required": ["type", "name", "content"],
              "properties": {
                "type": {"enum": ["A", "AAAA", "CNAME", "MX", "TXT", "NS", "CAA"]},
                "name": {"type": "string"},
                "content": {"type": "string"},
                "provider": {"type": "string"},
                "proxied": {"type": "boolean"},
                "ttl": {"type": "integer", "minimum": 30}
              }
            }
          }
        }
      }
    }
  }
}
```

## `szl-v14/schemas/export_bundle.schema.json`

<!-- extract: szl-v14/schemas/export_bundle.schema.json -->
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://szl.dev/schemas/export_bundle.schema.json",
  "title": "SZL v14 export bundle manifest",
  "type": "object",
  "required": ["bundle", "format", "subjects"],
  "additionalProperties": false,
  "properties": {
    "bundle": {"type": "string", "minLength": 1},
    "format": {"const": "szl/v14-export-bundle"},
    "subjects": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "required": ["name", "digest"],
        "additionalProperties": false,
        "properties": {
          "name": {"type": "string", "minLength": 1},
          "digest": {
            "type": "object",
            "required": ["sha256"],
            "additionalProperties": false,
            "properties": {
              "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"}
            }
          }
        }
      }
    }
  }
}
```

## `szl-v14/schemas/khipu_package.schema.json`

<!-- extract: szl-v14/schemas/khipu_package.schema.json -->
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://szl.dev/schemas/khipu_package.schema.json",
  "title": "KHIPU .khipu package manifest — inherits the four correctness fixes at birth",
  "type": "object",
  "required": ["format", "graph", "weights", "abi", "quantization", "digests", "signatures"],
  "properties": {
    "format": {"const": "khipu-package/1"},
    "graph": {"type": "string"},
    "weights": {"type": "array", "items": {"type": "string"}},
    "abi": {"type": "string"},
    "quantization": {"type": "object"},
    "digests": {
      "type": "object",
      "description": "sha256 over the ACTUAL BYTES of each weight file and the JCS-canonical manifest; never over names",
      "additionalProperties": {"type": "string", "pattern": "^[0-9a-f]{64}$"}
    },
    "signatures": {
      "type": "array",
      "description": "[] while unsigned; the file is then named *.unsigned.json"
    }
  },
  "additionalProperties": true
}
```

## `szl-v14/schemas/kids.schema.json`

<!-- extract: szl-v14/schemas/kids.schema.json -->
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://szl.dev/schemas/kids.schema.json",
  "title": "KIDS — KHIPU Instruction-set/Descriptor Specification v0.1 (frozen before RTL)",
  "type": "object",
  "required": ["kids_version", "precision", "memory_budget_bytes", "supported_blocks"],
  "properties": {
    "kids_version": {"type": "string", "const": "0.1"},
    "precision": {"type": "array", "items": {"enum": ["INT8", "BF16", "INT4"]},
                  "description": "INT8/BF16 first; INT4 only after measured accuracy qualification"},
    "memory_budget_bytes": {"type": "integer", "exclusiveMinimum": 0},
    "supported_blocks": {"type": "array", "items": {"type": "string"}},
    "receipt_hash": {"enum": ["SHA-256", "SHA3-256"],
                     "description": "ONE function across the whole provenance chain, or explicit domain separation with cross-language test vectors"},
    "conformance_vectors_digest": {"type": "string", "pattern": "^[0-9a-f]{64}$"}
  },
  "additionalProperties": true
}
```

## `szl-v14/scripts/deploy_pages_dns.sh`

<!-- extract: szl-v14/scripts/deploy_pages_dns.sh mode=755 -->
```bash
#!/usr/bin/env bash
# Print the GitHub Pages DNS plan. Mutates nothing without ./AUTHORIZE present,
# and even then only prints — actual writes go through the authorization packet.
set -euo pipefail
zone="${1:?usage: deploy_pages_dns.sh <zone> <org>}"
org="${2:?usage: deploy_pages_dns.sh <zone> <org>}"
cat <<PLAN
DNS plan for ${zone} (GitHub Pages, DNS-only during cert issuance):
  A     @     185.199.108.153   proxied=false
  A     @     185.199.109.153   proxied=false
  A     @     185.199.110.153   proxied=false
  A     @     185.199.111.153   proxied=false
  CNAME www   ${org}.github.io. proxied=false
prechecks: zone exported to rollback bundle first; Full (strict) set BEFORE any proxying
PLAN
if [ ! -f ./AUTHORIZE ]; then
  echo "state: AWAITING_AUTHORIZATION (no ./AUTHORIZE file; nothing was written)"
  exit 0
fi
echo "AUTHORIZE present — route this plan through 'szl-v14 dns apply' packet flow anyway."
```

## `szl-v14/scripts/nxdomain_triage.sh`

<!-- extract: szl-v14/scripts/nxdomain_triage.sh mode=755 -->
```bash
#!/usr/bin/env bash
# NXDOMAIN triage order: registrar -> delegation -> SOA. Read-only.
set -euo pipefail
domain="${1:?usage: nxdomain_triage.sh <domain>}"
echo "== 1/3 whois ${domain} (registrar state) =="
whois "${domain}" 2>/dev/null | grep -iE 'registrar|status|expir|name server' | head -20 || echo "whois unavailable"
echo "== 2/3 dig +trace NS ${domain} (delegation) =="
dig +trace NS "${domain}" 2>/dev/null | tail -20 || true
echo "== 3/3 dig SOA ${domain} =="
dig SOA "${domain}" +short || true
echo "note: .dev is HSTS-preloaded — DNS -> cert -> curl-verify -> announce"
```

## `szl-v14/scripts/tunnel_triage.sh`

<!-- extract: szl-v14/scripts/tunnel_triage.sh mode=755 -->
```bash
#!/usr/bin/env bash
# 530/1033 on a tunnel host = no cloudflared connector registered on the ORIGIN.
# This is not a DNS problem. Run ON THE ORIGIN BOX. Read-only.
set -euo pipefail
echo "== systemctl status cloudflared =="
systemctl status cloudflared --no-pager 2>&1 | head -20 || true
echo "== journalctl -u cloudflared --since 24 hours ago =="
journalctl -u cloudflared --since "24 hours ago" --no-pager 2>&1 | tail -30 || true
echo "== cloudflared tunnel list =="
cloudflared tunnel list 2>&1 || true
echo "finding code: TUNNEL_1033 — never remove Cloudflare Access to turn a 403 into a 200"
```

## `szl-v14/scripts/verify_cf_token.sh`

<!-- extract: szl-v14/scripts/verify_cf_token.sh mode=755 -->
```bash
#!/usr/bin/env bash
# Verify a Cloudflare API token before trusting it. Never prints the token.
set -euo pipefail
: "${CF_API_TOKEN:?set CF_API_TOKEN in the environment (value is never printed)}"
status=$(curl -s https://api.cloudflare.com/client/v4/user/tokens/verify \
  -H "Authorization: Bearer ${CF_API_TOKEN}" | jq -r '.result.status // "error"')
if [ "$status" = "active" ]; then
  echo "token status: active"
  exit 0
fi
echo "token status: ${status} — expected \"active\". Regenerate: My Profile -> API Tokens -> 'Edit zone DNS' template, scopes Zone:DNS:Edit + Zone:Zone:Read, target zones only." >&2
exit 1
```

## `szl-v14/src/szl_v14/__init__.py`

<!-- extract: szl-v14/src/szl_v14/__init__.py -->
```python
"""szl-v14 — SZL Holdings estate control plane."""

__version__ = "14.0.0"
```

## `szl-v14/src/szl_v14/__main__.py`

<!-- extract: szl-v14/src/szl_v14/__main__.py -->
```python
from szl_v14.cli import app

if __name__ == "__main__":
    app()
```

## `szl-v14/src/szl_v14/cli.py`

<!-- extract: szl-v14/src/szl_v14/cli.py -->
```python
"""szl-v14 CLI. Every command: --json, receipt, exit 0 ok / 2 FAIL / 3 misuse."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from szl_v14.lib import receipts
from szl_v14.lib.states import Report, State, emit_json, render_findings
from szl_v14.modules import audit as m_audit
from szl_v14.modules import deploy as m_deploy
from szl_v14.modules import dns as m_dns
from szl_v14.modules import doctor as m_doctor
from szl_v14.modules import export as m_export
from szl_v14.modules import inventory as m_inventory
from szl_v14.modules import mcp as m_mcp
from szl_v14.modules import provenance as m_provenance
from szl_v14.modules import remediate as m_remediate
from szl_v14.modules import verify_claims as m_verify_claims

app = typer.Typer(help="SZL Holdings estate control plane (read-only; mutating verbs print authorization packets).", no_args_is_help=True)
dns_app = typer.Typer(help="DNS validate/plan/apply (apply prints an authorization packet and stops).", no_args_is_help=True)
app.add_typer(dns_app, name="dns")

_WORK = Path("artifacts")


def _finish(report: Report, as_json: bool, receipt_root: Path) -> None:
    rcpt = receipts.write(receipt_root, report.cmd, {"json": as_json},
                          outputs=report.outputs, state=report.state.value)
    if as_json:
        print(emit_json(report))
    else:
        from szl_v14.modules.doctor import render_text as doctor_text
        print(doctor_text(report) if report.cmd == "doctor" else f"[{report.state.value}] {report.cmd}")
        render_findings(report.findings)
        for k, v in report.summary.items():
            if k not in ("results", "plans", "deployments", "blockers"):
                print(f"  {k}: {v}")
        print(f"receipt: {rcpt}")
    raise SystemExit(0 if report.state != State.FAIL else 2)


@app.command()
def doctor(snapshot_dir: Path = typer.Option(Path("estate"), help="estate snapshot root"),
           json: bool = typer.Option(False, "--json"),
           receipt_root: Path = typer.Option(_WORK)) -> None:
    """Environment triage; first section is BLOCKERS THAT OUTRANK ALL COSMETIC WORK."""
    _finish(m_doctor.run(snapshot_dir), json, receipt_root)


@app.command()
def inventory(snapshot_dir: Path = typer.Option(Path("estate")),
              out_dir: Path = typer.Option(Path("artifacts/inventory")),
              json: bool = typer.Option(False, "--json"),
              receipt_root: Path = typer.Option(_WORK)) -> None:
    """Build repos.yaml from snapshots; two-source disagreement -> PARTIAL."""
    _finish(m_inventory.run(snapshot_dir, out_dir), json, receipt_root)


@app.command()
def audit(snapshot_dir: Path = typer.Option(Path("estate")),
          out_dir: Path = typer.Option(Path("artifacts")),
          json: bool = typer.Option(False, "--json"),
          receipt_root: Path = typer.Option(_WORK)) -> None:
    """One audit file per repo (Jinja template) + REPOSITORY_MATRIX.csv."""
    _finish(m_audit.run(snapshot_dir, out_dir), json, receipt_root)


@app.command("verify-claims")
def verify_claims(snapshot_dir: Path = typer.Option(Path("estate")),
                  claims: Optional[Path] = typer.Option(None),
                  json: bool = typer.Option(False, "--json"),
                  receipt_root: Path = typer.Option(_WORK)) -> None:
    """Re-measure claims.yaml; mismatch -> CLAIM_DRIFT."""
    _finish(m_verify_claims.run(snapshot_dir, claims), json, receipt_root)


@dns_app.command("validate")
def dns_validate(targets: Optional[Path] = typer.Option(None),
                 json: bool = typer.Option(False, "--json"),
                 receipt_root: Path = typer.Option(_WORK)) -> None:
    """Validate dns-targets.yaml: schema + impossible-state rejection."""
    _finish(m_dns.run_validate(targets), json, receipt_root)


@dns_app.command("plan")
def dns_plan(targets: Optional[Path] = typer.Option(None),
             json: bool = typer.Option(False, "--json"),
             receipt_root: Path = typer.Option(_WORK)) -> None:
    """Print the per-zone record plan with rollback sources. Read-only."""
    _finish(m_dns.run_plan(targets), json, receipt_root)


@dns_app.command("apply")
def dns_apply(targets: Optional[Path] = typer.Option(None),
              json: bool = typer.Option(False, "--json"),
              receipt_root: Path = typer.Option(_WORK)) -> None:
    """Print the AUTHORIZATION PACKET and stop. Never mutates."""
    _finish(m_dns.run_apply(targets), json, receipt_root)


@app.command()
def deploy(targets: Optional[Path] = typer.Option(None),
           probe_file: Optional[Path] = typer.Option(None),
           json: bool = typer.Option(False, "--json"),
           receipt_root: Path = typer.Option(_WORK)) -> None:
    """Inspect-only deployment state table."""
    _finish(m_deploy.run(targets, probe_file), json, receipt_root)


@app.command()
def provenance(target_dir: Path,
               out_dir: Path = typer.Option(Path("artifacts/provenance")),
               json: bool = typer.Option(False, "--json"),
               receipt_root: Path = typer.Option(_WORK)) -> None:
    """in-toto Statement v1 + DSSE *.unsigned.json over a directory."""
    _finish(m_provenance.run(target_dir, out_dir), json, receipt_root)


@app.command()
def mcp(json: bool = typer.Option(False, "--json"),
        receipt_root: Path = typer.Option(_WORK)) -> None:
    """Drift fixtures: canonical-equivalence zero-drift; refusal-then-leak -3.0."""
    _finish(m_mcp.run(), json, receipt_root)


@app.command()
def remediate(findings_json: Path,
              out_dir: Path = typer.Option(Path("artifacts/remediate")),
              json: bool = typer.Option(False, "--json"),
              receipt_root: Path = typer.Option(_WORK)) -> None:
    """Findings JSON -> ordered remediation plan."""
    _finish(m_remediate.run(findings_json, out_dir), json, receipt_root)


@app.command(name="export")
def export_cmd(target_dir: Path,
               out_dir: Path = typer.Option(Path("artifacts/export")),
               bundle_name: str = typer.Option("bundle"),
               json: bool = typer.Option(False, "--json"),
               receipt_root: Path = typer.Option(_WORK)) -> None:
    """Bundle a directory: schema-validated manifest + unsigned envelope + receipt."""
    _finish(m_export.run(target_dir, out_dir, bundle_name), json, receipt_root)
```

## `szl-v14/src/szl_v14/lib/__init__.py`

<!-- extract: szl-v14/src/szl_v14/lib/__init__.py -->
```python
"""Shared library: digests, canonical JSON, envelopes, statements, states."""
```

## `szl-v14/src/szl_v14/lib/digest.py`

<!-- extract: szl-v14/src/szl_v14/lib/digest.py -->
```python
"""Byte digests over actual file contents. Never a name. Never a string."""

from __future__ import annotations

import hashlib
from pathlib import Path

CHUNK = 1 << 20  # 1 MiB


def sha256_file(path: str | Path, chunk: int = CHUNK) -> str:
    """SHA-256 of a file's actual bytes, read in chunks."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    """SHA-256 of an in-memory byte string."""
    return hashlib.sha256(data).hexdigest()


def digest_map(root: str | Path, chunk: int = CHUNK) -> dict[str, str]:
    """{relative_posix_path: sha256} for every file under root, sorted."""
    root = Path(root)
    return {
        p.relative_to(root).as_posix(): sha256_file(p, chunk)
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }
```

## `szl-v14/src/szl_v14/lib/dsse.py`

<!-- extract: szl-v14/src/szl_v14/lib/dsse.py -->
```python
"""DSSE envelopes with honest unsigned naming.

An artifact without a signature is named ``*.unsigned.json`` and carries
``signatures: []``. An empty signature list is never described as signed.
"""

from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any


def envelope(payload: bytes, payload_type: str = "application/vnd.in-toto+json") -> dict[str, Any]:
    """Build a DSSE envelope. Always honestly unsigned at creation time."""
    return {
        "payloadType": payload_type,
        "payload": base64.b64encode(payload).decode("ascii"),
        "signatures": [],
    }


def write_unsigned(env: dict[str, Any], path: str | Path) -> Path:
    """Write an unsigned envelope, enforcing the naming contract."""
    path = Path(path)
    if not path.name.endswith(".unsigned.json"):
        raise ValueError(f"unsigned envelopes must be named *.unsigned.json (got {path.name})")
    if env.get("signatures") != []:
        raise ValueError("envelope claims signatures but file is named unsigned")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(env, indent=2) + "\n")
    return path


def verify_unsigned(path: str | Path) -> dict[str, Any]:
    """Load an envelope and assert name/signature honesty. Raises on violation."""
    path = Path(path)
    env = json.loads(path.read_text())
    sigs = env.get("signatures", None)
    if path.name.endswith(".unsigned.json"):
        if sigs not in ([], None):
            raise ValueError("envelope claims signatures but file is named unsigned")
    else:
        if sigs == []:
            raise ValueError("envelope has no signatures but is not named *.unsigned.json")
    return env
```

## `szl-v14/src/szl_v14/lib/estate.py`

<!-- extract: szl-v14/src/szl_v14/lib/estate.py -->
```python
"""Load estate snapshots. A missing file is UNKNOWN, never a guess, never a crash."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class EstateSnapshot:
    root: Path
    github_repos: list[dict[str, Any]] = field(default_factory=list)   # repos_cli.json
    github_enumeration: dict[str, Any] = field(default_factory=dict)   # enumeration.json
    hf_estate: dict[str, Any] = field(default_factory=dict)            # hf_estate.json
    cloudflare_status: dict[str, Any] = field(default_factory=dict)    # status.json
    unknown: list[str] = field(default_factory=list)                   # snapshot names that were missing

    @property
    def estate_completeness(self) -> str:
        return self.github_enumeration.get("estate_completeness", "UNKNOWN")


def _load(root: Path, rel: str, unknown: list[str]) -> Any:
    p = root / rel
    if not p.exists():
        unknown.append(rel)
        return None
    try:
        return json.loads(p.read_text())
    except Exception:
        unknown.append(rel)
        return None


def load_snapshots(root: str | Path) -> EstateSnapshot:
    root = Path(root)
    unknown: list[str] = []
    return EstateSnapshot(
        root=root,
        github_repos=_load(root, "github/repos_cli.json", unknown) or [],
        github_enumeration=_load(root, "github/enumeration.json", unknown) or {},
        hf_estate=_load(root, "hf/hf_estate.json", unknown) or {},
        cloudflare_status=_load(root, "cloudflare/status.json", unknown) or {},
        unknown=unknown,
    )
```

## `szl-v14/src/szl_v14/lib/http.py`

<!-- extract: szl-v14/src/szl_v14/lib/http.py -->
```python
"""HTTP helpers. Secrets are never logged, never echoed, never in errors."""

from __future__ import annotations

import re
from typing import Any

import httpx

_BEARER = re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._\-]+")
_KEYVAL = re.compile(r"(?i)(token|secret|api[_-]?key|password|pat)([\"'\s:=]+)[^\s\"',}]+")


def _redact(text: str) -> str:
    text = _BEARER.sub(r"\1<redacted>", text)
    text = _KEYVAL.sub(lambda m: f"{m.group(1)}{m.group(2)}<redacted>", text)
    return text


def get_json(url: str, headers: dict[str, str] | None = None, timeout: float = 30.0) -> Any:
    """GET a URL and parse JSON. Errors are redacted before they surface."""
    try:
        resp = httpx.get(url, headers=headers or {}, timeout=timeout, follow_redirects=True)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:  # httpx errors may embed Authorization headers
        raise RuntimeError(_redact(f"{type(exc).__name__}: {exc}")) from None


def post_json(url: str, body: Any, headers: dict[str, str] | None = None, timeout: float = 30.0) -> Any:
    """POST JSON and parse the response. Errors are redacted."""
    try:
        resp = httpx.post(url, json=body, headers=headers or {}, timeout=timeout, follow_redirects=True)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        raise RuntimeError(_redact(f"{type(exc).__name__}: {exc}")) from None
```

## `szl-v14/src/szl_v14/lib/intoto.py`

<!-- extract: szl-v14/src/szl_v14/lib/intoto.py -->
```python
"""in-toto Statement v1 construction with real byte digests."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from szl_v14.lib.digest import sha256_file

_STATEMENT_TYPE = "https://in-toto.io/Statement/v1"


def statement(
    subjects: Iterable[tuple[str, str | Path]],
    predicate_type: str,
    predicate: dict[str, Any],
) -> dict[str, Any]:
    """Build an in-toto Statement v1.

    subjects: iterable of (name, path); the digest is over the file's bytes.
    """
    return {
        "_type": _STATEMENT_TYPE,
        "subject": [
            {"name": name, "digest": {"sha256": sha256_file(path)}}
            for name, path in subjects
        ],
        "predicateType": predicate_type,
        "predicate": predicate,
    }
```

## `szl-v14/src/szl_v14/lib/jcs.py`

<!-- extract: szl-v14/src/szl_v14/lib/jcs.py -->
```python
"""Canonical JSON per RFC 8785, via the real library. sort_keys is not JCS."""

from __future__ import annotations

import sys
from typing import Any

_INSTALL = "rfc8785 is not installed. Run: pip install rfc8785  (json.dumps with sorted keys is NOT JCS)"


def _lib():
    try:
        import rfc8785  # type: ignore
    except ImportError:
        sys.stderr.write(f"FATAL: {_INSTALL}\n")
        raise SystemExit(2)
    return rfc8785


def canonical(obj: Any) -> str:
    """Serialize obj to its RFC 8785 canonical form."""
    out = _lib().dumps(obj)
    return out.decode("utf-8") if isinstance(out, (bytes, bytearray)) else out


def jcs_digest(obj: Any) -> str:
    """SHA-256 of the canonical form."""
    from szl_v14.lib.digest import sha256_bytes

    return sha256_bytes(canonical(obj).encode("utf-8"))
```

## `szl-v14/src/szl_v14/lib/receipts.py`

<!-- extract: szl-v14/src/szl_v14/lib/receipts.py -->
```python
"""Command receipts — the ONLY place timestamps are allowed."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from szl_v14.lib.digest import sha256_file
from szl_v14.lib.jcs import canonical, jcs_digest


@dataclass
class Receipt:
    cmd: str
    args_digest: str
    inputs: dict[str, str] = field(default_factory=dict)   # path -> sha256
    outputs: dict[str, str] = field(default_factory=dict)  # path -> sha256
    state: str = "UNKNOWN"
    timestamp_utc: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def write(
    root: str | Path,
    cmd: str,
    args: dict[str, Any],
    inputs: dict[str, str] | None = None,
    outputs: dict[str, str] | None = None,
    state: str = "UNKNOWN",
    extra_inputs: list[str | Path] | None = None,
) -> Path:
    """Write receipts/<cmd>-<ts>.json under root and return its path."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    ins = dict(inputs or {})
    for p in extra_inputs or []:
        p = Path(p)
        if p.exists():
            ins[str(p)] = sha256_file(p)
    rcpt = Receipt(
        cmd=cmd,
        args_digest=jcs_digest(args),
        inputs=ins,
        outputs=outputs or {},
        state=state,
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
    )
    outdir = Path(root) / "receipts"
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / f"{cmd.replace(' ', '_')}-{ts}.json"
    path.write_text(canonical(rcpt.to_dict()) + "\n")
    return path
```

## `szl-v14/src/szl_v14/lib/states.py`

<!-- extract: szl-v14/src/szl_v14/lib/states.py -->
```python
"""Evidence states and findings.

PASS | WARN | FAIL | BLOCKED | UNKNOWN. UNKNOWN is never coerced to PASS.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Iterable


class State(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"
    UNKNOWN = "UNKNOWN"


def promote(state: State, target: State) -> State:
    """Promote an evidence state. UNKNOWN can never become PASS."""
    state, target = State(state), State(target)
    if state == State.UNKNOWN and target == State.PASS:
        raise ValueError("UNKNOWN is never coerced to PASS")
    return target


@dataclass
class Finding:
    severity: str  # CRITICAL | HIGH | MEDIUM | LOW | INFO
    code: str
    message: str
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass
class Report:
    cmd: str
    state: State
    findings: list[Finding] = field(default_factory=list)
    outputs: dict[str, str] = field(default_factory=dict)  # path -> sha256
    summary: dict[str, Any] = field(default_factory=dict)


def render_findings(findings: Iterable[Finding]) -> None:
    from rich.console import Console
    from rich.table import Table

    findings = list(findings)
    console = Console()
    if not findings:
        console.print("[green]no findings[/green]")
        return
    table = Table(title="Findings")
    for col in ("severity", "code", "message"):
        table.add_column(col)
    color = {"CRITICAL": "red", "HIGH": "red", "MEDIUM": "yellow",
             "LOW": "cyan", "INFO": "white"}
    for f in findings:
        table.add_row(f"[{color.get(f.severity, 'white')}]{f.severity}[/]",
                      f.code, f.message)
    console.print(table)


def worst_state(findings: Iterable[Finding]) -> State:
    ranking = {"CRITICAL": State.FAIL, "HIGH": State.FAIL,
               "MEDIUM": State.WARN, "LOW": State.WARN, "INFO": State.PASS}
    out = State.PASS
    for f in findings:
        s = ranking.get(f.severity, State.WARN)
        if s == State.FAIL:
            return State.FAIL
        if s == State.WARN:
            out = State.WARN
    return out


def to_jsonable(obj: Any) -> Any:
    if isinstance(obj, (State,)):
        return obj.value
    if isinstance(obj, (Finding, Report)):
        return to_jsonable(asdict(obj))
    if isinstance(obj, dict):
        return {k: to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_jsonable(v) for v in obj]
    return obj


def emit_json(report: Report) -> str:
    return json.dumps(to_jsonable(report), indent=2)
```

## `szl-v14/src/szl_v14/modules/__init__.py`

<!-- extract: szl-v14/src/szl_v14/modules/__init__.py -->
```python
"""Command modules. Every command: --json, receipt, exit codes 0/2/3."""
```

## `szl-v14/src/szl_v14/modules/audit.py`

<!-- extract: szl-v14/src/szl_v14/modules/audit.py -->
```python
"""audit — one audit file per repo from a Jinja template + REPOSITORY_MATRIX.csv.

Fields not probed are UNKNOWN. Never guessed, never carried forward.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from szl_v14.lib.digest import sha256_file
from szl_v14.lib.estate import load_snapshots
from szl_v14.lib.states import Finding, Report, State

FORBIDDEN_DOMAIN = re.compile(r"(?<!-)a11oy\.com")

_TEMPLATE_DIR = Path(__file__).resolve().parents[3] / "templates"

MATRIX_FIELDS = ["name", "visibility", "archived", "default_branch", "language",
                 "license", "pushed_at", "open_prs", "has_pages", "forbidden_refs", "state"]


def _repo_view(r: dict, enrichment: dict | None) -> dict:
    e = enrichment or {}
    text = " ".join(str(r.get(k) or "") for k in ("description", "url")) + " " + str(e.get("homepage") or "")
    return {
        "name": r.get("name", "UNKNOWN"),
        "visibility": r.get("visibility", "UNKNOWN"),
        "archived": r.get("isArchived", "UNKNOWN"),
        "default_branch": (r.get("defaultBranchRef") or {}).get("name", "UNKNOWN"),
        "language": (r.get("primaryLanguage") or {}).get("name", "UNKNOWN"),
        "license": (r.get("licenseInfo") or {}).get("spdxId", "UNKNOWN"),
        "pushed_at": (r.get("pushedAt") or "UNKNOWN")[:10],
        "description": r.get("description") or "UNKNOWN",
        "url": r.get("url", "UNKNOWN"),
        "open_prs": e.get("open_prs", "UNKNOWN"),
        "has_pages": e.get("has_pages", "UNKNOWN"),
        "homepage": e.get("homepage", "UNKNOWN"),
        "topics": [t.get("name") for t in (r.get("repositoryTopics") or [])] or "UNKNOWN",
        "forbidden_refs": len(FORBIDDEN_DOMAIN.findall(text)),
        "state": "FAIL" if FORBIDDEN_DOMAIN.findall(text) else "PASS",
    }


def run(snapshot_dir: Path, out_dir: Path) -> Report:
    snap = load_snapshots(snapshot_dir)
    findings: list[Finding] = []
    audits = out_dir / "audits" / "repos"
    audits.mkdir(parents=True, exist_ok=True)

    enrichment: dict[str, dict] = {}
    edir = snapshot_dir / "github" / "enrichment"
    if edir.is_dir():
        import json as _json
        for f in edir.glob("*.json"):
            try:
                d = _json.loads(f.read_text())
                if d.get("name"):
                    enrichment[d["name"]] = d
            except Exception:
                pass
    else:
        findings.append(Finding("INFO", "NO_ENRICHMENT", "no per-repo enrichment; deep fields are UNKNOWN"))

    env = Environment(loader=FileSystemLoader(str(_TEMPLATE_DIR)),
                      autoescape=select_autoescape(disabled_extensions=("md", "j2")))
    tpl = env.get_template("REPO_AUDIT.j2")

    rows: list[dict] = []
    outputs: dict[str, str] = {}
    for r in sorted(snap.github_repos, key=lambda x: x.get("name", "")):
        view = _repo_view(r, enrichment.get(r.get("name")))
        if view["forbidden_refs"]:
            findings.append(Finding("CRITICAL", "FORBIDDEN_LINK",
                                    f"{view['name']}: forbidden domain reference in metadata"))
        path = audits / f"{view['name']}.md"
        path.write_text(tpl.render(repo=view))
        outputs[str(path)] = sha256_file(path)
        rows.append(view)

    matrix = out_dir / "REPOSITORY_MATRIX.csv"
    with open(matrix, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=MATRIX_FIELDS)
        w.writeheader()
        for v in rows:
            w.writerow({k: v.get(k, "UNKNOWN") for k in MATRIX_FIELDS})
    outputs[str(matrix)] = sha256_file(matrix)

    state = State.FAIL if any(f.severity == "CRITICAL" for f in findings) else (
        State.WARN if findings else State.PASS)
    return Report(cmd="audit", state=state, findings=findings, outputs=outputs,
                  summary={"repos_audited": len(rows),
                           "forbidden_refs": sum(v["forbidden_refs"] for v in rows)})
```

## `szl-v14/src/szl_v14/modules/deploy.py`

<!-- extract: szl-v14/src/szl_v14/modules/deploy.py -->
```python
"""deploy — inspect-only deployment state. No mutation anywhere."""

from __future__ import annotations

from pathlib import Path

from szl_v14.modules.dns import _load_targets
from szl_v14.lib.states import Finding, Report, State


def run(targets: Path | None, probe_file: Path | None) -> Report:
    findings: list[Finding] = []
    doc = _load_targets(targets) if (targets or True) else {}
    rows = []
    try:
        doc = _load_targets(targets)
    except FileNotFoundError as e:
        return Report(cmd="deploy", state=State.UNKNOWN,
                      findings=[Finding("MEDIUM", "MISSING_CONFIG", str(e))])

    for z in doc.get("zones", []):
        rows.append({"zone": z["zone"], "role": z.get("role", "UNKNOWN"),
                     "target": z.get("target_summary", "UNKNOWN"),
                     "notes": z.get("notes", "")})
    findings.append(Finding(
        "INFO", "HSTS_PRELOAD",
        ".dev is HSTS-preloaded: order is DNS -> cert -> curl-verify -> announce; "
        "linking szl.dev before a valid cert exists is a hard browser failure"))
    findings.append(Finding(
        "INFO", "ACCESS_403_OK",
        "never remove Cloudflare Access to turn a 403 into a 200; 403 means Access is working"))
    return Report(cmd="deploy", state=State.PASS, findings=findings,
                  summary={"deployments": rows})
```

## `szl-v14/src/szl_v14/modules/dns.py`

<!-- extract: szl-v14/src/szl_v14/modules/dns.py -->
```python
"""dns — validate targets, print plans, and (never mutate) print authorization packets."""

from __future__ import annotations

import json
from pathlib import Path

import yaml
from jsonschema import validate as js_validate

from szl_v14.lib.states import Finding, Report, State

_TARGETS = Path(__file__).resolve().parents[3] / "dns-targets.yaml"
_SCHEMA = Path(__file__).resolve().parents[3] / "schemas" / "dns_plan.schema.json"


def _load_targets(path: Path | None) -> dict:
    p = path or _TARGETS
    if not p.exists():
        raise FileNotFoundError(f"dns targets file missing: {p}")
    return yaml.safe_load(p.read_text())


def impossible_states(doc: dict) -> list[Finding]:
    """Reject impossible DNS states at compile/validate time, not at 2am."""
    findings: list[Finding] = []
    for z in doc.get("zones", []):
        apex_cnames = [r for r in z.get("records", [])
                       if r.get("type") == "CNAME" and r.get("name") in ("@", z.get("zone"))]
        if apex_cnames and not z.get("apex_cname_flattening", False):
            findings.append(Finding("CRITICAL", "IMPOSSIBLE_DNS",
                                    f"{z['zone']}: apex CNAME without confirmed flattening"))
        others = [r for r in z.get("records", [])
                  if r.get("name") == "@" and r.get("type") != "CNAME"]
        if apex_cnames and others:
            findings.append(Finding("CRITICAL", "IMPOSSIBLE_DNS",
                                    f"{z['zone']}: coexisting records at the CNAME label"))
        targets = {r.get("provider") for r in z.get("records", []) if r.get("provider")}
        if len(targets) > 1:
            findings.append(Finding("HIGH", "MIXED_CANONICAL",
                                    f"{z['zone']}: mixed provider targets {sorted(targets)}"))
        if not z.get("rollback_source"):
            findings.append(Finding("HIGH", "NO_ROLLBACK",
                                    f"{z['zone']}: no rollback source declared"))
        for r in z.get("records", []):
            if r.get("proxied") and str(r.get("content", "")).startswith("185.199."):
                findings.append(Finding("CRITICAL", "PAGES_ORANGE_CLOUD",
                                        f"{z['zone']}: proxied:true on a GitHub Pages IP breaks cert issuance"))
    return findings


def run_validate(targets: Path | None) -> Report:
    try:
        doc = _load_targets(targets)
    except FileNotFoundError as e:
        return Report(cmd="dns validate", state=State.FAIL,
                      findings=[Finding("HIGH", "MISSING_CONFIG", str(e))])
    if _SCHEMA.exists():
        schema = json.loads(_SCHEMA.read_text())
        try:
            js_validate(doc, schema)
        except Exception as e:
            return Report(cmd="dns validate", state=State.FAIL,
                          findings=[Finding("HIGH", "SCHEMA_MISMATCH", str(e)[:300])])
    findings = impossible_states(doc)
    state = State.FAIL if findings else State.PASS
    return Report(cmd="dns validate", state=state, findings=findings,
                  summary={"zones": [z["zone"] for z in doc.get("zones", [])]})


def run_plan(targets: Path | None) -> Report:
    v = run_validate(targets)
    if v.state == State.FAIL:
        v.cmd = "dns plan"
        return v
    doc = _load_targets(targets)
    plans = []
    for z in doc.get("zones", []):
        plans.append({
            "zone": z["zone"], "role": z.get("role", "UNKNOWN"),
            "prechecks": z.get("prechecks", []),
            "records": z.get("records", []),
            "rollback_source": z.get("rollback_source"),
            "rule": "snapshot the zone to the rollback_source BEFORE any write; one record set at a time; poll propagation between sets",
        })
    return Report(cmd="dns plan", state=State.PASS, findings=v.findings,
                  summary={"plans": plans})


def run_apply(targets: Path | None) -> Report:
    """Print the AUTHORIZATION PACKET and stop. Never mutates. R10."""
    plan = run_plan(targets)
    packet = {
        "state": "AWAITING_AUTHORIZATION",
        "warning": "this CLI never mutates; hand this packet to an operator",
        "prechecks_required": [
            "token verified active at /user/tokens/verify with Zone:DNS:Edit + Zone:Zone:Read scoped to target zones",
            "zone exported to rollback bundle on disk BEFORE any write",
            "one record set at a time with propagation polling between sets",
        ],
        "plans": plan.summary.get("plans", []),
    }
    return Report(cmd="dns apply", state=State.BLOCKED, findings=plan.findings,
                  summary=packet)
```

## `szl-v14/src/szl_v14/modules/doctor.py`

<!-- extract: szl-v14/src/szl_v14/modules/doctor.py -->
```python
"""doctor — environment triage. First section: BLOCKERS THAT OUTRANK ALL COSMETIC WORK."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from szl_v14.lib.estate import load_snapshots
from szl_v14.lib.states import Finding, Report, State

BLOCKER_HEADER = "BLOCKERS THAT OUTRANK ALL COSMETIC WORK"

_BINARIES = ["gh", "dig", "jq", "curl", "openssl"]


def run(snapshot_dir: Path) -> Report:
    findings: list[Finding] = []
    blockers: list[str] = []

    if sys.version_info < (3, 12):
        findings.append(Finding("CRITICAL", "PY_VERSION", f"python {sys.version.split()[0]} < 3.12"))

    try:
        import rfc8785  # noqa: F401
    except ImportError:
        findings.append(Finding("CRITICAL", "NO_RFC8785", "real JCS library missing; every digest claim is theater"))

    try:
        import importlib.metadata as md
        v = md.version("huggingface_hub")
        if int(v.split(".")[0]) < 1:
            findings.append(Finding("CRITICAL", "HF_HUB_VERSION", f"huggingface_hub {v} < 1.0 (bucket visibility)"))
    except Exception:
        findings.append(Finding("CRITICAL", "NO_HF_HUB", "huggingface_hub >= 1.0 missing — the only bucket-visible call"))

    for b in _BINARIES:
        if not shutil.which(b):
            findings.append(Finding("HIGH", "MISSING_BINARY", f"{b} not on PATH"))
    if not shutil.which("cosign"):
        findings.append(Finding("LOW", "NO_COSIGN", "cosign absent — signing path stays unsigned-honest until armed"))

    snap = load_snapshots(snapshot_dir)
    if not snap.github_repos:
        findings.append(Finding("CRITICAL", "NO_GH_SNAPSHOT", "github/repos_cli.json missing or empty"))
        blockers.append("GitHub estate snapshot missing")
    if not snap.hf_estate:
        findings.append(Finding("CRITICAL", "NO_HF_SNAPSHOT", "hf/hf_estate.json missing"))
        blockers.append("Hugging Face estate snapshot missing")
    cf = snap.cloudflare_status
    if cf.get("status") == "BLOCKED":
        msg = cf.get("diagnosis", "Cloudflare credential blocked")
        findings.append(Finding("HIGH", "CF_TOKEN_BLOCKED", msg,
                                {"error": cf.get("error"), "needed_scopes": cf.get("needed_scopes")}))
        blockers.append(f"Cloudflare: {msg}")
    if snap.estate_completeness not in ("VERIFIED", "VERIFIED (3 independent sources agree at 100)"):
        findings.append(Finding("MEDIUM", "ESTATE_NOT_VERIFIED",
                                f"estate completeness = {snap.estate_completeness}"))
    for missing in snap.unknown:
        findings.append(Finding("MEDIUM", "SNAPSHOT_MISSING", f"snapshot file missing: {missing}"))

    state = State.FAIL if any(f.severity == "CRITICAL" for f in findings) else (
        State.WARN if findings else State.PASS)
    return Report(cmd="doctor", state=state, findings=findings,
                  summary={"blockers_header": BLOCKER_HEADER, "blockers": blockers,
                           "estate_completeness": snap.estate_completeness})


def render_text(report: Report) -> str:
    lines = [BLOCKER_HEADER, "=" * len(BLOCKER_HEADER), ""]
    if report.summary["blockers"]:
        for b in report.summary["blockers"]:
            lines.append(f"  - {b}")
    else:
        lines.append("  (none)")
    lines.append("")
    lines.append(f"estate completeness: {report.summary['estate_completeness']}")
    lines.append(f"state: {report.state.value}")
    return "\n".join(lines)
```

## `szl-v14/src/szl_v14/modules/export.py`

<!-- extract: szl-v14/src/szl_v14/modules/export.py -->
```python
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
```

## `szl-v14/src/szl_v14/modules/inventory.py`

<!-- extract: szl-v14/src/szl_v14/modules/inventory.py -->
```python
"""inventory — build repos.yaml from snapshots. Sources disagree -> PARTIAL."""

from __future__ import annotations

from pathlib import Path

import yaml

from szl_v14.lib.digest import sha256_file
from szl_v14.lib.estate import load_snapshots
from szl_v14.lib.states import Finding, Report, State


def run(snapshot_dir: Path, out_dir: Path) -> Report:
    snap = load_snapshots(snapshot_dir)
    findings: list[Finding] = []

    enum = snap.github_enumeration
    srcs = enum.get("sources", {})
    counts = [v for v in srcs.values() if isinstance(v, int)]
    if len(set(counts)) > 1:
        findings.append(Finding("HIGH", "SOURCE_DISAGREE",
                                f"enumeration sources disagree: {srcs}"))
        completeness = "PARTIAL"
    elif not counts:
        completeness = "UNKNOWN"
        findings.append(Finding("MEDIUM", "NO_ENUM", "no enumeration evidence"))
    else:
        completeness = enum.get("estate_completeness", "PARTIAL")
        if completeness != "VERIFIED" and not completeness.startswith("VERIFIED"):
            findings.append(Finding("MEDIUM", "ESTATE_PARTIAL", completeness))

    repos = []
    for r in snap.github_repos:
        repos.append({
            "name": r.get("name"),
            "visibility": r.get("visibility"),
            "archived": r.get("isArchived"),
            "default_branch": (r.get("defaultBranchRef") or {}).get("name"),
            "language": (r.get("primaryLanguage") or {}).get("name"),
            "pushed_at": r.get("pushedAt"),
            "license": (r.get("licenseInfo") or {}).get("spdxId"),
            "description": r.get("description"),
            "url": r.get("url"),
        })

    hf = snap.hf_estate
    doc = {
        "schema": "szl/v14-inventory",
        "estate_completeness": completeness,
        "github": {"org": "szl-holdings", "count": len(repos),
                   "sources": srcs, "repos": repos},
        "huggingface": {"org": "SZLHOLDINGS",
                        "counts": hf.get("counts", {}),
                        "names": hf.get("names", {})},
        "cloudflare": {"status": snap.cloudflare_status.get("status", "UNKNOWN"),
                       "error": snap.cloudflare_status.get("error")},
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "repos.yaml"
    path.write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True))
    state = State.WARN if findings else State.PASS
    return Report(cmd="inventory", state=state, findings=findings,
                  outputs={str(path): sha256_file(path)},
                  summary={"github_repos": len(repos), "hf": hf.get("counts", {}),
                           "estate_completeness": completeness})
```

## `szl-v14/src/szl_v14/modules/mcp.py`

<!-- extract: szl-v14/src/szl_v14/modules/mcp.py -->
```python
"""mcp — attestation fixtures. Deny-on-drift: exit 2 on any drift.

The two fixtures that matter most:
1. A whitespace-only canonical-equivalent JSON pair MUST produce zero drift.
   If it drifts, the JCS implementation is fake.
2. A refusal phrase followed by leaked data nets -3.0, not +1.5 - 3.0.
"""

from __future__ import annotations

import json

from szl_v14.lib.jcs import canonical, jcs_digest
from szl_v14.lib.states import Finding, Report, State


def _refusal_leak_score(text: str, refusal_reward: float = 1.5, leak_penalty: float = -3.0) -> float:
    """Refusal-then-leak nets -3.0 exactly; no cancelling arithmetic."""
    refused = text.strip().lower().startswith(("i cannot", "i can't", "i'm unable", "sorry, i can"))
    leaked = "SECRET" in text or "canary" in text.lower()
    if leaked:
        return leak_penalty  # leak dominates; refusal earns nothing
    if refused:
        return refusal_reward
    return 0.0


def run() -> Report:
    findings: list[Finding] = []

    # Fixture 1: canonical equivalence -> zero drift.
    a = {"b": [1, 2], "a": "x"}
    b_text = '{ "a" : "x", "b" : [ 1, 2 ] }'
    b = json.loads(b_text)
    if canonical(a) != canonical(b) or jcs_digest(a) != jcs_digest(b):
        findings.append(Finding("CRITICAL", "JCS_DRIFT",
                                "whitespace-only canonical-equivalent pair produced drift — JCS is not real"))
    else:
        findings.append(Finding("INFO", "JCS_OK", "canonical-equivalent pair: zero drift (real RFC 8785)"))

    # Fixture 2: refusal-then-leak nets -3.0.
    score = _refusal_leak_score("I cannot share that. SECRET=42 canary")
    if score != -3.0:
        findings.append(Finding("CRITICAL", "REWARD_HACK",
                                f"refusal-then-leak scored {score} != -3.0 — reward-hacking hole open"))
    else:
        findings.append(Finding("INFO", "REFUSAL_OK", "refusal-then-leak nets -3.0; no +1.5 offset"))

    state = State.FAIL if any(f.severity == "CRITICAL" for f in findings) else State.PASS
    return Report(cmd="mcp", state=state, findings=findings,
                  summary={"fixtures": 2, "policy": "deny-on-drift, exit 2"})
```

## `szl-v14/src/szl_v14/modules/provenance.py`

<!-- extract: szl-v14/src/szl_v14/modules/provenance.py -->
```python
"""provenance — in-toto statement + honestly unsigned DSSE envelope for a directory."""

from __future__ import annotations

from pathlib import Path

from szl_v14.lib.digest import sha256_file
from szl_v14.lib.dsse import envelope, write_unsigned
from szl_v14.lib.intoto import statement
from szl_v14.lib.jcs import canonical
from szl_v14.lib.states import Finding, Report, State


def run(target_dir: Path, out_dir: Path, predicate_type: str = "https://szl.dev/predicates/provenance/v1") -> Report:
    if not target_dir.is_dir():
        return Report(cmd="provenance", state=State.FAIL,
                      findings=[Finding("HIGH", "MISSING_INPUT", f"no such directory: {target_dir}")])
    subjects = [(p.relative_to(target_dir).as_posix(), p)
                for p in sorted(target_dir.rglob("*")) if p.is_file()]
    stmt = statement(subjects, predicate_type, {"builder": {"id": "szl-v14 provenance"}})

    out_dir.mkdir(parents=True, exist_ok=True)
    stmt_path = out_dir / "statement.intoto.json"
    stmt_path.write_text(canonical(stmt) + "\n")
    env = envelope(canonical(stmt).encode("utf-8"))
    env_path = write_unsigned(env, out_dir / "payload.unsigned.json")

    return Report(cmd="provenance", state=State.PASS,
                  outputs={str(stmt_path): sha256_file(stmt_path),
                           str(env_path): sha256_file(env_path)},
                  summary={"subjects": len(subjects),
                           "signing": "unsigned (signatures: []); honest naming enforced"})
```

## `szl-v14/src/szl_v14/modules/remediate.py`

<!-- extract: szl-v14/src/szl_v14/modules/remediate.py -->
```python
"""remediate — findings JSON -> ORDERED plan. Credentials -> DNS -> origin-host -> code -> cosmetic."""

from __future__ import annotations

import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from szl_v14.lib.digest import sha256_file
from szl_v14.lib.states import Finding, Report, State

_TEMPLATE_DIR = Path(__file__).resolve().parents[3] / "templates"

_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}
_LANE = {"CF_TOKEN_BLOCKED": 0, "NO_HF_HUB": 0, "MISSING_BINARY": 0,
         "PAGES_ORANGE_CLOUD": 1, "IMPOSSIBLE_DNS": 1,
         "TUNNEL_1033": 2, "ESTATE_PARTIAL": 2,
         "FORBIDDEN_LINK": 3, "CLAIM_DRIFT": 3}


def run(findings_json: Path, out_dir: Path) -> Report:
    if not findings_json.exists():
        return Report(cmd="remediate", state=State.UNKNOWN,
                      findings=[Finding("MEDIUM", "NO_FINDINGS", f"missing: {findings_json}")])
    raw = json.loads(findings_json.read_text())
    items = raw if isinstance(raw, list) else raw.get("findings", [])
    items.sort(key=lambda f: (_ORDER.get(f.get("severity", "INFO"), 4),
                              _LANE.get(f.get("code", ""), 4)))

    plan = []
    for i, f in enumerate(items, 1):
        plan.append({"order": i, "severity": f.get("severity"), "code": f.get("code"),
                     "action": f.get("message"),
                     "verify": f.get("verify", "re-run the producing command; state must improve or stay honestly UNKNOWN")})

    out_dir.mkdir(parents=True, exist_ok=True)
    env = Environment(loader=FileSystemLoader(str(_TEMPLATE_DIR)),
                      autoescape=select_autoescape(disabled_extensions=("md", "j2")))
    path = out_dir / "REMEDIATION_PLAN.md"
    path.write_text(env.get_template("REPORT.j2").render(title="Remediation plan", plan=plan, items=plan))
    return Report(cmd="remediate", state=State.PASS,
                  outputs={str(path): sha256_file(path)},
                  summary={"items": len(plan)})
```

## `szl-v14/src/szl_v14/modules/verify_claims.py`

<!-- extract: szl-v14/src/szl_v14/modules/verify_claims.py -->
```python
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
        vis = claim["measure"]["visibility"]
        return sum(1 for r in snap.github_repos if r.get("visibility") == vis) if snap.github_repos else None
    if kind == "hf_repo_count":
        rtype = claim["measure"]["repo_type"]
        return snap.hf_estate.get("counts", {}).get(rtype)
    if kind == "github_repo_present":
        return claim["measure"]["repo"] in {r.get("name") for r in snap.github_repos}
    return None


def run(snapshot_dir: Path, claims_path: Path | None = None) -> Report:
    claims_path = claims_path or _CLAIMS_FILE
    findings: list[Finding] = []
    results = []
    if not claims_path.exists():
        return Report(cmd="verify-claims", state=State.UNKNOWN,
                      findings=[Finding("MEDIUM", "NO_CLAIMS", f"claims file missing: {claims_path}")])

    claims = yaml.safe_load(claims_path.read_text()) or []
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
```

## `szl-v14/templates/DNS_PLAN.j2`

<!-- extract: szl-v14/templates/DNS_PLAN.j2 -->
```jinja
# DNS plan: {{ zone }}

role: {{ role }}

## Prechecks
{% for p in prechecks -%}
- {{ p }}
{% endfor %}

## Records
| type | name | content | proxied | ttl |
|---|---|---|---|---|
{% for r in records -%}
| {{ r.type }} | {{ r.name }} | {{ r.content }} | {{ r.proxied | default(false) }} | {{ r.ttl | default(300) }} |
{% endfor %}

## Rollback
source: {{ rollback_source }}
Rule: export the zone to the rollback source BEFORE any write; one record set at
a time; poll propagation between sets.
```

## `szl-v14/templates/OPERATOR_PACKET.j2`

<!-- extract: szl-v14/templates/OPERATOR_PACKET.j2 -->
````jinja
# OPERATOR PACKET

Everything else in the export tree is supporting evidence for this page.
Every one of the fifteen answers below is mandatory; an omission is a FAIL.

1. Verified (digests): {{ verified | default('UNKNOWN') }}
2. Fixed (post-fix verification): {{ fixed | default('UNKNOWN') }}
3. Remaining failures (finding codes): {{ failing | default('UNKNOWN') }}
4. Blocked on credentials (exact scope): {{ blocked_credentials | default('UNKNOWN') }}
5. Exact DNS record diff proposed: {{ dns_diff | default('UNKNOWN') }}
6. Exact rollback records: {{ rollback | default('UNKNOWN') }}
7. Exact next safe command: {{ next_command | default('UNKNOWN') }}
8. Per-domain DNS state: {{ dns_state | default('UNKNOWN') }}
9. Per-domain TLS state: {{ tls_state | default('UNKNOWN') }}
10. Per-domain app state: {{ app_state | default('UNKNOWN') }}
11. Forbidden-domain references remaining (must be 0): {{ forbidden_refs | default('UNKNOWN') }}
12. V11 artifacts (verified / regressed / unknown, with SHAs): {{ v11 | default('UNKNOWN') }}
13. Estate completeness: {{ estate_completeness | default('UNKNOWN') }}
14. Claims: pass {{ claims_pass | default('?') }}, CLAIM_DRIFT {{ claims_drift | default('?') }}, UNMEASURABLE {{ claims_unmeasurable | default('?') }}
15. publication_eligible: {{ publication_eligible | default('False') }} — false inputs: {{ eligibility_blockers | default('UNKNOWN') }}

## Per-phase block

```
STATUS:           <PASS|WARN|FAIL|BLOCKED|UNKNOWN>
EVIDENCE:         <paths + digests>
ROLLBACK:         <file + records, or "n/a — read-only phase">
NEXT SAFE ACTION: <one command>
RECEIPT:          <path>
```
````

## `szl-v14/templates/RECEIPT.j2`

<!-- extract: szl-v14/templates/RECEIPT.j2 -->
```jinja
# Receipt: {{ cmd }}

- state: {{ state }}
- timestamp_utc: {{ timestamp_utc }}
- args_digest: {{ args_digest }}
- inputs: {{ inputs | length }} file(s)
- outputs: {{ outputs | length }} file(s)
{% for path, digest in outputs.items() -%}
- {{ path }} — sha256:{{ digest }}
{% endfor %}
```

## `szl-v14/templates/REPORT.j2`

<!-- extract: szl-v14/templates/REPORT.j2 -->
```jinja
# {{ title }}

| order | severity | code | action | verify |
|---|---|---|---|---|
{% for i in items -%}
| {{ i.order }} | {{ i.severity }} | {{ i.code }} | {{ i.action }} | {{ i.verify }} |
{% endfor %}
```

## `szl-v14/templates/REPO_AUDIT.j2`

<!-- extract: szl-v14/templates/REPO_AUDIT.j2 -->
```jinja
# Repo audit: {{ repo.name }}

| Field | Value |
|---|---|
| url | {{ repo.url }} |
| visibility | {{ repo.visibility }} |
| archived | {{ repo.archived }} |
| default_branch | {{ repo.default_branch }} |
| language | {{ repo.language }} |
| license | {{ repo.license }} |
| pushed_at | {{ repo.pushed_at }} |
| open_prs | {{ repo.open_prs }} |
| has_pages | {{ repo.has_pages }} |
| homepage | {{ repo.homepage }} |
| topics | {{ repo.topics }} |
| forbidden_refs | {{ repo.forbidden_refs }} |
| state | {{ repo.state }} |

description: {{ repo.description }}

Unprobed fields are UNKNOWN by construction — never guessed, never carried forward.
```

## `szl-v14/tests/test_digest.py`

<!-- extract: szl-v14/tests/test_digest.py -->
```python
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
```

## `szl-v14/tests/test_dns.py`

<!-- extract: szl-v14/tests/test_dns.py -->
```python
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
```

## `szl-v14/tests/test_dsse.py`

<!-- extract: szl-v14/tests/test_dsse.py -->
```python
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
```

## `szl-v14/tests/test_export.py`

<!-- extract: szl-v14/tests/test_export.py -->
```python
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
```

## `szl-v14/tests/test_jcs.py`

<!-- extract: szl-v14/tests/test_jcs.py -->
```python
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
```

## `szl-v14/tests/test_states.py`

<!-- extract: szl-v14/tests/test_states.py -->
```python
import pytest

from szl_v14.lib.states import State, promote, worst_state, Finding


def test_unknown_never_promotes_to_pass():
    with pytest.raises(ValueError):
        promote(State.UNKNOWN, State.PASS)


def test_unknown_can_be_acknowledged_but_not_passed():
    assert promote(State.UNKNOWN, State.BLOCKED) == State.BLOCKED


def test_worst_state_critical_is_fail():
    assert worst_state([Finding("CRITICAL", "X", "y")]) == State.FAIL


def test_worst_state_info_is_pass():
    assert worst_state([Finding("INFO", "X", "y")]) == State.PASS
```
