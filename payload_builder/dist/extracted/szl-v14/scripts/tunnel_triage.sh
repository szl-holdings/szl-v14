#!/usr/bin/env bash
# 530/1033 on a tunnel host = no cloudflared connector registered on the ORIGIN.
# This is not a DNS problem. Run ON THE ORIGIN BOX. Read-only.
set -euo pipefail
echo "== systemctl status cloudflared =="
systemctl status cloudflared --no-pager 2>&1 | head -20 || true
echo "== journalctl -u cloudflared --since 24 hours ago =="
journalctl -u cloudflared --since "24 hours ago" --no-pager 2>&1 | tail -30 || true
echo "== cloudflared tunnel list =="
cloudflared tunnel list 2>&1 || true
echo "finding code: TUNNEL_1033 — never remove Cloudflare Access to turn a 403 into a 200"
