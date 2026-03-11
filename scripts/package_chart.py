from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from common import DIST, ROOT, chart_metadata, check, ensure_dir, load_yaml, maybe_run_command, package_directory


def validate_chart_structure(chart_dir: Path) -> dict[str, str]:
    required_files = [
        chart_dir / "Chart.yaml",
        chart_dir / "values.yaml",
        chart_dir / "templates" / "_helpers.tpl",
        chart_dir / "templates" / "collector-snippets-configmap.yaml",
        chart_dir / "templates" / "bering-deployment.yaml",
        chart_dir / "templates" / "sheaft-deployment.yaml",
        chart_dir / "templates" / "NOTES.txt",
    ]
    for path in required_files:
        check(path.exists(), f"Missing required chart file: {path.relative_to(ROOT)}")

    metadata = chart_metadata(chart_dir)
    check(metadata.get("name") == "mb3r-otel-addon", "Chart name must be mb3r-otel-addon")
    check("version" in metadata, "Chart.yaml must define version")

    values = load_yaml(chart_dir / "values.yaml")
    check(isinstance(values, dict), "values.yaml must contain a mapping")
    return {"name": str(metadata["name"]), "version": str(metadata["version"])}


def package_chart(output_dir: Path) -> Path:
    chart_dir = ROOT / "charts" / "mb3r-otel-addon"
    metadata = validate_chart_structure(chart_dir)
    ensure_dir(output_dir)
    target = output_dir / f"{metadata['name']}-{metadata['version']}.tgz"
    package_directory(chart_dir, target, arcname=chart_dir.name)

    if shutil.which("helm"):
        lint = maybe_run_command(["helm", "lint", str(chart_dir)])
        if lint.returncode != 0:
            raise ValueError(f"helm lint failed:\n{lint.stdout}\n{lint.stderr}".strip())

    return target


def main() -> int:
    parser = argparse.ArgumentParser(description="Package the mb3r-otel-addon Helm chart.")
    parser.add_argument("--output-dir", default=str(DIST / "charts"))
    args = parser.parse_args()
    package_path = package_chart(Path(args.output_dir))
    try:
        print(package_path.relative_to(ROOT))
    except ValueError:
        print(package_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
