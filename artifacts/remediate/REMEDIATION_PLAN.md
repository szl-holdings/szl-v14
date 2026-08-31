# Remediation plan

| order | severity | code | action | verify |
|---|---|---|---|---|
| 1 | HIGH | CF_TOKEN_BLOCKED | Connector API key malformed (X-Auth-Key invalid). Matches Phase -1 diagnosis: regenerate token. | re-run the producing command; state must improve or stay honestly UNKNOWN |
| 2 | LOW | NO_COSIGN | cosign absent — signing path stays unsigned-honest until armed | re-run the producing command; state must improve or stay honestly UNKNOWN |
