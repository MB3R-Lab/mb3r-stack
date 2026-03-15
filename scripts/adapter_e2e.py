from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from common import ROOT, check

WORKDIR = ROOT / ".tmp" / "adapter-e2e"
PYTHON = sys.executable


def run(command: list[str], *, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"command failed ({result.returncode}): {' '.join(command)}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
    return result


def write_command_script(path: Path, payload: dict[str, object]) -> str:
    script = "\n".join(
        [
            "import json",
            "import os",
            "from pathlib import Path",
            f"payload = {json.dumps(payload)}",
            'Path(os.environ["MB3R_PAYLOAD_JSON"]).write_text(json.dumps(payload), encoding="utf-8")',
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(script + "\n", encoding="utf-8")
    return f'"{PYTHON}" "{path}"'


def assert_contract(report_path: Path, *, kind: str, adapter: str) -> dict[str, object]:
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    check(payload["schemaVersion"] == "v1alpha1", f"{report_path.name} must use schemaVersion v1alpha1")
    check(payload["kind"] == kind, f"{report_path.name} must use kind {kind}")
    check(payload["adapter"] == adapter, f"{report_path.name} must use adapter {adapter}")
    return payload


def validate_sources() -> None:
    expectations = {
        ROOT / ".github" / "workflows" / "bering-discover.yml": [
            '"kind": "mb3r.bering.discovery"',
            '"adapter": "github-reusable-workflow"',
        ],
        ROOT / ".github" / "workflows" / "sheaft-gate.yml": [
            '"kind": "mb3r.sheaft.gate"',
            '"adapter": "github-reusable-workflow"',
        ],
        ROOT / ".github" / "workflows" / "mb3r-report.yml": [
            '"kind": "mb3r.stack.report"',
            '"adapter": "github-reusable-workflow"',
        ],
        ROOT / "templates" / "bering-discover.yml": [
            '"kind": "mb3r.bering.discovery"',
            '"adapter": "gitlab-component"',
        ],
        ROOT / "templates" / "sheaft-gate.yml": [
            '"kind": "mb3r.sheaft.gate"',
            '"adapter": "gitlab-component"',
        ],
        ROOT / "templates" / "mb3r-report.yml": [
            '"kind": "mb3r.stack.report"',
            '"adapter": "gitlab-component"',
        ],
        ROOT / "ci" / "jenkins" / "vars" / "mb3rBeringDiscover.groovy": [
            "adapter: 'jenkins-shared-library'",
            "kind: 'mb3r.bering.discovery'",
        ],
        ROOT / "ci" / "jenkins" / "vars" / "mb3rSheaftGate.groovy": [
            "adapter: 'jenkins-shared-library'",
            "kind: 'mb3r.sheaft.gate'",
        ],
        ROOT / "ci" / "jenkins" / "vars" / "mb3rPublishReport.groovy": [
            "adapter: 'jenkins-shared-library'",
            "kind: 'mb3r.stack.report'",
        ],
    }
    for path, needles in expectations.items():
        text = path.read_text(encoding="utf-8")
        for needle in needles:
            check(needle in text, f"{path.relative_to(ROOT)} must contain {needle!r}")


def run_adapter_flow(adapter: str, workspace: Path) -> None:
    env = dict(os.environ)
    discovery_dir = workspace / "bering"
    gate_dir = workspace / "sheaft"
    report_dir = workspace / "report"
    commands_dir = workspace / "commands"
    discovery_command = write_command_script(commands_dir / "discovery.py", {"summary": f"{adapter} discovery"})
    gate_precheck_command = write_command_script(commands_dir / "gate-precheck.py", {"summary": f"{adapter} gate precheck"})
    gate_pass_command = write_command_script(commands_dir / "gate-pass.py", {"decision": "pass", "summary": "gate ok"})

    run(
        [
            PYTHON,
            str(ROOT / "scripts" / "adapter_cli.py"),
            "discovery",
            "--adapter",
            adapter,
            "--target-path",
            ".",
            "--output-dir",
            str(discovery_dir),
            "--command",
            discovery_command,
            "--image-ref",
            "ghcr.io/mb3r-lab/bering@sha256:8e8ce6599b43477b0653617e829d41c62a3189d16b60ecb424cca718fc0e2674",
            "--artifact-name",
            "mb3r-bering-discovery",
            "--env-path",
            str(discovery_dir / "bering.env"),
        ],
        env=env,
    )
    discovery = assert_contract(discovery_dir / "bering-discovery.json", kind="mb3r.bering.discovery", adapter=adapter)
    check(discovery["status"] == "success", f"{adapter} discovery must succeed")

    run(
        [
            PYTHON,
            str(ROOT / "scripts" / "adapter_cli.py"),
            "gate",
            "--adapter",
            adapter,
            "--discovery-report",
            str(discovery_dir / "bering-discovery.json"),
            "--output-dir",
            str(gate_dir),
            "--command",
            gate_precheck_command,
            "--image-ref",
            "ghcr.io/mb3r-lab/sheaft@sha256:eb1ebf9d96c55c5bb29e226e07496d152eb3a66b52dd9d34ba799fa4aef70624",
            "--artifact-name",
            "mb3r-sheaft-gate",
            "--default-decision",
            "review",
            "--env-path",
            str(gate_dir / "sheaft.env"),
        ],
        env=env,
    )
    gate = assert_contract(gate_dir / "sheaft-gate.json", kind="mb3r.sheaft.gate", adapter=adapter)
    check(gate["status"] == "success", f"{adapter} gate must succeed")
    check(gate["decision"] == "review", f"{adapter} gate decision must remain review when payload omits decision")
    run(
        [
            PYTHON,
            str(ROOT / "scripts" / "adapter_cli.py"),
            "gate",
            "--adapter",
            adapter,
            "--discovery-report",
            str(discovery_dir / "bering-discovery.json"),
            "--output-dir",
            str(gate_dir),
            "--command",
            gate_pass_command,
            "--image-ref",
            "ghcr.io/mb3r-lab/sheaft@sha256:eb1ebf9d96c55c5bb29e226e07496d152eb3a66b52dd9d34ba799fa4aef70624",
            "--artifact-name",
            "mb3r-sheaft-gate",
            "--default-decision",
            "review",
            "--env-path",
            str(gate_dir / "sheaft.env"),
        ],
        env=env,
    )
    gate = assert_contract(gate_dir / "sheaft-gate.json", kind="mb3r.sheaft.gate", adapter=adapter)
    check(gate["decision"] == "pass", f"{adapter} gate must propagate payload decision")

    run(
        [
            PYTHON,
            str(ROOT / "scripts" / "adapter_cli.py"),
            "report",
            "--adapter",
            adapter,
            "--discovery-report",
            str(discovery_dir / "bering-discovery.json"),
            "--gate-report",
            str(gate_dir / "sheaft-gate.json"),
            "--output-dir",
            str(report_dir),
            "--artifact-name",
            "mb3r-report",
            "--env-path",
            str(report_dir / "mb3r-report.env"),
        ],
        env=env,
    )
    report = assert_contract(report_dir / "mb3r-report.json", kind="mb3r.stack.report", adapter=adapter)
    check(report["overallDecision"] == "pass", f"{adapter} report must propagate overall decision")
    check((report_dir / "mb3r-report.md").exists(), f"{adapter} report markdown must exist")


def validate_examples() -> None:
    example_consumer = (ROOT / ".github" / "workflows" / "example-consumer.yml").read_text(encoding="utf-8")
    check("uses: ./.github/workflows/bering-discover.yml" in example_consumer, "GitHub example must call bering-discover workflow")
    check("uses: ./.github/workflows/sheaft-gate.yml" in example_consumer, "GitHub example must call sheaft-gate workflow")
    check("uses: ./.github/workflows/mb3r-report.yml" in example_consumer, "GitHub example must call mb3r-report workflow")

    jenkinsfile = (ROOT / "examples" / "jenkins" / "Jenkinsfile").read_text(encoding="utf-8")
    check("@Library('mb3r-stack@v0.2.0')" in jenkinsfile, "Jenkins example must pin the shared library version")
    for symbol in ("mb3rBeringDiscover", "mb3rSheaftGate", "mb3rPublishReport"):
        check(symbol in jenkinsfile, f"Jenkins example must call {symbol}")

    gitlab_example = (ROOT / "examples" / "gitlab" / ".gitlab-ci.yml").read_text(encoding="utf-8")
    for component in ("bering-discover", "sheaft-gate", "mb3r-report"):
        check(component in gitlab_example, f"GitLab example must reference {component}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run adapter end-to-end contract checks.")
    parser.parse_args()

    if WORKDIR.exists():
        shutil.rmtree(WORKDIR)
    WORKDIR.mkdir(parents=True, exist_ok=True)

    try:
        validate_sources()
        validate_examples()
        for adapter in ("github-reusable-workflow", "gitlab-component", "jenkins-shared-library"):
            run_adapter_flow(adapter, WORKDIR / adapter)
    except Exception as exc:
        print(f"e2e-adapters: failed: {exc}", file=sys.stderr)
        return 1

    print("e2e-adapters: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
