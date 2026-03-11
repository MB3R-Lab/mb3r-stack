# Compatibility

This repository is the integration layer for MB3R stack releases. It is not the source of truth for Bering or Sheaft core logic.

The machine-readable compatibility contract is split across:

- `compat/stack-manifest.json`
- `compat/compatibility-matrix.json`

## Principles

- Pin upstream versions explicitly.
- Pin image tags and digests explicitly.
- Pin chart, dashboard, and config pack versions explicitly.
- Do not invent compatibility statements.
- Use `TODO-*` placeholders until upstream releases are verified together.

## Conservative Status Values

- `todo-verify`: candidate bundle definition only
- `candidate`: internally staged and awaiting broader verification
- `verified`: supported integration statement
- `deprecated`: retained for history but no longer the preferred bundle
