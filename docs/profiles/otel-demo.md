# OpenTelemetry Demo Profile

OpenTelemetry Demo is a showcase profile for the generic stack, not the core contract.

- stack values: `examples/profiles/otel-demo/mb3r-values.yaml`
- OTel Demo values: `examples/profiles/otel-demo/opentelemetry-demo-values.yaml`
- optional collector patch: `examples/profiles/otel-demo/collector-patch.yaml`
- documented public Bering endpoint: `http://bering-discovery:4318`

## Install

```bash
kubectl create namespace mb3r-demo

helm upgrade --install mb3r ./charts/mb3r-stack \
  --namespace mb3r-demo \
  --create-namespace \
  -f examples/profiles/otel-demo/mb3r-values.yaml

helm repo add open-telemetry https://open-telemetry.github.io/opentelemetry-helm-charts
helm repo update

helm upgrade --install otel-demo open-telemetry/opentelemetry-demo \
  --namespace mb3r-demo \
  --version 0.40.5 \
  -f examples/profiles/otel-demo/opentelemetry-demo-values.yaml
```

## What This Profile Reuses From Core

- generic Bering OTLP ingest on `4318`
- generic Bering latest artifact publication
- generic Sheaft consumption of that artifact
- generic public service aliasing instead of a fixed Helm release name

Verification commands for this profile live in `docs/verification/otel-demo-e2e.md`.
