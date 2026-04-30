from __future__ import annotations

import sys
from pathlib import Path

from common import DIST, ROOT, check, clean_dir, ensure_dir, maybe_run_command, sha256_file


def run_script(script_name: str) -> None:
    result = maybe_run_command([sys.executable, str(ROOT / "scripts" / script_name)])
    if result.returncode != 0:
        raise ValueError(f"{script_name} failed:\n{result.stdout}\n{result.stderr}".strip())


def write_checksums() -> Path:
    checksum_path = DIST / "SHA256SUMS.txt"
    lines = []
    for path in sorted(DIST.rglob("*")):
        if not path.is_file() or path.name in {checksum_path.name, "release-assets.txt"}:
            continue
        lines.append(f"{sha256_file(path)}  {path.relative_to(DIST).as_posix()}")
    checksum_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return checksum_path


def validate_checksum_coverage() -> None:
    release_assets = [
        line.strip()
        for line in (DIST / "release-assets.txt").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    checksum_entries = {
        line.split("  ", 1)[1]
        for line in (DIST / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines()
        if "  " in line
    }
    expected = [asset for asset in release_assets if asset != "SHA256SUMS.txt"]
    missing = [asset for asset in expected if asset not in checksum_entries]
    check(not missing, f"SHA256SUMS.txt missing release assets: {', '.join(missing)}")
    check("release-manifest.json" in checksum_entries, "SHA256SUMS.txt must cover release-manifest.json")
    check("SHA256SUMS.txt" not in checksum_entries, "SHA256SUMS.txt must not recursively checksum itself")


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
    run_script("generate_release_manifest.py")
    write_checksums()
    validate_checksum_coverage()
    print(DIST.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
