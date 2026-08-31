#!/usr/bin/env bash
# Verify a Cloudflare API token before trusting it. Never prints the token.
set -euo pipefail
: "${CF_API_TOKEN:?set CF_API_TOKEN in the environment (value is never printed)}"
status=$(curl -s https://api.cloudflare.com/client/v4/user/tokens/verify \
  -H "Authorization: Bearer ${CF_API_TOKEN}" | jq -r '.result.status // "error"')
if [ "$status" = "active" ]; then
  echo "token status: active"
  exit 0
fi
echo "token status: ${status} — expected \"active\". Regenerate: My Profile -> API Tokens -> 'Edit zone DNS' template, scopes Zone:DNS:Edit + Zone:Zone:Read, target zones only." >&2
exit 1
