#!/usr/bin/env bash
# Print the GitHub Pages DNS plan. Mutates nothing without ./AUTHORIZE present,
# and even then only prints — actual writes go through the authorization packet.
set -euo pipefail
zone="${1:?usage: deploy_pages_dns.sh <zone> <org>}"
org="${2:?usage: deploy_pages_dns.sh <zone> <org>}"
cat <<PLAN
DNS plan for ${zone} (GitHub Pages, DNS-only during cert issuance):
  A     @     185.199.108.153   proxied=false
  A     @     185.199.109.153   proxied=false
  A     @     185.199.110.153   proxied=false
  A     @     185.199.111.153   proxied=false
  CNAME www   ${org}.github.io. proxied=false
prechecks: zone exported to rollback bundle first; Full (strict) set BEFORE any proxying
PLAN
if [ ! -f ./AUTHORIZE ]; then
  echo "state: AWAITING_AUTHORIZATION (no ./AUTHORIZE file; nothing was written)"
  exit 0
fi
echo "AUTHORIZE present — route this plan through 'szl-v14 dns apply' packet flow anyway."
