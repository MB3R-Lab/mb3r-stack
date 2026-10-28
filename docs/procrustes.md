# Procrustes static preflight

The stack includes Procrustes as an optional operator-invoked stage before
collection and Bering discovery. Its exact source revision comes from
`compat/stack-manifest.json`; the launcher never follows upstream main. The
`1.3.0` candidate pins merged revision `39f76000f8a39c971155e08ebffde829b525911b`
of preview `0.1.0`. Procrustes is source-built; no OCI artifact is invented.

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

Use the [pinned goal and evidence documentation](https://github.com/MB3R-Lab/Procrustes/blob/39f76000f8a39c971155e08ebffde829b525911b/README.md).
The goal, test scenario, Bering endpoint, and downstream predicate must describe
the same operation. Exit 2 means blocked static preconditions; exit 1 is invalid
input or execution failure. Exit 0 alone is not proof of complete readiness:
inspect `goal_status` for EXPECTED, PARTIAL, or NOT_ASSESSED as well.

## Explicit OBI collection

```bash
python scripts/procrustes.py -- analyze \
  --source deployment=./manifests --goal goal.yaml \
  --collection-source ebpf-obi --source-domain production --out-dir preflight
```

OBI mode emits report and collection-plan contracts `0.2.0`. The goal remains
`0.1.0`, and the default native mode retains report/plan `0.1.0` and its SDK,
exporter and propagation checks. Source selection and the collection domain are
operator declarations. OBI coverage, kernel access, delivery and exact context
links remain outside this static assessment and require separate runtime
evidence. A declared Bering source does not verify kernel attachment. Otherwise
valid inputs can produce `PARTIAL`; missing static facts or conflicts can still block.

Use the same collection domain for agents in one deployment. The chart's
[OBI profile](../examples/profiles/ebpf-obi/README.md) passes the matching domain
to Bering without deploying a collector or granting Bering kernel privileges.

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

For the declared OBI source, replay retained raw exports directly:

```bash
bering discover --input ./obi-capture --input-type ebpf-obi \
  --source-domain production --overlay preflight/bering.overlay.yaml \
  --out model.json --snapshot-out snapshot.json
```

This source path requires Bering 1.1.0. Overlay service/count facts remain
static assistance, and endpoint semantics come from the supplied operation
goal. They do not establish observed edges, mandatory calls or actual coverage.

Use the Sheaft version and immutable image pin recorded in the stack manifest
for downstream analysis. The `1.3.0` candidate targets Sheaft `1.3.2`; its release
and compatibility verification remain pending.
