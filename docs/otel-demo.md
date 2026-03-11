# OTel Demo Integration

This repository includes small value overrides for integrating the OpenTelemetry Demo with the addon bundle.

Files:

- `examples/otel-demo/mb3r-values.yaml`
- `examples/otel-demo/opentelemetry-demo-values.yaml`
- `collector/overlays/local-demo-collector-patch.yaml`

## Suggested Evaluation Flow

1. Install the addon chart with `examples/otel-demo/mb3r-values.yaml`.
2. Install or upgrade the OpenTelemetry Demo chart with `examples/otel-demo/opentelemetry-demo-values.yaml`.
3. Confirm the demo collector exports traces and metrics to the Bering endpoint exposed by the addon chart.

These examples are deliberately small. Adjust service names and namespaces to the exact release names used in your environment.
