from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"

TASK_MAP = {
    "lint": [["validate.py"]],
    "validate": [["validate.py"]],
    "smoke-generic": [["acceptance_generic.py", "--mode", "smoke"]],
    "e2e-generic": [["acceptance_generic.py", "--mode", "e2e"]],
    "k8s-smoke-generic": [["live_k8s_smoke.py"]],
    "smoke-otel-demo": [["acceptance_otel_demo.py", "--mode", "smoke"]],
    "e2e-otel-demo": [["acceptance_otel_demo.py", "--mode", "e2e"]],
    "package-assets": [["package_assets.py"]],
    "chart-package": [["package_chart.py"]],
    "release-dry-run": [["release_dry_run.py"]],
    "stack-manifest": [["generate_stack_manifest.py"]],
}


def run(script_and_args: list[str]) -> int:
    command = [sys.executable, str(SCRIPTS / script_and_args[0]), *script_and_args[1:]]
    result = subprocess.run(command, cwd=ROOT, check=False)
    return result.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="Task runner for mb3r-stack.")
    parser.add_argument("task", choices=sorted(TASK_MAP))
    args = parser.parse_args()

    for script in TASK_MAP[args.task]:
        status = run(script)
        if status != 0:
            return status
    return 0


if __name__ == "__main__":
    sys.exit(main())
