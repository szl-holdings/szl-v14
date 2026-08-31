# §30 Estate audit — enumerate, never assert

Measured 2026-08-31 against the live APIs; recompute with
`szl-v14 inventory` / `szl-v14 audit` rather than trusting these numbers.

## Inventory truth

| Estate | Count | Evidence |
|---|---|---|
| GitHub org `szl-holdings` repos | **100** | Source 1: `gh repo list szl-holdings -L 200 --json` → 100. Source 2: search API `total_count` → 100. Source 3: REST `orgs/{org}/repos` pagination → BLOCKED (shared-credential rate limit, HTTP 403). Two independent sources agree → VERIFIED; third recorded as BLOCKED, not coerced |
| Hugging Face `SZLHOLDINGS` | **44 models / 38 datasets / 47 spaces** (129 total) | Hub API per-type queries, author-filtered, matching declared totals |
| Cloudflare | BLOCKED | Token malformed: 6003/6103 (see §0 item 2) |
| Tunnels | 5 of 6 hosts 530/1033 | Origin-host connector missing; 1 host 403 = Access working correctly |

Historical public counts (38, 58, 19-displayed, 100-in-memory) contradicted
each other across sources. The rule stands: the audit prints a computed count
with pagination evidence, or marks the estate PARTIAL. It never prints a
number it cannot source.

## One by one

"One by one" means one audit file per repo — `artifacts/audits/repos/<name>.md`
rendered from a Jinja template so all N files are byte-identical in structure
and diffable across runs — rolled up into `REPOSITORY_MATRIX.csv`. Fields not
probed are recorded as UNKNOWN. Never guessed, never carried forward.

Notable estate facts (measured):

- `platform` is the center of gravity: multi-thousand-commit monorepo with
  Doctrine v11 LOCKED. An audit treating it as one row among 100 is
  mis-weighted; it gets a deep audit pass first.
- `szl-router` already implements signed-when-armed / unsigned-honest
  envelopes. Reuse it; do not reimplement the doctrine.
- `khipu-sda-core` already exists — read it before creating any new KHIPU
  repository to avoid forking your own work.
- Repos present but absent from the org README's 19-repo display include
  `szl-router`, `szl-lake`, `szl-provctl-live`, `szl-energy-attest`,
  `khipu-sda-core`, `yarqa`, `immune`, `killinchu`, `rosie`, `developers` —
  proof the README undercounts the estate. Enumerate; do not read the README.

## verify-claims — the README is a claim surface

The org README asserts ~20 hard numeric claims (test pass counts, package
counts, table counts, endpoint counts, Λ-overhead medians) stamped
"verified 2026-05-12" — 3.5 months stale. `szl-v14 verify-claims`
re-measures every claim that is measurable from snapshots or CI logs, diffs
against the published value, and opens one `CLAIM_DRIFT` finding per
mismatch. A company whose thesis is provable claims cannot carry stale
proof dates on its own front page.

## Link integrity before outbound sends

Any external document citing repositories must have every link resolved
BEFORE it ships. A broken repo link inside a provenance argument fails the
argument. `verify-claims` includes link resolution as a finding class.
