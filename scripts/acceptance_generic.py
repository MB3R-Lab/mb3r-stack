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
    render_stack_chart,
)

RELEASE_NAME = "mb3r"
PROFILE_VALUES = ROOT / "examples" / "profiles" / "synthetic-otlp" / "values.yaml"
WORKDIR_BASE = ROOT / ".tmp" / "acceptance-generic"


def run_acceptance(mode: str) -> None:
    workdir = prepare_workdir(WORKDIR_BASE / mode)
    documents, _, _ = render_stack_chart(workdir, PROFILE_VALUES, release_name=RELEASE_NAME)
    prefix = f"{RELEASE_NAME}-mb3r-stack"

    bering_deployment = find_document(documents, "Deployment", f"{prefix}-bering")
    bering_service = find_document(documents, "Service", f"{prefix}-bering")
    sheaft_service = find_document(documents, "Service", f"{prefix}-sheaft")
    bering_public_service = find_document(documents, "Service", "bering-discovery")
    sheaft_public_service = find_document(documents, "Service", "sheaft-reports")
    bering_cfg = find_document(documents, "ConfigMap", f"{prefix}-bering-config")
    sheaft_cfg = find_document(documents, "ConfigMap", f"{prefix}-sheaft-config")

    check(
        maybe_find_document(documents, "ConfigMap", f"{prefix}-collector-snippets") is None,
        "synthetic generic profile must not require collector snippets",
    )
    check(
        maybe_find_document(documents, "Deployment", f"{prefix}-sheaft") is None,
        "synthetic generic profile should use the default co-located artifact handoff",
    )

    bering_config = yaml.safe_load(bering_cfg["data"]["serve.yaml"])
    sheaft_analysis_text = sheaft_cfg["data"]["analysis.yaml"]
    sheaft_config = yaml.safe_load(sheaft_cfg["data"]["sheaft.yaml"])

    check(
        bering_service["metadata"]["labels"]["mb3r.io/service-role"] == "primary",
        "primary Bering service must be labeled for generic monitoring selectors",
    )
    check(
        sheaft_service["metadata"]["labels"]["mb3r.io/service-role"] == "primary",
        "primary Sheaft service must be labeled for generic monitoring selectors",
    )
    check(
        bering_public_service["metadata"]["labels"]["mb3r.io/service-role"] == "public-contract",
        "public Bering service must be explicit",
    )
    check(
        sheaft_public_service["metadata"]["labels"]["mb3r.io/service-role"] == "public-contract",
        "public Sheaft service must be explicit",
    )
    check(bering_config["server"]["listen_address"] == ":4318", "Bering must listen on OTLP/HTTP 4318")
    check(
        bering_config["sink"]["latest_path"] == "/var/lib/mb3r/bering/latest.json",
        "Bering must publish a stable latest artifact path",
    )
    check(
        sheaft_config["artifact"]["path"] == bering_config["sink"]["latest_path"],
        "Sheaft must consume the same generic artifact handoff path that Bering publishes",
    )
    check(
        any(container["name"] == "sheaft" for container in bering_deployment["spec"]["template"]["spec"]["containers"]),
        "generic synthetic profile must exercise the in-chart producer to consumer handoff",
    )

    if mode == "e2e":
        exercise_local_handoff(
            workdir,
            bering_config=bering_config,
            sheaft_config=sheaft_config,
            sheaft_analysis_text=sheaft_analysis_text,
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run generic stack acceptance checks.")
    parser.add_argument("--mode", choices=("smoke", "e2e"), required=True)
    args = parser.parse_args()

    try:
        run_acceptance(args.mode)
    except Exception as exc:
        print(f"{args.mode}-generic: failed: {exc}", file=sys.stderr)
        return 1

    print(f"{args.mode}-generic: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
