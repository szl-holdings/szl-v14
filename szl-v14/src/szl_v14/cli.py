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
