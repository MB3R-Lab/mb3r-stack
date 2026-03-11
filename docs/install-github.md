# Install On GitHub

This repository exposes GitHub reusable workflows under `.github/workflows/` using `workflow_call`.

Available adapters:

- `bering-discover.yml`
- `sheaft-gate.yml`
- `mb3r-report.yml`

## Consumption Model

The reusable workflows are an integration wrapper. They do not ship Bering or Sheaft logic. Instead, they accept explicit commands and image references so a downstream repository can invoke upstream released artifacts in a controlled way.

## Minimal Pattern

Use the example caller in `examples/github/example-caller.yml` or `.github/workflows/example-consumer.yml` as a starting point.

Typical flow:

1. Call `bering-discover.yml` with a command that writes JSON to `$MB3R_PAYLOAD_JSON`.
2. Call `sheaft-gate.yml` with a command that writes JSON to `$MB3R_PAYLOAD_JSON`.
3. Call `mb3r-report.yml` to merge the generated discovery and gate envelopes.

## Outputs

The reusable workflows expose stable outputs for downstream automation:

- artifact names
- report paths
- gate decision values
- overall report decision
