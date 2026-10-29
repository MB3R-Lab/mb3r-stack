# Generic eBPF OTLP source handoff

This profile declares a producer-neutral eBPF OTLP boundary in Bering. The
external producer is selected and operated separately; the stack neither asks
for a vendor name nor deploys kernel instrumentation. The release-ready source
targets Bering 1.3.0 at its published immutable image pin. Stack compatibility
was verified at the exact revision recorded in the compatibility matrix.

## Static collection handoff

Build the source-pinned Procrustes preflight and select the generic source kind:

```bash
python scripts/procrustes.py -- analyze \
  --source deployment=./manifests --goal goal.yaml \
  --collection-source ebpf-otlp --source-domain production --out-dir preflight
```

The generic selection emits report and collection-plan contract `0.3.0`. Its
fingerprint depends on the static inputs, `ebpf-otlp` source kind, and logical
domain—not a producer label. Kernel compatibility, protocol support, process
coverage, delivery, and causal context remain runtime unknowns. The overlay
contains static inventory and operation facts but no invented runtime edges.

## Runtime source

Render the release-ready source with:

```bash
helm upgrade --install mb3r charts/mb3r-stack \
  --namespace observability --create-namespace \
  -f examples/profiles/ebpf-otlp/values.yaml
```

The profile declares:

```yaml
sources:
  - id: telemetry-main
    type: ebpf-otlp
    domain: production
    capture_directory: /var/lib/mb3r/bering/ebpf-capture
```

Configure the external OTLP/HTTP traces exporter for either the source base URL
or complete traces URL, according to whether it appends `/v1/traces`:

```text
http://bering-discovery.observability.svc.cluster.local:4318/sources/telemetry-main
http://bering-discovery.observability.svc.cluster.local:4318/sources/telemetry-main/v1/traces
```

The ID is a logical source boundary and the domain names one collection
deployment. Neither is a host, process, replica, or producer identity. Bering
retains accepted wire payloads, constructs the model from observed OTLP, and
publishes the unchanged model/snapshot contract consumed by Sheaft. A declared
source does not prove that submitted spans came from eBPF, that all protocols
were observed, or that missing parent/async links exist.

The default capture path uses the shared artifact volume and may be ephemeral.
Apply an appropriate persistent-volume and telemetry-retention policy when raw
captures must survive pod replacement.
