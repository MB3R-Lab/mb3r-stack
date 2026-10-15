# Procrustes static preflight

Stack 1.2.0 includes Procrustes 0.1.0 as the first, optional operator-invoked
stage, before trace collection and Bering discovery. The stack manifest pins
commit `378f35f242f25fda7392646bfbba66312b669144`; it never follows upstream main.
No upstream Procrustes OCI release exists for this pin. The included launcher
therefore builds it from source instead of pretending that a published image exists.

## Requirements and quick check

Use Python 3.10+, Git, and Go 1.26.2+. Network access is needed for the initial
source and Go dependency download. From the repository or extracted asset pack:

```bash
python scripts/procrustes.py --example
```

The command builds the exact pin and checks its upstream static ready fixture.
Outputs are `.tmp/preflight/report.json`, `summary.md`, `collection-plan.json`,
and `bering.overlay.yaml`. This is a packaging check, not a deployment or experiment.
Modified source caches are rejected, never reset or overwritten.

## Your application

```bash
python scripts/procrustes.py -- analyze \
  --source application=/path/to/rendered-static-evidence \
  --goal /path/to/goal.yaml \
  --out-dir out/preflight \
  --fail-on-blocked
```

Use the [upstream goal and evidence documentation](https://github.com/MB3R-Lab/Procrustes/blob/378f35f242f25fda7392646bfbba66312b669144/README.md).
The goal, test scenario, Bering endpoint, and downstream predicate must describe
the same operation. Exit 2 means blocked static preconditions; exit 1 is invalid
input or execution failure. Exit 0 alone is not proof of complete readiness:
inspect `goal_status` for EXPECTED, PARTIAL, or NOT_ASSESSED as well.

## Handoff into Bering

Inspect the collection plan, collect actual traces separately, then supply the
generated overlay to the pinned Bering CLI:

```bash
bering discover --input traces.json \
  --overlay out/preflight/bering.overlay.yaml --out model.json
```

The overlay carries confirmed static facts; Procrustes does not infer runtime
edges or guarantee operation success. Bering owns discovery and Sheaft owns
analysis. Procrustes does not run as a Kubernetes Deployment or as a hidden
step in `helm install`. CI validates successful and blocked preflight, actual
asset-pack execution, and Bering's acceptance of the emitted overlay.

Use [Sheaft v1.3.1](https://github.com/MB3R-Lab/Sheaft/releases/tag/v1.3.1) for the
downstream analysis. Paper data and the reproducible three-tool experiment remain
in [the separate reproduction repository](https://github.com/MB3R-Lab/mb3r-software-complex-repro).
