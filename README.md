# SZL V14 — payload builder + estate control plane + live audit bundle

- `payload_builder/` — the thing that builds the payload. `python build.py all && python build.py verify && make idempotent`.
- `szl-v14/` — the estate control plane (`pip install -e szl-v14`, `szl-v14 doctor|inventory|audit|verify-claims|dns|deploy|provenance|mcp|remediate|export`). Read-only; `dns apply` prints an authorization packet and stops.
- `estate/` — live snapshots (captured 2026-08-31): GitHub (100 repos, 3-source VERIFIED), Hugging Face (44/38/47), Cloudflare (BLOCKED, 6003/6103).
- `artifacts/` — per-repo audits (100), matrix, inventory, receipts, export bundle.
- `OPERATOR_PACKET.md` — the one file to read first.

Sections are the source. dist/ is derived. Never hand-edit dist/.
