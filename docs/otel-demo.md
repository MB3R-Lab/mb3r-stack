# OTel Demo Integration

This repository now ships a single documented baseline path for:

`OpenTelemetry Demo -> Bering -> Sheaft`

The path is intentionally opinionated so the install is reproducible without post-install YAML edits:

- namespace: `mb3r-demo`
- addon chart values: `examples/otel-demo/mb3r-values.yaml`
- OTel Demo chart values: `examples/otel-demo/opentelemetry-demo-values.yaml`
- OTel Demo chart version: `0.40.5`
- Bering ingest path: OTLP/HTTP on `mb3r-otel-addon-bering:4318`
- Bering -> Sheaft handoff: shared in-pod volume with Sheaft watching `/var/lib/mb3r/bering/latest.json`

## Install

```bash
kubectl create namespace mb3r-demo

helm upgrade --install mb3r ./charts/mb3r-otel-addon \
  --namespace mb3r-demo \
  --create-namespace \
  -f examples/otel-demo/mb3r-values.yaml

helm repo add open-telemetry https://open-telemetry.github.io/opentelemetry-helm-charts
helm repo update

helm upgrade --install otel-demo open-telemetry/opentelemetry-demo \
  --namespace mb3r-demo \
  --version 0.40.5 \
  -f examples/otel-demo/opentelemetry-demo-values.yaml
```

The example addon values set `fullnameOverride: mb3r-otel-addon`, so the Bering and Sheaft service names stay stable regardless of the Helm release name.

## Runtime Behavior

- Bering runs in upstream `serve --config` mode.
- The addon exposes only the real Bering HTTP port by default: `4318`.
- `/metrics`, `/readyz`, and `/healthz` are served from that same Bering HTTP listener.
- The OTel Demo collector exports traces to `otlphttp/bering`.
- Metrics and logs stay on the OTel Demo defaults and are not sent to Bering.
- Sheaft is co-located with Bering in the same pod and watches the stable latest artifact file.

## Verify The Flow

Wait for the addon deployment and the OTel Demo collector:

```bash
kubectl rollout status deployment/mb3r-otel-addon-bering -n mb3r-demo
kubectl rollout status daemonset/otel-collector-agent -n mb3r-demo
```

The OTel Demo load-generator starts automatically, so traffic begins without extra patching. Then verify:

1. Bering is receiving telemetry and emitting snapshots:

```bash
kubectl logs deployment/mb3r-otel-addon-bering -n mb3r-demo -c bering --tail=50
```

Look for log lines containing `snapshot emitted`.

2. Sheaft is consuming the latest Bering artifact:

```bash
kubectl port-forward service/mb3r-otel-addon-sheaft -n mb3r-demo 8080:8080
curl http://127.0.0.1:8080/current-report
curl http://127.0.0.1:8080/readyz
```

`/current-report` is the baseline demo handoff proof that the Sheaft watcher has consumed the Bering artifact and produced an analysis report.

## Local Smoke Check

The repository includes a local smoke target that renders both Helm charts, validates the merged OTel Demo collector config, runs upstream Bering in `serve` mode, posts OTLP/HTTP traces, validates the emitted snapshot, and runs Sheaft against that artifact:

```bash
make smoke-otel-demo
```

This smoke path does not require a live Kubernetes cluster, but it uses the same chart-generated Bering and Sheaft configs that the addon installs.

Direct Python entrypoint:

```bash
python scripts/smoke_oteldemo.py
```
