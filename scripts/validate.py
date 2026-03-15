from __future__ import annotations

import argparse
import compileall
import shutil
import sys
import tempfile
from pathlib import Path

from common import ROOT, check, load_json, load_yaml, maybe_run_command, validate_schema


def validate_python() -> None:
    compiled = compileall.compile_dir(str(ROOT / "scripts"), quiet=1)
    check(compiled, "Python scripts failed to compile")


def validate_json_contracts() -> None:
    validate_schema(ROOT / "compat" / "stack-manifest.json", ROOT / "schemas" / "stack-manifest.schema.json")
    validate_schema(
        ROOT / "compat" / "compatibility-matrix.json",
        ROOT / "schemas" / "compatibility-matrix.schema.json",
    )


def validate_chart() -> None:
    chart_dir = ROOT / "charts" / "mb3r-stack"
    required = [
        chart_dir / "Chart.yaml",
        chart_dir / "values.yaml",
        chart_dir / "templates" / "_helpers.tpl",
        chart_dir / "templates" / "collector-snippets-configmap.yaml",
        chart_dir / "templates" / "bering-deployment.yaml",
        chart_dir / "templates" / "sheaft-deployment.yaml",
        chart_dir / "templates" / "public-services.yaml",
        chart_dir / "templates" / "NOTES.txt",
    ]
    for path in required:
        check(path.exists(), f"Missing chart file {path.relative_to(ROOT)}")

    metadata = load_yaml(chart_dir / "Chart.yaml")
    check(metadata["name"] == "mb3r-stack", "Chart name must be mb3r-stack")
    load_yaml(chart_dir / "values.yaml")

    if shutil.which("helm"):
        result = maybe_run_command(["helm", "lint", str(chart_dir)])
        if result.returncode != 0:
            raise ValueError((result.stdout + result.stderr).strip())
        for values_path in (
            ROOT / "examples" / "profiles" / "synthetic-otlp" / "values.yaml",
            ROOT / "examples" / "profiles" / "minimal-production-eval" / "values.yaml",
            ROOT / "examples" / "profiles" / "otel-demo" / "mb3r-values.yaml",
        ):
            render = maybe_run_command(["helm", "template", "mb3r", str(chart_dir), "-f", str(values_path)])
            if render.returncode != 0:
                raise ValueError((render.stdout + render.stderr).strip())

    with tempfile.TemporaryDirectory() as tempdir:
        result = maybe_run_command(
            [sys.executable, str(ROOT / "scripts" / "package_chart.py"), "--output-dir", tempdir]
        )
        if result.returncode != 0:
            raise ValueError((result.stdout + result.stderr).strip())


def validate_yaml_files() -> None:
    yaml_paths = [
        ROOT / ".github" / "workflows" / "ci.yml",
        ROOT / ".github" / "workflows" / "release.yml",
        ROOT / ".github" / "workflows" / "example-consumer.yml",
        ROOT / ".gitlab-ci.yml",
        ROOT / "examples" / "profiles" / "synthetic-otlp" / "values.yaml",
        ROOT / "examples" / "profiles" / "synthetic-otlp" / "collector-patch.yaml",
        ROOT / "examples" / "profiles" / "minimal-production-eval" / "values.yaml",
        ROOT / "examples" / "profiles" / "minimal-production-eval" / "collector-patch.yaml",
        ROOT / "examples" / "profiles" / "otel-demo" / "mb3r-values.yaml",
        ROOT / "examples" / "profiles" / "otel-demo" / "collector-patch.yaml",
        ROOT / "examples" / "profiles" / "otel-demo" / "opentelemetry-demo-values.yaml",
        ROOT / "collector" / "snippets" / "bering-exporter.yaml",
        ROOT / "collector" / "snippets" / "prometheus-receiver.yaml",
    ]
    for path in yaml_paths:
        load_yaml(path)


def validate_dashboards() -> None:
    for path in sorted((ROOT / "dashboards").rglob("*.json")):
        data = load_json(path)
        check("title" in data, f"Dashboard missing title: {path.relative_to(ROOT)}")
        check("panels" in data, f"Dashboard missing panels: {path.relative_to(ROOT)}")


def validate_github_workflows() -> None:
    reusable = [
        ROOT / ".github" / "workflows" / "bering-discover.yml",
        ROOT / ".github" / "workflows" / "sheaft-gate.yml",
        ROOT / ".github" / "workflows" / "mb3r-report.yml",
    ]
    for path in reusable:
        workflow = load_yaml(path, loader="base")
        check("on" in workflow and "workflow_call" in workflow["on"], f"{path.name} must use workflow_call")
        check("jobs" in workflow and workflow["jobs"], f"{path.name} must define jobs")
        workflow_call = workflow["on"]["workflow_call"]
        check("outputs" in workflow_call and workflow_call["outputs"], f"{path.name} must expose outputs")

    for path in (
        ROOT / ".github" / "workflows" / "ci.yml",
        ROOT / ".github" / "workflows" / "release.yml",
        ROOT / ".github" / "workflows" / "example-consumer.yml",
    ):
        workflow = load_yaml(path, loader="base")
        check("jobs" in workflow and workflow["jobs"], f"{path.name} must define jobs")


def validate_gitlab_components() -> None:
    for path in (
        ROOT / "templates" / "bering-discover.yml",
        ROOT / "templates" / "sheaft-gate.yml",
        ROOT / "templates" / "mb3r-report.yml",
    ):
        documents = load_yaml(path, multi=True, loader="base")
        check(len(documents) >= 2, f"{path.name} must contain spec and job documents")
        spec = documents[0].get("spec")
        check(spec is not None, f"{path.name} must define spec")
        check(spec.get("inputs"), f"{path.name} must define spec.inputs")
        check(documents[1], f"{path.name} must define at least one job")

    gitlab_ci = load_yaml(ROOT / ".gitlab-ci.yml", loader="base")
    check("stages" in gitlab_ci, ".gitlab-ci.yml must define stages")


def validate_jenkins_library() -> None:
    base = ROOT / "ci" / "jenkins"
    for name in ("mb3rBeringDiscover", "mb3rSheaftGate", "mb3rPublishReport"):
        groovy = base / "vars" / f"{name}.groovy"
        doc = base / "vars" / f"{name}.txt"
        check(groovy.exists(), f"Missing Jenkins step {groovy.relative_to(ROOT)}")
        check(doc.exists(), f"Missing Jenkins step documentation {doc.relative_to(ROOT)}")
        check("def call" in groovy.read_text(encoding="utf-8"), f"{groovy.name} must expose call()")

    helper = base / "src" / "org" / "mb3r" / "AdapterSupport.groovy"
    check(helper.exists(), f"Missing Jenkins helper {helper.relative_to(ROOT)}")
    check((ROOT / "examples" / "jenkins" / "Jenkinsfile").exists(), "Missing Jenkins example Jenkinsfile")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the mb3r-stack repository.")
    parser.parse_args()

    validate_python()
    validate_json_contracts()
    validate_chart()
    validate_yaml_files()
    validate_dashboards()
    validate_github_workflows()
    validate_gitlab_components()
    validate_jenkins_library()
    print("validation-ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
