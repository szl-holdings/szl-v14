#!/usr/bin/env python3
"""Bootstrap tool: wrap a real source tree into sections/90_control_plane.md.

Run ONCE after the control-plane tree changes shape during authoring:
    python tools/sync_sections.py ../szl-v14

After the wrap, sections/90_control_plane.md IS the source of truth and is
edited by hand; `build.py extract` must reproduce the tree byte-for-byte.
Files whose content contains triple backticks get longer fences so the
extractor's fence regex stays unambiguous.
"""
import sys
from pathlib import Path

LANG = {".py": "python", ".toml": "toml", ".md": "markdown", ".json": "json",
        ".j2": "jinja", ".yaml": "yaml", ".yml": "yaml", ".sh": "bash",
        ".cfg": "ini", ".txt": "text"}
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", "dist", "build", ".venv",
             ".ruff_cache", ".mypy_cache", ".tox", "node_modules"}
SKIP_FILES = {"BUILD_REPORT.md"}


def fence_for(content: str) -> str:
    n = 3
    while "`" * n in content:
        n += 1
    return "`" * n


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    tree = Path(sys.argv[1] if len(sys.argv) > 1 else "../szl-v14").resolve()
    prefix = sys.argv[2] if len(sys.argv) > 2 else "szl-v14"
    if not tree.is_dir():
        sys.exit(f"tree not found: {tree}")
    files = []
    for p in sorted(tree.rglob("*")):
        if not p.is_file():
            continue
        if any(part in SKIP_DIRS or part.endswith(".egg-info") for part in p.parts):
            continue
        if p.name in SKIP_FILES or p.suffix == ".pyc":
            continue
        files.append(p)

    out = ["# §90 Control plane — szl-v14 (machine-wrapped source of truth)", "",
           "Every file below is written to `dist/extracted/` by `build.py extract`.",
           "Edit here, not in `dist/`. Regenerate only when the tree changes shape.", ""]
    for p in files:
        rel = p.relative_to(tree).as_posix()
        content = p.read_text()
        f = fence_for(content)
        mode = " mode=755" if p.suffix == ".sh" else ""
        lang = LANG.get(p.suffix, "text")
        out.append(f"## `{prefix}/{rel}`")
        out.append("")
        out.append(f"<!-- extract: {prefix}/{rel}{mode} -->")
        out.append(f"{f}{lang}")
        out.append(content.rstrip("\n"))
        out.append(f)
        out.append("")
    dest = root / "sections" / "90_control_plane.md"
    dest.write_text("\n".join(out))
    print(f"sync_sections: wrapped {len(files)} files -> {dest}")


if __name__ == "__main__":
    main()
