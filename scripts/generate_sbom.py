from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

from common import DIST, ROOT, sha256_file, stack_manifest, write_json


def generate_sbom(output_path: Path) -> Path:
    manifest = stack_manifest()
    excluded = {
        output_path.name,
        "release-assets.txt",
    }
    components = []
    for path in sorted(DIST.rglob("*")):
        if not path.is_file() or path.name in excluded:
            continue
        components.append(
            {
                "type": "file",
                "name": path.name,
                "version": manifest["stack"]["version"],
                "hashes": [{"alg": "SHA-256", "content": sha256_file(path)}],
                "properties": [{"name": "mb3r:path", "value": path.relative_to(ROOT).as_posix()}],
            }
        )

    sbom = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "version": 1,
        "metadata": {
            "timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "component": {
                "type": "platform",
                "name": "mb3r-stack",
                "version": manifest["stack"]["version"],
            },
        },
        "components": components,
    }
    write_json(output_path, sbom)
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a CycloneDX SBOM for dist artifacts.")
    parser.add_argument("--output", default=str(DIST / "sbom.cdx.json"))
    args = parser.parse_args()
    output = generate_sbom(Path(args.output))
    print(output.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
