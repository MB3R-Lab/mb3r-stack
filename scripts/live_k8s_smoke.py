from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from acceptance_common import (
    BERING_VERSION,
    ROOT,
    SHEAFT_VERSION,
    check,
    ensure_helm,
    ensure_kind,
    ensure_release_binary_for_platform,
    helm_env,
    synthetic_otlp_payload,
    wait_for_http,
)

PROFILE_VALUES = ROOT / "examples" / "profiles" / "synthetic-otlp" / "values.yaml"
CHART_DIR = ROOT / "charts" / "mb3r-stack"
WORKDIR = ROOT / ".tmp" / "live-k8s-smoke"
CLUSTER_NAME = "mb3r-stack-smoke"
NAMESPACE = "mb3r-smoke"
RELEASE_NAME = "mb3r"


def run(
    command: list[str],
    *,
    env: dict[str, str] | None = None,
    capture: bool = True,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=ROOT,
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


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_local_image(product: str, version: str, image_ref: str) -> str:
    build_dir = WORKDIR / "images" / product
    build_dir.mkdir(parents=True, exist_ok=True)
    binary_path = ensure_release_binary_for_platform(product, version, "linux", "amd64")
    target_binary = build_dir / product
    shutil.copyfile(binary_path, target_binary)
    dockerfile = (
        "FROM debian:bookworm-slim\n"
        f"COPY {product} /usr/local/bin/{product}\n"
        f"RUN chmod +x /usr/local/bin/{product}\n"
        f'ENTRYPOINT ["/usr/local/bin/{product}"]\n'
    )
    write_text(build_dir / "Dockerfile", dockerfile)
    run(["docker", "build", "-t", image_ref, str(build_dir)])
    return image_ref


def wait_for_json(url: str, *, attempts: int = 120, delay: float = 1.0) -> dict[str, object]:
    last_error = ""
    for _ in range(attempts):
        try:
            with urllib.request.urlopen(url, timeout=3) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            last_error = str(exc)
            time.sleep(delay)
    raise RuntimeError(f"timed out waiting for JSON response from {url}: {last_error}")


def wait_for_port_forward(url: str) -> None:
    wait_for_http(url, attempts=120, delay=0.5)


def pod_name() -> str:
    result = run(
        [
            "kubectl",
            "get",
            "pods",
            "-n",
            NAMESPACE,
            "-l",
            "app.kubernetes.io/component=bering",
            "-o",
            "jsonpath={.items[0].metadata.name}",
        ]
    )
    name = result.stdout.strip()
    check(name != "", "failed to resolve live smoke pod name")
    return name


def wait_for_container_ready(pod: str, container_name: str, *, timeout_seconds: int = 240) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        result = run(["kubectl", "get", "pod", pod, "-n", NAMESPACE, "-o", "json"], capture=True)
        payload = json.loads(result.stdout)
        for status in payload.get("status", {}).get("containerStatuses", []):
            if status.get("name") == container_name and status.get("ready") is True:
                return
        time.sleep(2)
    raise RuntimeError(f"timed out waiting for container {container_name} in pod {pod} to become ready")


def wait_for_service_endpoints(service_name: str, *, timeout_seconds: int = 180) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        result = run(["kubectl", "get", "endpoints", service_name, "-n", NAMESPACE, "-o", "json"], capture=True)
        payload = json.loads(result.stdout)
        subsets = payload.get("subsets") or []
        if any(subset.get("addresses") for subset in subsets):
            return
        time.sleep(2)
    raise RuntimeError(f"timed out waiting for endpoints on service {service_name}")


def post_trace_payload() -> None:
    request = urllib.request.Request(
        "http://127.0.0.1:14318/v1/traces",
        data=json.dumps(synthetic_otlp_payload()).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        check(response.status == 200, "Bering live-cluster OTLP/HTTP endpoint rejected the trace payload")


def cleanup(kind_bin: Path, keep_cluster: bool, port_forwards: list[subprocess.Popen[str]]) -> None:
    for process in port_forwards:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)

    if not keep_cluster:
        try:
            run([str(kind_bin), "delete", "cluster", "--name", CLUSTER_NAME])
        except Exception:
            pass

    if WORKDIR.exists():
        shutil.rmtree(WORKDIR, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a live generic Kubernetes smoke against a kind cluster.")
    parser.add_argument("--keep-cluster", action="store_true", help="Preserve the kind cluster after the run.")
    args = parser.parse_args()

    keep_cluster = args.keep_cluster or os.environ.get("MB3R_KEEP_CLUSTER") == "1"
    kind_bin = ensure_kind()
    helm_bin = ensure_helm()
    helm_environment = helm_env(helm_bin)
    port_forwards: list[subprocess.Popen[str]] = []

    if WORKDIR.exists():
        shutil.rmtree(WORKDIR, ignore_errors=True)
    WORKDIR.mkdir(parents=True, exist_ok=True)

    try:
        run([str(kind_bin), "delete", "cluster", "--name", CLUSTER_NAME])
    except Exception:
        pass

    try:
        print("[cluster] create kind cluster", flush=True)
        run([str(kind_bin), "create", "cluster", "--name", CLUSTER_NAME, "--wait", "180s"], capture=True)

        print("[images] build and load local Bering and Sheaft images", flush=True)
        bering_image = build_local_image("bering", BERING_VERSION, "mb3r-local/bering:live-smoke")
        sheaft_image = build_local_image("sheaft", SHEAFT_VERSION, "mb3r-local/sheaft:live-smoke")
        run([str(kind_bin), "load", "docker-image", "--name", CLUSTER_NAME, bering_image, sheaft_image])

        print("[deploy] install generic synthetic profile", flush=True)
        run(
            [
                str(helm_bin),
                "upgrade",
                "--install",
                RELEASE_NAME,
                str(CHART_DIR),
                "--namespace",
                NAMESPACE,
                "--create-namespace",
                "-f",
                str(PROFILE_VALUES),
                "--set-string",
                "bering.image.repository=mb3r-local/bering",
                "--set-string",
                "bering.image.tag=live-smoke",
                "--set-string",
                "bering.image.digest=",
                "--set-string",
                "sheaft.image.repository=mb3r-local/sheaft",
                "--set-string",
                "sheaft.image.tag=live-smoke",
                "--set-string",
                "sheaft.image.digest=",
            ],
            env=helm_environment,
        )

        pod = pod_name()
        wait_for_container_ready(pod, "bering")

        print("[verify] port-forward live smoke pod", flush=True)
        port_forward_log = (WORKDIR / "pod-port-forward.log").open("w", encoding="utf-8")
        port_forwards.append(
            subprocess.Popen(
                ["kubectl", "port-forward", f"pod/{pod}", "14318:4318", "18080:8080", "-n", NAMESPACE],
                cwd=ROOT,
                stdout=port_forward_log,
                stderr=subprocess.STDOUT,
                text=True,
            )
        )

        wait_for_port_forward("http://127.0.0.1:14318/readyz")

        print("[verify] post synthetic OTLP payload", flush=True)
        post_trace_payload()

        print("[verify] wait for Sheaft report", flush=True)
        report = wait_for_json("http://127.0.0.1:18080/current-report")
        decision = report["policy_evaluation"]["decision"]
        check(decision in {"warn", "pass", "fail", "report"}, "Sheaft live-cluster current-report is malformed")
        wait_for_service_endpoints("bering-discovery")
        wait_for_service_endpoints("sheaft-reports")

        print("k8s-smoke-generic: ok")
        return 0
    except Exception as exc:
        print(f"k8s-smoke-generic: failed: {exc}", file=sys.stderr)
        return 1
    finally:
        cleanup(kind_bin, keep_cluster, port_forwards)


if __name__ == "__main__":
    raise SystemExit(main())
