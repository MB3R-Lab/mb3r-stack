# OTel Demo Verification

Use these commands only for the OpenTelemetry Demo showcase profile.

```bash
make smoke-otel-demo
make e2e-otel-demo
```

What they check:

- the generic stack chart renders correctly with the OTel Demo profile values
- the OTel Demo collector is wired to the generic public Bering service
- OTel Demo keeps its own metrics and logs exporters instead of turning them into a core assumption
- the profile still uses the same generic artifact handoff into Sheaft

Passing this profile is necessary for the demo path, but it is not sufficient proof of generic stack readiness by itself.
