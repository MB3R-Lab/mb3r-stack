# Minimal Production Eval Profile

This profile keeps the core stack generic while showing a more production-like topology.

- values: `examples/profiles/minimal-production-eval/values.yaml`
- optional collector patch: `examples/profiles/minimal-production-eval/collector-patch.yaml`

## Characteristics

- external image registry override
- existing collector deployment declared explicitly
- stable public Bering and Sheaft service aliases
- ServiceMonitor resources enabled
- no OpenTelemetry Demo dependency

## Install

```bash
helm upgrade --install mb3r ./charts/mb3r-stack \
  -f examples/profiles/minimal-production-eval/values.yaml
```

Use the profile collector patch only if your collector operator expects an `OpenTelemetryCollector`-style overlay. Otherwise, wire your collector directly to `http://bering-discovery.observability.svc.cluster.local:4318`.
