# §20 Doctor — environment triage that exits non-zero

`szl-v14 doctor` is the first control-plane command. Its output opens with a
section literally titled:

```
BLOCKERS THAT OUTRANK ALL COSMETIC WORK
```

The ordering is forced into the artifact rather than trusted to the reader.

## Checks

| Check | Severity on failure | Notes |
|---|---|---|
| Python >= 3.12 | FATAL | |
| `rfc8785` importable | FATAL | without real JCS every digest claim is theater |
| `huggingface_hub >= 1.0` | FATAL | the only bucket-visible call; without it the HF estate is invisible |
| `gh`, `dig`, `jq`, `curl`, `openssl` on PATH | FATAL | |
| `cosign` on PATH | WARN | signing path stays unsigned-honest until armed |
| GitHub snapshot present + two-source agreement | FATAL if absent | PARTIAL if sources disagree |
| HF snapshot present | FATAL if absent | 44 models / 38 datasets / 47 spaces expected as of 2026-08-31 |
| Cloudflare status file shows BLOCKED | blocker row | with the exact 6003/6103 evidence and required scopes |
| Estate snapshot age > 24h | WARN | stale truth is not truth |

## Semantics

- Exit 0: no FATAL findings. Exit 2: any FATAL.
- UNKNOWN is printed as UNKNOWN. It is never rendered green, never counted
  as PASS, never summarized away.
- `--json` emits the machine form; a receipt is written either way.
