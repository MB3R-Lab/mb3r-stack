"""Build and run the stack's exact Procrustes source pin (standard library only)."""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def pin(root: Path = ROOT) -> dict:
    manifest = root / "compat" / "stack-manifest.json"
    if not manifest.is_file():
        manifest = root / "stack-manifest.json"  # extracted asset pack
    component = json.loads(manifest.read_text(encoding="utf-8"))["components"]["procrustes"]
    if not re.fullmatch(r"[0-9a-f]{40}", component["source"]["commit"]):
        raise ValueError("Procrustes requires a complete immutable source commit")
    return component


def run(command: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(command, cwd=cwd, check=True, text=True, capture_output=True)


def prepare(root: Path = ROOT) -> tuple[Path, Path]:
    component = pin(root)
    commit = component["source"]["commit"]
    cache = root / ".tmp" / "procrustes" / commit
    source = cache / "source"
    if not source.exists():
        source.mkdir(parents=True)
        run(["git", "init", str(source)])
        run(["git", "-C", str(source), "remote", "add", "origin", component["source"]["repository"]])
        run(["git", "-C", str(source), "fetch", "--depth", "1", "origin", commit])
        run(["git", "-C", str(source), "checkout", "--detach", "FETCH_HEAD"])
    actual = run(["git", "-C", str(source), "rev-parse", "HEAD"]).stdout.strip()
    dirty = run(["git", "-C", str(source), "status", "--porcelain", "--untracked-files=all"]).stdout.strip()
    if actual != commit or dirty:
        raise ValueError(f"Refusing modified or mismatched source cache: {source}")
    binary = cache / ("procrustes.exe" if os.name == "nt" else "procrustes")
    run(["go", "build", "-trimpath", "-o", str(binary), "./cmd/procrustes"], cwd=source)
    print(f"Procrustes {component['version']} source={commit}", flush=True)
    return binary, source


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--example", action="store_true", help="run the pinned upstream ready fixture")
    parser.add_argument("arguments", nargs=argparse.REMAINDER, help="-- analyze --source alias=path --goal goal.yaml --out-dir out --fail-on-blocked")
    args = parser.parse_args()
    command = args.arguments
    if command[:1] == ["--"]:
        command = command[1:]
    if args.example and command:
        parser.error("--example cannot be combined with CLI arguments")
    if not args.example and not command:
        parser.error("select --example or supply Procrustes CLI arguments after --")
    binary, source = prepare()
    if args.example:
        fixture = source / "testdata" / "ready"
        command = ["analyze", "--source", f"ready={fixture}", "--goal", str(fixture / "goal.yaml"),
                   "--out-dir", str(ROOT / ".tmp" / "preflight"), "--fail-on-blocked"]
    # Preserve caller cwd so user-provided input and output paths retain their meaning.
    return subprocess.run([str(binary), *command], check=False).returncode


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as error:
        print(str(error), file=sys.stderr)
        if isinstance(error, subprocess.CalledProcessError):
            print(error.stderr, file=sys.stderr)
        sys.exit(1)
