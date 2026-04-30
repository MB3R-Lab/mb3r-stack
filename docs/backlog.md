# Backlog

This document is a dated snapshot of the GitHub issue backlog for `MB3R-Lab/mb3r-stack`.

Source of truth: GitHub Issues in the repository itself.

Snapshot date: `2026-05-01`

## Open issues

At the time of this snapshot there are six open issues:

- [#20](https://github.com/MB3R-Lab/mb3r-stack/issues/20) `Migrate GitHub Actions workflows off deprecated Node.js 20 actions`
- [#21](https://github.com/MB3R-Lab/mb3r-stack/issues/21) `[P0] Define verified-bundle acceptance criteria`
- [#22](https://github.com/MB3R-Lab/mb3r-stack/issues/22) `[P0] Publish first-user synthetic-otlp path from install to Sheaft report`
- [#23](https://github.com/MB3R-Lab/mb3r-stack/issues/23) `[P1] Add profile maturity matrix for synthetic-otlp, minimal-production-eval, and otel-demo`
- [#24](https://github.com/MB3R-Lab/mb3r-stack/issues/24) `[P1] Add CI adapter maturity and contract notes for GitHub, GitLab, and Jenkins`
- [#25](https://github.com/MB3R-Lab/mb3r-stack/issues/25) `[P1] Attach release evidence for stack-level runtime confidence`

## Current status

- The repository has already moved `actions/checkout` to `v6` and `actions/setup-python` to `v6`.
- `azure/setup-helm@v4.3.1` still emits the GitHub Node.js 20 deprecation annotation.
- `ci` run `23407592947` for commit `ce14aef6dd2ee99571a7ef4d6a211f9cf9173aba` succeeded functionally but did not satisfy the backlog acceptance criteria for issue `#20`.
- Issue `#20` remains open until `.github/workflows/ci.yml` and `.github/workflows/release.yml` stop using a Node 20-based Helm setup action or otherwise run without the annotation.

## Product capability backlog

The issue tracker remains the source of truth for committed implementation tasks. The following backlog items capture the product work needed for `mb3r-stack` to move from a candidate integration bundle to a stronger first-user and pilot surface.

### Verified bundle milestone

Tracker: [#21](https://github.com/MB3R-Lab/mb3r-stack/issues/21)

Current bundle status is `candidate`, backed by explicit upstream pins and smoke evidence, not by a broad operational compatibility statement.

Backlog outcome:

- define the evidence required to promote a bundle from `candidate` to `verified`;
- record which Kubernetes versions, install profiles, image pull paths, and artifact handoff modes were exercised;
- make the compatibility matrix distinguish "contract aligned" from "operationally verified";
- keep OpenTelemetry Demo as a showcase profile, not the proof of generic readiness.

### First-user path

Tracker: [#22](https://github.com/MB3R-Lab/mb3r-stack/issues/22)

The repository has working profiles, but the product path still reads like an integration kit.

Backlog outcome:

- maintain one copy-paste path from Helm install to Bering artifact to Sheaft report;
- make `synthetic-otlp` the smallest supported path and `minimal-production-eval` the recommended pilot path;
- keep the OTel Demo profile documented as optional showcase-only material;
- publish the expected report and gate outputs for the minimal path.

### Profile maturity

Tracker: [#23](https://github.com/MB3R-Lab/mb3r-stack/issues/23)

The stack needs clearer maturity boundaries per profile.

Backlog outcome:

- define maturity states for `synthetic-otlp`, `minimal-production-eval`, and `otel-demo`;
- document which profile proves rendering, live OTLP ingest, artifact handoff, Sheaft batch, Sheaft serve, metrics, and pinned-image startup;
- add profile-specific troubleshooting for image pull, collector routing, and missing artifact handoff.

### Adapter maturity

Tracker: [#24](https://github.com/MB3R-Lab/mb3r-stack/issues/24)

GitHub, GitLab, and Jenkins adapters currently wrap upstream tools and exchange artifacts through v1alpha1 payload shapes.

Backlog outcome:

- publish adapter maturity and compatibility notes per CI system;
- keep report paths, artifact names, dotenv outputs, and gate decision fields stable across examples;
- add a migration note before changing adapter contract fields;
- ensure the combined report workflow produces a useful single summary artifact for downstream jobs.

### Release evidence

Tracker: [#25](https://github.com/MB3R-Lab/mb3r-stack/issues/25)

Release assets exist, but stack-level product confidence depends on tying them to runnable evidence.

Backlog outcome:

- attach release evidence for chart render, generic smoke, adapter e2e, and pinned-image startup to each release;
- ensure release manifests identify upstream Bering and Sheaft app versions, image digests, chart versions, and contract lines;
- keep candidate/verified status conservative until runtime evidence catches up with the metadata pins.

## Near-term priority

1. [#20](https://github.com/MB3R-Lab/mb3r-stack/issues/20): Resolve CI/release Node.js 20 deprecation annotations.
2. [#21](https://github.com/MB3R-Lab/mb3r-stack/issues/21): Define verified-bundle acceptance criteria in `docs/compatibility.md`.
3. [#22](https://github.com/MB3R-Lab/mb3r-stack/issues/22): Add a first-user path summary that starts from `synthetic-otlp` and ends with a Sheaft report.
4. [#23](https://github.com/MB3R-Lab/mb3r-stack/issues/23): Add profile maturity notes for `synthetic-otlp`, `minimal-production-eval`, and `otel-demo`.
5. [#24](https://github.com/MB3R-Lab/mb3r-stack/issues/24): Add adapter maturity notes for GitHub, GitLab, and Jenkins.
6. [#25](https://github.com/MB3R-Lab/mb3r-stack/issues/25): Attach release evidence for stack-level runtime confidence.
