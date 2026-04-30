from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ALLOWED_DECISIONS = {"fail", "pass", "report", "review", "warn"}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_json_if_exists(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_env(path: Path, values: dict[str, str]) -> None:
    ensure_dir(path.parent)
    lines = [f"{key}={value}" for key, value in values.items()]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_outputs(path: Path | None, values: dict[str, str]) -> None:
    if path is None:
        return
    ensure_dir(path.parent)
    with path.open("a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def run_command(command: str, env: dict[str, str]) -> int:
    if not command.strip():
        return 0
    return subprocess.run(command, shell=True, env=env, check=False).returncode


def normalize_decision(value: Any, *, source: str) -> str:
    if not isinstance(value, str) or value not in ALLOWED_DECISIONS:
        allowed = ", ".join(sorted(ALLOWED_DECISIONS))
        raise ValueError(f"{source} decision must be one of {allowed}: {value!r}")
    return value


def generate_discovery_report(
    *,
    adapter: str,
    target_path: str,
    output_dir: Path,
    command: str,
    image_ref: str,
    artifact_name: str,
    process_env: dict[str, str],
    outputs_path: Path | None = None,
    env_path: Path | None = None,
) -> dict[str, Any]:
    ensure_dir(output_dir)
    payload_path = output_dir / "bering-payload.json"
    report_path = output_dir / "bering-discovery.json"

    command_env = dict(process_env)
    command_env["MB3R_TARGET_PATH"] = target_path
    command_env["MB3R_PAYLOAD_JSON"] = str(payload_path)
    command_env["MB3R_IMAGE_REF"] = image_ref

    exit_code = run_command(command, command_env)
    status = "pending"
    if command.strip():
        status = "success" if exit_code == 0 else "failed"

    payload = load_json_if_exists(payload_path)
    if payload is not None and exit_code == 0:
        status = "success"

    report = {
        "schemaVersion": "v1alpha1",
        "kind": "mb3r.bering.discovery",
        "adapter": adapter,
        "generatedAt": now_iso(),
        "targetPath": target_path,
        "imageRef": image_ref,
        "command": command,
        "status": status,
        "exitCode": exit_code,
        "payloadPath": payload_path.as_posix(),
        "artifactName": artifact_name,
        "payload": payload,
    }
    write_json(report_path, report)

    env_values = {
        "MB3R_BERING_REPORT": report_path.as_posix(),
        "MB3R_BERING_PAYLOAD": payload_path.as_posix(),
        "MB3R_BERING_ARTIFACT": artifact_name,
        "MB3R_BERING_STATUS": status,
    }
    if env_path is not None:
        write_env(env_path, env_values)

    write_outputs(
        outputs_path,
        {
            "report-path": report_path.as_posix(),
            "payload-path": payload_path.as_posix(),
            "artifact-name": artifact_name,
            "status": status,
        },
    )

    report["reportPath"] = report_path.as_posix()
    if exit_code != 0:
        raise SystemExit(exit_code)
    return report


def generate_gate_report(
    *,
    adapter: str,
    discovery_report: Path,
    output_dir: Path,
    command: str,
    image_ref: str,
    artifact_name: str,
    default_decision: str,
    process_env: dict[str, str],
    outputs_path: Path | None = None,
    env_path: Path | None = None,
) -> dict[str, Any]:
    ensure_dir(output_dir)
    payload_path = output_dir / "sheaft-payload.json"
    report_path = output_dir / "sheaft-gate.json"

    command_env = dict(process_env)
    command_env["MB3R_DISCOVERY_REPORT"] = discovery_report.as_posix()
    command_env["MB3R_PAYLOAD_JSON"] = str(payload_path)
    command_env["MB3R_IMAGE_REF"] = image_ref

    exit_code = run_command(command, command_env)
    status = "pending"
    decision = normalize_decision(default_decision, source="default")
    if command.strip():
        status = "success" if exit_code == 0 else "failed"
        if exit_code != 0:
            decision = "fail"

    payload = load_json_if_exists(payload_path)
    if payload is not None:
        if "decision" in payload:
            decision = normalize_decision(payload["decision"], source="payload")
        if exit_code == 0:
            status = "success"

    report = {
        "schemaVersion": "v1alpha1",
        "kind": "mb3r.sheaft.gate",
        "adapter": adapter,
        "generatedAt": now_iso(),
        "discoveryReport": discovery_report.as_posix(),
        "imageRef": image_ref,
        "command": command,
        "decision": decision,
        "status": status,
        "exitCode": exit_code,
        "payloadPath": payload_path.as_posix(),
        "artifactName": artifact_name,
        "payload": payload,
    }
    write_json(report_path, report)

    env_values = {
        "MB3R_SHEAFT_REPORT": report_path.as_posix(),
        "MB3R_SHEAFT_PAYLOAD": payload_path.as_posix(),
        "MB3R_SHEAFT_ARTIFACT": artifact_name,
        "MB3R_SHEAFT_STATUS": status,
        "MB3R_SHEAFT_DECISION": decision,
    }
    if env_path is not None:
        write_env(env_path, env_values)

    write_outputs(
        outputs_path,
        {
            "report-path": report_path.as_posix(),
            "payload-path": payload_path.as_posix(),
            "artifact-name": artifact_name,
            "decision": decision,
            "status": status,
        },
    )

    report["reportPath"] = report_path.as_posix()
    if exit_code != 0:
        raise SystemExit(exit_code)
    return report


def generate_stack_report(
    *,
    adapter: str,
    discovery_report: Path,
    gate_report: Path,
    output_dir: Path,
    artifact_name: str,
    outputs_path: Path | None = None,
    env_path: Path | None = None,
) -> dict[str, Any]:
    ensure_dir(output_dir)
    report_json = output_dir / "mb3r-report.json"
    report_markdown = output_dir / "mb3r-report.md"

    discovery = json.loads(discovery_report.read_text(encoding="utf-8"))
    gate = json.loads(gate_report.read_text(encoding="utf-8"))
    overall_decision = normalize_decision(gate.get("decision", "review"), source="gate")

    report = {
        "schemaVersion": "v1alpha1",
        "kind": "mb3r.stack.report",
        "adapter": adapter,
        "generatedAt": now_iso(),
        "overallDecision": overall_decision,
        "discovery": {
            "status": discovery.get("status"),
            "path": discovery_report.as_posix(),
            "artifactName": discovery.get("artifactName"),
        },
        "gate": {
            "decision": overall_decision,
            "status": gate.get("status"),
            "path": gate_report.as_posix(),
            "artifactName": gate.get("artifactName"),
        },
    }
    write_json(report_json, report)

    markdown = "\n".join(
        [
            "# MB3R Report",
            "",
            f"- Generated at: {report['generatedAt']}",
            f"- Discovery status: {report['discovery']['status']}",
            f"- Gate status: {report['gate']['status']}",
            f"- Overall decision: {overall_decision}",
        ]
    )
    report_markdown.write_text(markdown + "\n", encoding="utf-8")

    env_values = {
        "MB3R_REPORT_JSON": report_json.as_posix(),
        "MB3R_REPORT_MARKDOWN": report_markdown.as_posix(),
        "MB3R_REPORT_ARTIFACT": artifact_name,
        "MB3R_OVERALL_DECISION": overall_decision,
    }
    if env_path is not None:
        write_env(env_path, env_values)

    write_outputs(
        outputs_path,
        {
            "report-json": report_json.as_posix(),
            "report-markdown": report_markdown.as_posix(),
            "artifact-name": artifact_name,
            "overall-decision": overall_decision,
        },
    )
    report["reportJson"] = report_json.as_posix()
    report["reportMarkdown"] = report_markdown.as_posix()
    return report
