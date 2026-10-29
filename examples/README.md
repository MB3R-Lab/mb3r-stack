# Examples

These examples are intentionally small and operator-editable.

The current Helm profile values track the `1.4.0` candidate with Bering `1.2.0` and Sheaft `1.3.2`. External CI examples stage `v1.4.0` references for integration validation; operators should use the published `v1.3.0` tag until the candidate is released. The latest release is
[v1.3.0](https://github.com/MB3R-Lab/mb3r-stack/releases/tag/v1.3.0).
Historical release packs retain their own component pins.

- `profiles/synthetic-otlp/` is the smallest generic profile and the non-OTel acceptance baseline.
- `profiles/minimal-production-eval/` shows conservative pinning and external registry overrides.
- `profiles/ebpf-obi/` declares an external OBI source and its collection domain.
- `profiles/otel-demo/` shows how the generic stack integrates with OpenTelemetry Demo.
- `profiles/failure-tolerance/` opts a base profile into Sheaft `1.2` sweeps and minimum-boundary gating.
- `github/`, `gitlab/`, and `jenkins/` contain consumer CI examples.

Procrustes 0.1.0 is included as a source-pinned static preflight. Use
[the launcher instructions](../docs/procrustes.md) before collecting traces for
an application-specific operation; it is not a third deployed service.
