# §10 Phase -1 — DNS + credential repair (ahead of everything)

Nothing downstream verifies while credentials are malformed. This phase is
enforced twice: by its position in this document and by the builder's
`require_dns_first` compile gate — the build refuses to emit a payload whose
training or chip sections precede this one.

## Step 1 — verify the credential before trusting it

Regenerate per §0 item 2, then confirm `/user/tokens/verify` returns
`"status":"active"` with scopes `Zone:DNS:Edit` + `Zone:Zone:Read` scoped to
the target zones. Current connector evidence (captured 2026-08-31): HTTP 400,
code 6003 / 6103, `Invalid format for X-Auth-Key header` — the stored key is
malformed. `scripts/verify_cf_token.sh` (extracted) performs this check and
never prints the token.

## Step 2 — snapshot before any write

Before ANY record change, export the zone and write the rollback bundle
first: `artifacts/dns/<zone>.rollback.json`. No rollback bundle on disk →
no write. Every DNS apply is one record set at a time, with propagation
polling between sets.

## Step 3 — per-domain plans (from §05 truth table)

**a11oy.net** → GitHub Pages. Add/modify: apex A records 185.199.108.153,
185.199.109.153, 185.199.110.153, 185.199.111.153; `www` CNAME → org
Pages host. All `proxied: false` while GitHub provisions the certificate —
proxied apex records break Pages cert issuance. Removing records is part of
the rollback manifest, not improvisation.

**a-11-oy.com** → CNAME → `hf.space`. Precheck FIRST: Spaces custom domains
require PRO/Team/Enterprise; a free tier stays `pending` forever. SZLHOLDINGS
is Team plan (verified) → precheck PASS. Apex CNAME only if flattening is
confirmed for the zone; otherwise `www` CNAME + intentional apex 301. No
coexisting A/AAAA/CNAME at the same label.

**szl.dev** → registrar/delegation triage only: `whois szl.dev` →
`dig +trace NS szl.dev` → SOA. `.dev` is HSTS-preloaded; the deployment
order is DNS → cert → curl-verify → announce. No exceptions; linking early
is a hard failure in every browser.

**Tunnels** → the five 530/1033 hosts are an origin-host `cloudflared`
problem (error 1033 = no connector). This phase does NOT touch DNS for
them. Run `scripts/tunnel_triage.sh`, collect the origin-host outputs, fix
the service registration on the box.

## Step 4 — authorization packet, then STOP

Before any mutation: print the authorization packet — current zone state
digest, proposed add/modify/remove diff, exact rollback records, precheck
results — and STOP. `szl-v14 dns apply` does not mutate; it prints the
packet and exits with state AWAITING_AUTHORIZATION. The rollback file and
every rollback record must exist on disk before the packet is even printed.
