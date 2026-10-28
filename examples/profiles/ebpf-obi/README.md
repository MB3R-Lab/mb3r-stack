# External OBI source handoff

This profile prepares the Bering source configuration for an external
OpenTelemetry eBPF Instrumentation (OBI) collector. It targets Bering 1.1.0 and
the stack 1.3.0 candidate. Upstream release pins and integration verification
are pending; this candidate must not be published or installed with TODO pins.

Once those pins are finalized, enable the profile with:

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
