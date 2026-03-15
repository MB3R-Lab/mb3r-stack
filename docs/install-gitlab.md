# Install On GitLab

GitLab CI/CD Catalog-compatible component files live in the repository root `templates/` directory because GitLab expects that layout for component projects.

This repository also keeps GitLab-oriented docs and examples under `ci/gitlab/`.

Available components:

- `bering-discover`
- `sheaft-gate`
- `mb3r-report`

## Consumption Model

The components are wrappers around upstream Bering and Sheaft releases. Consumers pass explicit commands, image references, and output directories. The components emit dotenv variables and artifacts that downstream jobs can consume.

## Minimal Include Example

See `examples/gitlab/.gitlab-ci.yml` for a minimal include-based pipeline.

Use component references pinned by tag, for example:

```yaml
include:
  - component: $CI_SERVER_FQDN/group/mb3r-stack/bering-discover@v0.2.0
```

Keep the tag aligned with the `mb3r-stack` integration bundle release, not with any upstream Bering or Sheaft release number.
