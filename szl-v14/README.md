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
