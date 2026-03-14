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
- Use `TODO-*` placeholders only when a required upstream pin or digest is not yet available.

## Conservative Status Values

- `todo-verify`: candidate bundle definition only
- `candidate`: internally staged and awaiting broader verification
- `verified`: supported integration statement
- `deprecated`: retained for history but no longer the preferred bundle

## Current Bundle

`mb3r-stack` `0.1.0` currently tracks:

- Bering `0.1.0`
- Sheaft `0.1.1`

That bundle is marked `candidate` because the pins are backed by published upstream release metadata and strict contract alignment, while broader operational verification remains outside this repository's release contract.
