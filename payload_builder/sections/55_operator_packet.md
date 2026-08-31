# §55 OPERATOR_PACKET.md — the one file you actually read

Everything else in the export tree is supporting evidence for this page. It
is rendered from `templates/OPERATOR_PACKET.j2`, and every one of these
fifteen answers is mandatory — an omitted answer is a FAIL, not a gap.

1. What was verified (with digests).
2. What was fixed (with post-fix verification output).
3. What remains failing (finding codes).
4. What is blocked on credentials (exact scope needed).
5. The exact DNS record diff proposed.
6. The exact rollback records for that diff.
7. The exact next safe command.
8. Per-domain DNS state (pass/fail/blocked, each domain separately).
9. Per-domain TLS state (each domain separately).
10. Per-domain app state (each domain separately).
11. Whether any forbidden-domain references remain (count; must be 0).
12. V11 artifacts: verified / regressed / unknown (with SHAs).
13. Estate completeness: VERIFIED or PARTIAL, with the source counts.
14. Claims re-measured: pass count, `CLAIM_DRIFT` count, UNMEASURABLE count.
15. `publication_eligible`: the computed boolean and which of its inputs
    are false.

Per-phase print block, after every phase, without exception:

```
STATUS:           <PASS|WARN|FAIL|BLOCKED|UNKNOWN>
EVIDENCE:         <paths + digests>
ROLLBACK:         <file + records, or "n/a — read-only phase">
NEXT SAFE ACTION: <one command>
RECEIPT:          <path>
```
