# mb3r-stack

`mb3r-stack` is the MB3R integration and distribution repository.

It is not a third core engine and it does not vendor Bering or Sheaft source code. This repository sits above the upstream products and owns the bundle layer:

- stack-level compatibility metadata
- OCI-distributed Helm installation for the addon bundle
- OpenTelemetry collector integration overlays
- versioned dashboards and observability examples
- reusable CI adapters for GitHub, GitLab, and Jenkins

## What This Repo Releases

A stack release publishes:

- an OCI-publishable Helm chart: `mb3r-otel-addon`
- a packaged asset archive with `collector/`, `dashboards/`, and `examples/`
- `stack-manifest.json`
- `compatibility-matrix.json`
- `SHA256SUMS.txt`
- a CycloneDX SBOM for the packaged release assets

## What This Repo Does Not Own

- Bering discovery engine source code
- Sheaft simulation or gate engine source code
- application business logic
- the canonical release cadence of upstream Bering or Sheaft artifacts

Upstream Bering and Sheaft releases are pinned here conservatively through manifests and placeholders until the integration contract is verified against released upstream artifacts.

## Repository Layout

- `charts/` Helm bundle chart source.
- `compat/` stack manifest and machine-readable compatibility matrix.
- `collector/` OpenTelemetry collector snippets and overlays.
- `dashboards/` versioned Grafana dashboard JSON.
- `examples/` example values files and CI consumer examples.
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
make stack-manifest
make chart-package
make package-assets
make release-dry-run
```

Direct Python equivalents are also available:

```bash
python scripts/tasks.py validate
python scripts/tasks.py release-dry-run
```

## Compatibility Notes

The compatibility files in `compat/` are the source of truth for stack-level assertions. Where upstream certainty is not yet established, fields are kept as explicit `TODO-*` placeholders instead of inventing unsupported compatibility claims.
