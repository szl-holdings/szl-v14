# OPERATOR PACKET — SZL V14 build + estate audit (evidence captured 2026-08-31)

## The fifteen mandatory answers

1. **Verified (digests):** payload `SZL_MASTER_PAYLOAD_V14.md` sha256 `fc94c346…` (full value in `dist/manifest.json`); 15 sections compiled green; 46 control-plane files extracted **byte-identical** to source; 22/22 tests pass, including from the extracted copy; rebuild proven byte-identical (`make idempotent`).
2. **Fixed (with post-fix verification):** rfc8785 bytes/str boundary; extraction trailing-newline drift; typer constructor; repo-root asset paths; two lint self-trips. Each verified by re-running `build.py all && verify && idempotent`.
3. **Remaining failures (estate-level, finding codes):** `TUNNEL_1033` (5 of 6 tunnel hosts — origin-host, not DNS); `szl.dev` NXDOMAIN.
4. **Blocked on credentials:** Cloudflare connector key malformed — HTTP 400, code 6003, error-chain 6103 (`Invalid format for X-Auth-Key header`). Scope needed: `Zone:DNS:Edit` + `Zone:Zone:Read`, target zones only; verify at `/user/tokens/verify` → `"active"`.
5. **DNS record diff proposed:** NONE — live state already matches plan: `a11oy.net` has all 4 apex A (185.199.108–111.153) + `www` CNAME → `szl-holdings.github.io`; `a-11-oy.com` resolves via Cloudflare and serves the honest endpoint (200).
6. **Rollback records:** n/a — read-only phase; no zone writes were made. Rollback bundle required before any future write.
7. **Next safe command:** regenerate the Cloudflare token, then run `scripts/verify_cf_token.sh` (never prints the token).
8. **Per-domain DNS:** a11oy.net PASS · a-11-oy.com PASS · szl.dev FAIL (NXDOMAIN — registrar/delegation, run `nxdomain_triage.sh`).
9. **Per-domain TLS:** a11oy.net PASS (Let's Encrypt, valid to 2026-10-14) · a-11-oy.com PASS (GTS, valid to 2026-11-23) · szl.dev UNKNOWN (no delegation).
10. **Per-domain app:** a11oy.net `/health.json` 200 (GitHub Pages, static — signer unavailable, not DSSE-LIVE, exactly as README states) · a-11-oy.com `/api/a11oy/v1/honest` 200 · szl.dev unreachable.
11. **Forbidden-domain references remaining:** **0** across all 100 repo audits, the payload, and the export bundle (compile gate + audit scan + export scan).
12. **V11 artifacts:** UNKNOWN this run (not probed; run `verify-v11` with head/base/merge SHAs next). The "12 stuck PRs" concern is stale — measured open PRs across 17 key repos: 1 (`a11oy`), 0 elsewhere.
13. **Estate completeness:** VERIFIED — 3 independent GitHub sources agree at **100 repos**; Hugging Face **44 models / 38 datasets / 47 spaces** (129 total).
14. **Claims:** 6 PASS · 0 CLAIM_DRIFT · 0 UNMEASURABLE (repo counts, HF counts, khipu-sda-core existence). The README's older 38/58/19/100 discrepancies are superseded by measured 100/95-public.
15. **publication_eligible: False** — false inputs: Cloudflare credential blocked; tunnels down; szl.dev undelegated; V11 unverified; cosign not armed; KIDS v0.1 not frozen.

## What changed vs. the thread's assumptions

- `a11oy.net` and `a-11-oy.com` are **already live with valid TLS and matching DNS** — Phase -1's DNS plans for these two are maintenance, not repair.
- HF org is **Team plan** → the `a-11-oy.com` Spaces-custom-domain precheck passes.
- `khipu-sda-core`, `khipu-consensus`, `khipu-lab`, `khipu-pages`, `szl-khipu` exist on GitHub; 5 KHIPU-family models exist on HF. Read before creating anything.
- `szl-router` already ships signed-when-armed/unsigned-honest envelopes — reuse it.

## Human actions required (nothing else can do these)

1. **Daybreak Blue hardware key — closes Sept 1. Non-recoverable. Do it first.**
2. Regenerate the Cloudflare API token (§4 above) and re-run the connector check.
3. Origin host: `systemctl status cloudflared`, `journalctl -u cloudflared --since "24 hours ago"`, `cloudflared tunnel list`.
4. `whois szl.dev` → `dig +trace NS szl.dev` → SOA. Then DNS → cert → curl-verify → announce (`.dev` is HSTS-preloaded).
