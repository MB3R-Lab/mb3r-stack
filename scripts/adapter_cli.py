from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from adapter_contracts import generate_discovery_report, generate_gate_report, generate_stack_report


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate MB3R adapter contract artifacts.")
    subparsers = parser.add_subparsers(dest="command_name", required=True)

    discovery = subparsers.add_parser("discovery")
    discovery.add_argument("--adapter", required=True)
    discovery.add_argument("--target-path", default=".")
    discovery.add_argument("--output-dir", required=True)
    discovery.add_argument("--command", default="")
    discovery.add_argument("--image-ref", required=True)
    discovery.add_argument("--artifact-name", default="mb3r-bering-discovery")
    discovery.add_argument("--outputs-path")
    discovery.add_argument("--env-path")

    gate = subparsers.add_parser("gate")
    gate.add_argument("--adapter", required=True)
    gate.add_argument("--discovery-report", required=True)
    gate.add_argument("--output-dir", required=True)
    gate.add_argument("--command", default="")
    gate.add_argument("--image-ref", required=True)
    gate.add_argument("--artifact-name", default="mb3r-sheaft-gate")
    gate.add_argument("--default-decision", default="review")
    gate.add_argument("--outputs-path")
    gate.add_argument("--env-path")

    report = subparsers.add_parser("report")
    report.add_argument("--adapter", required=True)
    report.add_argument("--discovery-report", required=True)
    report.add_argument("--gate-report", required=True)
    report.add_argument("--output-dir", required=True)
    report.add_argument("--artifact-name", default="mb3r-report")
    report.add_argument("--outputs-path")
    report.add_argument("--env-path")

    args = parser.parse_args()

    if args.command_name == "discovery":
        result = generate_discovery_report(
            adapter=args.adapter,
            target_path=args.target_path,
            output_dir=Path(args.output_dir),
            command=args.command,
            image_ref=args.image_ref,
            artifact_name=args.artifact_name,
            process_env=dict(os.environ),
            outputs_path=Path(args.outputs_path) if args.outputs_path else None,
            env_path=Path(args.env_path) if args.env_path else None,
        )
    elif args.command_name == "gate":
        result = generate_gate_report(
            adapter=args.adapter,
            discovery_report=Path(args.discovery_report),
            output_dir=Path(args.output_dir),
            command=args.command,
            image_ref=args.image_ref,
            artifact_name=args.artifact_name,
            default_decision=args.default_decision,
            process_env=dict(os.environ),
            outputs_path=Path(args.outputs_path) if args.outputs_path else None,
            env_path=Path(args.env_path) if args.env_path else None,
        )
    else:
        result = generate_stack_report(
            adapter=args.adapter,
            discovery_report=Path(args.discovery_report),
            gate_report=Path(args.gate_report),
            output_dir=Path(args.output_dir),
            artifact_name=args.artifact_name,
            outputs_path=Path(args.outputs_path) if args.outputs_path else None,
            env_path=Path(args.env_path) if args.env_path else None,
        )

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
