# Generic E2E

This is the required non-OTel acceptance path for the repository.

```bash
make e2e-generic
make k8s-smoke-generic
make k8s-smoke-generic-pinned
```

What it checks:

- chart-generated generic configs from `examples/profiles/synthetic-otlp/values.yaml`
- live OTLP/HTTP trace ingestion into Bering using a synthetic payload
- stable artifact emission from Bering
- Sheaft batch and serve consumption of that artifact
- report generation and persisted history output
- live-cluster install smoke through `kind` with locally rebuilt images from the pinned release binaries
- clean-cluster startup of the chart's default pinned `ghcr.io/mb3r-lab/bering` and `ghcr.io/mb3r-lab/sheaft` images
- anonymous pull by default for pinned-image smoke, with an optional temporary `imagePullSecret` from `MB3R_GHCR_USERNAME` and `MB3R_GHCR_TOKEN`
- pinned-image smoke wired into repository CI on every push now that the upstream Bering and Sheaft GHCR packages are public
- explicit failure attribution when Kubernetes reports image-pull or auth errors instead of letting them collapse into a generic timeout

If this path fails, generic stack readiness is not proven even if the OTel Demo profile still passes.
