# §35 V11 verification — verify, do not recreate

Doctrine v11 is LOCKED and merged. The failure mode this phase prevents is
an agent enthusiastically recreating merged work. Verify state instead.

## Checks (per artifact)

For each of the four V11 PRs, `model-bom`, and `prove-it`:

1. Existence and state (merged/closed/open) — recorded, not assumed.
2. Head SHA, base SHA, merge SHA — all three recorded in the audit file.
3. CI status at the merge SHA.
4. Regression evidence: did anything downstream change behavior since merge?

## Promotion rule

Evidence states are PASS / WARN / FAIL / BLOCKED / UNKNOWN per artifact.
UNKNOWN never promotes. If a check cannot be run — credential blocked,
rate-limited, missing log — the artifact is UNKNOWN for that check and the
summary says so in words. A verification pass that cannot see CI is not a
pass; it is BLOCKED with the blocker named.

## Output

`artifacts/audits/v11/<artifact>.md` per artifact plus a roll-up line in
`OPERATOR_PACKET.md`: verified / regressed / unknown, with SHAs.
