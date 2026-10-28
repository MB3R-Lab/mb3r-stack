# Examples

These examples are intentionally small and operator-editable.

They track the `mb3r-stack v1.3.0` candidate and the pinned runtime pair Bering
`1.1.1` plus Sheaft `1.3.2`. External CI examples use the matching `v1.3.0`
bundle tag, which becomes available when the candidate is published. The latest
published bundle is still `v1.2.0`; use its released asset pack for that line.

- `profiles/synthetic-otlp/` is the smallest generic profile and the non-OTel acceptance baseline.
- `profiles/minimal-production-eval/` shows conservative pinning and external registry overrides.
- `profiles/ebpf-obi/` declares an external OBI source and its collection domain.
- `profiles/otel-demo/` shows how the generic stack integrates with OpenTelemetry Demo.
- `profiles/failure-tolerance/` opts a base profile into Sheaft `1.2` sweeps and minimum-boundary gating.
- `github/`, `gitlab/`, and `jenkins/` contain consumer CI examples.

Procrustes 0.1.0 is included as a source-pinned static preflight. Use
[the launcher instructions](../docs/procrustes.md) before collecting traces for
an application-specific operation; it is not a third deployed service.
