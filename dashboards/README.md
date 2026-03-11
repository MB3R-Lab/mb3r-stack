# Dashboards

Dashboards are versioned as release assets for the integration bundle.

- `dashboards/bering/` contains Bering-focused views.
- `dashboards/sheaft/` contains Sheaft-focused views.

The Helm chart does not inline these dashboards. Instead, it provides Grafana provisioning hooks so operators can mount these JSON files through ConfigMaps or sidecar discovery.
