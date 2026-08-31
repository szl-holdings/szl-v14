# §60 Two-pass execution contract

## Pass 1 — read-only (no authorization needed)

1. Build the payload builder: `make all && make verify && make idempotent`.
2. Materialize the control plane from `dist/extracted/`; `pip install -e .`;
   `pytest -q` green.
3. `doctor` → `inventory` → `audit` → `verify-v11` → `dns inspect` →
   `tunnel-audit` → `deploy inspect` → `extract` → `remediate plan` →
   `dns plan` → `dns validate` → `export all`.
4. Print the per-phase block (§55) after each phase.
5. STOP. Expected output: evidence tree + blocker list. That is success,
   not failure.

## Pass 2 — authorized-only (each line needs explicit approval)

- Pin versions.
- Baseline eval of the UNMODIFIED base model on the sealed suite — without
  this, any fine-tuned score is unfalsifiable; the delta is the only claim.
- Corpus: dedupe first, then split by source-repo LINEAGE (never random
  rows — ~100 repos share recurring policy text; random shuffle puts
  near-duplicates on both sides of the seal and the held-out eval measures
  memorization), then SEAL BEFORE TRAINING. The seal is the falsifiability
  proof; sealing after training makes eligibility unfalsifiable.
- DNS apply: one record set at a time; pre-change zone export; propagation
  polling between sets.
- Train; sealed eval; attest; sign (cosign when armed); publish — each
  gated on the computed boolean and nothing else.

## Stuck-queue rule

Resolve the currently open PRs before opening more. An agent that adds to a
12-PR backlog is generating load, not progress.

## Kernel shipping rule

Ship `lambda-gate` first; hold `receipt-hash` until there is a measured
crossover against an OPTIMIZED CPU baseline (p50/p95/p99, documented batch
at crossover). SHA-256/Ed25519 at small batch are often slower on GPU once
host-to-device transfer is counted; benchmark first, claim second.
