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
