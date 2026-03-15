from __future__ import annotations

import argparse
import sys
from pathlib import Path

from common import DIST, ROOT, chart_metadata, check, load_json, stack_manifest, validate_schema, write_json


def stage_stack_metadata(output_dir: Path) -> list[Path]:
    manifest_path = ROOT / "compat" / "stack-manifest.json"
    matrix_path = ROOT / "compat" / "compatibility-matrix.json"
    manifest_schema = ROOT / "schemas" / "stack-manifest.schema.json"
    matrix_schema = ROOT / "schemas" / "compatibility-matrix.schema.json"

    validate_schema(manifest_path, manifest_schema)
    validate_schema(matrix_path, matrix_schema)

    manifest = stack_manifest()
    chart = chart_metadata(ROOT / "charts" / "mb3r-stack")
    check(
        manifest["artifacts"]["chart"]["version"] == chart["version"],
        "stack-manifest chart version must match charts/mb3r-stack/Chart.yaml",
    )
    check(
        manifest["stack"]["version"] == chart["version"],
        "stack-manifest stack version must match the chart version for this repository",
    )

    dashboard_root = ROOT / "dashboards"
    for component, version in manifest["artifacts"]["dashboards"].items():
        check(
            (dashboard_root / component / f"v{version}").exists(),
            f"Missing dashboard directory dashboards/{component}/v{version}",
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_target = output_dir / "stack-manifest.json"
    matrix_target = output_dir / "compatibility-matrix.json"
    write_json(manifest_target, manifest)
    write_json(matrix_target, load_json(matrix_path))
    return [manifest_target, matrix_target]


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate and stage stack metadata.")
    parser.add_argument("--output-dir", default=str(DIST))
    args = parser.parse_args()
    files = stage_stack_metadata(Path(args.output_dir))
    for path in files:
        print(path.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
