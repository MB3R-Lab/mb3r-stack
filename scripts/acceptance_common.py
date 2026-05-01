from __future__ import annotations

import json
import os
import platform
import shutil
import socket
import subprocess
import tarfile
import time
import urllib.request
import zipfile
from pathlib import Path
from typing import Any

import yaml

from common import ROOT

HELM_VERSION = "v3.16.4"
OTEL_DEMO_CHART_VERSION = "0.40.5"
KIND_VERSION = "v0.31.0"
BERING_VERSION = "0.3.2"
SHEAFT_VERSION = "0.2.2"

STACK_CHART_DIR = ROOT / "charts" / "mb3r-stack"
TOOLS_DIR = ROOT / ".tmp" / "tools-cache"


def check(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def run(
    command: list[str],
    *,
    cwd: Path = ROOT,
    env: dict[str, str] | None = None,
    capture: bool = True,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=capture,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"command failed ({result.returncode}): {' '.join(command)}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
    return result


def current_platform() -> tuple[str, str]:
    system = platform.system().lower()
    machine = platform.machine().lower()
    os_name = {"windows": "windows", "linux": "linux", "darwin": "darwin"}.get(system)
    if os_name is None:
        raise RuntimeError(f"unsupported platform: {platform.system()}")
    arch = {
        "amd64": "amd64",
        "x86_64": "amd64",
        "arm64": "arm64",
        "aarch64": "arm64",
    }.get(machine)
    if arch is None:
        raise RuntimeError(f"unsupported architecture: {platform.machine()}")
    return os_name, arch


def download(url: str, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url) as response:
        destination.write_bytes(response.read())
    return destination


def extract_archive(archive_path: Path, destination: Path) -> None:
    if archive_path.suffix == ".zip":
        with zipfile.ZipFile(archive_path) as handle:
            handle.extractall(destination)
        return
    with tarfile.open(archive_path, "r:*") as handle:
        handle.extractall(destination)


def os_environ() -> dict[str, str]:
    return dict(os.environ)


def reserve_local_port(*, exclude: set[int] | None = None) -> int:
    excluded = exclude or set()
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as handle:
            handle.bind(("127.0.0.1", 0))
            port = int(handle.getsockname()[1])
        if port not in excluded:
            return port


def ensure_helm() -> Path:
    explicit = os_environ().get("HELM_BIN")
    if explicit:
        helm = Path(explicit)
        check(helm.exists(), f"HELM_BIN does not exist: {helm}")
        return helm

    found = shutil.which("helm")
    if found:
        return Path(found)

    os_name, arch = current_platform()
    extension = "zip" if os_name == "windows" else "tar.gz"
    archive_name = f"helm-{HELM_VERSION}-{os_name}-{arch}.{extension}"
    archive_path = TOOLS_DIR / archive_name
    extract_dir = TOOLS_DIR / f"helm-{HELM_VERSION}-{os_name}-{arch}"
    binary_name = "helm.exe" if os_name == "windows" else "helm"
    binary_path = extract_dir / f"{os_name}-{arch}" / binary_name
    if binary_path.exists():
        return binary_path
    if extract_dir.exists():
        shutil.rmtree(extract_dir)
    if not archive_path.exists():
        print(f"[download] helm {HELM_VERSION}", flush=True)
        download(f"https://get.helm.sh/{archive_name}", archive_path)
    extract_dir.mkdir(parents=True, exist_ok=True)
    extract_archive(archive_path, extract_dir)
    check(binary_path.exists(), f"helm binary not found after extract: {binary_path}")
    return binary_path


def ensure_release_binary_for_platform(product: str, version: str, os_name: str, arch: str) -> Path:
    extension = "zip" if os_name == "windows" else "tar.gz"
    archive_name = f"{product}_{version}_{os_name}_{arch}.{extension}"
    archive_path = TOOLS_DIR / archive_name
    extract_dir = TOOLS_DIR / f"{product}-{version}-{os_name}-{arch}"
    binary_name = f"{product}.exe" if os_name == "windows" else product
    binary_path = extract_dir / binary_name
    if binary_path.exists():
        return binary_path
    if extract_dir.exists():
        shutil.rmtree(extract_dir)
    if not archive_path.exists():
        print(f"[download] {product} {version}", flush=True)
        download(
            f"https://github.com/MB3R-Lab/{product.capitalize()}/releases/download/v{version}/{archive_name}",
            archive_path,
        )
    extract_dir.mkdir(parents=True, exist_ok=True)
    extract_archive(archive_path, extract_dir)
    if binary_path.exists():
        return binary_path
    matches = list(extract_dir.rglob(binary_name))
    check(matches, f"{product} binary not found after extract")
    return matches[0]


def ensure_release_binary(product: str, version: str) -> Path:
    os_name, arch = current_platform()
    return ensure_release_binary_for_platform(product, version, os_name, arch)


def ensure_kind() -> Path:
    explicit = os_environ().get("KIND_BIN")
    if explicit:
        kind = Path(explicit)
        check(kind.exists(), f"KIND_BIN does not exist: {kind}")
        return kind

    found = shutil.which("kind")
    if found:
        return Path(found)

    os_name, arch = current_platform()
    asset_name = f"kind-{os_name}-{arch}"
    if os_name != "windows":
        binary_name = "kind"
    else:
        binary_name = "kind.exe"
    destination_dir = TOOLS_DIR / f"kind-{KIND_VERSION}-{os_name}-{arch}"
    binary_path = destination_dir / binary_name
    if binary_path.exists():
        return binary_path
    destination_dir.mkdir(parents=True, exist_ok=True)
    print(f"[download] kind {KIND_VERSION}", flush=True)
    download(f"https://github.com/kubernetes-sigs/kind/releases/download/{KIND_VERSION}/{asset_name}", binary_path)
    if os_name != "windows":
        binary_path.chmod(0o755)
    check(binary_path.exists(), f"kind binary not found after download: {binary_path}")
    return binary_path


def ensure_kubectl() -> Path:
    explicit = os_environ().get("KUBECTL_BIN")
    if explicit:
        kubectl = Path(explicit)
        check(kubectl.exists(), f"KUBECTL_BIN does not exist: {kubectl}")
        return kubectl

    found = shutil.which("kubectl")
    if found:
        return Path(found)

    os_name, arch = current_platform()
    binary_name = "kubectl.exe" if os_name == "windows" else "kubectl"
    destination_dir = TOOLS_DIR / f"kubectl-{os_name}-{arch}"
    binary_path = destination_dir / binary_name
    if binary_path.exists():
        return binary_path

    destination_dir.mkdir(parents=True, exist_ok=True)
    print("[download] kubectl stable", flush=True)
    stable_version = urllib.request.urlopen("https://dl.k8s.io/release/stable.txt").read().decode("utf-8").strip()
    download(f"https://dl.k8s.io/release/{stable_version}/bin/{os_name}/{arch}/{binary_name}", binary_path)
    if os_name != "windows":
        binary_path.chmod(0o755)
    check(binary_path.exists(), f"kubectl binary not found after download: {binary_path}")
    return binary_path


def helm_env(helm_root: Path) -> dict[str, str]:
    env = os_environ()
    repo_dir = helm_root.parent / "helm-repo"
    repo_cache = repo_dir / "repository"
    repo_dir.mkdir(parents=True, exist_ok=True)
    repo_cache.mkdir(parents=True, exist_ok=True)
    env["HELM_REPOSITORY_CONFIG"] = str(repo_dir / "repositories.yaml")
    env["HELM_REPOSITORY_CACHE"] = str(repo_cache)
    return env


def load_yaml_documents(text: str) -> list[dict[str, Any]]:
    documents: list[dict[str, Any]] = []
    for document in yaml.safe_load_all(text):
        if isinstance(document, dict):
            documents.append(document)
    return documents


def find_document(documents: list[dict[str, Any]], kind: str, name: str) -> dict[str, Any]:
    for document in documents:
        if document.get("kind") == kind and document.get("metadata", {}).get("name") == name:
            return document
    raise RuntimeError(f"missing document {kind}/{name}")


def maybe_find_document(documents: list[dict[str, Any]], kind: str, name: str) -> dict[str, Any] | None:
    for document in documents:
        if document.get("kind") == kind and document.get("metadata", {}).get("name") == name:
            return document
    return None


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def prepare_workdir(path: Path) -> Path:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)
    return path


def render_stack_chart(workdir: Path, values_path: Path, *, release_name: str = "mb3r") -> tuple[list[dict[str, Any]], Path, dict[str, str]]:
    helm = ensure_helm()
    environment = helm_env(helm)
    run([str(helm), "lint", str(STACK_CHART_DIR)], env=environment)
    rendered = run(
        [str(helm), "template", release_name, str(STACK_CHART_DIR), "-f", str(values_path)],
        env=environment,
    ).stdout
    write_text(workdir / "rendered" / "mb3r-stack.yaml", rendered)
    return load_yaml_documents(rendered), helm, environment


def render_otel_demo_chart(workdir: Path, values_path: Path, *, helm: Path, environment: dict[str, str]) -> list[dict[str, Any]]:
    run(
        [
            str(helm),
            "repo",
            "add",
            "open-telemetry",
            "https://open-telemetry.github.io/opentelemetry-helm-charts",
            "--force-update",
        ],
        env=environment,
    )
    run([str(helm), "repo", "update"], env=environment)
    rendered = run(
        [
            str(helm),
            "template",
            "otel-demo",
            "open-telemetry/opentelemetry-demo",
            "--version",
            OTEL_DEMO_CHART_VERSION,
            "-f",
            str(values_path),
        ],
        env=environment,
    ).stdout
    write_text(workdir / "rendered" / "opentelemetry-demo.yaml", rendered)
    return load_yaml_documents(rendered)


def synthetic_otlp_payload() -> dict[str, Any]:
    base = time.time_ns()
    trace_id = "11111111111111111111111111111111"

    def make_span(
        service: str,
        span_id: str,
        parent_span_id: str | None,
        name: str,
        kind: int,
        start_offset_ms: int,
        end_offset_ms: int,
        attributes: list[dict[str, Any]],
    ) -> dict[str, Any]:
        span: dict[str, Any] = {
            "traceId": trace_id,
            "spanId": span_id,
            "name": name,
            "kind": kind,
            "startTimeUnixNano": str(base + start_offset_ms * 1_000_000),
            "endTimeUnixNano": str(base + end_offset_ms * 1_000_000),
            "attributes": attributes,
        }
        if parent_span_id:
            span["parentSpanId"] = parent_span_id
        return {
            "resource": {"attributes": [{"key": "service.name", "value": {"stringValue": service}}]},
            "scopeSpans": [{"scope": {"name": "acceptance"}, "spans": [span]}],
        }

    return {
        "resourceSpans": [
            make_span(
                "frontend",
                "1111111111111111",
                None,
                "GET /checkout",
                2,
                0,
                100,
                [
                    {"key": "http.request.method", "value": {"stringValue": "GET"}},
                    {"key": "http.route", "value": {"stringValue": "/checkout"}},
                ],
            ),
            make_span(
                "checkout",
                "2222222222222222",
                "1111111111111111",
                "POST /place-order",
                2,
                10,
                90,
                [
                    {"key": "http.request.method", "value": {"stringValue": "POST"}},
                    {"key": "http.route", "value": {"stringValue": "/place-order"}},
                ],
            ),
            make_span("inventory", "3333333333333333", "2222222222222222", "reserve inventory", 3, 20, 40, []),
            make_span(
                "payment",
                "4444444444444444",
                "2222222222222222",
                "publish payment-events",
                4,
                20,
                30,
                [
                    {"key": "messaging.system", "value": {"stringValue": "rabbitmq"}},
                    {"key": "messaging.destination", "value": {"stringValue": "payment-events"}},
                ],
            ),
        ]
    }


def wait_for_http(url: str, *, attempts: int = 60, delay: float = 0.25) -> str:
    last_error = ""
    for _ in range(attempts):
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                return response.read().decode("utf-8", errors="replace")
        except Exception as exc:
            last_error = str(exc)
            time.sleep(delay)
    raise RuntimeError(f"timed out waiting for {url}: {last_error}")


def deep_copy(value: Any) -> Any:
    return json.loads(json.dumps(value))


def exercise_local_handoff(
    workdir: Path,
    *,
    bering_config: dict[str, Any],
    sheaft_config: dict[str, Any],
    sheaft_analysis_text: str,
) -> None:
    bering_bin = ensure_release_binary("bering", BERING_VERSION)
    sheaft_bin = ensure_release_binary("sheaft", SHEAFT_VERSION)

    runtime_dir = workdir / "runtime"
    artifacts_dir = runtime_dir / "artifacts"
    snapshots_dir = artifacts_dir / "snapshots"
    history_dir = runtime_dir / "history"
    sheaft_run_dir = runtime_dir / "sheaft-run"
    snapshots_dir.mkdir(parents=True)
    history_dir.mkdir(parents=True)

    local_bering_config = deep_copy(bering_config)
    local_sheaft_config = deep_copy(sheaft_config)
    bering_port = reserve_local_port()
    sheaft_port = reserve_local_port(exclude={bering_port})

    local_bering_config["server"]["listen_address"] = f":{bering_port}"
    local_bering_config["server"]["grpc_listen_address"] = ""
    local_bering_config["runtime"]["flush_interval"] = "2s"
    local_bering_config["runtime"]["window_size"] = "5s"
    local_bering_config["sink"]["directory"] = snapshots_dir.as_posix()
    local_bering_config["sink"]["latest_path"] = (artifacts_dir / "latest.json").as_posix()

    local_sheaft_config["listen"] = f":{sheaft_port}"
    local_sheaft_config["artifact"]["path"] = local_bering_config["sink"]["latest_path"]
    local_sheaft_config["poll_interval"] = "2s"
    local_sheaft_config["history"]["disk_dir"] = history_dir.as_posix()

    local_bering_config_path = runtime_dir / "bering-serve.yaml"
    local_sheaft_config_path = runtime_dir / "sheaft.yaml"
    local_sheaft_analysis_path = runtime_dir / "analysis.yaml"
    write_text(local_bering_config_path, yaml.safe_dump(local_bering_config, sort_keys=False))
    write_text(local_sheaft_config_path, yaml.safe_dump(local_sheaft_config, sort_keys=False))
    write_text(local_sheaft_analysis_path, sheaft_analysis_text)

    bering_log = (runtime_dir / "bering.log").open("w", encoding="utf-8")
    bering_proc = subprocess.Popen(
        [str(bering_bin), "serve", "--config", str(local_bering_config_path)],
        cwd=ROOT,
        stdout=bering_log,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        wait_for_http(f"http://127.0.0.1:{bering_port}/readyz")
        request = urllib.request.Request(
            f"http://127.0.0.1:{bering_port}/v1/traces",
            data=json.dumps(synthetic_otlp_payload()).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            check(response.status == 200, "Bering OTLP/HTTP endpoint did not accept the trace payload")

        latest_artifact = Path(local_bering_config["sink"]["latest_path"])
        for _ in range(90):
            if latest_artifact.exists():
                break
            time.sleep(0.5)
        check(latest_artifact.exists(), "Bering did not write the stable latest artifact")
        check(any(snapshots_dir.glob("*.json")), "Bering did not write rolling snapshot files")
    finally:
        bering_proc.terminate()
        try:
            bering_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            bering_proc.kill()
            bering_proc.wait(timeout=5)
        bering_log.close()

    run([str(bering_bin), "validate", "--input", str(latest_artifact)])

    run(
        [
            str(sheaft_bin),
            "run",
            "--model",
            str(latest_artifact),
            "--analysis",
            str(local_sheaft_analysis_path),
            "--out-dir",
            str(sheaft_run_dir),
        ]
    )
    check((sheaft_run_dir / "report.json").exists(), "Sheaft run did not write report.json")
    check((sheaft_run_dir / "summary.md").exists(), "Sheaft run did not write summary.md")
    check((sheaft_run_dir / "model.json").exists(), "Sheaft run did not write model.json")

    sheaft_log = (runtime_dir / "sheaft.log").open("w", encoding="utf-8")
    sheaft_proc = subprocess.Popen(
        [str(sheaft_bin), "serve", "--config", str(local_sheaft_config_path)],
        cwd=ROOT,
        stdout=sheaft_log,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        wait_for_http(f"http://127.0.0.1:{sheaft_port}/readyz")
        report = json.loads(wait_for_http(f"http://127.0.0.1:{sheaft_port}/current-report"))
        decision = report["policy_evaluation"]["decision"]
        check(decision in {"warn", "pass", "fail", "report"}, "Sheaft current-report is malformed")
        check(any(history_dir.glob("*.json")), "Sheaft serve mode did not persist history output")
    finally:
        sheaft_proc.terminate()
        try:
            sheaft_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            sheaft_proc.kill()
            sheaft_proc.wait(timeout=5)
        sheaft_log.close()
