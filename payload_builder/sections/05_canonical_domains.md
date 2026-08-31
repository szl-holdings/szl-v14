# §05 Canonical domain truth table

One table. Every other document derives from it. Any reference to the
forbidden domain anywhere — code, docs, tags, DNS names, badges — is finding
`CRITICAL/FORBIDDEN_LINK` and breaks the build.

| Domain | Role | Target | DNS posture | Constraint |
|---|---|---|---|---|
| `a11oy.net` | Public proof origin | GitHub Pages: 4 apex A records 185.199.108.153, 185.199.109.153, 185.199.110.153, 185.199.111.153 + `www` CNAME → `<org>.github.io` | `proxied: false` (DNS-only) during certificate issuance | If the orange cloud is ever wanted, set SSL/TLS to Full (strict) BEFORE enabling proxying, never after |
| `a-11-oy.com` | Command center | CNAME → `hf.space` (Hugging Face Spaces custom domain) | Flat label, no coexisting records at the same label | Requires PRO/Team/Enterprise on the org — verify plan tier BEFORE any DNS work, otherwise the domain stays `pending` forever regardless of record correctness. SZLHOLDINGS org is Team plan (verified 2026-08-31) → precheck PASS |
| `szl.dev` | Developer surface | Registrar/delegation first: `whois` → `dig +trace NS` → SOA | No records until delegation confirmed | `.dev` is on the HSTS preload list with no opt-out: order is DNS → certificate → curl-verify → announce. Announcing before a valid cert exists = hard browser failure, not a warning |
| the forbidden domain (`a11oy[.]com`) | — none — | — none — | — none — | Third-party WordPress furniture store. FORBIDDEN. `CRITICAL/FORBIDDEN_LINK` on any reference |

## Construct-URL map trap (externalized, never hardcode in modules)

Hugging Face API parameter asymmetry, encoded once here and consumed from
config: listing endpoints use `author=` for models, datasets, and spaces —
but `collections` uses `owner=`. `collections?author=` silently returns
wrong results. The control plane reads this map from config; a lint pattern
in `lint/forbidden.txt` fails the build on the collections-endpoint
author-parameter form.

## Tunnel estate

Five of six tunnel hosts fail 530/1033: no connector registered on the
origin. The sixth (`gpu2`) returns 403 via Cloudflare Access — that means
Access is working correctly. Rule: never remove Cloudflare Access to turn a
403 into a green probe. A green probe obtained by deleting the gate is a
false PASS.
