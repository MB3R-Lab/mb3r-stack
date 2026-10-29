# External OBI source handoff

This profile prepares the Bering source configuration for an external
OpenTelemetry eBPF Instrumentation (OBI) collector. It targets published Bering 1.2.0 in the candidate stack 1.4.0 bundle. The previous stack 1.3.0 integration check remains historical;
[stack integration CI passed](https://github.com/MB3R-Lab/mb3r-stack/actions/runs/40640730443).
This profile supplies an
explicit source configuration rather than a verified collector installation.

## Static collection handoff

Prepare an explicit OBI collection plan using the merged Procrustes revision
pinned in the stack manifest before collecting runtime observations:

```bash
python scripts/procrustes.py -- analyze \
  --source deployment=./manifests --goal goal.yaml \
  --collection-source ebpf-obi --source-domain production --out-dir preflight
```

The launcher forwards these arguments to the pinned CLI. The selected OBI mode
emits report and collection-plan contract `0.2.0`; the goal and default native
report/plan remain `0.1.0`. Kernel access, process coverage, export delivery and
causal context remain `UNKNOWN`, so valid static inputs can produce `PARTIAL`.
An explicit source selection does not establish runtime readiness. Identity
conflicts and missing deployment or operation evidence remain visible.

Inspect the emitted collection plan and overlay. Confirmed inventory facts and
declared operation semantics are distinct from runtime-discovered dependencies.
The profile does not automatically read the local `preflight` directory; apply
an appropriate overlay through Bering's explicit file/configuration handoff.

## Runtime source

Enable the profile for integration evaluation with:

```bash
helm upgrade --install mb3r charts/mb3r-stack \
  --namespace observability --create-namespace \
  -f examples/profiles/ebpf-obi/values.yaml
```

The chart renders this Bering configuration:

```yaml
sources:
  - id: obi-main
    type: ebpf-obi
    domain: production
    capture_directory: /var/lib/mb3r/bering/obi-capture
```

Configure the external collector's OTLP/HTTP traces exporter to use:

```text
http://bering-discovery.observability.svc.cluster.local:4318/sources/obi-main/v1/traces
```

For an exporter that appends `/v1/traces` to a common OTLP endpoint, use the
base URL ending in `/sources/obi-main`. Configure exactly one of these forms
according to the collector's exporter settings. Generic native OTLP traffic
continues to use `/v1/traces`; do not send it to the declared OBI source merely
to label it as eBPF.

`id` identifies the Bering source URL. `domain` identifies the collection
deployment's context namespace. Agents on different hosts in one deployment
share a domain so exact parent links can survive transport. Independent
collection deployments use different domains. Host and collector-instance
identities remain observation evidence rather than domain substitutes.

Bering receives raw collector exports and builds the model itself. No
application-specific conversion to a graph or normalized-span file is required.
The source declaration records the configured boundary; it does not prove that
every submitted observation came from a kernel probe. Missing causal context
remains unknown, and client-only structural dependencies do not establish a
server receipt or business completion.

OBI remains a separate Linux deployment with its documented kernel access and
privileges. This profile does not deploy the collector or change Bering's
non-root security context. It also leaves generic collector snippets disabled.

The capture directory lies on the chart's shared artifact volume. The default
`emptyDir` is ephemeral. Select an existing persistent volume and an appropriate
telemetry retention policy when raw capture must survive pod replacement.
Capture files can contain application or infrastructure attributes.

Sheaft consumes Bering's model/snapshot through the existing artifact handoff.
The profile supplies no business-success predicate, fault law, reliability
estimate, desired replica inventory or physical database identity. Supply those
inputs explicitly when needed.
