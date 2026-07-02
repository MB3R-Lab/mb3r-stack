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

## Verification Evidence

A bundle can move from `candidate` to `verified` only when stack-level runtime evidence exists in addition to upstream version and digest pins.

Required evidence:

- chart lint and render for the generic bundle;
- live generic OTLP ingest through Bering;
- stable artifact handoff from Bering to Sheaft;
- Sheaft batch report generation from the handed-off artifact;
- Sheaft `serve` startup and current-report/current-diff availability;
- pinned-image startup from the published upstream GHCR digests;
- adapter e2e coverage for GitHub, GitLab, and Jenkins v1alpha1 payloads;
- release evidence identifying Kubernetes version, profile, upstream app versions, image digests, and contract lines.

OpenTelemetry Demo can be part of the evidence set, but it is not sufficient by itself because it is a showcase profile rather than the core compatibility path.

## Current Bundle

`mb3r-stack` `1.0.0` is currently a draft stack entry for:

- Bering `1.0.0`
- Sheaft `1.0.0`

That bundle is marked `todo-verify` because the upstream v1 release manifests and immutable image digests are not published yet. The intended v1 pairing keeps the stack-level adapter envelopes on `v1alpha1` while aligning the Bering-to-Sheaft artifact handoff on the Bering `1.3.0` model/snapshot schema line and Sheaft's v1 stochastic-connectivity consumer semantics.

The previous published stack bundle `0.3.4` remains in the compatibility matrix as a historical `candidate` entry for Bering `0.3.4` and Sheaft `0.2.4`.

OpenTelemetry Demo can be used as one profile and one acceptance scenario, but it does not widen the formal compatibility statement on its own.
