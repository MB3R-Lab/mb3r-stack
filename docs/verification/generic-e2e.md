# Generic E2E

This is the required non-OTel acceptance path for the repository.

```bash
make e2e-generic
```

What it checks:

- chart-generated generic configs from `examples/profiles/synthetic-otlp/values.yaml`
- live OTLP/HTTP trace ingestion into Bering using a synthetic payload
- stable artifact emission from Bering
- Sheaft batch and serve consumption of that artifact
- report generation and persisted history output

If this path fails, generic stack readiness is not proven even if the OTel Demo profile still passes.
