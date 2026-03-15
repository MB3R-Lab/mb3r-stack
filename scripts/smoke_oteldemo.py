from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from typing import Any

import yaml

from common import ROOT

HELM_VERSION = "v3.16.4"
OTEL_DEMO_CHART_VERSION = "0.40.5"
BERING_VERSION = "0.1.0"
SHEAFT_VERSION = "0.1.1"

WORKDIR = ROOT / ".tmp" / "smoke-oteldemo"
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
    ext = "zip" if os_name == "windows" else "tar.gz"
    archive_name = f"helm-{HELM_VERSION}-{os_name}-{arch}.{ext}"
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


def ensure_release_binary(product: str, version: str) -> Path:
    os_name, arch = current_platform()
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


def os_environ() -> dict[str, str]:
    return dict(**{k: v for k, v in os.environ.items()})


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
    docs: list[dict[str, Any]] = []
    for document in yaml.safe_load_all(text):
        if isinstance(document, dict):
            docs.append(document)
    return docs


def find_document(documents: list[dict[str, Any]], kind: str, name: str) -> dict[str, Any]:
    for document in documents:
        if document.get("kind") == kind and document.get("metadata", {}).get("name") == name:
            return document
    raise RuntimeError(f"missing document {kind}/{name}")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


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
            "scopeSpans": [{"scope": {"name": "smoke"}, "spans": [span]}],
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
        except Exception as exc:  # pragma: no cover - network retry
            last_error = str(exc)
            time.sleep(delay)
    raise RuntimeError(f"timed out waiting for {url}: {last_error}")


def main() -> int:
    if WORKDIR.exists():
        shutil.rmtree(WORKDIR)
    WORKDIR.mkdir(parents=True)

    helm = ensure_helm()
    helm_environment = helm_env(helm)
    run(
        [str(helm), "repo", "add", "open-telemetry", "https://open-telemetry.github.io/opentelemetry-helm-charts", "--force-update"],
        env=helm_environment,
    )
    run([str(helm), "repo", "update"], env=helm_environment)

    print("[check] helm lint addon chart", flush=True)
    run([str(helm), "lint", str(ROOT / "charts" / "mb3r-otel-addon")], env=helm_environment)

    print("[check] render addon chart", flush=True)
    addon_render = run(
        [
            str(helm),
            "template",
            "mb3r",
            str(ROOT / "charts" / "mb3r-otel-addon"),
            "-f",
            str(ROOT / "examples" / "otel-demo" / "mb3r-values.yaml"),
        ],
        env=helm_environment,
    ).stdout
    write_text(WORKDIR / "rendered" / "mb3r-addon.yaml", addon_render)
    addon_docs = load_yaml_documents(addon_render)

    print("[check] render OTel Demo chart", flush=True)
    otel_render = run(
        [
            str(helm),
            "template",
            "otel-demo",
            "open-telemetry/opentelemetry-demo",
            "--version",
            OTEL_DEMO_CHART_VERSION,
            "-f",
            str(ROOT / "examples" / "otel-demo" / "opentelemetry-demo-values.yaml"),
        ],
        env=helm_environment,
    ).stdout
    write_text(WORKDIR / "rendered" / "opentelemetry-demo.yaml", otel_render)
    otel_docs = load_yaml_documents(otel_render)

    bering_deployment = find_document(addon_docs, "Deployment", "mb3r-otel-addon-bering")
    bering_service = find_document(addon_docs, "Service", "mb3r-otel-addon-bering")
    sheaft_service = find_document(addon_docs, "Service", "mb3r-otel-addon-sheaft")
    bering_cfg = find_document(addon_docs, "ConfigMap", "mb3r-otel-addon-bering-config")
    sheaft_cfg = find_document(addon_docs, "ConfigMap", "mb3r-otel-addon-sheaft-config")

    try:
        find_document(addon_docs, "Deployment", "mb3r-otel-addon-sheaft")
        raise RuntimeError("otel-demo example should not render a standalone Sheaft deployment")
    except RuntimeError:
        pass

    bering_service_ports = bering_service["spec"]["ports"]
    check(len(bering_service_ports) == 1, "Bering service must expose only the HTTP port by default")
    check(bering_service_ports[0]["name"] == "http", "Bering service must expose HTTP as the canonical port")
    check(bering_service_ports[0]["port"] == 4318, "Bering HTTP service port must be 4318")
    check("/metrics" == bering_service["metadata"]["annotations"]["prometheus.io/path"], "Bering metrics path must be /metrics")

    sheaft_service_ports = sheaft_service["spec"]["ports"]
    check(len(sheaft_service_ports) == 1 and sheaft_service_ports[0]["port"] == 8080, "Sheaft service must expose only the HTTP port")

    containers = {container["name"]: container for container in bering_deployment["spec"]["template"]["spec"]["containers"]}
    check(set(containers) == {"bering", "sheaft"}, "Bering deployment must co-locate Sheaft in the otel-demo path")
    check(containers["bering"]["args"][:2] == ["serve", "--config"], "Bering must run in serve mode with an explicit config")
    check(containers["sheaft"]["args"][:2] == ["serve", "--config"], "Sheaft must run in serve mode with an explicit config")
    check(containers["bering"]["readinessProbe"]["httpGet"]["path"] == "/readyz", "Bering readiness probe must target /readyz")
    check(containers["sheaft"]["readinessProbe"]["httpGet"]["path"] == "/readyz", "Sheaft readiness probe must target /readyz")
    check(any(mount["name"] == "shared-artifacts" for mount in containers["bering"]["volumeMounts"]), "Bering must mount the shared artifacts volume")
    check(any(mount["name"] == "shared-artifacts" for mount in containers["sheaft"]["volumeMounts"]), "Sheaft must mount the shared artifacts volume")

    bering_config = yaml.safe_load(bering_cfg["data"]["serve.yaml"])
    sheaft_analysis_text = sheaft_cfg["data"]["analysis.yaml"]
    sheaft_config = yaml.safe_load(sheaft_cfg["data"]["sheaft.yaml"])
    check(bering_config["server"]["listen_address"] == ":4318", "Bering config must listen on OTLP/HTTP 4318")
    check(bering_config["sink"]["latest_path"] == "/var/lib/mb3r/bering/latest.json", "Bering config must publish a stable latest snapshot path")
    check(sheaft_config["artifact"]["path"] == "/var/lib/mb3r/bering/latest.json", "Sheaft config must watch the Bering latest artifact")

    collector_cfg_map = find_document(otel_docs, "ConfigMap", "otel-collector-agent")
    collector_cfg = yaml.safe_load(collector_cfg_map["data"]["relay"])
    exporters = collector_cfg["service"]["pipelines"]["traces"]["exporters"]
    metrics_exporters = collector_cfg["service"]["pipelines"]["metrics"]["exporters"]
    logs_exporters = collector_cfg["service"]["pipelines"]["logs"]["exporters"]
    check("otlphttp/bering" in exporters, "OTel Demo traces pipeline must include otlphttp/bering")
    check("spanmetrics" in exporters, "OTel Demo traces pipeline must preserve spanmetrics")
    check("otlp/jaeger" in exporters and "debug" in exporters, "OTel Demo traces pipeline must preserve default exporters")
    check("otlphttp/bering" not in metrics_exporters, "OTel Demo metrics pipeline must not export to Bering")
    check("otlphttp/bering" not in logs_exporters, "OTel Demo logs pipeline must not export to Bering")
    check(
        collector_cfg["exporters"]["otlphttp/bering"]["endpoint"] == "http://mb3r-otel-addon-bering:4318",
        "OTel Demo collector must target Bering over OTLP/HTTP",
    )
    check(
        "spanmetrics" in collector_cfg["service"]["pipelines"]["metrics"]["receivers"],
        "OTel Demo metrics pipeline must still receive spanmetrics output",
    )

    bering_bin = ensure_release_binary("bering", BERING_VERSION)
    sheaft_bin = ensure_release_binary("sheaft", SHEAFT_VERSION)

    runtime_dir = WORKDIR / "runtime"
    artifacts_dir = runtime_dir / "artifacts"
    snapshots_dir = artifacts_dir / "snapshots"
    history_dir = runtime_dir / "history"
    sheaft_run_dir = runtime_dir / "sheaft-run"
    snapshots_dir.mkdir(parents=True)
    history_dir.mkdir(parents=True)

    local_bering_config = dict(bering_config)
    local_bering_config["server"]["listen_address"] = ":14318"
    local_bering_config["server"]["grpc_listen_address"] = ""
    local_bering_config["runtime"]["flush_interval"] = "2s"
    local_bering_config["runtime"]["window_size"] = "5s"
    local_bering_config["sink"]["directory"] = snapshots_dir.as_posix()
    local_bering_config["sink"]["latest_path"] = (artifacts_dir / "latest.json").as_posix()

    local_sheaft_config = dict(sheaft_config)
    local_sheaft_config["listen"] = ":18080"
    local_sheaft_config["artifact"]["path"] = local_bering_config["sink"]["latest_path"]
    local_sheaft_config["poll_interval"] = "2s"
    local_sheaft_config["history"]["disk_dir"] = history_dir.as_posix()

    local_bering_config_path = runtime_dir / "bering-serve.yaml"
    local_sheaft_config_path = runtime_dir / "sheaft.yaml"
    local_sheaft_analysis_path = runtime_dir / "analysis.yaml"
    write_text(local_bering_config_path, yaml.safe_dump(local_bering_config, sort_keys=False))
    write_text(local_sheaft_config_path, yaml.safe_dump(local_sheaft_config, sort_keys=False))
    write_text(local_sheaft_analysis_path, sheaft_analysis_text)

    print("[check] Bering OTLP/HTTP ingest -> snapshot", flush=True)
    bering_log = (runtime_dir / "bering.log").open("w", encoding="utf-8")
    bering_proc = subprocess.Popen(
        [str(bering_bin), "serve", "--config", str(local_bering_config_path)],
        cwd=ROOT,
        stdout=bering_log,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        wait_for_http("http://127.0.0.1:14318/readyz")
        request = urllib.request.Request(
            "http://127.0.0.1:14318/v1/traces",
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

    print("[check] Sheaft batch run on Bering artifact", flush=True)
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

    print("[check] Sheaft watch/serve handoff", flush=True)
    sheaft_log = (runtime_dir / "sheaft.log").open("w", encoding="utf-8")
    sheaft_proc = subprocess.Popen(
        [str(sheaft_bin), "serve", "--config", str(local_sheaft_config_path)],
        cwd=ROOT,
        stdout=sheaft_log,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        wait_for_http("http://127.0.0.1:18080/readyz")
        report_body = wait_for_http("http://127.0.0.1:18080/current-report")
        report = json.loads(report_body)
        check(report["policy_evaluation"]["decision"] in {"warn", "pass", "fail", "report"}, "Sheaft current-report is malformed")
        check(any(history_dir.glob("*.json")), "Sheaft serve mode did not persist history output")
    finally:
        sheaft_proc.terminate()
        try:
            sheaft_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            sheaft_proc.kill()
            sheaft_proc.wait(timeout=5)
        sheaft_log.close()

    print("smoke-otel-demo: ok")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - CLI failure path
        print(f"smoke-otel-demo: failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
