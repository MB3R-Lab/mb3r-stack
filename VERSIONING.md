# VERSIONING

`mb3r-stack` uses SemVer for the integration bundle itself.

## Scope Of The Version

The `mb3r-stack` version covers:

- the `mb3r-otel-addon` chart version
- the stack manifest contract
- the compatibility matrix format and assertions
- the packaged collector, dashboard, and example asset packs
- the GitHub, GitLab, and Jenkins adapter contracts

It does not redefine upstream Bering or Sheaft versioning.

## Rules

`MAJOR`

- incompatible changes to manifest shape, adapter contracts, or bundle install behavior

`MINOR`

- backwards-compatible new adapters, dashboards, example overlays, or chart features

`PATCH`

- backwards-compatible fixes to packaging, docs, examples, and validation

## Upstream Pins

Upstream Bering and Sheaft versions must be pinned in `compat/stack-manifest.json`.

If a pin is unknown, keep it explicit with `TODO-*` placeholders and mark the compatibility state conservatively in `compat/compatibility-matrix.json`.

## Tagging

Repository tags should use `v<semver>`, for example `v0.1.0`.

The initial bundle is `0.1.0`, which should be treated as pre-GA integration packaging.
