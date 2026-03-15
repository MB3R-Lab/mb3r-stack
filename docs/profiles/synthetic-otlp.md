# Synthetic OTLP Profile

This is the smallest reusable profile in the repository.

- values: `examples/profiles/synthetic-otlp/values.yaml`
- sample OTLP payload: `examples/profiles/synthetic-otlp/payload.json`
- optional collector patch: `examples/profiles/synthetic-otlp/collector-patch.yaml`

## What It Proves

- the core chart can run Bering and Sheaft without OpenTelemetry Demo
- Bering publishes a generic latest artifact
- Sheaft consumes the same artifact contract
- external producers can target the stable `bering-discovery` service when needed

## Install

```bash
helm upgrade --install mb3r ./charts/mb3r-stack \
  -f examples/profiles/synthetic-otlp/values.yaml
```

## Send A Minimal Trace

```bash
kubectl port-forward service/bering-discovery 4318:4318
curl -X POST http://127.0.0.1:4318/v1/traces \
  -H 'content-type: application/json' \
  --data-binary @examples/profiles/synthetic-otlp/payload.json
```

Then query Sheaft through `service/sheaft-reports` or run the automated checks in `docs/verification/generic-e2e.md`.
