# SZL_MASTER_PAYLOAD_V14

<!-- section:read_first sha256:fc509e850b64f3d30fc56c0722d5da61ff07003890f79eb06313686400996b65 -->
# §0 READ FIRST — four manual actions (no agent can do these)

Everything in this payload is machine-executable except the four items below.
They outrank all build, audit, DNS, chip, and training work. Do them first,
in this order.

## 1. Daybreak Blue hardware key — deadline September 1, non-recoverable

This is the only item in the entire program that cannot be redone later.
If the deadline passes, it is gone. Do it now, before reading further.

## 2. Regenerate the Cloudflare API token

The currently configured connector key is confirmed malformed. Evidence: a
read-only account-list call on 2026-08-31 returned HTTP 400, code 6003
(`Invalid request headers`), error-chain code 6103 (`Invalid format for
X-Auth-Key header`). Every stalled DNS write and the `szl.dev` NXDOMAIN stall
trace back to this.

Action: Cloudflare dashboard → My Profile → API Tokens → create from the
"Edit zone DNS" template with `Zone:DNS:Edit` + `Zone:Zone:Read`, scoped to
your zones only (scoping to one zone errors on every other zone — scope to
the target zones). Then verify before trusting it:

```bash
curl -s https://api.cloudflare.com/client/v4/user/tokens/verify \
  -H "Authorization: Bearer $CF_API_TOKEN" | jq -e '.result.status == "active"'
```

If that does not return `"active"`, do not proceed to any DNS step. Never
echo or log the token value.

## 3. Pull origin-host tunnel state

Five of six tunnel hosts returning 530/1033 means no `cloudflared` connector
is registered — that is an origin-host problem, not DNS. On the origin box:

```bash
systemctl status cloudflared
journalctl -u cloudflared --since "24 hours ago"
cloudflared tunnel list
```

Paste those three outputs into the audit. `TUNNEL_1033` is the finding code.

## 4. Collect `szl.dev` registrar facts

`szl.dev` NXDOMAIN is a registrar/delegation state, not a records problem.
Collect, in this order:

```bash
whois szl.dev
dig +trace NS szl.dev
dig SOA szl.dev
```

No DNS records fix a delegation that does not exist.

---

<!-- section:canonical_domains sha256:2d1f1dd1b4b813ca71515026341e04708a4b1a247e46a161e26f0b514c38b057 -->
# §05 Canonical domain truth table

One table. Every other document derives from it. Any reference to the
forbidden domain anywhere — code, docs, tags, DNS names, badges — is finding
`CRITICAL/FORBIDDEN_LINK` and breaks the build.

| Domain | Role | Target | DNS posture | Constraint |
|---|---|---|---|---|
| `a11oy.net` | Public proof origin | GitHub Pages: 4 apex A records 185.199.108.153, 185.199.109.153, 185.199.110.153, 185.199.111.153 + `www` CNAME → `<org>.github.io` | `proxied: false` (DNS-only) during certificate issuance | If the orange cloud is ever wanted, set SSL/TLS to Full (strict) BEFORE enabling proxying, never after |
| `a-11-oy.com` | Command center | CNAME → `hf.space` (Hugging Face Spaces custom domain) | Flat label, no coexisting records at the same label | Requires PRO/Team/Enterprise on the org — verify plan tier BEFORE any DNS work, otherwise the domain stays `pending` forever regardless of record correctness. SZLHOLDINGS org is Team plan (verified 2026-08-31) → precheck PASS |
| `szl.dev` | Developer surface | Registrar/delegation first: `whois` → `dig +trace NS` → SOA | No records until delegation confirmed | `.dev` is on the HSTS preload list with no opt-out: order is DNS → certificate → curl-verify → announce. Announcing before a valid cert exists = hard browser failure, not a warning |
| the forbidden domain (`a11oy[.]com`) | — none — | — none — | — none — | Third-party WordPress furniture store. FORBIDDEN. `CRITICAL/FORBIDDEN_LINK` on any reference |

## Construct-URL map trap (externalized, never hardcode in modules)

Hugging Face API parameter asymmetry, encoded once here and consumed from
config: listing endpoints use `author=` for models, datasets, and spaces —
but `collections` uses `owner=`. `collections?author=` silently returns
wrong results. The control plane reads this map from config; a lint pattern
in `lint/forbidden.txt` fails the build on the collections-endpoint
author-parameter form.

## Tunnel estate

Five of six tunnel hosts fail 530/1033: no connector registered on the
origin. The sixth (`gpu2`) returns 403 via Cloudflare Access — that means
Access is working correctly. Rule: never remove Cloudflare Access to turn a
403 into a green probe. A green probe obtained by deleting the gate is a
false PASS.

---

<!-- section:phase_neg1_dns sha256:abd44a63e131d229699a256c48f094258072fec62a64ffd0ccebd4ec08f61902 -->
# §10 Phase -1 — DNS + credential repair (ahead of everything)

Nothing downstream verifies while credentials are malformed. This phase is
enforced twice: by its position in this document and by the builder's
`require_dns_first` compile gate — the build refuses to emit a payload whose
training or chip sections precede this one.

## Step 1 — verify the credential before trusting it

Regenerate per §0 item 2, then confirm `/user/tokens/verify` returns
`"status":"active"` with scopes `Zone:DNS:Edit` + `Zone:Zone:Read` scoped to
the target zones. Current connector evidence (captured 2026-08-31): HTTP 400,
code 6003 / 6103, `Invalid format for X-Auth-Key header` — the stored key is
malformed. `scripts/verify_cf_token.sh` (extracted) performs this check and
never prints the token.

## Step 2 — snapshot before any write

Before ANY record change, export the zone and write the rollback bundle
first: `artifacts/dns/<zone>.rollback.json`. No rollback bundle on disk →
no write. Every DNS apply is one record set at a time, with propagation
polling between sets.

## Step 3 — per-domain plans (from §05 truth table)

**a11oy.net** → GitHub Pages. Add/modify: apex A records 185.199.108.153,
185.199.109.153, 185.199.110.153, 185.199.111.153; `www` CNAME → org
Pages host. All `proxied: false` while GitHub provisions the certificate —
proxied apex records break Pages cert issuance. Removing records is part of
the rollback manifest, not improvisation.

**a-11-oy.com** → CNAME → `hf.space`. Precheck FIRST: Spaces custom domains
require PRO/Team/Enterprise; a free tier stays `pending` forever. SZLHOLDINGS
is Team plan (verified) → precheck PASS. Apex CNAME only if flattening is
confirmed for the zone; otherwise `www` CNAME + intentional apex 301. No
coexisting A/AAAA/CNAME at the same label.

**szl.dev** → registrar/delegation triage only: `whois szl.dev` →
`dig +trace NS szl.dev` → SOA. `.dev` is HSTS-preloaded; the deployment
order is DNS → cert → curl-verify → announce. No exceptions; linking early
is a hard failure in every browser.

**Tunnels** → the five 530/1033 hosts are an origin-host `cloudflared`
problem (error 1033 = no connector). This phase does NOT touch DNS for
them. Run `scripts/tunnel_triage.sh`, collect the origin-host outputs, fix
the service registration on the box.

## Step 4 — authorization packet, then STOP

Before any mutation: print the authorization packet — current zone state
digest, proposed add/modify/remove diff, exact rollback records, precheck
results — and STOP. `szl-v14 dns apply` does not mutate; it prints the
packet and exits with state AWAITING_AUTHORIZATION. The rollback file and
every rollback record must exist on disk before the packet is even printed.

---

<!-- section:install_manifest sha256:052dd0171cd8334f1c81fd60742102f5586e708d0adbc243755a10cceb2deae2 -->
# §15 Install manifest — what to install, in three tiers

Tier 0 runs tonight with no license and no hardware. Tier 1 builds and tests
the entire chip datapath in simulation with no vendor tools. Tier 2 is
blocked pending decisions — do not install it early.

## Tier 0 — control plane (tonight, nothing blocked)

| Software | Pin | Purpose |
|---|---|---|
| Python | 3.12+ | everything |
| uv | latest | fast envs |
| git, gh, jq, curl, openssl, dig (bind-utils) | system | estate + DNS reads |
| cosign | latest | attestation path (keyless, when armed) |
| hf (huggingface_hub[cli]) | >= 1.0 | estate reads; `list_user_repos` is the only bucket-visible call |
| Python pkgs | `typer rich pydantic httpx jinja2 pyyaml jsonschema rfc8785 pytest ruff mypy` | control plane + builder |

## Tier 1 — chip simulation (no license, no hardware, runs in CI)

| Software | Pin | Purpose |
|---|---|---|
| Verilator | 5.x | RTL simulation of GEMM/RMSNorm/DMA datapath |
| cocotb | latest | Python testbenches, differential tests vs golden sim |
| numpy, torch (CPU), onnx | latest | golden references, differential oracles |
| CIRCT | optional | MLIR hardware-compiler experiments only |

Verilator + cocotb prove the datapath before any board exists. This removes
vendor licensing and board procurement from the critical path.

## Tier 2 — FPGA/ASIC (BLOCKED — pending decision packet)

| Software | Status | Purpose |
|---|---|---|
| AMD Vitis/Vivado 2026.1 | BLOCKED on license | FPGA build, HLS, on-board run |
| Versal-class board/SOM | BLOCKED on Jenny Phase 0 reply + procurement | prototype target — OPEN DECISION, do not name a part before the reply |
| OpenROAD | optional, research only | RTL-to-GDSII exploration; not a tapeout path |

Recording a blocker is a feature. A plan that names a board it does not have
is a claim, not a plan.

---

<!-- section:doctor sha256:a106bf6fd2ef0a913edaad201363f7dbb7ba1664e786fd768ff5e3a309872e45 -->
# §20 Doctor — environment triage that exits non-zero

`szl-v14 doctor` is the first control-plane command. Its output opens with a
section literally titled:

```
BLOCKERS THAT OUTRANK ALL COSMETIC WORK
```

The ordering is forced into the artifact rather than trusted to the reader.

## Checks

| Check | Severity on failure | Notes |
|---|---|---|
| Python >= 3.12 | FATAL | |
| `rfc8785` importable | FATAL | without real JCS every digest claim is theater |
| `huggingface_hub >= 1.0` | FATAL | the only bucket-visible call; without it the HF estate is invisible |
| `gh`, `dig`, `jq`, `curl`, `openssl` on PATH | FATAL | |
| `cosign` on PATH | WARN | signing path stays unsigned-honest until armed |
| GitHub snapshot present + two-source agreement | FATAL if absent | PARTIAL if sources disagree |
| HF snapshot present | FATAL if absent | 44 models / 38 datasets / 47 spaces expected as of 2026-08-31 |
| Cloudflare status file shows BLOCKED | blocker row | with the exact 6003/6103 evidence and required scopes |
| Estate snapshot age > 24h | WARN | stale truth is not truth |

## Semantics

- Exit 0: no FATAL findings. Exit 2: any FATAL.
- UNKNOWN is printed as UNKNOWN. It is never rendered green, never counted
  as PASS, never summarized away.
- `--json` emits the machine form; a receipt is written either way.

---

<!-- section:correctness_defects sha256:98ceeecb838c1092bc360407802ffd349abf6ca3d51082b397d0a1858141c6c2 -->
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

---

<!-- section:estate_audit sha256:6ed6b5b7a75eccf75a75832a0583b172a76540e9aa51bf234de3f9aba71b400f -->
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

---

<!-- section:v11_verification sha256:272b2b87b9ee3e92489bce448def698387a5c94964891420e99f281d6accb143 -->
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

---

<!-- section:mcp_attestation sha256:12c02405bb46900ddb92429ce4548012f85f773baa97d5a7a270b7a68a072313 -->
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

---

<!-- section:remediate_export sha256:2c4c1412a86da0c1a44c399ef482b3b7965b1421918afe02f10bf3f857a2134a -->
# §45 Remediate + export — evidence discipline

## Remediate (plan only)

`szl-v14 remediate` reads findings JSON and emits an ORDERED plan. Order is
not negotiable: credential repair first, then DNS, then origin-host services,
then code fixes, then cosmetic work. Each item carries the finding code it
closes, the exact safe next command, and the verification that proves it
worked. "Fixed" without a post-fix check is not fixed. "Deployed" without a
serving revision is not deployed.

## Export (every bundle, every time)

Every export gets a manifest; every manifest gets a digest; every bundle
records inputs and outputs. The bundle manifest itself is validated against
`schemas/export_bundle.schema.json` — "every bundle has a manifest" is
checkable, not aspirational. Reports are Jinja-derived from structured
sources: regenerate them; never hand-maintain prose.

## Export destination policy

| Artifact | Destination | Visibility | Signing |
|---|---|---|---|
| `SZL_MASTER_PAYLOAD_V14.md` + manifest + in-toto + unsigned envelope | `platform` repo | committed | unsigned until cosign armed |
| Per-repo audit files + matrix | `platform/artifacts/audits/` | committed | unsigned |
| Zone snapshots + rollback bundles | local + private vault dataset | local-only | unsigned |
| `OPERATOR_PACKET.md` | operator + `platform` | committed | unsigned |
| DNS plans + authorization packets | local until authorized | local-only | unsigned |
| Build + command receipts | append-only receipt sink | committed | unsigned until cosign armed |

No artifact is published while `publication_eligible` is false, and nothing
in this payload computes it true. When a signing key is armed, the envelope
is re-emitted with a real signature and renamed — never edited in place.

---

<!-- section:khipu sha256:c96a85eacf4fd67697b8f832454cfc61ec6e67755ff60d9d9943ccd92c3eac52 -->
# §50 KHIPU — the chip line, sequenced honestly

Source: `A11oy_KHIPU_X1_Chip_Software_Build_Manual` (August 2026). The manual
names seven new repositories and fixes a build order. Neither is negotiable,
and the estate is NOT greenfield: `khipu-sda-core`, `khipu-consensus`,
`khipu-lab`, `khipu-pages`, and `szl-khipu` already exist on GitHub, and
`szl-khipu-kernels`, `szl-khipu`, `szl-block-kv`, `YARQA-ATTN`,
`szl-receipt-attn` exist on the Hub. READ EXISTING WORK FIRST.

## Repositories to create (private; README + LICENSE + CI only — NO CODE until KIDS v0.1 is frozen)

| Repo | Contents (per manual) |
|---|---|
| `khipu-x1-hw` | RTL/HLS, FPGA projects, firmware, formal properties, evidence |
| `khipu-compiler` | IR, graph lowering, quantizer, memory planner, command generator |
| `khipu-runtime` | libkhipu, Python bindings, model loader, verifier |
| `khipu-driver` | Linux device/DMA/queue/reset boundary |
| `khipu-sim` | functional + performance simulators — **Apache-2.0** |
| `khipu-sdk` | CLI, profiler, examples, docs |
| `khipu-conformance` | golden vectors, fuzz corpus, compatibility matrix, benchmark harness — **Apache-2.0** |

`khipu-sim` and `khipu-conformance` are Apache-2.0 because conformance
vectors are only credible if a third party can run them. The rest stay
proprietary. Creating seven skeletons before KIDS is frozen produces seven
more empty repos joining the stuck-PR queue; the skeletons exist to reserve
names and CI, nothing more.

## Build order (the manual's own order — do not reorder)

1. Freeze KIDS v0.1: instruction-set/descriptor + register-map spec,
   precision (INT8/BF16 first; INT4 only after measured accuracy
   qualification), memory budget, supported transformer block.
2. Golden simulator + conformance vectors. The golden simulator IS the
   executable specification and precedes RTL; differential tests against
   PyTorch/NumPy are the only correctness proof.
3. GEMM/RMSNorm/DMA datapath + libkhipu runtime. (Verilator + cocotb first:
   no license, no board, runs in CI.)
4. Attention/YARQA + KV-cache engine with block-table commitment.
5. Receipt engine, attestation, RC1 firmware, measured energy.
6. Compiler/quantizer + tiny-transformer end-to-end.
7. PyTorch integration + one small qualified LLM.
8. Benchmark and attack-test. Only then decide whether ASIC feasibility is
   justified. No tapeout until FPGA proves correctness, workload value,
   memory architecture, and software usability.

## Hardware carries the same doctrine

- Report `UNAVAILABLE` rather than estimate when power measurement fails —
  the hardware analogue of UNKNOWN-never-PASS (the manual's own words).
- `.khipu` package format (graph + weights + ABI + quantization + hashes +
  signatures) inherits all four §25 fixes at birth: byte digests over weight
  files, real RFC 8785 over the manifest, honest unsigned naming, no pinned
  spec-version strings.
- **Hash-function decision required BEFORE RTL**: the manual specifies a
  SHA3-256 receipt/event-chain engine while the rest of the estate is
  SHA-256. Two hash functions in one provenance chain is the same class of
  cross-domain defect as the SIGv1/DSSEv1 envelope split already fixed once.
  Pick one, or specify domain separation with a cross-language test vector.
- RC1 acceptance tests RC1-01→04 map 1:1 onto existing policy-gate tests;
  RC1-04 (Linux bypass attempt) is the test that proves the claim.
- No first-of-its-kind language anywhere: prior art exists and is cited in
  the manual itself. The builder's banned-claims lint fails on it.
- Vitis/Vivado 2026.1 licensing is recorded as a reproducibility limitation,
  not hidden (§15 Tier 2).

---

<!-- section:operator_packet sha256:3cde4e73c9050dd4cebb5f2907ec951672cfbadcfe78e7ee12e3055fc7930643 -->
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

---

<!-- section:two_pass_run sha256:fcce4bb2f203e81e25ef3ec5413c46f0cb883ed0f5fea52cf128695ab7436444 -->
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

---

<!-- section:phase_b_builder sha256:7dea4c5143cb26e52a3f434754161868e51820da29f875acaacc0d264ff4c4f3 -->
# §70 Phase B — the builder, specified by itself

This payload is generated by `payload_builder/`, the directory this section
ships. The builder enforces in code what the doctrine says in prose.

## Contract

| Verb | Behavior |
|---|---|
| `generate` | Scaffold missing section stubs from `manifest.toml`; idempotent, never overwrites, stubs are marked as stubs |
| `compile` | Hard fail (exit 1) on: section-order violation (`require_dns_first`), missing `must_contain` tokens, any `lint/forbidden.txt` match, any `lint/banned_claims.txt` match |
| `extract` | Write every extract-tag's (`<!‑extract: path mode=… ‑‑>`, written without the dashes) immediately-following code fence to `dist/extracted/`; path-escape checked (`..` or absolute → fail); duplicate target → fail |
| `export` | Assemble payload with inline per-section digest comments (`<!-- section:<id> sha256:<hex> -->`), JCS `manifest.json`, in-toto Statement v1, DSSE `payload.unsigned.json` with `signatures: []`, and the ONLY timestamped artifact: `dist/receipts/build-*.json` |
| `verify` | Re-digest every manifest subject against bytes on disk; assert the envelope's `signatures` is empty while named unsigned; grep all of `dist/` for the forbidden domain; assert `publication_eligible` is false |
| `all` | compile → extract → export. No destructive apply exists in this codebase |

## Why these design decisions are non-obvious

- **No timestamp in the body.** A build timestamp inside the payload makes
  every rebuild produce a different digest and renders the reproducibility
  claim unfalsifiable. Time lives only in receipts.
- **Explicit section list, never a glob.** A glob silently reorders the
  payload when a file is added — and DNS stops being Phase -1 without
  anyone noticing.
- **`must_contain` token assertions.** The DNS section must literally
  contain the token-verify endpoint, the DNS scopes, the Pages IPs, the
  Spaces CNAME target, the letters HSTS, the word rollback, and the tunnel
  error code — or the build refuses to emit. Those are the constraints most
  likely to be dropped in a casual edit, and one of them (linking a
  certless HSTS-preloaded domain) is externally visible damage.
- **Inline per-section digests.** Diff two payload versions and know
  instantly which section changed; verify one phase without re-reading the
  document.
- **Extract-path escape check.** This document is consumed by agents; a
  malformed extract tag must not be able to write outside the tree.

## CI

`.github/workflows/build.yml` runs: build → verify → byte-identical-rebuild
proof → install the extracted control plane → run its test suite. The
payload and the software it ships are gated by the same pipeline.

---

<!-- section:control_plane sha256:6c2fbf758489c64618690874ee8a3d68003093abab8588ab559f1520f19bba09 -->
# §90 Control plane — szl-v14 (machine-wrapped source of truth)

Every file below is written to `dist/extracted/` by `build.py extract`.
Edit here, not in `dist/`. Regenerate only when the tree changes shape.

## `szl-v14/README.md`

<!-- extract: szl-v14/README.md -->
````markdown
# szl-v14 — SZL Holdings estate control plane

Audit the GitHub / Hugging Face / Cloudflare estate from snapshots, plan DNS
repair, build provenance, and export digest-bearing evidence bundles.
**Read-only by construction**: every mutating verb prints an authorization
packet and stops with state `AWAITING_AUTHORIZATION`.

## Install

```bash
pip install -e .
```

## Commands

| Command | Purpose |
|---|---|
| `szl-v14 doctor` | Environment triage; first section is `BLOCKERS THAT OUTRANK ALL COSMETIC WORK`; exit 2 on any FATAL |
| `szl-v14 inventory --snapshot-dir <dir>` | Build `repos.yaml` from estate snapshots; two-source agreement check; PARTIAL on disagreement |
| `szl-v14 audit --snapshot-dir <dir>` | One audit file per repo from `REPO_AUDIT.j2` + `REPOSITORY_MATRIX.csv`; unprobed fields are UNKNOWN |
| `szl-v14 verify-claims --snapshot-dir <dir>` | Re-measure `claims.yaml`; mismatches become CLAIM_DRIFT findings |
| `szl-v14 dns plan` / `dns validate` / `dns apply` | Plan and validate `dns-targets.yaml`; `apply` prints the AUTHORIZATION PACKET and stops |
| `szl-v14 deploy` | Inspect-only deployment state table |
| `szl-v14 provenance <dir>` | in-toto Statement v1 + DSSE `*.unsigned.json` envelope over a directory |
| `szl-v14 mcp` | Drift fixtures: canonical-equivalence must show zero drift; refusal-then-leak nets −3.0 |
| `szl-v14 remediate <findings.json>` | Ordered remediation plan (credentials → DNS → origin-host → code → cosmetic) |
| `szl-v14 export <dir>` | Bundle: `manifest.json` (schema-validated), `manifest.unsigned.json`, receipt |

Every command supports `--json` and writes a receipt. Exit codes: 0 ok,
2 FAIL/CRITICAL finding, 3 misuse. BLOCKED and UNKNOWN print prominently and
are never coerced to PASS.

## Doctrine

Digests are over actual file bytes. Canonical JSON is real RFC 8785.
Unsigned artifacts are named `*.unsigned.json` and carry `signatures: []`.
No timestamps inside artifact bodies — time lives only in receipts.
The forbidden domain (`a11oy[.]com`) fails any command it appears in.
````

## `szl-v14/claims.yaml`

<!-- extract: szl-v14/claims.yaml -->
```yaml
# Published claims, re-measured against live snapshots. Mismatch -> CLAIM_DRIFT.
- id: gh-repo-count
  claim: GitHub org repository count
  source: estate enumeration 2026-08-31 (3-source agreement)
  expected: 100
  measure: {kind: github_repo_count}
- id: gh-public-count
  claim: GitHub org public repository count
  source: estate enumeration 2026-08-31
  expected: 95
  measure: {kind: github_visibility_count, visibility: PUBLIC}
- id: hf-model-count
  claim: Hugging Face model count
  source: hub_repo_search author=SZLHOLDINGS 2026-08-31
  expected: 44
  measure: {kind: hf_repo_count, repo_type: model}
- id: hf-dataset-count
  claim: Hugging Face dataset count
  source: hub_repo_search author=SZLHOLDINGS 2026-08-31
  expected: 38
  measure: {kind: hf_repo_count, repo_type: dataset}
- id: hf-space-count
  claim: Hugging Face space count
  source: hub_repo_search author=SZLHOLDINGS 2026-08-31
  expected: 47
  measure: {kind: hf_repo_count, repo_type: space}
- id: khipu-sda-core-exists
  claim: khipu-sda-core exists (the KHIPU line is not greenfield)
  source: estate enumeration 2026-08-31
  expected: true
  measure: {kind: github_repo_present, repo: khipu-sda-core}
```

## `szl-v14/dns-targets.yaml`

<!-- extract: szl-v14/dns-targets.yaml -->
```yaml
# Canonical DNS plan for the SZL estate. The command center is a-11-oy.com;
# the public proof origin is a11oy.net. The forbidden domain appears nowhere.
zones:
  - zone: a11oy.net
    role: public proof origin
    apex_cname_flattening: false
    rollback_source: artifacts/dns/a11oy.net.rollback.json
    target_summary: GitHub Pages (4 apex A + www CNAME)
    notes: proxied=false while GitHub provisions the certificate; if proxying is ever wanted, set Full (strict) BEFORE enabling it
    prechecks:
      - zone exported to rollback source before any write
      - token verified active at /user/tokens/verify
    records:
      - {type: A, name: "@", content: "185.199.108.153", provider: github_pages, proxied: false, ttl: 300}
      - {type: A, name: "@", content: "185.199.109.153", provider: github_pages, proxied: false, ttl: 300}
      - {type: A, name: "@", content: "185.199.110.153", provider: github_pages, proxied: false, ttl: 300}
      - {type: A, name: "@", content: "185.199.111.153", provider: github_pages, proxied: false, ttl: 300}
      - {type: CNAME, name: "www", content: "szl-holdings.github.io.", provider: github_pages, proxied: false, ttl: 300}
  - zone: a-11-oy.com
    role: command center
    apex_cname_flattening: true
    rollback_source: artifacts/dns/a-11-oy.com.rollback.json
    target_summary: Hugging Face Spaces custom domain (hf.space)
    notes: Spaces custom domains require PRO/Team/Enterprise; SZLHOLDINGS org is Team plan (verified) — precheck PASS. Cloudflare flattens apex CNAME natively.
    prechecks:
      - HF plan tier verified PRO/Team/Enterprise before any DNS work
      - no coexisting A/AAAA/CNAME at the label
    records:
      - {type: CNAME, name: "@", content: "hf.space.", provider: hf_spaces, proxied: false, ttl: 300}
  - zone: szl.dev
    role: developer surface
    apex_cname_flattening: false
    rollback_source: artifacts/dns/szl.dev.rollback.json
    target_summary: triage only — registrar/delegation first
    notes: .dev is HSTS-preloaded; order DNS -> cert -> curl-verify -> announce; run whois -> dig +trace NS -> SOA before any record work
    prechecks:
      - whois szl.dev
      - dig +trace NS szl.dev
      - dig SOA szl.dev
    records: []
```

## `szl-v14/pyproject.toml`

<!-- extract: szl-v14/pyproject.toml -->
```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "szl-v14"
version = "14.0.0"
description = "SZL Holdings estate control plane: audit, DNS planning, provenance, evidence export. Read-only; mutating verbs print authorization packets and stop."
requires-python = ">=3.12"
dependencies = [
    "typer>=0.12",
    "rich>=13.7",
    "pydantic>=2.6",
    "httpx>=0.27",
    "jinja2>=3.1",
    "pyyaml>=6.0",
    "jsonschema>=4.21",
    "rfc8785>=0.1.2",
]

[project.optional-dependencies]
dev = ["pytest>=8.0"]

[project.scripts]
szl-v14 = "szl_v14.cli:app"

[tool.setuptools.packages.find]
where = ["src"]

[tool.setuptools.package-data]
szl_v14 = ["py.typed"]
```

## `szl-v14/schemas/dns_plan.schema.json`

<!-- extract: szl-v14/schemas/dns_plan.schema.json -->
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://szl.dev/schemas/dns_plan.schema.json",
  "title": "SZL v14 DNS targets",
  "type": "object",
  "required": ["zones"],
  "properties": {
    "zones": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["zone", "records"],
        "properties": {
          "zone": {"type": "string"},
          "role": {"type": "string"},
          "apex_cname_flattening": {"type": "boolean"},
          "rollback_source": {"type": "string"},
          "prechecks": {"type": "array", "items": {"type": "string"}},
          "target_summary": {"type": "string"},
          "notes": {"type": "string"},
          "records": {
            "type": "array",
            "items": {
              "type": "object",
              "required": ["type", "name", "content"],
              "properties": {
                "type": {"enum": ["A", "AAAA", "CNAME", "MX", "TXT", "NS", "CAA"]},
                "name": {"type": "string"},
                "content": {"type": "string"},
                "provider": {"type": "string"},
                "proxied": {"type": "boolean"},
                "ttl": {"type": "integer", "minimum": 30}
              }
            }
          }
        }
      }
    }
  }
}
```

## `szl-v14/schemas/export_bundle.schema.json`

<!-- extract: szl-v14/schemas/export_bundle.schema.json -->
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://szl.dev/schemas/export_bundle.schema.json",
  "title": "SZL v14 export bundle manifest",
  "type": "object",
  "required": ["bundle", "format", "subjects"],
  "additionalProperties": false,
  "properties": {
    "bundle": {"type": "string", "minLength": 1},
    "format": {"const": "szl/v14-export-bundle"},
    "subjects": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "required": ["name", "digest"],
        "additionalProperties": false,
        "properties": {
          "name": {"type": "string", "minLength": 1},
          "digest": {
            "type": "object",
            "required": ["sha256"],
            "additionalProperties": false,
            "properties": {
              "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"}
            }
          }
        }
      }
    }
  }
}
```

## `szl-v14/schemas/khipu_package.schema.json`

<!-- extract: szl-v14/schemas/khipu_package.schema.json -->
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://szl.dev/schemas/khipu_package.schema.json",
  "title": "KHIPU .khipu package manifest — inherits the four correctness fixes at birth",
  "type": "object",
  "required": ["format", "graph", "weights", "abi", "quantization", "digests", "signatures"],
  "properties": {
    "format": {"const": "khipu-package/1"},
    "graph": {"type": "string"},
    "weights": {"type": "array", "items": {"type": "string"}},
    "abi": {"type": "string"},
    "quantization": {"type": "object"},
    "digests": {
      "type": "object",
      "description": "sha256 over the ACTUAL BYTES of each weight file and the JCS-canonical manifest; never over names",
      "additionalProperties": {"type": "string", "pattern": "^[0-9a-f]{64}$"}
    },
    "signatures": {
      "type": "array",
      "description": "[] while unsigned; the file is then named *.unsigned.json"
    }
  },
  "additionalProperties": true
}
```

## `szl-v14/schemas/kids.schema.json`

<!-- extract: szl-v14/schemas/kids.schema.json -->
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://szl.dev/schemas/kids.schema.json",
  "title": "KIDS — KHIPU Instruction-set/Descriptor Specification v0.1 (frozen before RTL)",
  "type": "object",
  "required": ["kids_version", "precision", "memory_budget_bytes", "supported_blocks"],
  "properties": {
    "kids_version": {"type": "string", "const": "0.1"},
    "precision": {"type": "array", "items": {"enum": ["INT8", "BF16", "INT4"]},
                  "description": "INT8/BF16 first; INT4 only after measured accuracy qualification"},
    "memory_budget_bytes": {"type": "integer", "exclusiveMinimum": 0},
    "supported_blocks": {"type": "array", "items": {"type": "string"}},
    "receipt_hash": {"enum": ["SHA-256", "SHA3-256"],
                     "description": "ONE function across the whole provenance chain, or explicit domain separation with cross-language test vectors"},
    "conformance_vectors_digest": {"type": "string", "pattern": "^[0-9a-f]{64}$"}
  },
  "additionalProperties": true
}
```

## `szl-v14/scripts/deploy_pages_dns.sh`

<!-- extract: szl-v14/scripts/deploy_pages_dns.sh mode=755 -->
```bash
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
```

## `szl-v14/scripts/nxdomain_triage.sh`

<!-- extract: szl-v14/scripts/nxdomain_triage.sh mode=755 -->
```bash
#!/usr/bin/env bash
# NXDOMAIN triage order: registrar -> delegation -> SOA. Read-only.
set -euo pipefail
domain="${1:?usage: nxdomain_triage.sh <domain>}"
echo "== 1/3 whois ${domain} (registrar state) =="
whois "${domain}" 2>/dev/null | grep -iE 'registrar|status|expir|name server' | head -20 || echo "whois unavailable"
echo "== 2/3 dig +trace NS ${domain} (delegation) =="
dig +trace NS "${domain}" 2>/dev/null | tail -20 || true
echo "== 3/3 dig SOA ${domain} =="
dig SOA "${domain}" +short || true
echo "note: .dev is HSTS-preloaded — DNS -> cert -> curl-verify -> announce"
```

## `szl-v14/scripts/tunnel_triage.sh`

<!-- extract: szl-v14/scripts/tunnel_triage.sh mode=755 -->
```bash
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
```

## `szl-v14/scripts/verify_cf_token.sh`

<!-- extract: szl-v14/scripts/verify_cf_token.sh mode=755 -->
```bash
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
```

## `szl-v14/src/szl_v14/__init__.py`

<!-- extract: szl-v14/src/szl_v14/__init__.py -->
```python
"""szl-v14 — SZL Holdings estate control plane."""

__version__ = "14.0.0"
```

## `szl-v14/src/szl_v14/__main__.py`

<!-- extract: szl-v14/src/szl_v14/__main__.py -->
```python
from szl_v14.cli import app

if __name__ == "__main__":
    app()
```

## `szl-v14/src/szl_v14/cli.py`

<!-- extract: szl-v14/src/szl_v14/cli.py -->
```python
"""szl-v14 CLI. Every command: --json, receipt, exit 0 ok / 2 FAIL / 3 misuse."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from szl_v14.lib import receipts
from szl_v14.lib.states import Report, State, emit_json, render_findings
from szl_v14.modules import audit as m_audit
from szl_v14.modules import deploy as m_deploy
from szl_v14.modules import dns as m_dns
from szl_v14.modules import doctor as m_doctor
from szl_v14.modules import export as m_export
from szl_v14.modules import inventory as m_inventory
from szl_v14.modules import mcp as m_mcp
from szl_v14.modules import provenance as m_provenance
from szl_v14.modules import remediate as m_remediate
from szl_v14.modules import verify_claims as m_verify_claims

app = typer.Typer(help="SZL Holdings estate control plane (read-only; mutating verbs print authorization packets).", no_args_is_help=True)
dns_app = typer.Typer(help="DNS validate/plan/apply (apply prints an authorization packet and stops).", no_args_is_help=True)
app.add_typer(dns_app, name="dns")

_WORK = Path("artifacts")


def _finish(report: Report, as_json: bool, receipt_root: Path) -> None:
    rcpt = receipts.write(receipt_root, report.cmd, {"json": as_json},
                          outputs=report.outputs, state=report.state.value)
    if as_json:
        print(emit_json(report))
    else:
        from szl_v14.modules.doctor import render_text as doctor_text
        print(doctor_text(report) if report.cmd == "doctor" else f"[{report.state.value}] {report.cmd}")
        render_findings(report.findings)
        for k, v in report.summary.items():
            if k not in ("results", "plans", "deployments", "blockers"):
                print(f"  {k}: {v}")
        print(f"receipt: {rcpt}")
    raise SystemExit(0 if report.state != State.FAIL else 2)


@app.command()
def doctor(snapshot_dir: Path = typer.Option(Path("estate"), help="estate snapshot root"),
           json: bool = typer.Option(False, "--json"),
           receipt_root: Path = typer.Option(_WORK)) -> None:
    """Environment triage; first section is BLOCKERS THAT OUTRANK ALL COSMETIC WORK."""
    _finish(m_doctor.run(snapshot_dir), json, receipt_root)


@app.command()
def inventory(snapshot_dir: Path = typer.Option(Path("estate")),
              out_dir: Path = typer.Option(Path("artifacts/inventory")),
              json: bool = typer.Option(False, "--json"),
              receipt_root: Path = typer.Option(_WORK)) -> None:
    """Build repos.yaml from snapshots; two-source disagreement -> PARTIAL."""
    _finish(m_inventory.run(snapshot_dir, out_dir), json, receipt_root)


@app.command()
def audit(snapshot_dir: Path = typer.Option(Path("estate")),
          out_dir: Path = typer.Option(Path("artifacts")),
          json: bool = typer.Option(False, "--json"),
          receipt_root: Path = typer.Option(_WORK)) -> None:
    """One audit file per repo (Jinja template) + REPOSITORY_MATRIX.csv."""
    _finish(m_audit.run(snapshot_dir, out_dir), json, receipt_root)


@app.command("verify-claims")
def verify_claims(snapshot_dir: Path = typer.Option(Path("estate")),
                  claims: Optional[Path] = typer.Option(None),
                  json: bool = typer.Option(False, "--json"),
                  receipt_root: Path = typer.Option(_WORK)) -> None:
    """Re-measure claims.yaml; mismatch -> CLAIM_DRIFT."""
    _finish(m_verify_claims.run(snapshot_dir, claims), json, receipt_root)


@dns_app.command("validate")
def dns_validate(targets: Optional[Path] = typer.Option(None),
                 json: bool = typer.Option(False, "--json"),
                 receipt_root: Path = typer.Option(_WORK)) -> None:
    """Validate dns-targets.yaml: schema + impossible-state rejection."""
    _finish(m_dns.run_validate(targets), json, receipt_root)


@dns_app.command("plan")
def dns_plan(targets: Optional[Path] = typer.Option(None),
             json: bool = typer.Option(False, "--json"),
             receipt_root: Path = typer.Option(_WORK)) -> None:
    """Print the per-zone record plan with rollback sources. Read-only."""
    _finish(m_dns.run_plan(targets), json, receipt_root)


@dns_app.command("apply")
def dns_apply(targets: Optional[Path] = typer.Option(None),
              json: bool = typer.Option(False, "--json"),
              receipt_root: Path = typer.Option(_WORK)) -> None:
    """Print the AUTHORIZATION PACKET and stop. Never mutates."""
    _finish(m_dns.run_apply(targets), json, receipt_root)


@app.command()
def deploy(targets: Optional[Path] = typer.Option(None),
           probe_file: Optional[Path] = typer.Option(None),
           json: bool = typer.Option(False, "--json"),
           receipt_root: Path = typer.Option(_WORK)) -> None:
    """Inspect-only deployment state table."""
    _finish(m_deploy.run(targets, probe_file), json, receipt_root)


@app.command()
def provenance(target_dir: Path,
               out_dir: Path = typer.Option(Path("artifacts/provenance")),
               json: bool = typer.Option(False, "--json"),
               receipt_root: Path = typer.Option(_WORK)) -> None:
    """in-toto Statement v1 + DSSE *.unsigned.json over a directory."""
    _finish(m_provenance.run(target_dir, out_dir), json, receipt_root)


@app.command()
def mcp(json: bool = typer.Option(False, "--json"),
        receipt_root: Path = typer.Option(_WORK)) -> None:
    """Drift fixtures: canonical-equivalence zero-drift; refusal-then-leak -3.0."""
    _finish(m_mcp.run(), json, receipt_root)


@app.command()
def remediate(findings_json: Path,
              out_dir: Path = typer.Option(Path("artifacts/remediate")),
              json: bool = typer.Option(False, "--json"),
              receipt_root: Path = typer.Option(_WORK)) -> None:
    """Findings JSON -> ordered remediation plan."""
    _finish(m_remediate.run(findings_json, out_dir), json, receipt_root)


@app.command(name="export")
def export_cmd(target_dir: Path,
               out_dir: Path = typer.Option(Path("artifacts/export")),
               bundle_name: str = typer.Option("bundle"),
               json: bool = typer.Option(False, "--json"),
               receipt_root: Path = typer.Option(_WORK)) -> None:
    """Bundle a directory: schema-validated manifest + unsigned envelope + receipt."""
    _finish(m_export.run(target_dir, out_dir, bundle_name), json, receipt_root)
```

## `szl-v14/src/szl_v14/lib/__init__.py`

<!-- extract: szl-v14/src/szl_v14/lib/__init__.py -->
```python
"""Shared library: digests, canonical JSON, envelopes, statements, states."""
```

## `szl-v14/src/szl_v14/lib/digest.py`

<!-- extract: szl-v14/src/szl_v14/lib/digest.py -->
```python
"""Byte digests over actual file contents. Never a name. Never a string."""

from __future__ import annotations

import hashlib
from pathlib import Path

CHUNK = 1 << 20  # 1 MiB


def sha256_file(path: str | Path, chunk: int = CHUNK) -> str:
    """SHA-256 of a file's actual bytes, read in chunks."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    """SHA-256 of an in-memory byte string."""
    return hashlib.sha256(data).hexdigest()


def digest_map(root: str | Path, chunk: int = CHUNK) -> dict[str, str]:
    """{relative_posix_path: sha256} for every file under root, sorted."""
    root = Path(root)
    return {
        p.relative_to(root).as_posix(): sha256_file(p, chunk)
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }
```

## `szl-v14/src/szl_v14/lib/dsse.py`

<!-- extract: szl-v14/src/szl_v14/lib/dsse.py -->
```python
"""DSSE envelopes with honest unsigned naming.

An artifact without a signature is named ``*.unsigned.json`` and carries
``signatures: []``. An empty signature list is never described as signed.
"""

from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any


def envelope(payload: bytes, payload_type: str = "application/vnd.in-toto+json") -> dict[str, Any]:
    """Build a DSSE envelope. Always honestly unsigned at creation time."""
    return {
        "payloadType": payload_type,
        "payload": base64.b64encode(payload).decode("ascii"),
        "signatures": [],
    }


def write_unsigned(env: dict[str, Any], path: str | Path) -> Path:
    """Write an unsigned envelope, enforcing the naming contract."""
    path = Path(path)
    if not path.name.endswith(".unsigned.json"):
        raise ValueError(f"unsigned envelopes must be named *.unsigned.json (got {path.name})")
    if env.get("signatures") != []:
        raise ValueError("envelope claims signatures but file is named unsigned")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(env, indent=2) + "\n")
    return path


def verify_unsigned(path: str | Path) -> dict[str, Any]:
    """Load an envelope and assert name/signature honesty. Raises on violation."""
    path = Path(path)
    env = json.loads(path.read_text())
    sigs = env.get("signatures", None)
    if path.name.endswith(".unsigned.json"):
        if sigs not in ([], None):
            raise ValueError("envelope claims signatures but file is named unsigned")
    else:
        if sigs == []:
            raise ValueError("envelope has no signatures but is not named *.unsigned.json")
    return env
```

## `szl-v14/src/szl_v14/lib/estate.py`

<!-- extract: szl-v14/src/szl_v14/lib/estate.py -->
```python
"""Load estate snapshots. A missing file is UNKNOWN, never a guess, never a crash."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class EstateSnapshot:
    root: Path
    github_repos: list[dict[str, Any]] = field(default_factory=list)   # repos_cli.json
    github_enumeration: dict[str, Any] = field(default_factory=dict)   # enumeration.json
    hf_estate: dict[str, Any] = field(default_factory=dict)            # hf_estate.json
    cloudflare_status: dict[str, Any] = field(default_factory=dict)    # status.json
    unknown: list[str] = field(default_factory=list)                   # snapshot names that were missing

    @property
    def estate_completeness(self) -> str:
        return self.github_enumeration.get("estate_completeness", "UNKNOWN")


def _load(root: Path, rel: str, unknown: list[str]) -> Any:
    p = root / rel
    if not p.exists():
        unknown.append(rel)
        return None
    try:
        return json.loads(p.read_text())
    except Exception:
        unknown.append(rel)
        return None


def load_snapshots(root: str | Path) -> EstateSnapshot:
    root = Path(root)
    unknown: list[str] = []
    return EstateSnapshot(
        root=root,
        github_repos=_load(root, "github/repos_cli.json", unknown) or [],
        github_enumeration=_load(root, "github/enumeration.json", unknown) or {},
        hf_estate=_load(root, "hf/hf_estate.json", unknown) or {},
        cloudflare_status=_load(root, "cloudflare/status.json", unknown) or {},
        unknown=unknown,
    )
```

## `szl-v14/src/szl_v14/lib/http.py`

<!-- extract: szl-v14/src/szl_v14/lib/http.py -->
```python
"""HTTP helpers. Secrets are never logged, never echoed, never in errors."""

from __future__ import annotations

import re
from typing import Any

import httpx

_BEARER = re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._\-]+")
_KEYVAL = re.compile(r"(?i)(token|secret|api[_-]?key|password|pat)([\"'\s:=]+)[^\s\"',}]+")


def _redact(text: str) -> str:
    text = _BEARER.sub(r"\1<redacted>", text)
    text = _KEYVAL.sub(lambda m: f"{m.group(1)}{m.group(2)}<redacted>", text)
    return text


def get_json(url: str, headers: dict[str, str] | None = None, timeout: float = 30.0) -> Any:
    """GET a URL and parse JSON. Errors are redacted before they surface."""
    try:
        resp = httpx.get(url, headers=headers or {}, timeout=timeout, follow_redirects=True)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:  # httpx errors may embed Authorization headers
        raise RuntimeError(_redact(f"{type(exc).__name__}: {exc}")) from None


def post_json(url: str, body: Any, headers: dict[str, str] | None = None, timeout: float = 30.0) -> Any:
    """POST JSON and parse the response. Errors are redacted."""
    try:
        resp = httpx.post(url, json=body, headers=headers or {}, timeout=timeout, follow_redirects=True)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        raise RuntimeError(_redact(f"{type(exc).__name__}: {exc}")) from None
```

## `szl-v14/src/szl_v14/lib/intoto.py`

<!-- extract: szl-v14/src/szl_v14/lib/intoto.py -->
```python
"""in-toto Statement v1 construction with real byte digests."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from szl_v14.lib.digest import sha256_file

_STATEMENT_TYPE = "https://in-toto.io/Statement/v1"


def statement(
    subjects: Iterable[tuple[str, str | Path]],
    predicate_type: str,
    predicate: dict[str, Any],
) -> dict[str, Any]:
    """Build an in-toto Statement v1.

    subjects: iterable of (name, path); the digest is over the file's bytes.
    """
    return {
        "_type": _STATEMENT_TYPE,
        "subject": [
            {"name": name, "digest": {"sha256": sha256_file(path)}}
            for name, path in subjects
        ],
        "predicateType": predicate_type,
        "predicate": predicate,
    }
```

## `szl-v14/src/szl_v14/lib/jcs.py`

<!-- extract: szl-v14/src/szl_v14/lib/jcs.py -->
```python
"""Canonical JSON per RFC 8785, via the real library. sort_keys is not JCS."""

from __future__ import annotations

import sys
from typing import Any

_INSTALL = "rfc8785 is not installed. Run: pip install rfc8785  (json.dumps with sorted keys is NOT JCS)"


def _lib():
    try:
        import rfc8785  # type: ignore
    except ImportError:
        sys.stderr.write(f"FATAL: {_INSTALL}\n")
        raise SystemExit(2)
    return rfc8785


def canonical(obj: Any) -> str:
    """Serialize obj to its RFC 8785 canonical form."""
    out = _lib().dumps(obj)
    return out.decode("utf-8") if isinstance(out, (bytes, bytearray)) else out


def jcs_digest(obj: Any) -> str:
    """SHA-256 of the canonical form."""
    from szl_v14.lib.digest import sha256_bytes

    return sha256_bytes(canonical(obj).encode("utf-8"))
```

## `szl-v14/src/szl_v14/lib/receipts.py`

<!-- extract: szl-v14/src/szl_v14/lib/receipts.py -->
```python
"""Command receipts — the ONLY place timestamps are allowed."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from szl_v14.lib.digest import sha256_file
from szl_v14.lib.jcs import canonical, jcs_digest


@dataclass
class Receipt:
    cmd: str
    args_digest: str
    inputs: dict[str, str] = field(default_factory=dict)   # path -> sha256
    outputs: dict[str, str] = field(default_factory=dict)  # path -> sha256
    state: str = "UNKNOWN"
    timestamp_utc: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def write(
    root: str | Path,
    cmd: str,
    args: dict[str, Any],
    inputs: dict[str, str] | None = None,
    outputs: dict[str, str] | None = None,
    state: str = "UNKNOWN",
    extra_inputs: list[str | Path] | None = None,
) -> Path:
    """Write receipts/<cmd>-<ts>.json under root and return its path."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    ins = dict(inputs or {})
    for p in extra_inputs or []:
        p = Path(p)
        if p.exists():
            ins[str(p)] = sha256_file(p)
    rcpt = Receipt(
        cmd=cmd,
        args_digest=jcs_digest(args),
        inputs=ins,
        outputs=outputs or {},
        state=state,
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
    )
    outdir = Path(root) / "receipts"
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / f"{cmd.replace(' ', '_')}-{ts}.json"
    path.write_text(canonical(rcpt.to_dict()) + "\n")
    return path
```

## `szl-v14/src/szl_v14/lib/states.py`

<!-- extract: szl-v14/src/szl_v14/lib/states.py -->
```python
"""Evidence states and findings.

PASS | WARN | FAIL | BLOCKED | UNKNOWN. UNKNOWN is never coerced to PASS.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Iterable


class State(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"
    UNKNOWN = "UNKNOWN"


def promote(state: State, target: State) -> State:
    """Promote an evidence state. UNKNOWN can never become PASS."""
    state, target = State(state), State(target)
    if state == State.UNKNOWN and target == State.PASS:
        raise ValueError("UNKNOWN is never coerced to PASS")
    return target


@dataclass
class Finding:
    severity: str  # CRITICAL | HIGH | MEDIUM | LOW | INFO
    code: str
    message: str
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass
class Report:
    cmd: str
    state: State
    findings: list[Finding] = field(default_factory=list)
    outputs: dict[str, str] = field(default_factory=dict)  # path -> sha256
    summary: dict[str, Any] = field(default_factory=dict)


def render_findings(findings: Iterable[Finding]) -> None:
    from rich.console import Console
    from rich.table import Table

    findings = list(findings)
    console = Console()
    if not findings:
        console.print("[green]no findings[/green]")
        return
    table = Table(title="Findings")
    for col in ("severity", "code", "message"):
        table.add_column(col)
    color = {"CRITICAL": "red", "HIGH": "red", "MEDIUM": "yellow",
             "LOW": "cyan", "INFO": "white"}
    for f in findings:
        table.add_row(f"[{color.get(f.severity, 'white')}]{f.severity}[/]",
                      f.code, f.message)
    console.print(table)


def worst_state(findings: Iterable[Finding]) -> State:
    ranking = {"CRITICAL": State.FAIL, "HIGH": State.FAIL,
               "MEDIUM": State.WARN, "LOW": State.WARN, "INFO": State.PASS}
    out = State.PASS
    for f in findings:
        s = ranking.get(f.severity, State.WARN)
        if s == State.FAIL:
            return State.FAIL
        if s == State.WARN:
            out = State.WARN
    return out


def to_jsonable(obj: Any) -> Any:
    if isinstance(obj, (State,)):
        return obj.value
    if isinstance(obj, (Finding, Report)):
        return to_jsonable(asdict(obj))
    if isinstance(obj, dict):
        return {k: to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_jsonable(v) for v in obj]
    return obj


def emit_json(report: Report) -> str:
    return json.dumps(to_jsonable(report), indent=2)
```

## `szl-v14/src/szl_v14/modules/__init__.py`

<!-- extract: szl-v14/src/szl_v14/modules/__init__.py -->
```python
"""Command modules. Every command: --json, receipt, exit codes 0/2/3."""
```

## `szl-v14/src/szl_v14/modules/audit.py`

<!-- extract: szl-v14/src/szl_v14/modules/audit.py -->
```python
"""audit — one audit file per repo from a Jinja template + REPOSITORY_MATRIX.csv.

Fields not probed are UNKNOWN. Never guessed, never carried forward.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from szl_v14.lib.digest import sha256_file
from szl_v14.lib.estate import load_snapshots
from szl_v14.lib.states import Finding, Report, State

FORBIDDEN_DOMAIN = re.compile(r"(?<!-)a11oy\.com")

_TEMPLATE_DIR = Path(__file__).resolve().parents[3] / "templates"

MATRIX_FIELDS = ["name", "visibility", "archived", "default_branch", "language",
                 "license", "pushed_at", "open_prs", "has_pages", "forbidden_refs", "state"]


def _repo_view(r: dict, enrichment: dict | None) -> dict:
    e = enrichment or {}
    text = " ".join(str(r.get(k) or "") for k in ("description", "url")) + " " + str(e.get("homepage") or "")
    return {
        "name": r.get("name", "UNKNOWN"),
        "visibility": r.get("visibility", "UNKNOWN"),
        "archived": r.get("isArchived", "UNKNOWN"),
        "default_branch": (r.get("defaultBranchRef") or {}).get("name", "UNKNOWN"),
        "language": (r.get("primaryLanguage") or {}).get("name", "UNKNOWN"),
        "license": (r.get("licenseInfo") or {}).get("spdxId", "UNKNOWN"),
        "pushed_at": (r.get("pushedAt") or "UNKNOWN")[:10],
        "description": r.get("description") or "UNKNOWN",
        "url": r.get("url", "UNKNOWN"),
        "open_prs": e.get("open_prs", "UNKNOWN"),
        "has_pages": e.get("has_pages", "UNKNOWN"),
        "homepage": e.get("homepage", "UNKNOWN"),
        "topics": [t.get("name") for t in (r.get("repositoryTopics") or [])] or "UNKNOWN",
        "forbidden_refs": len(FORBIDDEN_DOMAIN.findall(text)),
        "state": "FAIL" if FORBIDDEN_DOMAIN.findall(text) else "PASS",
    }


def run(snapshot_dir: Path, out_dir: Path) -> Report:
    snap = load_snapshots(snapshot_dir)
    findings: list[Finding] = []
    audits = out_dir / "audits" / "repos"
    audits.mkdir(parents=True, exist_ok=True)

    enrichment: dict[str, dict] = {}
    edir = snapshot_dir / "github" / "enrichment"
    if edir.is_dir():
        import json as _json
        for f in edir.glob("*.json"):
            try:
                d = _json.loads(f.read_text())
                if d.get("name"):
                    enrichment[d["name"]] = d
            except Exception:
                pass
    else:
        findings.append(Finding("INFO", "NO_ENRICHMENT", "no per-repo enrichment; deep fields are UNKNOWN"))

    env = Environment(loader=FileSystemLoader(str(_TEMPLATE_DIR)),
                      autoescape=select_autoescape(disabled_extensions=("md", "j2")))
    tpl = env.get_template("REPO_AUDIT.j2")

    rows: list[dict] = []
    outputs: dict[str, str] = {}
    for r in sorted(snap.github_repos, key=lambda x: x.get("name", "")):
        view = _repo_view(r, enrichment.get(r.get("name")))
        if view["forbidden_refs"]:
            findings.append(Finding("CRITICAL", "FORBIDDEN_LINK",
                                    f"{view['name']}: forbidden domain reference in metadata"))
        path = audits / f"{view['name']}.md"
        path.write_text(tpl.render(repo=view))
        outputs[str(path)] = sha256_file(path)
        rows.append(view)

    matrix = out_dir / "REPOSITORY_MATRIX.csv"
    with open(matrix, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=MATRIX_FIELDS)
        w.writeheader()
        for v in rows:
            w.writerow({k: v.get(k, "UNKNOWN") for k in MATRIX_FIELDS})
    outputs[str(matrix)] = sha256_file(matrix)

    state = State.FAIL if any(f.severity == "CRITICAL" for f in findings) else (
        State.WARN if findings else State.PASS)
    return Report(cmd="audit", state=state, findings=findings, outputs=outputs,
                  summary={"repos_audited": len(rows),
                           "forbidden_refs": sum(v["forbidden_refs"] for v in rows)})
```

## `szl-v14/src/szl_v14/modules/deploy.py`

<!-- extract: szl-v14/src/szl_v14/modules/deploy.py -->
```python
"""deploy — inspect-only deployment state. No mutation anywhere."""

from __future__ import annotations

from pathlib import Path

from szl_v14.modules.dns import _load_targets
from szl_v14.lib.states import Finding, Report, State


def run(targets: Path | None, probe_file: Path | None) -> Report:
    findings: list[Finding] = []
    rows = []
    try:
        doc = _load_targets(targets)
    except FileNotFoundError as e:
        return Report(cmd="deploy", state=State.UNKNOWN,
                      findings=[Finding("MEDIUM", "MISSING_CONFIG", str(e))])

    for z in doc.get("zones", []):
        rows.append({"zone": z["zone"], "role": z.get("role", "UNKNOWN"),
                     "target": z.get("target_summary", "UNKNOWN"),
                     "notes": z.get("notes", "")})
    findings.append(Finding(
        "INFO", "HSTS_PRELOAD",
        ".dev is HSTS-preloaded: order is DNS -> cert -> curl-verify -> announce; "
        "linking szl.dev before a valid cert exists is a hard browser failure"))
    findings.append(Finding(
        "INFO", "ACCESS_403_OK",
        "never remove Cloudflare Access to turn a 403 into a 200; 403 means Access is working"))
    return Report(cmd="deploy", state=State.PASS, findings=findings,
                  summary={"deployments": rows})
```

## `szl-v14/src/szl_v14/modules/dns.py`

<!-- extract: szl-v14/src/szl_v14/modules/dns.py -->
```python
"""dns — validate targets, print plans, and (never mutate) print authorization packets."""

from __future__ import annotations

import json
from pathlib import Path

import yaml
from jsonschema import validate as js_validate

from szl_v14.lib.states import Finding, Report, State

_TARGETS = Path(__file__).resolve().parents[3] / "dns-targets.yaml"
_SCHEMA = Path(__file__).resolve().parents[3] / "schemas" / "dns_plan.schema.json"


def _load_targets(path: Path | None) -> dict:
    p = path or _TARGETS
    if not p.exists():
        raise FileNotFoundError(f"dns targets file missing: {p}")
    return yaml.safe_load(p.read_text())


def impossible_states(doc: dict) -> list[Finding]:
    """Reject impossible DNS states at compile/validate time, not at 2am."""
    findings: list[Finding] = []
    for z in doc.get("zones", []):
        apex_cnames = [r for r in z.get("records", [])
                       if r.get("type") == "CNAME" and r.get("name") in ("@", z.get("zone"))]
        if apex_cnames and not z.get("apex_cname_flattening", False):
            findings.append(Finding("CRITICAL", "IMPOSSIBLE_DNS",
                                    f"{z['zone']}: apex CNAME without confirmed flattening"))
        others = [r for r in z.get("records", [])
                  if r.get("name") == "@" and r.get("type") != "CNAME"]
        if apex_cnames and others:
            findings.append(Finding("CRITICAL", "IMPOSSIBLE_DNS",
                                    f"{z['zone']}: coexisting records at the CNAME label"))
        targets = {r.get("provider") for r in z.get("records", []) if r.get("provider")}
        if len(targets) > 1:
            findings.append(Finding("HIGH", "MIXED_CANONICAL",
                                    f"{z['zone']}: mixed provider targets {sorted(targets)}"))
        if not z.get("rollback_source"):
            findings.append(Finding("HIGH", "NO_ROLLBACK",
                                    f"{z['zone']}: no rollback source declared"))
        for r in z.get("records", []):
            if r.get("proxied") and str(r.get("content", "")).startswith("185.199."):
                findings.append(Finding("CRITICAL", "PAGES_ORANGE_CLOUD",
                                        f"{z['zone']}: proxied:true on a GitHub Pages IP breaks cert issuance"))
    return findings


def run_validate(targets: Path | None) -> Report:
    try:
        doc = _load_targets(targets)
    except FileNotFoundError as e:
        return Report(cmd="dns validate", state=State.FAIL,
                      findings=[Finding("HIGH", "MISSING_CONFIG", str(e))])
    if _SCHEMA.exists():
        schema = json.loads(_SCHEMA.read_text())
        try:
            js_validate(doc, schema)
        except Exception as e:
            return Report(cmd="dns validate", state=State.FAIL,
                          findings=[Finding("HIGH", "SCHEMA_MISMATCH", str(e)[:300])])
    findings = impossible_states(doc)
    state = State.FAIL if findings else State.PASS
    return Report(cmd="dns validate", state=state, findings=findings,
                  summary={"zones": [z["zone"] for z in doc.get("zones", [])]})


def run_plan(targets: Path | None) -> Report:
    v = run_validate(targets)
    if v.state == State.FAIL:
        v.cmd = "dns plan"
        return v
    doc = _load_targets(targets)
    plans = []
    for z in doc.get("zones", []):
        plans.append({
            "zone": z["zone"], "role": z.get("role", "UNKNOWN"),
            "prechecks": z.get("prechecks", []),
            "records": z.get("records", []),
            "rollback_source": z.get("rollback_source"),
            "rule": "snapshot the zone to the rollback_source BEFORE any write; one record set at a time; poll propagation between sets",
        })
    return Report(cmd="dns plan", state=State.PASS, findings=v.findings,
                  summary={"plans": plans})


def run_apply(targets: Path | None) -> Report:
    """Print the AUTHORIZATION PACKET and stop. Never mutates. R10."""
    plan = run_plan(targets)
    packet = {
        "state": "AWAITING_AUTHORIZATION",
        "warning": "this CLI never mutates; hand this packet to an operator",
        "prechecks_required": [
            "token verified active at /user/tokens/verify with Zone:DNS:Edit + Zone:Zone:Read scoped to target zones",
            "zone exported to rollback bundle on disk BEFORE any write",
            "one record set at a time with propagation polling between sets",
        ],
        "plans": plan.summary.get("plans", []),
    }
    return Report(cmd="dns apply", state=State.BLOCKED, findings=plan.findings,
                  summary=packet)
```

## `szl-v14/src/szl_v14/modules/doctor.py`

<!-- extract: szl-v14/src/szl_v14/modules/doctor.py -->
```python
"""doctor — environment triage. First section: BLOCKERS THAT OUTRANK ALL COSMETIC WORK."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from szl_v14.lib.estate import load_snapshots
from szl_v14.lib.states import Finding, Report, State

BLOCKER_HEADER = "BLOCKERS THAT OUTRANK ALL COSMETIC WORK"

_BINARIES = ["gh", "dig", "jq", "curl", "openssl"]


def run(snapshot_dir: Path) -> Report:
    findings: list[Finding] = []
    blockers: list[str] = []

    if sys.version_info < (3, 12):
        findings.append(Finding("CRITICAL", "PY_VERSION", f"python {sys.version.split()[0]} < 3.12"))

    try:
        import rfc8785  # noqa: F401
    except ImportError:
        findings.append(Finding("CRITICAL", "NO_RFC8785", "real JCS library missing; every digest claim is theater"))

    try:
        import importlib.metadata as md
        v = md.version("huggingface_hub")
        if int(v.split(".")[0]) < 1:
            findings.append(Finding("CRITICAL", "HF_HUB_VERSION", f"huggingface_hub {v} < 1.0 (bucket visibility)"))
    except Exception:
        findings.append(Finding("CRITICAL", "NO_HF_HUB", "huggingface_hub >= 1.0 missing — the only bucket-visible call"))

    for b in _BINARIES:
        if not shutil.which(b):
            findings.append(Finding("HIGH", "MISSING_BINARY", f"{b} not on PATH"))
    if not shutil.which("cosign"):
        findings.append(Finding("LOW", "NO_COSIGN", "cosign absent — signing path stays unsigned-honest until armed"))

    snap = load_snapshots(snapshot_dir)
    if not snap.github_repos:
        findings.append(Finding("CRITICAL", "NO_GH_SNAPSHOT", "github/repos_cli.json missing or empty"))
        blockers.append("GitHub estate snapshot missing")
    if not snap.hf_estate:
        findings.append(Finding("CRITICAL", "NO_HF_SNAPSHOT", "hf/hf_estate.json missing"))
        blockers.append("Hugging Face estate snapshot missing")
    cf = snap.cloudflare_status
    if cf.get("status") == "BLOCKED":
        msg = cf.get("diagnosis", "Cloudflare credential blocked")
        findings.append(Finding("HIGH", "CF_TOKEN_BLOCKED", msg,
                                {"error": cf.get("error"), "needed_scopes": cf.get("needed_scopes")}))
        blockers.append(f"Cloudflare: {msg}")
    if snap.estate_completeness not in ("VERIFIED", "VERIFIED (3 independent sources agree at 100)"):
        findings.append(Finding("MEDIUM", "ESTATE_NOT_VERIFIED",
                                f"estate completeness = {snap.estate_completeness}"))
    for missing in snap.unknown:
        findings.append(Finding("MEDIUM", "SNAPSHOT_MISSING", f"snapshot file missing: {missing}"))

    state = State.FAIL if any(f.severity == "CRITICAL" for f in findings) else (
        State.WARN if findings else State.PASS)
    return Report(cmd="doctor", state=state, findings=findings,
                  summary={"blockers_header": BLOCKER_HEADER, "blockers": blockers,
                           "estate_completeness": snap.estate_completeness})


def render_text(report: Report) -> str:
    lines = [BLOCKER_HEADER, "=" * len(BLOCKER_HEADER), ""]
    if report.summary["blockers"]:
        for b in report.summary["blockers"]:
            lines.append(f"  - {b}")
    else:
        lines.append("  (none)")
    lines.append("")
    lines.append(f"estate completeness: {report.summary['estate_completeness']}")
    lines.append(f"state: {report.state.value}")
    return "\n".join(lines)
```

## `szl-v14/src/szl_v14/modules/export.py`

<!-- extract: szl-v14/src/szl_v14/modules/export.py -->
```python
"""export — bundle a directory: digest manifest (schema-validated), DSSE unsigned envelope, receipt.

Every export gets a manifest; every manifest gets a digest; every bundle records
inputs and outputs. The manifest itself is validated against export_bundle.schema.json.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from jsonschema import validate as js_validate

from szl_v14.lib.digest import digest_map, sha256_file
from szl_v14.lib.dsse import envelope, write_unsigned
from szl_v14.lib.jcs import canonical
from szl_v14.lib.states import Finding, Report, State

FORBIDDEN_DOMAIN = re.compile(r"(?<!-)a11oy\.com")
_SCHEMA = Path(__file__).resolve().parents[3] / "schemas" / "export_bundle.schema.json"


def run(target_dir: Path, out_dir: Path, bundle_name: str = "bundle") -> Report:
    if not target_dir.is_dir():
        return Report(cmd="export", state=State.FAIL,
                      findings=[Finding("HIGH", "MISSING_INPUT", f"no such directory: {target_dir}")])

    files = digest_map(target_dir)
    findings: list[Finding] = []
    for rel in files:
        content = (target_dir / rel).read_text(errors="ignore")
        if FORBIDDEN_DOMAIN.search(content):
            findings.append(Finding("CRITICAL", "FORBIDDEN_LINK",
                                    f"forbidden domain reference in bundle member {rel}"))

    manifest = {"bundle": bundle_name,
                "format": "szl/v14-export-bundle",
                "subjects": [{"name": k, "digest": {"sha256": v}} for k, v in files.items()]}
    if _SCHEMA.exists():
        schema = json.loads(_SCHEMA.read_text())
        try:
            js_validate(manifest, schema)
        except Exception as e:
            return Report(cmd="export", state=State.FAIL,
                          findings=[Finding("HIGH", "SCHEMA_MISMATCH", f"bundle manifest invalid: {str(e)[:300]}")])

    out_dir.mkdir(parents=True, exist_ok=True)
    mpath = out_dir / "manifest.json"
    mpath.write_text(canonical(manifest) + "\n")
    env = envelope(canonical(manifest).encode("utf-8"), payload_type="application/vnd.szl.bundle-manifest+json")
    epath = write_unsigned(env, out_dir / "manifest.unsigned.json")

    outputs = {str(mpath): sha256_file(mpath), str(epath): sha256_file(epath)}
    state = State.FAIL if any(f.severity == "CRITICAL" for f in findings) else State.PASS
    return Report(cmd="export", state=state, findings=findings, outputs=outputs,
                  summary={"files": len(files), "bundle": bundle_name,
                           "manifest_digest": outputs[str(mpath)]})
```

## `szl-v14/src/szl_v14/modules/inventory.py`

<!-- extract: szl-v14/src/szl_v14/modules/inventory.py -->
```python
"""inventory — build repos.yaml from snapshots. Sources disagree -> PARTIAL."""

from __future__ import annotations

from pathlib import Path

import yaml

from szl_v14.lib.digest import sha256_file
from szl_v14.lib.estate import load_snapshots
from szl_v14.lib.states import Finding, Report, State


def run(snapshot_dir: Path, out_dir: Path) -> Report:
    snap = load_snapshots(snapshot_dir)
    findings: list[Finding] = []

    enum = snap.github_enumeration
    srcs = enum.get("sources", {})
    counts = [v for v in srcs.values() if isinstance(v, int)]
    if len(set(counts)) > 1:
        findings.append(Finding("HIGH", "SOURCE_DISAGREE",
                                f"enumeration sources disagree: {srcs}"))
        completeness = "PARTIAL"
    elif not counts:
        completeness = "UNKNOWN"
        findings.append(Finding("MEDIUM", "NO_ENUM", "no enumeration evidence"))
    else:
        completeness = enum.get("estate_completeness", "PARTIAL")
        if completeness != "VERIFIED" and not completeness.startswith("VERIFIED"):
            findings.append(Finding("MEDIUM", "ESTATE_PARTIAL", completeness))

    repos = []
    for r in snap.github_repos:
        repos.append({
            "name": r.get("name"),
            "visibility": r.get("visibility"),
            "archived": r.get("isArchived"),
            "default_branch": (r.get("defaultBranchRef") or {}).get("name"),
            "language": (r.get("primaryLanguage") or {}).get("name"),
            "pushed_at": r.get("pushedAt"),
            "license": (r.get("licenseInfo") or {}).get("spdxId"),
            "description": r.get("description"),
            "url": r.get("url"),
        })

    hf = snap.hf_estate
    doc = {
        "schema": "szl/v14-inventory",
        "estate_completeness": completeness,
        "github": {"org": "szl-holdings", "count": len(repos),
                   "sources": srcs, "repos": repos},
        "huggingface": {"org": "SZLHOLDINGS",
                        "counts": hf.get("counts", {}),
                        "names": hf.get("names", {})},
        "cloudflare": {"status": snap.cloudflare_status.get("status", "UNKNOWN"),
                       "error": snap.cloudflare_status.get("error")},
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "repos.yaml"
    path.write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True))
    state = State.WARN if findings else State.PASS
    return Report(cmd="inventory", state=state, findings=findings,
                  outputs={str(path): sha256_file(path)},
                  summary={"github_repos": len(repos), "hf": hf.get("counts", {}),
                           "estate_completeness": completeness})
```

## `szl-v14/src/szl_v14/modules/mcp.py`

<!-- extract: szl-v14/src/szl_v14/modules/mcp.py -->
```python
"""mcp — attestation fixtures. Deny-on-drift: exit 2 on any drift.

The two fixtures that matter most:
1. A whitespace-only canonical-equivalent JSON pair MUST produce zero drift.
   If it drifts, the JCS implementation is fake.
2. A refusal phrase followed by leaked data nets -3.0, not +1.5 - 3.0.
"""

from __future__ import annotations

import json

from szl_v14.lib.jcs import canonical, jcs_digest
from szl_v14.lib.states import Finding, Report, State


def _refusal_leak_score(text: str, refusal_reward: float = 1.5, leak_penalty: float = -3.0) -> float:
    """Refusal-then-leak nets -3.0 exactly; no cancelling arithmetic."""
    refused = text.strip().lower().startswith(("i cannot", "i can't", "i'm unable", "sorry, i can"))
    leaked = "SECRET" in text or "canary" in text.lower()
    if leaked:
        return leak_penalty  # leak dominates; refusal earns nothing
    if refused:
        return refusal_reward
    return 0.0


def run() -> Report:
    findings: list[Finding] = []

    # Fixture 1: canonical equivalence -> zero drift.
    a = {"b": [1, 2], "a": "x"}
    b_text = '{ "a" : "x", "b" : [ 1, 2 ] }'
    b = json.loads(b_text)
    if canonical(a) != canonical(b) or jcs_digest(a) != jcs_digest(b):
        findings.append(Finding("CRITICAL", "JCS_DRIFT",
                                "whitespace-only canonical-equivalent pair produced drift — JCS is not real"))
    else:
        findings.append(Finding("INFO", "JCS_OK", "canonical-equivalent pair: zero drift (real RFC 8785)"))

    # Fixture 2: refusal-then-leak nets -3.0.
    score = _refusal_leak_score("I cannot share that. SECRET=42 canary")
    if score != -3.0:
        findings.append(Finding("CRITICAL", "REWARD_HACK",
                                f"refusal-then-leak scored {score} != -3.0 — reward-hacking hole open"))
    else:
        findings.append(Finding("INFO", "REFUSAL_OK", "refusal-then-leak nets -3.0; no +1.5 offset"))

    state = State.FAIL if any(f.severity == "CRITICAL" for f in findings) else State.PASS
    return Report(cmd="mcp", state=state, findings=findings,
                  summary={"fixtures": 2, "policy": "deny-on-drift, exit 2"})
```

## `szl-v14/src/szl_v14/modules/provenance.py`

<!-- extract: szl-v14/src/szl_v14/modules/provenance.py -->
```python
"""provenance — in-toto statement + honestly unsigned DSSE envelope for a directory."""

from __future__ import annotations

from pathlib import Path

from szl_v14.lib.digest import sha256_file
from szl_v14.lib.dsse import envelope, write_unsigned
from szl_v14.lib.intoto import statement
from szl_v14.lib.jcs import canonical
from szl_v14.lib.states import Finding, Report, State


def run(target_dir: Path, out_dir: Path, predicate_type: str = "https://szl.dev/predicates/provenance/v1") -> Report:
    if not target_dir.is_dir():
        return Report(cmd="provenance", state=State.FAIL,
                      findings=[Finding("HIGH", "MISSING_INPUT", f"no such directory: {target_dir}")])
    subjects = [(p.relative_to(target_dir).as_posix(), p)
                for p in sorted(target_dir.rglob("*")) if p.is_file()]
    stmt = statement(subjects, predicate_type, {"builder": {"id": "szl-v14 provenance"}})

    out_dir.mkdir(parents=True, exist_ok=True)
    stmt_path = out_dir / "statement.intoto.json"
    stmt_path.write_text(canonical(stmt) + "\n")
    env = envelope(canonical(stmt).encode("utf-8"))
    env_path = write_unsigned(env, out_dir / "payload.unsigned.json")

    return Report(cmd="provenance", state=State.PASS,
                  outputs={str(stmt_path): sha256_file(stmt_path),
                           str(env_path): sha256_file(env_path)},
                  summary={"subjects": len(subjects),
                           "signing": "unsigned (signatures: []); honest naming enforced"})
```

## `szl-v14/src/szl_v14/modules/remediate.py`

<!-- extract: szl-v14/src/szl_v14/modules/remediate.py -->
```python
"""remediate — findings JSON -> ORDERED plan. Credentials -> DNS -> origin-host -> code -> cosmetic."""

from __future__ import annotations

import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from szl_v14.lib.digest import sha256_file
from szl_v14.lib.states import Finding, Report, State

_TEMPLATE_DIR = Path(__file__).resolve().parents[3] / "templates"

_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}
_LANE = {"CF_TOKEN_BLOCKED": 0, "NO_HF_HUB": 0, "MISSING_BINARY": 0,
         "PAGES_ORANGE_CLOUD": 1, "IMPOSSIBLE_DNS": 1,
         "TUNNEL_1033": 2, "ESTATE_PARTIAL": 2,
         "FORBIDDEN_LINK": 3, "CLAIM_DRIFT": 3}


def run(findings_json: Path, out_dir: Path) -> Report:
    if not findings_json.exists():
        return Report(cmd="remediate", state=State.UNKNOWN,
                      findings=[Finding("MEDIUM", "NO_FINDINGS", f"missing: {findings_json}")])
    raw = json.loads(findings_json.read_text())
    items = raw if isinstance(raw, list) else raw.get("findings", [])
    items.sort(key=lambda f: (_ORDER.get(f.get("severity", "INFO"), 4),
                              _LANE.get(f.get("code", ""), 4)))

    plan = []
    for i, f in enumerate(items, 1):
        plan.append({"order": i, "severity": f.get("severity"), "code": f.get("code"),
                     "action": f.get("message"),
                     "verify": f.get("verify", "re-run the producing command; state must improve or stay honestly UNKNOWN")})

    out_dir.mkdir(parents=True, exist_ok=True)
    env = Environment(loader=FileSystemLoader(str(_TEMPLATE_DIR)),
                      autoescape=select_autoescape(disabled_extensions=("md", "j2")))
    path = out_dir / "REMEDIATION_PLAN.md"
    path.write_text(env.get_template("REPORT.j2").render(title="Remediation plan", plan=plan, items=plan))
    return Report(cmd="remediate", state=State.PASS,
                  outputs={str(path): sha256_file(path)},
                  summary={"items": len(plan)})
```

## `szl-v14/src/szl_v14/modules/verify_claims.py`

<!-- extract: szl-v14/src/szl_v14/modules/verify_claims.py -->
```python
"""verify-claims — re-measure published claims; mismatch -> CLAIM_DRIFT."""

from __future__ import annotations

from pathlib import Path

import yaml

from szl_v14.lib.estate import load_snapshots
from szl_v14.lib.states import Finding, Report, State

_CLAIMS_FILE = Path(__file__).resolve().parents[3] / "claims.yaml"


def _measure(claim: dict, snapshot_dir: Path):
    """Return measured value, or None when the claim is UNMEASURABLE here."""
    kind = claim.get("measure", {}).get("kind")
    snap = load_snapshots(snapshot_dir)
    if kind == "github_repo_count":
        return len(snap.github_repos) if snap.github_repos else None
    if kind == "github_visibility_count":
        vis = claim["measure"]["visibility"].upper()
        return sum(1 for r in snap.github_repos
                   if isinstance(r.get("visibility"), str)
                   and r["visibility"].upper() == vis) if snap.github_repos else None
    if kind == "hf_repo_count":
        rtype = claim["measure"]["repo_type"]
        return snap.hf_estate.get("counts", {}).get(rtype)
    if kind == "github_repo_present":
        if "github/repos_cli.json" in snap.unknown:
            return None
        return claim["measure"]["repo"] in {r.get("name") for r in snap.github_repos}
    return None


def _invalid_claims(reason: str) -> Report:
    return Report(cmd="verify-claims", state=State.FAIL,
                  findings=[Finding("HIGH", "INVALID_CLAIMS", reason)])


def _valid_claim(claim: object) -> bool:
    if not isinstance(claim, dict):
        return False
    if any(not isinstance(claim.get(key), str) or not claim[key].strip()
           for key in ("id", "claim")) or "expected" not in claim:
        return False
    measure = claim.get("measure")
    if not isinstance(measure, dict):
        return False
    kind = measure.get("kind")
    if not isinstance(kind, str) or not kind.strip():
        return False
    if kind in {"github_repo_count", "github_visibility_count", "hf_repo_count"}:
        if type(claim["expected"]) is not int or claim["expected"] < 0:
            return False
    if kind == "github_visibility_count":
        visibility = measure.get("visibility")
        return isinstance(visibility, str) and visibility.upper() in {"PUBLIC", "PRIVATE", "INTERNAL"}
    if kind == "hf_repo_count":
        repo_type = measure.get("repo_type")
        return isinstance(repo_type, str) and repo_type in {"model", "dataset", "space"}
    if kind == "github_repo_present":
        repo = measure.get("repo")
        return type(claim["expected"]) is bool and isinstance(repo, str) and bool(repo.strip())
    # A future nonempty measurement kind remains UNMEASURABLE, never PASS.
    return True


def run(snapshot_dir: Path, claims_path: Path | None = None) -> Report:
    claims_path = claims_path or _CLAIMS_FILE
    findings: list[Finding] = []
    results = []
    if not claims_path.exists():
        return Report(cmd="verify-claims", state=State.UNKNOWN,
                      findings=[Finding("MEDIUM", "NO_CLAIMS", f"claims file missing: {claims_path}")])

    try:
        claims = yaml.safe_load(claims_path.read_text())
    except OSError:
        return Report(cmd="verify-claims", state=State.UNKNOWN,
                      findings=[Finding("MEDIUM", "CLAIMS_UNAVAILABLE", "claims file could not be read")])
    except (yaml.YAMLError, UnicodeError, ValueError, RecursionError):
        return _invalid_claims("claims file could not be parsed")
    if claims is None or (isinstance(claims, list) and not claims):
        return Report(cmd="verify-claims", state=State.UNKNOWN,
                      findings=[Finding("MEDIUM", "NO_CLAIMS", "claims file contains no claims")])
    if not isinstance(claims, list):
        return _invalid_claims("claims document must be a nonempty list")
    seen = set()
    for index, claim in enumerate(claims, start=1):
        if not _valid_claim(claim):
            return _invalid_claims(f"claim {index} has an invalid schema")
        if claim["id"] in seen:
            return _invalid_claims(f"claim {index} repeats a claim id")
        seen.add(claim["id"])
    for c in claims:
        measured = _measure(c, snapshot_dir)
        if measured is None:
            results.append({"id": c.get("id"), "state": "UNMEASURABLE", "claim": c.get("claim")})
            continue
        expected = c.get("expected")
        ok = measured == expected
        results.append({"id": c.get("id"), "claim": c.get("claim"), "expected": expected,
                        "measured": measured, "state": "PASS" if ok else "FAIL"})
        if not ok:
            findings.append(Finding("HIGH", "CLAIM_DRIFT",
                                    f"{c.get('id')}: published {expected!r} != measured {measured!r}",
                                    {"claim": c.get("claim"), "source": c.get("source")}))

    passed = sum(1 for r in results if r["state"] == "PASS")
    drifted = sum(1 for r in results if r["state"] == "FAIL")
    unmeasurable = sum(1 for r in results if r["state"] == "UNMEASURABLE")
    state = State.FAIL if drifted else (State.WARN if unmeasurable else State.PASS)
    return Report(cmd="verify-claims", state=state, findings=findings,
                  summary={"pass": passed, "claim_drift": drifted,
                           "unmeasurable": unmeasurable, "results": results})
```

## `szl-v14/templates/DNS_PLAN.j2`

<!-- extract: szl-v14/templates/DNS_PLAN.j2 -->
```jinja
# DNS plan: {{ zone }}

role: {{ role }}

## Prechecks
{% for p in prechecks -%}
- {{ p }}
{% endfor %}

## Records
| type | name | content | proxied | ttl |
|---|---|---|---|---|
{% for r in records -%}
| {{ r.type }} | {{ r.name }} | {{ r.content }} | {{ r.proxied | default(false) }} | {{ r.ttl | default(300) }} |
{% endfor %}

## Rollback
source: {{ rollback_source }}
Rule: export the zone to the rollback source BEFORE any write; one record set at
a time; poll propagation between sets.
```

## `szl-v14/templates/OPERATOR_PACKET.j2`

<!-- extract: szl-v14/templates/OPERATOR_PACKET.j2 -->
````jinja
# OPERATOR PACKET

Everything else in the export tree is supporting evidence for this page.
Every one of the fifteen answers below is mandatory; an omission is a FAIL.

1. Verified (digests): {{ verified | default('UNKNOWN') }}
2. Fixed (post-fix verification): {{ fixed | default('UNKNOWN') }}
3. Remaining failures (finding codes): {{ failing | default('UNKNOWN') }}
4. Blocked on credentials (exact scope): {{ blocked_credentials | default('UNKNOWN') }}
5. Exact DNS record diff proposed: {{ dns_diff | default('UNKNOWN') }}
6. Exact rollback records: {{ rollback | default('UNKNOWN') }}
7. Exact next safe command: {{ next_command | default('UNKNOWN') }}
8. Per-domain DNS state: {{ dns_state | default('UNKNOWN') }}
9. Per-domain TLS state: {{ tls_state | default('UNKNOWN') }}
10. Per-domain app state: {{ app_state | default('UNKNOWN') }}
11. Forbidden-domain references remaining (must be 0): {{ forbidden_refs | default('UNKNOWN') }}
12. V11 artifacts (verified / regressed / unknown, with SHAs): {{ v11 | default('UNKNOWN') }}
13. Estate completeness: {{ estate_completeness | default('UNKNOWN') }}
14. Claims: pass {{ claims_pass | default('?') }}, CLAIM_DRIFT {{ claims_drift | default('?') }}, UNMEASURABLE {{ claims_unmeasurable | default('?') }}
15. publication_eligible: {{ publication_eligible | default('False') }} — false inputs: {{ eligibility_blockers | default('UNKNOWN') }}

## Per-phase block

```
STATUS:           <PASS|WARN|FAIL|BLOCKED|UNKNOWN>
EVIDENCE:         <paths + digests>
ROLLBACK:         <file + records, or "n/a — read-only phase">
NEXT SAFE ACTION: <one command>
RECEIPT:          <path>
```
````

## `szl-v14/templates/RECEIPT.j2`

<!-- extract: szl-v14/templates/RECEIPT.j2 -->
```jinja
# Receipt: {{ cmd }}

- state: {{ state }}
- timestamp_utc: {{ timestamp_utc }}
- args_digest: {{ args_digest }}
- inputs: {{ inputs | length }} file(s)
- outputs: {{ outputs | length }} file(s)
{% for path, digest in outputs.items() -%}
- {{ path }} — sha256:{{ digest }}
{% endfor %}
```

## `szl-v14/templates/REPORT.j2`

<!-- extract: szl-v14/templates/REPORT.j2 -->
```jinja
# {{ title }}

| order | severity | code | action | verify |
|---|---|---|---|---|
{% for i in items -%}
| {{ i.order }} | {{ i.severity }} | {{ i.code }} | {{ i.action }} | {{ i.verify }} |
{% endfor %}
```

## `szl-v14/templates/REPO_AUDIT.j2`

<!-- extract: szl-v14/templates/REPO_AUDIT.j2 -->
```jinja
# Repo audit: {{ repo.name }}

| Field | Value |
|---|---|
| url | {{ repo.url }} |
| visibility | {{ repo.visibility }} |
| archived | {{ repo.archived }} |
| default_branch | {{ repo.default_branch }} |
| language | {{ repo.language }} |
| license | {{ repo.license }} |
| pushed_at | {{ repo.pushed_at }} |
| open_prs | {{ repo.open_prs }} |
| has_pages | {{ repo.has_pages }} |
| homepage | {{ repo.homepage }} |
| topics | {{ repo.topics }} |
| forbidden_refs | {{ repo.forbidden_refs }} |
| state | {{ repo.state }} |

description: {{ repo.description }}

Unprobed fields are UNKNOWN by construction — never guessed, never carried forward.
```

## `szl-v14/tests/test_digest.py`

<!-- extract: szl-v14/tests/test_digest.py -->
```python
from szl_v14.lib.digest import sha256_file, sha256_bytes, digest_map

# known sha256 vector over real bytes
ABC = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def test_sha256_bytes_known_vector():
    assert sha256_bytes(b"abc") == ABC


def test_sha256_file_hashes_bytes_not_name(tmp_path):
    p = tmp_path / "SZLHOLDINGS"  # a name that must NOT be hashed
    p.write_bytes(b"abc")
    assert sha256_file(p) == ABC
    # and the name itself hashes to something different
    assert sha256_file(p) != sha256_bytes(b"SZLHOLDINGS")


def test_digest_map_relative(tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "f.txt").write_bytes(b"abc")
    m = digest_map(tmp_path)
    assert m == {"a/f.txt": ABC}
```

## `szl-v14/tests/test_dns.py`

<!-- extract: szl-v14/tests/test_dns.py -->
```python
from szl_v14.modules.dns import impossible_states


def _zone(**kw):
    base = {"zone": "example.net", "records": [], "rollback_source": "rb.json"}
    base.update(kw)
    return base


def test_apex_cname_without_flattening_is_rejected():
    doc = {"zones": [_zone(records=[{"type": "CNAME", "name": "@", "content": "hf.space."}])]}
    codes = [f.code for f in impossible_states(doc)]
    assert "IMPOSSIBLE_DNS" in codes


def test_apex_cname_with_flattening_passes():
    doc = {"zones": [_zone(apex_cname_flattening=True,
                           records=[{"type": "CNAME", "name": "@", "content": "hf.space."}])]}
    assert impossible_states(doc) == []


def test_proxied_pages_ip_is_rejected():
    doc = {"zones": [_zone(records=[{"type": "A", "name": "@", "content": "185.199.108.153",
                                     "proxied": True}])]}
    codes = [f.code for f in impossible_states(doc)]
    assert "PAGES_ORANGE_CLOUD" in codes


def test_unproxied_pages_ip_plus_rollback_passes():
    doc = {"zones": [_zone(records=[{"type": "A", "name": "@", "content": "185.199.108.153",
                                     "proxied": False}])]}
    assert impossible_states(doc) == []


def test_missing_rollback_source_flagged():
    z = _zone()
    del z["rollback_source"]
    doc = {"zones": [z]}
    assert "NO_ROLLBACK" in [f.code for f in impossible_states(doc)]
```

## `szl-v14/tests/test_dsse.py`

<!-- extract: szl-v14/tests/test_dsse.py -->
```python
import pytest

from szl_v14.lib.dsse import envelope, write_unsigned, verify_unsigned


def test_envelope_is_honestly_unsigned():
    env = envelope(b"payload")
    assert env["signatures"] == []
    assert env["payloadType"]


def test_write_unsigned_enforces_naming(tmp_path):
    env = envelope(b"x")
    with pytest.raises(ValueError):
        write_unsigned(env, tmp_path / "payload.json")  # wrong name -> error
    p = write_unsigned(env, tmp_path / "payload.unsigned.json")
    assert verify_unsigned(p)["signatures"] == []


def test_named_unsigned_but_claims_signatures_fails(tmp_path):
    env = envelope(b"x")
    env["signatures"] = [{"sig": "abc"}]
    with pytest.raises(ValueError):
        write_unsigned(env, tmp_path / "payload.unsigned.json")


def test_verify_rejects_empty_sigs_without_unsigned_name(tmp_path):
    env = envelope(b"x")
    p = tmp_path / "payload.json"
    p.write_text(__import__("json").dumps(env))
    with pytest.raises(ValueError):
        verify_unsigned(p)
```

## `szl-v14/tests/test_export.py`

<!-- extract: szl-v14/tests/test_export.py -->
```python
import json

from szl_v14.lib.digest import sha256_file, digest_map
from szl_v14.lib.states import State
from szl_v14.modules import export as m_export


def test_bundle_manifest_validates_and_digests_match(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.txt").write_text("alpha")
    (src / "b.txt").write_text("beta")
    out = tmp_path / "out"
    report = m_export.run(src, out, "t")
    assert report.state == State.PASS
    manifest = json.loads((out / "manifest.json").read_text())
    subjects = {s["name"]: s["digest"]["sha256"] for s in manifest["subjects"]}
    assert subjects == digest_map(src)
    # unsigned envelope present and honest
    env = json.loads((out / "manifest.unsigned.json").read_text())
    assert env["signatures"] == []


def test_forbidden_domain_in_bundle_is_critical(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "bad.md").write_text("see https://a11oy" + ".com for details")
    report = m_export.run(src, tmp_path / "out", "t")
    assert report.state == State.FAIL
    assert any(f.code == "FORBIDDEN_LINK" for f in report.findings)


def test_missing_dir_fails(tmp_path):
    assert m_export.run(tmp_path / "nope", tmp_path / "o", "t").state == State.FAIL
```

## `szl-v14/tests/test_jcs.py`

<!-- extract: szl-v14/tests/test_jcs.py -->
```python
import json

from szl_v14.lib.jcs import canonical, jcs_digest


def test_canonical_orders_keys_and_strips_whitespace():
    obj = {"b": [1, 2], "a": "x"}
    assert canonical(obj) == '{"a":"x","b":[1,2]}'


def test_whitespace_equivalent_docs_have_identical_digest():
    """The real-JCS proof: formatting-only differences produce zero drift."""
    a = {"z": 1, "a": [True, None]}
    b = json.loads('{ "a" : [ true , null ] , "z" : 1 }')
    assert canonical(a) == canonical(b)
    assert jcs_digest(a) == jcs_digest(b)


def test_unicode_and_numbers_are_rfc8785():
    # RFC 8785 serializes non-ASCII unescaped and integers without decoration
    assert canonical({"é": 1}) == '{"é":1}'
```

## `szl-v14/tests/test_states.py`

<!-- extract: szl-v14/tests/test_states.py -->
```python
import pytest

from szl_v14.lib.states import State, promote, worst_state, Finding


def test_unknown_never_promotes_to_pass():
    with pytest.raises(ValueError):
        promote(State.UNKNOWN, State.PASS)


def test_unknown_can_be_acknowledged_but_not_passed():
    assert promote(State.UNKNOWN, State.BLOCKED) == State.BLOCKED


def test_worst_state_critical_is_fail():
    assert worst_state([Finding("CRITICAL", "X", "y")]) == State.FAIL


def test_worst_state_info_is_pass():
    assert worst_state([Finding("INFO", "X", "y")]) == State.PASS
```


## `szl-v14/tests/test_deploy_config.py`

<!-- extract: szl-v14/tests/test_deploy_config.py -->
```python
"""Read-only deployment inspection reports missing inputs without a crash."""
from szl_v14.lib.states import State
from szl_v14.modules import deploy, dns


def test_missing_explicit_targets_is_unknown(tmp_path):
    report = deploy.run(tmp_path / "absent.yaml", None)
    assert report.state == State.UNKNOWN
    assert report.findings[0].code == "MISSING_CONFIG"


def test_missing_default_targets_is_unknown(tmp_path, monkeypatch):
    monkeypatch.setattr(dns, "_TARGETS", tmp_path / "absent-default.yaml")
    report = deploy.run(None, None)
    assert report.state == State.UNKNOWN
    assert report.findings[0].code == "MISSING_CONFIG"


def test_valid_targets_are_loaded_once(monkeypatch):
    calls = []
    def load(path):
        calls.append(path)
        return {"zones": [{"zone": "example.test", "role": "demo", "target_summary": "offline"}]}
    monkeypatch.setattr(deploy, "_load_targets", load)
    report = deploy.run(None, None)
    assert calls == [None]
    assert report.state == State.PASS
    assert report.summary["deployments"] == [{"zone": "example.test", "role": "demo", "target": "offline", "notes": ""}]
```


## `szl-v14/tests/test_verify_claims_admission.py`

<!-- extract: szl-v14/tests/test_verify_claims_admission.py -->
```python
"""A claim report requires actual, well-formed claims before measuring."""
import json
from pathlib import Path

import pytest
import yaml

from szl_v14.lib.states import State, emit_json
from szl_v14.modules import verify_claims


def claim(**changes):
    return {"id": "repo-count", "claim": "Repository count", "expected": 1,
            "measure": {"kind": "github_repo_count"}, **changes}


def run(tmp_path, text):
    path = tmp_path / "claims.yaml"
    path.write_text(text)
    root = tmp_path / "snapshots"
    (root / "github").mkdir(parents=True, exist_ok=True)
    (root / "github/repos_cli.json").write_text(json.dumps([{"name": "known", "visibility": "PUBLIC"}]))
    return verify_claims.run(root, path)


@pytest.mark.parametrize("text", ["", "# no claims\n", "null", "[]"])
def test_empty_document_is_unknown_without_measurement(tmp_path, monkeypatch, text):
    monkeypatch.setattr(verify_claims, "_measure", lambda *args: pytest.fail("empty claims measured"))
    report = run(tmp_path, text)
    assert report.state == State.UNKNOWN
    assert report.findings[0].code == "NO_CLAIMS"


@pytest.mark.parametrize("document", [False, 0, "claims", {}, {"id": "mapping"},
    [None], [1], ["claim"], [False], [{}], [claim(id="")], [claim(id=[])],
    [claim(claim="")], [claim(claim=0)], [claim(measure=None)],
    [claim(measure=[])], [claim(measure={})], [claim(measure={"kind": 1})],
    [claim(expected=True)], [claim(expected="1")], [claim(expected=-1)],
    [claim(expected=float("nan"))], [claim(expected=float("inf"))],
    [claim(measure={"kind": "github_visibility_count"})],
    [claim(measure={"kind": "github_visibility_count", "visibility": []})],
    [claim(measure={"kind": "hf_repo_count", "repo_type": {}})],
    [claim(measure={"kind": "github_repo_present", "repo": "known"}, expected=1)],
    [claim(measure={"kind": "github_repo_present", "repo": []}, expected=True)],
    [claim(), claim()],
])
def test_malformed_claim_set_fails_before_any_measurement(tmp_path, monkeypatch, document):
    monkeypatch.setattr(verify_claims, "_measure", lambda *args: pytest.fail("invalid claim set measured"))
    report = run(tmp_path, yaml.safe_dump(document))
    assert report.state == State.FAIL
    assert report.findings[0].code == "INVALID_CLAIMS"
    json.loads(emit_json(report))


def test_missing_expected_and_invalid_later_claim_cannot_partially_pass(tmp_path, monkeypatch):
    incomplete = claim(id="second")
    del incomplete["expected"]
    monkeypatch.setattr(verify_claims, "_measure", lambda *args: pytest.fail("partially admitted claims"))
    assert run(tmp_path, yaml.safe_dump([claim(), incomplete])).state == State.FAIL


@pytest.mark.parametrize("text", ["[unterminated", "- id: one\n  measure: [unclosed"])
def test_yaml_syntax_error_is_a_report_not_a_traceback(tmp_path, text):
    report = run(tmp_path, text)
    assert report.state == State.FAIL
    assert report.findings[0].code == "INVALID_CLAIMS"


def test_missing_file_preserves_unknown(tmp_path):
    report = verify_claims.run(tmp_path, tmp_path / "absent.yaml")
    assert report.state == State.UNKNOWN
    assert report.findings[0].code == "NO_CLAIMS"


def test_unreadable_file_is_unknown(tmp_path):
    report = verify_claims.run(tmp_path, tmp_path)
    assert report.state == State.UNKNOWN
    assert report.findings[0].code == "CLAIMS_UNAVAILABLE"


def test_valid_pass_drift_and_future_measure_kind_preserve_states(tmp_path):
    good = run(tmp_path, yaml.safe_dump([claim()]))
    assert good.state == State.PASS and good.summary["pass"] == 1
    drift = run(tmp_path, yaml.safe_dump([claim(expected=2)]))
    assert drift.state == State.FAIL and drift.summary["claim_drift"] == 1
    future = run(tmp_path, yaml.safe_dump([claim(measure={"kind": "future_metric"})]))
    assert future.state == State.WARN and future.summary["unmeasurable"] == 1


def test_missing_snapshot_cannot_prove_repository_absence(tmp_path):
    path = tmp_path / "claims.yaml"
    path.write_text(yaml.safe_dump([claim(expected=False, measure={"kind": "github_repo_present", "repo": "absent"})]))
    report = verify_claims.run(tmp_path / "missing", path)
    assert report.state == State.WARN
    assert report.summary["unmeasurable"] == 1


def test_present_empty_snapshot_can_prove_repository_absence(tmp_path):
    path = tmp_path / "claims.yaml"
    path.write_text(yaml.safe_dump([claim(expected=False, measure={"kind": "github_repo_present", "repo": "absent"})]))
    (tmp_path / "github").mkdir()
    (tmp_path / "github/repos_cli.json").write_text("[]")
    report = verify_claims.run(tmp_path, path)
    assert report.state == State.PASS and report.summary["pass"] == 1


@pytest.mark.parametrize("visibility", ["public", "PuBlIc"])
@pytest.mark.parametrize("expected,state", [(1, State.PASS), (0, State.FAIL)])
def test_visibility_admission_and_measurement_use_the_same_case(tmp_path, visibility, expected, state):
    report = run(tmp_path, yaml.safe_dump([claim(
        measure={"kind": "github_visibility_count", "visibility": visibility}, expected=expected)]))
    assert report.state == state
    assert report.summary["results"][0]["measured"] == 1
```

---
