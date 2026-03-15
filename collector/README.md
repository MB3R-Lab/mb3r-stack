# Collector Assets

These files are patch snippets and overlays for integrating an existing OpenTelemetry collector with upstream Bering.

- `snippets/` contains small composable config fragments.
- `overlays/` contains example OpenTelemetryCollector-style overlays for common evaluation scenarios.
- The baseline snippets and overlays are OTLP/HTTP-first and traces-only for Bering ingestion.
- If you override collector pipeline arrays in a concrete chart, preserve the chart's required default exporters and processors instead of replacing them blindly.

These assets are intentionally small and conservative. They should be merged into an existing collector deployment rather than treated as a full collector distribution.
