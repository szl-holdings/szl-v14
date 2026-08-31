# §25 The four correctness defects (fixed forever, enforced at compile)

These recurred across rounds. They are now compile-fail gates in the builder
and runtime invariants in the control plane — not review comments.

## Defect 1 — hashing a name instead of bytes

Symptom: a "digest" computed over a model or repository NAME string. That is
a digest of a label, not of content; it verifies nothing about the artifact.
Fix: chunked `sha256_file()` over actual bytes (1 MiB chunks), identical in
the builder and the control plane. Compile gate: the regex in
`lint/forbidden.txt` matching a string-literal-inside-hash pattern fails the
build.

## Defect 2 — fake JCS

Symptom: canonicalization via `json.dumps` with sorted keys passed off as
RFC 8785. Number and unicode serialization differ; two "canonical" documents
then diverge across implementations. Fix: the real `rfc8785` package, and a
hard import failure with install instructions if absent. Proof fixture: a
whitespace-only, canonical-equivalent document pair MUST produce identical
digests (the control plane's `mcp` module enforces this — it is the single
best test that the JCS implementation is real).

## Defect 3 — unsigned dishonesty

Symptom: an envelope with an empty signature field described as signed, or a
`keyid` placeholder like a not-yet-integrated sigstore identity. Fix:
artifacts without signatures are named `*.unsigned.json`, carry
`signatures: []`, and the verifier asserts both the name and the empty list.
The word "signed" is reserved for artifacts with a verifiable signature.
Signing path when armed: `cosign attest-blob --predicate ... --output-attestation`.

## Defect 4 — hardcoded spec versions and construct URLs

Symptom: a pinned attestation spec-version string frozen into code, and API
endpoints hardcoded inside implementation modules — including the HF
`collections` endpoint taking the wrong owner parameter. Fix: versions and
endpoint maps live in config; modules read config; lint fails the build on
the known-bad patterns.

## Compile-fail promotion

Two recurring review findings are promoted to build-breaking conditions:
hashing a name instead of file bytes (Defect 1), and accidental secret
logging — any print of a value whose name contains TOKEN/SECRET/API_KEY/PAT
fails the build via `lint/forbidden.txt`.
