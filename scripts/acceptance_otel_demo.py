from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

from acceptance_common import (
    ROOT,
    check,
    exercise_local_handoff,
    find_document,
    maybe_find_document,
    prepare_workdir,
    render_otel_demo_chart,
    render_stack_chart,
)

RELEASE_NAME = "mb3r"
STACK_VALUES = ROOT / "examples" / "profiles" / "otel-demo" / "mb3r-values.yaml"
OTEL_VALUES = ROOT / "examples" / "profiles" / "otel-demo" / "opentelemetry-demo-values.yaml"
WORKDIR_BASE = ROOT / ".tmp" / "acceptance-otel-demo"


def run_acceptance(mode: str) -> None:
    workdir = prepare_workdir(WORKDIR_BASE / mode)
    addon_docs, helm, environment = render_stack_chart(workdir, STACK_VALUES, release_name=RELEASE_NAME)
    otel_docs = render_otel_demo_chart(workdir, OTEL_VALUES, helm=helm, environment=environment)
    prefix = f"{RELEASE_NAME}-mb3r-stack"

    bering_deployment = find_document(addon_docs, "Deployment", f"{prefix}-bering")
    bering_service = find_document(addon_docs, "Service", f"{prefix}-bering")
    bering_public_service = find_document(addon_docs, "Service", "bering-discovery")
    sheaft_public_service = find_document(addon_docs, "Service", "sheaft-reports")
    bering_cfg = find_document(addon_docs, "ConfigMap", f"{prefix}-bering-config")
    sheaft_cfg = find_document(addon_docs, "ConfigMap", f"{prefix}-sheaft-config")
    snippet_cfg = find_document(addon_docs, "ConfigMap", f"{prefix}-collector-snippets")

    check(
        maybe_find_document(addon_docs, "Deployment", f"{prefix}-sheaft") is None,
        "otel-demo profile should use the default co-located artifact handoff",
    )

    bering_config = yaml.safe_load(bering_cfg["data"]["serve.yaml"])
    sheaft_analysis_text = sheaft_cfg["data"]["analysis.yaml"]
    sheaft_config = yaml.safe_load(sheaft_cfg["data"]["sheaft.yaml"])
    snippet_exporter = yaml.safe_load(snippet_cfg["data"]["exporter.yaml"])

    collector_cfg_map = find_document(otel_docs, "ConfigMap", "otel-collector-agent")
    collector_cfg = yaml.safe_load(collector_cfg_map["data"]["relay"])
    traces_exporters = collector_cfg["service"]["pipelines"]["traces"]["exporters"]
    metrics_exporters = collector_cfg["service"]["pipelines"]["metrics"]["exporters"]
    logs_exporters = collector_cfg["service"]["pipelines"]["logs"]["exporters"]
    containers = {container["name"]: container for container in bering_deployment["spec"]["template"]["spec"]["containers"]}

    check(bering_service["spec"]["ports"][0]["port"] == 4318, "Bering service must expose OTLP/HTTP 4318")
    check(
        bering_public_service["metadata"]["labels"]["mb3r.io/service-role"] == "public-contract",
        "OTel Demo profile must reuse the generic public Bering contract",
    )
    check(
        sheaft_public_service["metadata"]["labels"]["mb3r.io/service-role"] == "public-contract",
        "OTel Demo profile must reuse the generic public Sheaft contract",
    )
    check(
        snippet_exporter["exporters"]["otlphttp/bering"]["endpoint"] == "http://bering-discovery:4318",
        "collector snippets must use the generic public Bering contract",
    )
    check(set(containers) == {"bering", "sheaft"}, "OTel Demo profile must keep Bering and Sheaft co-located")
    check("otlphttp/bering" in traces_exporters, "OTel Demo traces pipeline must include otlphttp/bering")
    check("otlphttp/bering" not in metrics_exporters, "OTel Demo metrics pipeline must not export to Bering")
    check("otlphttp/bering" not in logs_exporters, "OTel Demo logs pipeline must not export to Bering")
    check(
        collector_cfg["exporters"]["otlphttp/bering"]["endpoint"] == "http://bering-discovery:4318",
        "OTel Demo collector must target the generic public Bering service",
    )
    check(
        sheaft_config["artifact"]["path"] == bering_config["sink"]["latest_path"],
        "OTel Demo profile must still use the generic artifact handoff contract",
    )

    if mode == "e2e":
        exercise_local_handoff(
            workdir,
            bering_config=bering_config,
            sheaft_config=sheaft_config,
            sheaft_analysis_text=sheaft_analysis_text,
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run OTel Demo profile acceptance checks.")
    parser.add_argument("--mode", choices=("smoke", "e2e"), required=True)
    args = parser.parse_args()

    try:
        run_acceptance(args.mode)
    except Exception as exc:
        print(f"{args.mode}-otel-demo: failed: {exc}", file=sys.stderr)
        return 1

    print(f"{args.mode}-otel-demo: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
