# Generic Getting Started

`mb3r-stack` is the generic integration bundle for connecting:

- Bering as the discovery and publishing side
- Sheaft as the downstream artifact consumer
- OTLP-based producers or artifact-based producers around that contract

The core chart lives at `charts/mb3r-stack`. It does not assume OpenTelemetry Demo, Astronomy Shop, or any other benchmark application.

## Core Interfaces

- OTLP ingest into Bering over HTTP on port `4318`
- artifact handoff from Bering to Sheaft through the published latest snapshot path
- optional public service aliases for stable producer/consumer DNS names
- optional collector snippets for OTLP-capable collectors

## Minimal Install

The smallest bundled profile is `examples/profiles/synthetic-otlp/values.yaml`:

```bash
helm upgrade --install mb3r ./charts/mb3r-stack \
  -f examples/profiles/synthetic-otlp/values.yaml
```

That profile enables both Bering and Sheaft, uses the generic artifact handoff inside the chart, and exposes stable public contract services `bering-discovery` and `sheaft-reports`.

## First-User Path

For first-time evaluation, use this sequence:

1. Install `synthetic-otlp`.
2. Send the checked-in synthetic OTLP payload to the `bering-discovery` service.
3. Confirm Bering writes the latest snapshot artifact.
4. Confirm Sheaft consumes that artifact and publishes a report.
5. Use `minimal-production-eval` only after the synthetic path works, because it assumes an external collector and a more production-like topology.

The expected product outcome is a visible Bering -> Sheaft handoff and a Sheaft posture report. The OTel Demo profile is a showcase path, not the first proof of generic readiness.

The current packaged bundle line is `v0.3.0`, which stages these release assets during `make release-dry-run`:

- `dist/charts/mb3r-stack-0.3.0.tgz`
- `dist/assets/mb3r-assets-0.3.0.tgz`
- `dist/release-manifest.json`

## Next Steps

- Use `docs/profiles/synthetic-otlp.md` for the smallest generic path.
- Use `docs/profiles/minimal-production-eval.md` for a conservative external-collector profile.
- Use `docs/profiles/otel-demo.md` only when you explicitly want the OpenTelemetry Demo showcase.
- Use `docs/verification/generic-smoke.md` and `docs/verification/generic-e2e.md` to verify generic readiness.
