# Failure-Tolerance Overlay

The failure-tolerance profile is an opt-in analysis overlay for Sheaft `v1.2.0`. It keeps Bering on the existing `io.mb3r.bering.snapshot@1.3.0` handoff and asks Sheaft to evaluate a selected operation over two fail-stop axes:

- independent replica-failure probability
- exact failed replica-slot count

Apply it after a base stack profile:

```bash
helm upgrade --install mb3r ./charts/mb3r-stack \
  -f examples/profiles/synthetic-otlp/values.yaml \
  -f examples/profiles/failure-tolerance/values.yaml
```

The checked-in overlay targets `frontend:GET /checkout`, which is produced by the synthetic OTLP profile. For another environment, replace the endpoint id, SLO, evaluated axis values, trial count, and minimum certified tolerance before treating the result as a release gate.

The default chart analysis remains schema `1.0`, warn-only, and does not enable a blocking boundary rule. This prevents a component upgrade from silently applying an environment-specific SLO. The overlay opts into analysis schema `1.2`, a fail-closed minimum-boundary rule, Wilson confidence certification, and raw sweep points in the Sheaft report.

This is a modelled fail-stop boundary. It does not predict traffic redistribution, per-replica capacity saturation, queues, retry-generated load, or an overload cascade. Those claims require future Bering capacity inputs and load/chaos validation.
