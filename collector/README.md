# Collector Assets

These files are patch snippets and overlays for integrating an existing OpenTelemetry collector with upstream Bering.

- `snippets/` contains small composable config fragments.
- `overlays/` contains example OpenTelemetryCollector-style overlays for common evaluation scenarios.

These assets are intentionally small and conservative. They should be merged into an existing collector deployment rather than treated as a full collector distribution.
