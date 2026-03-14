from __future__ import annotations

import sys
from pathlib import Path

from common import DIST, ROOT, clean_dir, ensure_dir, maybe_run_command, sha256_file


def run_script(script_name: str) -> None:
    result = maybe_run_command([sys.executable, str(ROOT / "scripts" / script_name)])
    if result.returncode != 0:
        raise ValueError(f"{script_name} failed:\n{result.stdout}\n{result.stderr}".strip())


def write_checksums() -> Path:
    checksum_path = DIST / "SHA256SUMS.txt"
    lines = []
    for path in sorted(DIST.rglob("*")):
        if not path.is_file() or path.name in {checksum_path.name, "release-manifest.json", "release-assets.txt"}:
            continue
        lines.append(f"{sha256_file(path)}  {path.relative_to(DIST).as_posix()}")
    checksum_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return checksum_path


def main() -> int:
    clean_dir(DIST)
    ensure_dir(DIST / "charts")
    ensure_dir(DIST / "assets")

    for script in (
        "validate.py",
        "generate_stack_manifest.py",
        "package_chart.py",
        "package_assets.py",
        "stage_release_metadata.py",
    ):
        run_script(script)

    run_script("generate_sbom.py")
    write_checksums()
    run_script("generate_release_manifest.py")
    print(DIST.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
