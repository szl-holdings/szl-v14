# SZL V14 — payload builder + estate control plane + live audit bundle

<!-- szl:header v1 -->
<!-- Native identity: szl-brand@4309f6fce89179331b0b3ed8c99494e76c5be256; Orbit v2 icon. -->
<p>
  <a href="https://github.com/szl-holdings">
    <img src="https://raw.githubusercontent.com/szl-holdings/szl-brand/4309f6fce89179331b0b3ed8c99494e76c5be256/kit/logos/orbit-v2/suite/szl-icon-32.svg" alt="SZL Holdings — Orbit v2" width="32" height="32" />
  </a>
</p>

**Control before action. Evidence after.**

[Product](https://a-11-oy.com) · [Proof](https://a11oy.net) · [GitHub organization](https://github.com/szl-holdings)
<!-- /szl:header -->

- `payload_builder/` — the thing that builds the payload. `python build.py all && python build.py verify && make idempotent`.
- `szl-v14/` — the estate control plane (`pip install -e szl-v14`, `szl-v14 doctor|inventory|audit|verify-claims|dns|deploy|provenance|mcp|remediate|export`). Read-only; `dns apply` prints an authorization packet and stops.
- `estate/` — live snapshots (captured 2026-08-31): GitHub (100 repos, 3-source VERIFIED), Hugging Face (44/38/47), Cloudflare (BLOCKED, 6003/6103).
- `artifacts/` — per-repo audits (100), matrix, inventory, receipts, export bundle.
- `OPERATOR_PACKET.md` — the one file to read first.

Sections are the source. dist/ is derived. Never hand-edit dist/.

Estate on Hugging Face: models, datasets and Spaces are published under the [SZLHOLDINGS](https://huggingface.co/SZLHOLDINGS) org.

## License

Apache-2.0 — see [LICENSE](LICENSE).
