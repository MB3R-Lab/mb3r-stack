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
from typing import TextIO

from acceptance_common import (
    BERING_VERSION,
    ROOT,
    SHEAFT_VERSION,
    check,
    ensure_helm,
    ensure_kind,
    ensure_kubectl,
    ensure_release_binary_for_platform,
    helm_env,
    synthetic_otlp_payload,
    wait_for_http,
)

PROFILE_VALUES = ROOT / "examples" / "profiles" / "synthetic-otlp" / "values.yaml"
CHART_DIR = ROOT / "charts" / "mb3r-stack"
WORKDIR_ROOT = ROOT / ".tmp" / "live-k8s-smoke"
CLUSTER_NAME = "mb3r-stack-smoke"
NAMESPACE = "mb3r-smoke"
RELEASE_NAME = "mb3r"
GHCR_PULL_SECRET_NAME = "mb3r-ghcr-pull"
CONTAINER_FAILURE_REASONS = {
    "CrashLoopBackOff",
    "CreateContainerConfigError",
    "CreateContainerError",
    "ErrImagePull",
    "ImagePullBackOff",
    "InvalidImageName",
    "RunContainerError",
}


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


def ensure_namespace(kubectl_bin: Path) -> None:
    result = subprocess.run(
        [str(kubectl_bin), "create", "namespace", NAMESPACE],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )
    if result.returncode == 0:
        return
    stderr = f"{result.stdout}\n{result.stderr}"
    if "AlreadyExists" in stderr:
        return
    raise RuntimeError(f"failed to create namespace {NAMESPACE}:\n{stderr}")


def ghcr_credentials() -> tuple[str, str] | None:
    explicit_username = os.environ.get("MB3R_GHCR_USERNAME")
    explicit_token = os.environ.get("MB3R_GHCR_TOKEN")
    if bool(explicit_username) != bool(explicit_token):
        raise RuntimeError(
            "both registry credentials must be set together: "
            "MB3R_GHCR_USERNAME + MB3R_GHCR_TOKEN"
        )
    if explicit_username and explicit_token:
        return explicit_username, explicit_token

    fallback_username = os.environ.get("GITHUB_ACTOR")
    fallback_token = os.environ.get("GITHUB_TOKEN")
    if fallback_username and fallback_token:
        return fallback_username, fallback_token
    return None


def configure_ghcr_pull_secret(kubectl_bin: Path, credentials: tuple[str, str] | None) -> list[str]:
    if credentials is None:
        return []

    username, token = credentials
    ensure_namespace(kubectl_bin)
    subprocess.run(
        [str(kubectl_bin), "delete", "secret", GHCR_PULL_SECRET_NAME, "-n", NAMESPACE, "--ignore-not-found"],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )
    run(
        [
            str(kubectl_bin),
            "create",
            "secret",
            "docker-registry",
            GHCR_PULL_SECRET_NAME,
            "-n",
            NAMESPACE,
            "--docker-server=ghcr.io",
            f"--docker-username={username}",
            f"--docker-password={token}",
        ]
    )
    return ["--set-string", f"global.imagePullSecrets[0].name={GHCR_PULL_SECRET_NAME}"]


def enrich_failure_message(message: str) -> str:
    if (
        "401 Unauthorized" in message
        or "403 Forbidden" in message
        or "failed to authorize" in message
    ):
        return (
            f"{message} "
            "Set MB3R_GHCR_USERNAME/MB3R_GHCR_TOKEN or GITHUB_ACTOR/GITHUB_TOKEN "
            "to validate authenticated pulls for pinned GHCR images. "
            "A 403 usually means the provided token does not have pull access to the upstream package."
        )
    return message


def build_local_image(product: str, version: str, image_ref: str) -> str:
    build_dir = WORKDIR_ROOT / "local" / "images" / product
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


def pod_name(kubectl_bin: Path, *, timeout_seconds: int = 240) -> str:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        result = run(
            [
                str(kubectl_bin),
                "get",
                "pods",
                "-n",
                NAMESPACE,
                "-l",
                "app.kubernetes.io/component=bering",
                "-o",
                "json",
            ],
            capture=True,
        )
        payload = json.loads(result.stdout)
        items = payload.get("items") or []
        if items:
            return items[0]["metadata"]["name"]
        time.sleep(2)
    raise RuntimeError("timed out waiting for the live smoke pod to be created")


def wait_for_container_ready(kubectl_bin: Path, pod: str, container_name: str, *, timeout_seconds: int = 240) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        result = run([str(kubectl_bin), "get", "pod", pod, "-n", NAMESPACE, "-o", "json"], capture=True)
        payload = json.loads(result.stdout)
        for status in payload.get("status", {}).get("containerStatuses", []):
            if status.get("name") != container_name:
                continue
            if status.get("ready") is True:
                return
            waiting = status.get("state", {}).get("waiting") or {}
            if waiting.get("reason") in CONTAINER_FAILURE_REASONS:
                reason = waiting.get("reason", "unknown")
                message = waiting.get("message", "").strip()
                raise RuntimeError(
                    f"container {container_name} in pod {pod} failed before ready: "
                    f"{reason}{': ' + enrich_failure_message(message) if message else ''}"
                )
            terminated = status.get("state", {}).get("terminated") or {}
            if terminated:
                reason = terminated.get("reason", "terminated")
                message = terminated.get("message", "").strip()
                raise RuntimeError(
                    f"container {container_name} in pod {pod} terminated before ready: "
                    f"{reason}{': ' + message if message else ''}"
                )
        time.sleep(2)
    raise RuntimeError(f"timed out waiting for container {container_name} in pod {pod} to become ready")


def wait_for_container_started(kubectl_bin: Path, pod: str, container_name: str, *, timeout_seconds: int = 240) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        result = run([str(kubectl_bin), "get", "pod", pod, "-n", NAMESPACE, "-o", "json"], capture=True)
        payload = json.loads(result.stdout)
        for status in payload.get("status", {}).get("containerStatuses", []):
            if status.get("name") != container_name:
                continue
            if status.get("ready") is True or status.get("state", {}).get("running"):
                return
            waiting = status.get("state", {}).get("waiting") or {}
            if waiting.get("reason") in CONTAINER_FAILURE_REASONS:
                reason = waiting.get("reason", "unknown")
                message = waiting.get("message", "").strip()
                raise RuntimeError(
                    f"container {container_name} in pod {pod} failed before start: "
                    f"{reason}{': ' + enrich_failure_message(message) if message else ''}"
                )
            terminated = status.get("state", {}).get("terminated") or {}
            if terminated:
                reason = terminated.get("reason", "terminated")
                message = terminated.get("message", "").strip()
                raise RuntimeError(
                    f"container {container_name} in pod {pod} terminated before start: "
                    f"{reason}{': ' + message if message else ''}"
                )
        time.sleep(2)
    raise RuntimeError(f"timed out waiting for container {container_name} in pod {pod} to start")


def wait_for_service_endpoints(kubectl_bin: Path, service_name: str, *, timeout_seconds: int = 180) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        result = run([str(kubectl_bin), "get", "endpoints", service_name, "-n", NAMESPACE, "-o", "json"], capture=True)
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


def cleanup(
    kind_bin: Path,
    keep_cluster: bool,
    workdir: Path,
    port_forwards: list[subprocess.Popen[str]],
    log_handles: list[TextIO],
) -> None:
    for process in port_forwards:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)

    for handle in log_handles:
        handle.close()

    if not keep_cluster:
        try:
            run([str(kind_bin), "delete", "cluster", "--name", CLUSTER_NAME])
        except Exception:
            pass

    if workdir.exists():
        shutil.rmtree(workdir, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a live generic Kubernetes smoke against a kind cluster.")
    parser.add_argument(
        "--image-source",
        choices=("local", "pinned"),
        default="local",
        help="Use locally rebuilt images from release binaries or the chart's pinned GHCR images.",
    )
    parser.add_argument("--keep-cluster", action="store_true", help="Preserve the kind cluster after the run.")
    args = parser.parse_args()

    keep_cluster = args.keep_cluster or os.environ.get("MB3R_KEEP_CLUSTER") == "1"
    image_source = args.image_source
    scenario_name = f"k8s-smoke-generic-{image_source}"
    kind_bin = ensure_kind()
    kubectl_bin = ensure_kubectl()
    helm_bin = ensure_helm()
    helm_environment = helm_env(helm_bin)
    port_forwards: list[subprocess.Popen[str]] = []
    log_handles: list[TextIO] = []
    workdir = WORKDIR_ROOT / image_source

    if workdir.exists():
        shutil.rmtree(workdir, ignore_errors=True)
    workdir.mkdir(parents=True, exist_ok=True)

    try:
        run([str(kind_bin), "delete", "cluster", "--name", CLUSTER_NAME])
    except Exception:
        pass

    try:
        print("[cluster] create kind cluster", flush=True)
        run([str(kind_bin), "create", "cluster", "--name", CLUSTER_NAME, "--wait", "180s"], capture=True)

        image_overrides: list[str] = []
        if image_source == "local":
            print("[images] build and load local Bering and Sheaft images", flush=True)
            bering_image = build_local_image("bering", BERING_VERSION, "mb3r-local/bering:live-smoke")
            sheaft_image = build_local_image("sheaft", SHEAFT_VERSION, "mb3r-local/sheaft:live-smoke")
            run([str(kind_bin), "load", "docker-image", "--name", CLUSTER_NAME, bering_image, sheaft_image])
            image_overrides = [
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
            ]
        else:
            pull_secret_args = configure_ghcr_pull_secret(kubectl_bin, ghcr_credentials())
            if pull_secret_args:
                print("[images] use chart-pinned GHCR images with authenticated pull secret", flush=True)
                image_overrides = pull_secret_args
            else:
                print("[images] use chart-pinned GHCR images with anonymous pull", flush=True)

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
                *image_overrides,
            ],
            env=helm_environment,
        )

        pod = pod_name(kubectl_bin)
        wait_for_container_ready(kubectl_bin, pod, "bering")
        wait_for_container_started(kubectl_bin, pod, "sheaft")

        print("[verify] port-forward live smoke pod", flush=True)
        port_forward_log = (workdir / "pod-port-forward.log").open("w", encoding="utf-8")
        log_handles.append(port_forward_log)
        port_forwards.append(
            subprocess.Popen(
                [str(kubectl_bin), "port-forward", f"pod/{pod}", "14318:4318", "18080:8080", "-n", NAMESPACE],
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
        wait_for_service_endpoints(kubectl_bin, "bering-discovery")
        wait_for_service_endpoints(kubectl_bin, "sheaft-reports")

        print(f"{scenario_name}: ok")
        return 0
    except Exception as exc:
        print(f"{scenario_name}: failed: {exc}", file=sys.stderr)
        return 1
    finally:
        cleanup(kind_bin, keep_cluster, workdir, port_forwards, log_handles)


if __name__ == "__main__":
    raise SystemExit(main())
