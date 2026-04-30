from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

from common import DIST, ROOT, check, load_json, maybe_run_command, sha256_file, stack_manifest, write_json, validate_schema


def prefixed_digest(path: Path) -> str:
    return f"sha256:{sha256_file(path)}"


def current_git_commit() -> str:
    result = maybe_run_command(["git", "rev-parse", "HEAD"])
    if result.returncode != 0:
        raise ValueError((result.stdout + result.stderr).strip())
    return result.stdout.strip()


def current_build_date() -> str:
    result = maybe_run_command(["git", "show", "-s", "--format=%cI", "HEAD"])
    if result.returncode != 0:
        raise ValueError((result.stdout + result.stderr).strip())
    raw = result.stdout.strip()
    parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    return parsed.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def release_title(version: str, status: str) -> str:
    if status == "ga":
        return f"mb3r-stack v{version} integration bundle"
    return f"mb3r-stack v{version} {status} integration bundle"


def compatibility_entry(version: str) -> dict[str, object]:
    matrix = load_json(ROOT / "compat" / "compatibility-matrix.json")
    for entry in matrix["entries"]:
        if entry["stackVersion"] == version:
            return entry
    raise ValueError(f"Missing compatibility entry for stack version {version}")


def generate_release_manifest(output_dir: Path) -> Path:
    manifest = stack_manifest()
    version = manifest["stack"]["version"]
    status = manifest["stack"]["status"]
    entry = compatibility_entry(version)

    chart_package_rel = Path("charts") / manifest["artifacts"]["chart"]["package"]
    asset_archive_rel = Path("assets") / manifest["artifacts"]["assetPack"]["archive"]

    required = {
        "chart": output_dir / chart_package_rel,
        "assetPack": output_dir / asset_archive_rel,
        "stackManifest": output_dir / "stack-manifest.json",
        "compatibilityMatrix": output_dir / "compatibility-matrix.json",
        "releaseNotes": output_dir / "release-notes.md",
        "releaseManifestSchema": output_dir / "release-manifest.schema.json",
        "sbom": output_dir / "sbom.cdx.json",
        "releaseAssets": output_dir / "release-assets.txt",
    }
    for label, path in required.items():
        check(path.exists(), f"Missing release artifact {label}: {path.relative_to(ROOT)}")

    release_assets = [
        line.strip()
        for line in required["releaseAssets"].read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    release_manifest = {
        "$schema": "release-manifest.schema.json",
        "schemaVersion": "1.0.0",
        "productName": "mb3r-stack",
        "releaseVersion": version,
        "gitTag": f"v{version}",
        "gitCommit": current_git_commit(),
        "buildDate": current_build_date(),
        "status": status,
        "title": release_title(version, status),
        "artifacts": {
            "chart": {
                "name": manifest["artifacts"]["chart"]["name"],
                "version": manifest["artifacts"]["chart"]["version"],
                "path": chart_package_rel.as_posix(),
                "digest": prefixed_digest(required["chart"]),
                "ociRepository": manifest["artifacts"]["chart"]["ociRepository"],
            },
            "assetPack": {
                "version": manifest["artifacts"]["assetPack"]["version"],
                "path": asset_archive_rel.as_posix(),
                "digest": prefixed_digest(required["assetPack"]),
            },
            "stackManifest": {
                "path": "stack-manifest.json",
                "digest": prefixed_digest(required["stackManifest"]),
            },
            "compatibilityMatrix": {
                "path": "compatibility-matrix.json",
                "digest": prefixed_digest(required["compatibilityMatrix"]),
            },
            "releaseNotes": {
                "path": "release-notes.md",
                "digest": prefixed_digest(required["releaseNotes"]),
            },
            "releaseManifestSchema": {
                "path": "release-manifest.schema.json",
                "digest": prefixed_digest(required["releaseManifestSchema"]),
            },
            "sbom": {
                "path": "sbom.cdx.json",
                "digest": prefixed_digest(required["sbom"]),
            },
            "checksums": {
                "path": "SHA256SUMS.txt",
            },
        },
        "components": manifest["components"],
        "compatibility": {
            "state": entry["compatibilityState"],
            "evidence": entry["evidence"],
            "contracts": entry["contracts"],
            "dashboards": entry["dashboards"],
            "notes": entry["notes"],
        },
        "releaseAssets": release_assets,
    }

    output_path = output_dir / "release-manifest.json"
    write_json(output_path, release_manifest)
    validate_schema(output_path, ROOT / "schemas" / "release-manifest.schema.json")
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate release-manifest.json for dist artifacts.")
    parser.add_argument("--output-dir", default=str(DIST))
    args = parser.parse_args()

    output = generate_release_manifest(Path(args.output_dir))
    print(output.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
