# VERSIONING

`mb3r-stack` uses SemVer for the integration bundle itself.

## Scope Of The Version

The `mb3r-stack` version covers:

- the `mb3r-stack` chart version
- the stack manifest contract
- the compatibility matrix format and assertions
- the packaged collector, dashboard, and example asset packs
- the GitHub, GitLab, and Jenkins adapter contracts
- the packaged Procrustes launcher and its static preflight handoff

It does not redefine upstream Procrustes, Bering, or Sheaft versioning. The separate reproduction repository also has its own release lifecycle; it is not a second version of this stack.

## Rules

`MAJOR`

- incompatible changes to manifest shape, adapter contracts, or bundle install behavior

`MINOR`

- backwards-compatible new adapters, dashboards, example overlays, or chart features

`PATCH`

- backwards-compatible fixes to packaging, docs, examples, and validation

## Upstream Pins

Upstream Bering and Sheaft versions must be pinned in `compat/stack-manifest.json`.
Procrustes is also pinned there by version and exact source commit. It is source-built until an upstream release image exists; do not invent an OCI pin.

If a pin is unknown, keep it explicit with `TODO-*` placeholders and mark the compatibility state conservatively in `compat/compatibility-matrix.json`.

## Tagging

Repository tags should use `v<semver>`, for example `v0.3.3`.

The current bundle line is GA integration packaging. Minor releases may advance a compatible upstream component while preserving the bundle's manifest and adapter contracts; the compatibility matrix must record the exact pairing and evidence.
