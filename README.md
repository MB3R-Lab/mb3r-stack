# mb3r-stack

[![release](https://img.shields.io/github/v/release/MB3R-Lab/mb3r-stack?label=release)](https://github.com/MB3R-Lab/mb3r-stack/releases)
[![checks](https://img.shields.io/github/actions/workflow/status/MB3R-Lab/mb3r-stack/ci.yml?branch=main&label=checks)](https://github.com/MB3R-Lab/mb3r-stack/actions/workflows/ci.yml)
[![bundle](https://img.shields.io/badge/bundle-verified-brightgreen)](https://github.com/MB3R-Lab/mb3r-stack/blob/main/compat/stack-manifest.json)

## Related MB3R repositories

[Bering](https://github.com/MB3R-Lab/Bering) owns discovery and artifact publishing; [Sheaft](https://github.com/MB3R-Lab/Sheaft) owns downstream resilience analysis and CI/CD gating. This repository packages compatible releases and integration assets above both projects.

`mb3r-stack` is the MB3R integration and distribution repository.

It is not a third core engine and it does not vendor Bering or Sheaft source code. This repository sits above the upstream products and owns the bundle layer:

- stack-level compatibility metadata
- OCI-distributed Helm installation for the generic stack bundle
- OTLP and artifact handoff integration helpers
- versioned dashboards and observability examples
- reusable CI adapters for GitHub, GitLab, and Jenkins

## What This Repo Releases

A stack release publishes:

- an OCI-publishable Helm chart: `mb3r-stack`
- a packaged asset archive with `collector/`, `dashboards/`, and `examples/`
- `stack-manifest.json`
- `compatibility-matrix.json`
- `release-manifest.json`
- `release-manifest.schema.json`
- `release-notes.md`
- `SHA256SUMS.txt`
- a CycloneDX SBOM for the packaged release assets

## What This Repo Does Not Own

- Bering discovery engine source code
- Sheaft simulation or gate engine source code
- application business logic
- the canonical release cadence of upstream Bering or Sheaft artifacts

Current bundle metadata is verified for the Bering `1.0.0` and Sheaft `1.0.0` major line. It records the v1 stack contract and immutable GHCR image digests for the upstream releases.

## Research and Evidence

- Formal model: [Stochastic Connectivity as the Foundation of a Runtime Model for Microservice Availability Analysis](https://www.alphaxiv.org/abs/2607.00740)
- DeathStarBench empirical anchor: [Model Discovery and Graph Simulation: A Lightweight Gateway to Chaos Engineering](https://www.alphaxiv.org/abs/2506.11176)
- OpenTelemetry Demo async-semantics case study: [Evaluating Asynchronous Semantics in Trace-Discovered Resilience Models: A Case Study on the OpenTelemetry Demo](https://www.alphaxiv.org/abs/2512.12314v1)

Expected packaged release assets for `v1.0.0` are:

- `dist/charts/mb3r-stack-1.0.0.tgz`
- `dist/assets/mb3r-assets-1.0.0.tgz`
- `dist/release-manifest.json`
- `dist/SHA256SUMS.txt`
- `dist/sbom.cdx.json`

## Repository Layout

- `charts/` Helm bundle chart source.
- `compat/` stack manifest and machine-readable compatibility matrix.
- `collector/` generic OTLP/collector snippets.
- `dashboards/` versioned Grafana dashboard JSON.
- `examples/profiles/` reusable profile-specific values and optional collector patches.
- `examples/` also contains CI consumer examples.
- `ci/github/` GitHub adapter docs and notes.
- `ci/gitlab/` GitLab adapter docs; catalog-compatible components live in top-level `templates/`.
- `ci/jenkins/` Jenkins Shared Library base path.
- `docs/` install and integration guides.
- `schemas/` JSON schemas for release metadata.
- `scripts/` platform-neutral validation and packaging entrypoints.
- `.github/workflows/` reusable workflows plus repo CI/release automation.
- `templates/` GitLab CI/CD Catalog-compatible component definitions.

## Local Commands

Install the Python dependencies once:

```bash
python -m pip install -r requirements.txt
```

Primary local entrypoints:

```bash
make lint
make validate
make smoke-generic
make e2e-generic
make k8s-smoke-generic
make k8s-smoke-generic-pinned
make e2e-adapters
make smoke-otel-demo
make e2e-otel-demo
make stack-manifest
make chart-package
make package-assets
make release-dry-run
```

Direct Python equivalents are also available:

```bash
python scripts/tasks.py validate
python scripts/tasks.py e2e-generic
python scripts/tasks.py k8s-smoke-generic-pinned
python scripts/tasks.py e2e-adapters
python scripts/tasks.py release-dry-run
```

`make k8s-smoke-generic` verifies the live generic runtime contract with locally rebuilt images from the pinned release binaries. `make k8s-smoke-generic-pinned` verifies the clean-cluster startup path for the chart's default pinned `ghcr.io/mb3r-lab/bering` and `ghcr.io/mb3r-lab/sheaft` images. The default path is now anonymous pull against public GHCR packages; optional `MB3R_GHCR_USERNAME` and `MB3R_GHCR_TOKEN` are still supported when you need to validate an authenticated pull path explicitly.

## Compatibility Notes

The compatibility files in `compat/` are the source of truth for stack-level assertions. The current `1.0.0` bundle entry is `verified` against Bering and Sheaft v1 release manifests, immutable GHCR digests, stack release dry-run, live synthetic-otlp smoke, pinned-image startup, and adapter e2e evidence. OpenTelemetry Demo remains one example profile and one acceptance scenario, not the design center of the core bundle.

## License

MIT, see [LICENSE](LICENSE).
