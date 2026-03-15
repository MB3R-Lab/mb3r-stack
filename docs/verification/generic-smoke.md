# Generic Smoke

This is the fastest profile-independent proof that the core stack renders correctly without OpenTelemetry Demo.

```bash
make smoke-generic
```

What it checks:

- the generic `mb3r-stack` chart lints and renders
- the synthetic profile produces Bering and Sheaft resources
- the generic artifact handoff path matches on both sides
- public contract services are explicit and do not depend on the release name
- the generic smoke path does not require collector snippets or OTel Demo
