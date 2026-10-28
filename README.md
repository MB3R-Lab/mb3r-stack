# mb3r-stack

[![release](https://img.shields.io/badge/release-v1.2.0-blue)](https://github.com/MB3R-Lab/mb3r-stack/releases/tag/v1.2.0)
[![checks](https://img.shields.io/github/actions/workflow/status/MB3R-Lab/mb3r-stack/ci.yml?branch=main&label=checks)](https://github.com/MB3R-Lab/mb3r-stack/actions/workflows/ci.yml)
[![bundle](https://img.shields.io/badge/bundle-1.3.0_candidate-orange)](https://github.com/MB3R-Lab/mb3r-stack/blob/main/compat/stack-manifest.json)

The working `1.3.0` candidate targets Bering `1.1.1`, Sheaft `1.3.2`, and a new
Procrustes source pin. Bering and Sheaft commits and image digests match their
published release manifests. Complete stack verification and review are pending;
this candidate is not a verified stack release.
The latest published stack remains `1.2.0`.

## Related MB3R repositories

[Procrustes](https://github.com/MB3R-Lab/Procrustes) owns static preflight before trace collection; [Bering](https://github.com/MB3R-Lab/Bering) owns discovery and artifact publishing; [Sheaft v1.3.2](https://github.com/MB3R-Lab/Sheaft/releases/tag/v1.3.2) owns downstream resilience analysis and CI/CD gating. This repository integrates all three tools.

`mb3r-stack` is the MB3R integration and distribution repository.

It is not another core engine and it does not vendor Procrustes, Bering, or Sheaft source code. This repository sits above the upstream products and owns the bundle layer:

- stack-level compatibility metadata
- a source-pinned Procrustes launcher and static-preflight handoff
- OCI-distributed Helm installation for the generic stack bundle
- OTLP and artifact handoff integration helpers
- versioned dashboards and observability examples
- reusable CI adapters for GitHub, GitLab, and Jenkins

## What This Repo Releases

A stack release publishes:

- an OCI-publishable Helm chart: `mb3r-stack`
- a packaged asset archive with collector/dashboard/examples, the Procrustes launcher, its instructions, and the stack manifest
- `stack-manifest.json`
- `compatibility-matrix.json`
- `release-manifest.json`
- `release-manifest.schema.json`
- `release-notes.md`
- `SHA256SUMS.txt`
- a CycloneDX SBOM for the packaged release assets

## What This Repo Does Not Own

- Bering discovery engine source code
- Procrustes static-analysis engine source code
- Sheaft simulation or gate engine source code
- application business logic
- the canonical release cadence of upstream Bering or Sheaft artifacts

Candidate bundle metadata is marked `todo-verify` for the target pairing. The
historical `1.2.0` entry retains its verified Procrustes `0.1.0`, Bering `1.0.0`
and Sheaft `1.3.1` pins and evidence. Procrustes remains a separately source-pinned
preflight stage; no OCI artifact is invented for its preview.

## External eBPF source

The chart forwards `bering.config.sources` to Bering. The opt-in
[OBI source profile](examples/profiles/ebpf-obi/README.md) documents the raw
collector handoff, collection-domain semantics and capture storage. OBI runs
separately on Linux; this chart keeps Bering unprivileged. The candidate profile
awaits the finalized release pins and integration evidence.

## Static preflight

```bash
python scripts/procrustes.py --example
```

This builds the pinned Procrustes and checks a static fixture; it does not deploy an application. For your own inputs and Bering overlay handoff, see [Procrustes setup](docs/procrustes.md). The launcher is also included in the release asset archive. The chart deploys Bering and Sheaft; Procrustes is an operator-invoked stage before trace collection.

The [three-tool reproduction repository](https://github.com/MB3R-Lab/mb3r-software-complex-repro) owns paper experiments and reference results, not this integration repository.

## Research and Evidence

- Formal model: [Stochastic Connectivity as the Foundation of a Runtime Model for Microservice Availability Analysis](https://www.alphaxiv.org/abs/2607.00740)
- DeathStarBench empirical anchor: [Model Discovery and Graph Simulation: A Lightweight Gateway to Chaos Engineering](https://www.alphaxiv.org/abs/2506.11176)
- OpenTelemetry Demo async-semantics case study: [Evaluating Asynchronous Semantics in Trace-Discovered Resilience Models: A Case Study on the OpenTelemetry Demo](https://www.alphaxiv.org/abs/2512.12314v1)

Planned packaged assets for the `1.3.0` candidate are:

- `dist/charts/mb3r-stack-1.3.0.tgz`
- `dist/assets/mb3r-assets-1.3.0.tgz`
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
make smoke-failure-tolerance
make e2e-failure-tolerance
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

After release pins are finalized, `make k8s-smoke-generic` checks the live
generic runtime contract with the selected release binaries, and
`make k8s-smoke-generic-pinned` checks the chart's immutable image references.
The pending candidate must not be used for these checks until its TODO pins are
resolved. The default pull path is anonymous; optional `MB3R_GHCR_USERNAME` and
`MB3R_GHCR_TOKEN` remain available for authenticated pulls.

The default chart analysis remains schema `1.0` and warn-only. To opt into Sheaft `v1.3.1` confidence-certified sweeps and a minimum-boundary gate, layer [examples/profiles/failure-tolerance/values.yaml](examples/profiles/failure-tolerance/values.yaml) over a base profile. See [docs/profiles/failure-tolerance.md](docs/profiles/failure-tolerance.md).

## Compatibility Notes

The compatibility files in `compat/` are the source of truth for stack-level
assertions. The new `1.3.0` entry is `todo-verify`. The `1.2.0` entry and its
published integration evidence remain historical verified records. The new
source feature does not inherit that verification automatically.

## License

MIT, see [LICENSE](LICENSE).
