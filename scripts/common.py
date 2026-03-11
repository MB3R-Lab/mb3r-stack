from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tarfile
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def clean_dir(path: Path) -> Path:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def load_yaml(path: Path, *, multi: bool = False, loader: str = "safe") -> Any:
    text = path.read_text(encoding="utf-8")
    yaml_loader = yaml.SafeLoader if loader == "safe" else yaml.BaseLoader
    if multi:
        return list(yaml.load_all(text, Loader=yaml_loader))
    return yaml.load(text, Loader=yaml_loader)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def check(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate_schema(instance_path: Path, schema_path: Path) -> None:
    instance = load_json(instance_path)
    schema = load_json(schema_path)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(instance), key=lambda error: list(error.path))
    if errors:
        lines = []
        for error in errors:
            location = ".".join(str(part) for part in error.path) or "<root>"
            lines.append(f"{instance_path.relative_to(ROOT)}:{location}: {error.message}")
        raise ValueError("\n".join(lines))


def maybe_run_command(command: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd or ROOT,
        check=False,
        text=True,
        capture_output=True,
    )


def chart_metadata(chart_dir: Path) -> dict[str, Any]:
    data = load_yaml(chart_dir / "Chart.yaml")
    check(isinstance(data, dict), f"{chart_dir / 'Chart.yaml'} must contain a mapping")
    return data


def stack_manifest() -> dict[str, Any]:
    return load_json(ROOT / "compat" / "stack-manifest.json")


def normalize_tarinfo(tarinfo: tarfile.TarInfo) -> tarfile.TarInfo:
    tarinfo.uid = 0
    tarinfo.gid = 0
    tarinfo.uname = ""
    tarinfo.gname = ""
    tarinfo.mtime = 0
    return tarinfo


def package_directory(source_dir: Path, output_path: Path, *, arcname: str) -> Path:
    ensure_dir(output_path.parent)
    with tarfile.open(output_path, "w:gz", format=tarfile.PAX_FORMAT) as archive:
        archive.add(source_dir, arcname=arcname, recursive=False, filter=normalize_tarinfo)
        for path in sorted(source_dir.rglob("*")):
            archive.add(
                path,
                arcname=(Path(arcname) / path.relative_to(source_dir)).as_posix(),
                recursive=False,
                filter=normalize_tarinfo,
            )
    return output_path
