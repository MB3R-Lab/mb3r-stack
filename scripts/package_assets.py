from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from pathlib import Path

from common import DIST, ROOT, ensure_dir, package_directory, stack_manifest


def package_assets(output_dir: Path) -> Path:
    manifest = stack_manifest()
    stack_version = manifest["stack"]["version"]
    ensure_dir(output_dir)
    archive = output_dir / f"mb3r-assets-{stack_version}.tgz"

    with tempfile.TemporaryDirectory() as tempdir:
        asset_root = Path(tempdir) / "mb3r-assets"
        asset_root.mkdir(parents=True, exist_ok=True)

        for name in ("collector", "dashboards", "examples"):
            shutil.copytree(ROOT / name, asset_root / name)

        return package_directory(asset_root, archive, arcname="mb3r-assets")


def main() -> int:
    parser = argparse.ArgumentParser(description="Package collector, dashboard, and example assets.")
    parser.add_argument("--output-dir", default=str(DIST / "assets"))
    args = parser.parse_args()
    package_path = package_assets(Path(args.output_dir))
    print(package_path.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
