# Collector Assets

These files are generic snippets for integrating an existing OTLP-capable collector with Bering and Sheaft.

- `snippets/` contains small composable config fragments.
- Profile-specific collector overlays live under `examples/profiles/*/`.
- The baseline snippets are OTLP/HTTP-first and traces-only for Bering ingestion.
- If you override collector pipeline arrays in a concrete chart, preserve the chart's required default exporters and processors instead of replacing them blindly.

These assets are intentionally small and conservative. They should be merged into an existing collector deployment rather than treated as a full collector distribution.
