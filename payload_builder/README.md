# payload_builder

The thing that builds the payload. `sections/` are the source of truth;
`dist/` is a derived artifact. Never hand-edit `dist/` — if you do, the sha256
in the build receipt becomes a lie, which is the name-hash defect at the
document layer.

## Verbs

| Command | Effect |
|---|---|
| `python build.py generate` | Scaffold any missing section stubs from `manifest.toml`. Idempotent; never overwrites. |
| `python build.py compile` | Hard gates: section order (`require_dns_first`), `must_contain` tokens, forbidden-pattern lint, banned-claims lint. Exit 1 on any violation. |
| `python build.py extract` | Write every `<!-- extract: path mode=755 -->` code fence to `dist/extracted/`. Path-escape checked. Duplicate targets are a compile error. |
| `python build.py export` | Assemble `dist/SZL_MASTER_PAYLOAD_V14.md` (inline per-section digests), `manifest.json`, DSSE `payload.unsigned.json` (`signatures: []`), `statement.intoto.json`, and a timestamped build receipt (the only place time appears). |
| `python build.py verify` | Re-digest everything, assert unsigned-naming honesty, grep the payload for the forbidden domain, assert `publication_eligible` is false. Exit 1 on failure. |
| `python build.py all` | compile → extract → export. No destructive apply exists anywhere in this build. |
| `make idempotent` | Prove a byte-identical rebuild (build → copy → rebuild → `diff -q`). |

## Deps

Python 3.12+, `rfc8785` (`pip install rfc8785`). Nothing else.

## Layout

```
manifest.toml          # explicit section order — never a glob
sections/              # the source
lint/forbidden.txt     # antipattern regexes -> compile FAIL
lint/banned_claims.txt # claim-language regexes -> compile FAIL
build.py               # the six verbs
tools/sync_sections.py # bootstrap: wrap a real tree into sections/90_control_plane.md
dist/                  # derived. digests here are promises.
```
