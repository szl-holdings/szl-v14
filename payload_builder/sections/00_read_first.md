# §0 READ FIRST — four manual actions (no agent can do these)

Everything in this payload is machine-executable except the four items below.
They outrank all build, audit, DNS, chip, and training work. Do them first,
in this order.

## 1. Daybreak Blue hardware key — deadline September 1, non-recoverable

This is the only item in the entire program that cannot be redone later.
If the deadline passes, it is gone. Do it now, before reading further.

## 2. Regenerate the Cloudflare API token

The currently configured connector key is confirmed malformed. Evidence: a
read-only account-list call on 2026-08-31 returned HTTP 400, code 6003
(`Invalid request headers`), error-chain code 6103 (`Invalid format for
X-Auth-Key header`). Every stalled DNS write and the `szl.dev` NXDOMAIN stall
trace back to this.

Action: Cloudflare dashboard → My Profile → API Tokens → create from the
"Edit zone DNS" template with `Zone:DNS:Edit` + `Zone:Zone:Read`, scoped to
your zones only (scoping to one zone errors on every other zone — scope to
the target zones). Then verify before trusting it:

```bash
curl -s https://api.cloudflare.com/client/v4/user/tokens/verify \
  -H "Authorization: Bearer $CF_API_TOKEN" | jq -e '.result.status == "active"'
```

If that does not return `"active"`, do not proceed to any DNS step. Never
echo or log the token value.

## 3. Pull origin-host tunnel state

Five of six tunnel hosts returning 530/1033 means no `cloudflared` connector
is registered — that is an origin-host problem, not DNS. On the origin box:

```bash
systemctl status cloudflared
journalctl -u cloudflared --since "24 hours ago"
cloudflared tunnel list
```

Paste those three outputs into the audit. `TUNNEL_1033` is the finding code.

## 4. Collect `szl.dev` registrar facts

`szl.dev` NXDOMAIN is a registrar/delegation state, not a records problem.
Collect, in this order:

```bash
whois szl.dev
dig +trace NS szl.dev
dig SOA szl.dev
```

No DNS records fix a delegation that does not exist.
