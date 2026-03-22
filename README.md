# mb3r-stack

[![Release](https://img.shields.io/github/v/release/MB3R-Lab/mb3r-stack)](https://github.com/MB3R-Lab/mb3r-stack/releases)
[![release](https://img.shields.io/github/actions/workflow/status/MB3R-Lab/mb3r-stack/release.yml?branch=main&label=release)](https://github.com/MB3R-Lab/mb3r-stack/actions/workflows/release.yml)
[![ci](https://img.shields.io/github/actions/workflow/status/MB3R-Lab/mb3r-stack/ci.yml?branch=main&label=ci)](https://github.com/MB3R-Lab/mb3r-stack/actions/workflows/ci.yml)
[![Status](https://img.shields.io/badge/status-candidate-orange)](https://github.com/MB3R-Lab/mb3r-stack/releases/tag/v0.3.0)
[![Upstream pins](https://img.shields.io/badge/Bering%20%7C%20Sheaft-0.3.1%20%7C%200.2.1-blue)](https://github.com/MB3R-Lab/mb3r-stack/blob/main/compat/stack-manifest.json)
[![Adapter contracts](https://img.shields.io/badge/adapter_contracts-v1alpha1-blue)](https://github.com/MB3R-Lab/mb3r-stack/blob/main/compat/compatibility-matrix.json)

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

Current bundle candidate pins published upstream artifacts explicitly: Bering `0.3.1` and Sheaft `0.2.1`, including immutable image digests and contract evidence in `compat/`.

Current packaged release assets for `v0.3.0` are:

- `dist/charts/mb3r-stack-0.3.0.tgz`
- `dist/assets/mb3r-assets-0.3.0.tgz`
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

The compatibility files in `compat/` are the source of truth for stack-level assertions. The current `0.3.0` bundle is recorded as a `candidate` integration statement backed by upstream release manifests, live generic smoke evidence, and Sheaft's published compatibility manifest, not as a broader verified operations guarantee. OpenTelemetry Demo remains one example profile and one acceptance scenario, not the design center of the core bundle.

## Backlog

The GitHub issue backlog was checked on `2026-03-22`. The only open repository issue is [#20](https://github.com/MB3R-Lab/mb3r-stack/issues/20), tracking migration away from deprecated Node.js 20 GitHub Actions runtimes. This branch updates the workflows to `actions/checkout@v6`, `actions/setup-python@v6`, and `azure/setup-helm@v4.3.1`; once CI on `main` is green, that issue can be closed.

## License

MIT, see [LICENSE](LICENSE).
