# §45 Remediate + export — evidence discipline

## Remediate (plan only)

`szl-v14 remediate` reads findings JSON and emits an ORDERED plan. Order is
not negotiable: credential repair first, then DNS, then origin-host services,
then code fixes, then cosmetic work. Each item carries the finding code it
closes, the exact safe next command, and the verification that proves it
worked. "Fixed" without a post-fix check is not fixed. "Deployed" without a
serving revision is not deployed.

## Export (every bundle, every time)

Every export gets a manifest; every manifest gets a digest; every bundle
records inputs and outputs. The bundle manifest itself is validated against
`schemas/export_bundle.schema.json` — "every bundle has a manifest" is
checkable, not aspirational. Reports are Jinja-derived from structured
sources: regenerate them; never hand-maintain prose.

## Export destination policy

| Artifact | Destination | Visibility | Signing |
|---|---|---|---|
| `SZL_MASTER_PAYLOAD_V14.md` + manifest + in-toto + unsigned envelope | `platform` repo | committed | unsigned until cosign armed |
| Per-repo audit files + matrix | `platform/artifacts/audits/` | committed | unsigned |
| Zone snapshots + rollback bundles | local + private vault dataset | local-only | unsigned |
| `OPERATOR_PACKET.md` | operator + `platform` | committed | unsigned |
| DNS plans + authorization packets | local until authorized | local-only | unsigned |
| Build + command receipts | append-only receipt sink | committed | unsigned until cosign armed |

No artifact is published while `publication_eligible` is false, and nothing
in this payload computes it true. When a signing key is armed, the envelope
is re-emitted with a real signature and renamed — never edited in place.
