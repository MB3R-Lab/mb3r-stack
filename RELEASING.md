# RELEASING

This repository releases integration artifacts, not application binaries.

The canonical source of truth is the local `dist/` payload plus `dist/release-manifest.json`. GitHub Releases and OCI chart publication are publishing surfaces around that payload.

## Release Outputs

Each stack release is expected to publish:

- `mb3r-stack-<version>.tgz`
- `mb3r-assets-<version>.tgz`
- `stack-manifest.json`
- `compatibility-matrix.json`
- `release-manifest.json`
- `release-manifest.schema.json`
- `release-notes.md`
- `SHA256SUMS.txt`
- `sbom.cdx.json`

## Pre-Release Checklist

The `1.3.0` candidate pins published upstream releases and an exact Procrustes
source revision. Complete stack verification remains pending. The strict
source-pin schema rejects unresolved commits; never weaken it or invent a
digest. Update chart/profile/adapter pins together from actual upstream release
manifests, then run the complete checklist below.

1. Update `compat/stack-manifest.json`.
2. Update `compat/compatibility-matrix.json`.
3. Confirm upstream release manifests, chart references, and image digests match the chosen Bering and Sheaft releases. Pin Procrustes to an exact source commit and verify its packaged launcher.
4. Confirm dashboard and collector asset versions match the manifest.
5. Run:

```bash
python -m pip install -r requirements.txt
make validate
make release-dry-run
```

6. Review the generated files in `dist/`.
7. Require successful stack CI on the release revision, including `make e2e-procrustes`, adapter/failure-tolerance checks, and pinned-image live Kubernetes startup. Runtime integration checks run in GitHub Actions; packaging alone is not compatibility evidence.

For the eBPF source feature, also verify that the `ebpf-obi` profile renders the
exact declared source configuration, preserves Bering's security context, and
hands a model produced through the source endpoint to Sheaft. Record the actual
upstream collector acceptance evidence separately from the stack checks.

## Publishing

The canonical packaging logic lives in `scripts/`.

GitHub release automation consumes those scripts to:

- package the Helm chart
- package the asset archive
- generate checksums
- generate a CycloneDX SBOM
- publish the chart to an OCI registry
- attach release assets to the tagged release

## OCI Chart Publication

The chart is intended to be pushed with Helm to an OCI registry:

```bash
helm push dist/charts/mb3r-stack-<version>.tgz oci://<registry>/<namespace>/charts
```

Local dry runs do not require Helm, but CI installs Helm and performs `helm lint` plus OCI publication on release tags.
