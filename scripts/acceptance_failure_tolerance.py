from __future__ import annotations

import argparse
import sys

import yaml

from acceptance_common import (
    ROOT,
    check,
    exercise_local_handoff,
    find_document,
    prepare_workdir,
    render_stack_chart,
)

RELEASE_NAME = "mb3r"
BASE_VALUES = ROOT / "examples" / "profiles" / "synthetic-otlp" / "values.yaml"
OVERLAY_VALUES = ROOT / "examples" / "profiles" / "failure-tolerance" / "values.yaml"
WORKDIR_BASE = ROOT / ".tmp" / "acceptance-failure-tolerance"


def run_acceptance(mode: str) -> None:
    workdir = prepare_workdir(WORKDIR_BASE / mode)
    documents, _, _ = render_stack_chart(
        workdir,
        [BASE_VALUES, OVERLAY_VALUES],
        release_name=RELEASE_NAME,
    )
    prefix = f"{RELEASE_NAME}-mb3r-stack"
    bering_cfg = find_document(documents, "ConfigMap", f"{prefix}-bering-config")
    sheaft_cfg = find_document(documents, "ConfigMap", f"{prefix}-sheaft-config")

    bering_config = yaml.safe_load(bering_cfg["data"]["serve.yaml"])
    sheaft_analysis_text = sheaft_cfg["data"]["analysis.yaml"]
    sheaft_analysis = yaml.safe_load(sheaft_analysis_text)
    sheaft_config = yaml.safe_load(sheaft_cfg["data"]["sheaft.yaml"])

    check(sheaft_analysis["schema_version"] == "1.2", "failure-tolerance overlay must use analysis schema 1.2")
    check(len(sheaft_analysis["sweeps"]) == 2, "failure-tolerance overlay must render both supported axes")
    check(
        sheaft_analysis["gate"]["boundary_rules"][0]["minimum_certified_tolerance"] == 0.03,
        "failure-tolerance overlay must render the checkout minimum boundary",
    )

    if mode == "e2e":
        report = exercise_local_handoff(
            workdir,
            bering_config=bering_config,
            sheaft_config=sheaft_config,
            sheaft_analysis_text=sheaft_analysis_text,
        )
        sweeps = {sweep["name"]: sweep for sweep in report.get("sweeps", [])}
        check(
            "checkout-independent-replica-failures" in sweeps,
            "Sheaft report must contain the independent replica-failure sweep",
        )
        check(
            "checkout-failed-replica-slots" in sweeps,
            "Sheaft report must contain the exact failed-slot sweep",
        )
        boundary_results = report["policy_evaluation"].get("boundary_results", [])
        check(len(boundary_results) == 1, "Sheaft report must contain one evaluated minimum-boundary rule")
        check(boundary_results[0]["status"] == "pass", "synthetic checkout boundary must pass")


def main() -> int:
    parser = argparse.ArgumentParser(description="Exercise the Sheaft v1.2 failure-tolerance stack overlay.")
    parser.add_argument("--mode", choices=("smoke", "e2e"), required=True)
    args = parser.parse_args()

    try:
        run_acceptance(args.mode)
    except Exception as exc:
        print(f"{args.mode}-failure-tolerance: failed: {exc}", file=sys.stderr)
        return 1

    print(f"{args.mode}-failure-tolerance: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
