# §40 MCP attestation — deny-on-drift

The MCP layer attests tool-descriptor integrity: canonical digests of each
server's exposed tool schemas, compared against the attested baseline.
Drift in any of the 13 tracked classes (added tool, removed tool, renamed
tool, changed description, changed required params, changed types, changed
defaults, changed output schema, changed auth posture, endpoint change,
version bump, permission widening, semantic doc drift) denies the run:
exit 2, finding emitted, no coercion.

## The eight fixtures (all must pass)

1. **Canonical-equivalence** — a whitespace-only, canonical-equivalent JSON
   document pair MUST produce zero drift. If it drifts, the canonicalization
   is not real RFC 8785. This is the sharpest test in the estate.
2. **Added tool** → drift class `tool_added`, exit 2.
3. **Removed tool** → drift class `tool_removed`, exit 2.
4. **Changed required params** → drift, exit 2.
5. **Permission widening** → drift, exit 2 (highest severity).
6. **Refusal-then-leak reward fixture** — a response that opens with a
   refusal phrase then leaks the protected data nets **−3.0**, not
   +1.5 − 3.0. The over-refusal penalty must not be reward-hackable by
   prefixing a refusal.
7. **Baseline attestation replay** — identical descriptors → identical
   digest, byte-for-byte.
8. **Cross-implementation digest vector** — the same descriptor digests
   identically from the Python control plane and the reference vector file.

## Why this is the wedge

Provenance of documents is table stakes. Provenance of the tool surface an
agent is actually running against — enforced at invocation time, deny-on-
drift — is the product claim. Keep the fixtures green before anything else
ships.
