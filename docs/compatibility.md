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

## Candidate 1.4.0 Bundle

Current main pins published Bering `v1.2.0` and Sheaft `v1.3.2` with unchanged Bering model/snapshot `1.3.0` contracts. The chart exposes `bering.config.runtime.publicationMode` (default `windowed`) and `bering.config.runtime.reconciliation.enabled` (default `true`). To use Bering's opt-in `on_shutdown` publication, set both `publicationMode: on_shutdown` and `reconciliation.enabled: false`. This collects one batch until shutdown; the external orchestrator must permit finalization to complete. Full stack integration verification is pending. The `1.3.0` entry below retains its original pins and evidence.

## Verified 1.3.0 Bundle

The verified `1.3.0` bundle pins Bering `1.1.1`, Sheaft `1.3.2` and an updated
Procrustes source revision. Bering's
commit and image digest match its published `1.1.1` release manifest; Sheaft pins
match its published `1.3.2` manifest. [Complete stack CI passed](https://github.com/MB3R-Lab/mb3r-stack/actions/runs/40640730443)
at revision `a456508ac1be4ccd34437d101ec7a4084b95f517`.
Sheaft's own release checkpoint names Bering `1.1.0`; the stack independently
checks the pinned `1.1.1` producer against the same unchanged `1.3.0` contracts.
The [OBI source profile](../examples/profiles/ebpf-obi/README.md) passed
source-enabled Helm rendering and runtime handoff checks alongside native OTLP,
adapters, pinned-image Kubernetes startup, failure tolerance and release dry-run.
Its external collector installation remains separate from stack wiring checks.

## Published 1.2.0 Bundle

`mb3r-stack` `1.2.0` is a verified stack entry for:

- Bering `1.0.0`
- Sheaft `1.3.1`
- Procrustes `0.1.0` at an exact source commit, built by the packaged launcher

Procrustes adds a static preflight and an explicit Bering overlay handoff; it is
not a long-running chart service. Its absence from older entries is historical.
The current bundle additionally requires ready/blocked preflight checks and
successful Bering ingestion of the generated overlay from the extracted asset pack.

The verified entry is supported by the upstream release manifests, immutable multi-arch image digests, stack release dry-run, synthetic-otlp handoff, opt-in failure-tolerance e2e, pinned-image startup, and adapter e2e evidence in [the integration run](https://github.com/MB3R-Lab/mb3r-stack/actions/runs/38727806505). The pairing keeps stack adapter envelopes on `v1alpha1` and the Bering-to-Sheaft handoff on the immutable Bering `1.3.0` model/snapshot line. Sheaft analysis schema `1.2` is consumer-owned and does not require a new Bering contract.

The default chart remains warn-only on Sheaft analysis schema `1.0`. Failure-tolerance gating is an explicit profile overlay because endpoint ids, SLOs, trial budgets, and required margins are environment-specific. Capacity and overload prediction remain outside the verified claim.

The published `1.0.0` bundle remains in the matrix as a historical verified entry for Bering `1.0.0` and Sheaft `1.0.0`.

The previous published stack bundle `0.3.4` remains in the compatibility matrix as a historical `candidate` entry for Bering `0.3.4` and Sheaft `0.2.4`.

OpenTelemetry Demo can be used as one profile and one acceptance scenario, but it does not widen the formal compatibility statement on its own.
