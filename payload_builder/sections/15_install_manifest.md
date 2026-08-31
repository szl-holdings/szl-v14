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
