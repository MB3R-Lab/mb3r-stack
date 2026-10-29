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

        ebpf_output = work / "ebpf-preflight"
        subprocess.run([sys.executable, str(launcher), "--", "analyze",
            "--source", f"ready={source / 'testdata' / 'ready'}",
            "--goal", str(source / "testdata" / "ready" / "goal.yaml"),
            "--collection-source", "ebpf-obi", "--source-domain", "stack-handoff",
            "--out-dir", str(ebpf_output)], check=True)
        ebpf_report = json.loads((ebpf_output / "report.json").read_text())
        ebpf_plan = json.loads((ebpf_output / "collection-plan.json").read_text())
        check(ebpf_report["goal_status"] == "PARTIAL", "declared OBI coverage must remain partial")
        check(ebpf_report["contract"]["version"] == "0.2.0" and ebpf_plan["contract"]["version"] == "0.2.0",
              "OBI handoff must use its explicit report and plan contracts")
        check(len(ebpf_plan["trace_sources"]) == 1 and ebpf_plan["trace_sources"][0]["bering_input"] == "ebpf-obi"
              and ebpf_plan["trace_sources"][0]["domain"] == "stack-handoff",
              "collection source and domain must survive the packaged launcher")
        ebpf_overlay = yaml.safe_load((ebpf_output / "bering.overlay.yaml").read_text())
        check(not ebpf_overlay.get("edges"), "OBI preflight must not invent runtime edges")

        # Synthetic collector-format input checks the handoff; actual kernel
        # attachment is validated by the upstream Bering collector smoke.
        raw_export = work / "raw-obi-export.json"
        raw_export.write_text(json.dumps({"resourceSpans": [
            {"resource": {"attributes": [{"key": "service.name", "value": {"stringValue": service}}]},
             "scopeSpans": [{"spans": [{
                 "traceId": "00000000000000000000000000000001", "spanId": span,
                 **({"parentSpanId": "0000000000000001"} if service == "checkout" else {}),
                 "kind": "SPAN_KIND_SERVER", "name": "GET /checkout" if service == "frontend" else "process",
                 "attributes": ([{"key": "http.request.method", "value": {"stringValue": "GET"}},
                                 {"key": "http.route", "value": {"stringValue": "/checkout"}}]
                                if service == "frontend" else []),
             }]}]}
            for service, span in (("frontend", "0000000000000001"), ("checkout", "0000000000000002"))
        ]}))
        ebpf_model, ebpf_snapshot = work / "ebpf-model.json", work / "ebpf-snapshot.json"
        subprocess.run([str(bering), "discover", "--input", str(raw_export), "--input-type", "ebpf-obi",
            "--source-domain", "stack-handoff", "--overlay", str(ebpf_output / "bering.overlay.yaml"),
            "--out", str(ebpf_model), "--snapshot-out", str(ebpf_snapshot)], check=True)
        for artifact in (ebpf_model, ebpf_snapshot):
            subprocess.run([str(bering), "validate", "--input", str(artifact)], check=True)
        discovered = json.loads(ebpf_snapshot.read_text())
        check(any(item.get("type") == "ebpf" and item.get("connector") == "obi"
                  for item in discovered["sources"]), "Bering must retain declared collector provenance")
        check(any(edge["from"] == "frontend" and edge["to"] == "checkout"
                  for edge in discovered["model"]["edges"]), "Bering must recover the synthetic observed call")

        generic_output = work / "generic-ebpf-preflight"
        subprocess.run([sys.executable, str(launcher), "--", "analyze",
            "--source", f"ready={source / 'testdata' / 'ready'}",
            "--goal", str(source / "testdata" / "ready" / "goal.yaml"),
            "--collection-source", "ebpf-otlp", "--source-domain", "stack-handoff",
            "--out-dir", str(generic_output)], check=True)
        generic_report = json.loads((generic_output / "report.json").read_text())
        generic_plan = json.loads((generic_output / "collection-plan.json").read_text())
        check(generic_report["goal_status"] == "PARTIAL",
              "generic eBPF runtime capabilities must remain partial")
        check(generic_report["contract"]["version"] == "0.3.0"
              and generic_plan["contract"]["version"] == "0.3.0",
              "generic eBPF handoff must use report and plan contracts 0.3.0")
        check(len(generic_plan["trace_sources"]) == 1
              and generic_plan["trace_sources"][0]["bering_input"] == "ebpf-otlp"
              and generic_plan["trace_sources"][0]["domain"] == "stack-handoff",
              "generic source kind and domain must survive the packaged launcher")
        generic_serialized = json.dumps(generic_plan, sort_keys=True)
        check('"collector"' not in generic_serialized and '"vendor"' not in generic_serialized,
              "generic handoff must not add a collector or vendor parameter")
        generic_overlay = yaml.safe_load((generic_output / "bering.overlay.yaml").read_text())
        check(not generic_overlay.get("edges"), "generic preflight must not invent runtime edges")

        generic_model = work / "generic-ebpf-model.json"
        generic_snapshot = work / "generic-ebpf-snapshot.json"
        subprocess.run([str(bering), "discover", "--input", str(raw_export),
            "--input-type", "ebpf-otlp", "--source-id", "telemetry-main",
            "--source-domain", "stack-handoff",
            "--overlay", str(generic_output / "bering.overlay.yaml"),
            "--out", str(generic_model), "--snapshot-out", str(generic_snapshot)], check=True)
        for artifact in (generic_model, generic_snapshot):
            subprocess.run([str(bering), "validate", "--input", str(artifact)], check=True)
        generic_discovered = json.loads(generic_snapshot.read_text())
        check(any(item.get("type") == "ebpf" and item.get("connector") == "ebpf-otlp"
                  for item in generic_discovered["sources"]),
              "Bering must retain generic eBPF OTLP source provenance")
        check(any(edge["from"] == "frontend" and edge["to"] == "checkout"
                  for edge in generic_discovered["model"]["edges"]),
              "Bering must recover the synthetic generic observed call")
    print("procrustes-stack-e2e-ok ready=EXPECTED missing-scenario=BLOCKED overlay=accepted ebpf-obi=PARTIAL ebpf-otlp=PARTIAL sources=accepted")
    return 0


if __name__ == "__main__":
    sys.exit(main())
