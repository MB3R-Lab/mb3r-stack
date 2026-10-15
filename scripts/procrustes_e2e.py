"""Integration checks, not paper experiments: packaged preflight and overlay handoff."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

import yaml

from acceptance_common import BERING_VERSION, ROOT, ensure_release_binary
from common import check, stack_manifest
from package_assets import package_assets


def main() -> int:
    with tempfile.TemporaryDirectory() as temporary:
        work = Path(temporary)
        archive = package_assets(work)
        with tarfile.open(archive) as package:
            package.extractall(work, filter="data")
        extracted = work / "mb3r-assets"
        launcher = extracted / "scripts" / "procrustes.py"
        subprocess.run([sys.executable, str(launcher), "--example"], check=True)
        output = extracted / ".tmp" / "preflight"
        report = json.loads((output / "report.json").read_text())
        check(report["goal_status"] == "EXPECTED", "ready fixture must pass")
        for name in ("summary.md", "collection-plan.json", "bering.overlay.yaml"):
            check((output / name).is_file(), f"missing preflight handoff {name}")
        overlay = yaml.safe_load((output / "bering.overlay.yaml").read_text())
        check(not overlay.get("edges"), "static preflight must not invent runtime edges")

        commit = stack_manifest()["components"]["procrustes"]["source"]["commit"]
        source = extracted / ".tmp" / "procrustes" / commit / "source"
        blocked = work / "blocked"
        shutil.copytree(source / "testdata" / "ready", blocked)
        (blocked / "checkout.yaml").unlink()
        rejected = subprocess.run([sys.executable, str(launcher), "--", "analyze",
            "--source", f"blocked={blocked}", "--goal", str(blocked / "goal.yaml"),
            "--out-dir", str(work / "rejected"), "--fail-on-blocked"], check=False)
        check(rejected.returncode == 2, "launcher must propagate BLOCKED exit code 2")
        blocked_report = json.loads((work / "rejected" / "report.json").read_text())
        check(blocked_report["goal_status"] == "BLOCKED", "missing scenario must be blocked")

        traces = work / "traces.json"
        traces.write_text(json.dumps({"spans": [
            {"trace_id": "stack-smoke", "span_id": "1", "service": "frontend",
             "kind": "server", "name": "GET /checkout",
             "attributes": {"http.request.method": "GET", "http.route": "/checkout"}},
            {"trace_id": "stack-smoke", "span_id": "2", "parent_span_id": "1",
             "service": "checkout", "kind": "server", "name": "checkout"}
        ]}))
        bering = ensure_release_binary("bering", BERING_VERSION)
        model_path = work / "model.json"
        subprocess.run([str(bering), "discover", "--input", str(traces), "--overlay",
            str(output / "bering.overlay.yaml"), "--out", str(model_path)], check=True)
        subprocess.run([str(bering), "validate", "--input", str(model_path)], check=True)
        model = json.loads(model_path.read_text())
        check(any(endpoint["id"] == "frontend:GET /checkout" for endpoint in model["endpoints"]),
              "Bering must preserve the preflight operation")
        check(bool(model["edges"]), "Bering must discover the observed runtime edge")
    print("procrustes-stack-e2e-ok ready=EXPECTED missing-scenario=BLOCKED overlay=accepted")
    return 0


if __name__ == "__main__":
    sys.exit(main())
