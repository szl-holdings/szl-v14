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
