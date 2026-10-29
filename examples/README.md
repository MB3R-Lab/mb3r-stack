# Examples

These examples are intentionally small and operator-editable.

The current Helm profile values track the unpublished `1.5.0` candidate with published Bering `1.3.0` and Sheaft `1.3.2`; final stack compatibility evidence is still pending. External CI examples use the planned `v1.5.0` bundle tag for release coherence, but that tag is not published yet and must not be treated as installable before release. The latest published release remains
[v1.4.0](https://github.com/MB3R-Lab/mb3r-stack/releases/tag/v1.4.0).
Historical release packs retain their own component pins.

- `profiles/synthetic-otlp/` is the smallest generic profile and the non-OTel acceptance baseline.
- `profiles/minimal-production-eval/` shows conservative pinning and external registry overrides.
- `profiles/ebpf-obi/` declares an external OBI source and its collection domain.
- `profiles/ebpf-otlp/` declares a vendor-neutral external eBPF OTLP source and domain.
- `profiles/otel-demo/` shows how the generic stack integrates with OpenTelemetry Demo.
- `profiles/failure-tolerance/` opts a base profile into Sheaft `1.2` sweeps and minimum-boundary gating.
- `github/`, `gitlab/`, and `jenkins/` contain consumer CI examples.

Procrustes 0.1.0 is included as a source-pinned static preflight. Use
[the launcher instructions](../docs/procrustes.md) before collecting traces for
an application-specific operation; it is not a third deployed service.
