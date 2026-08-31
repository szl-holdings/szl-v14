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
