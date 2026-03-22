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

`mb3r-stack` `0.3.0` currently tracks:

- Bering `0.3.1`
- Sheaft `0.2.1`

That bundle is marked `candidate` because the pins are backed by published upstream release metadata and strict contract alignment, while broader operational verification remains outside this repository's release contract. The current upstream pairing keeps the stack-level adapter envelopes on `v1alpha1` while aligning the Bering-to-Sheaft artifact handoff on the published `io.mb3r.bering.model` and `io.mb3r.bering.snapshot` schema lines for both `1.0.0` and `1.1.0`. That still does not change the formal maturity of the bundle or the upstream preview status of Sheaft serve/watch behavior.

OpenTelemetry Demo can be used as one profile and one acceptance scenario, but it does not widen the formal compatibility statement on its own.
