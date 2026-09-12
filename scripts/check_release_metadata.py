"""Validate the version and changelog entry for a tagged release."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import tomllib

_VERSION = re.compile(r"^\d+\.\d+\.\d+$")


def _project_version(root: Path) -> str:
    with (root / "pyproject.toml").open("rb") as stream:
        version = tomllib.load(stream)["project"]["version"]
    if not isinstance(version, str) or not _VERSION.fullmatch(version):
        raise ValueError("pyproject project.version must be a stable X.Y.Z value")
    return version


def _changelog_entry(root: Path, version: str) -> list[str]:
    lines = (root / "CHANGELOG.md").read_text(encoding="utf-8").splitlines()
    heading = re.compile(rf"^## \[{re.escape(version)}\](?:\s+-.*)?$")
    try:
        start = (
            next(index for index, line in enumerate(lines) if heading.fullmatch(line))
            + 1
        )
    except StopIteration as error:
        raise ValueError(f"CHANGELOG.md has no [{version}] entry") from error
    end = next(
        (index for index in range(start, len(lines)) if lines[index].startswith("## ")),
        len(lines),
    )
    bullets = [line[2:].strip() for line in lines[start:end] if line.startswith("- ")]
    if not bullets:
        raise ValueError(f"CHANGELOG.md {heading} entry has no release bullets")
    if all(len(bullet.split()) < 5 for bullet in bullets):
        raise ValueError(f"CHANGELOG.md {heading} entry is not descriptive")
    return bullets


def validate_release_metadata(root: Path, tag: str) -> str:
    version = _project_version(root)
    expected_tag = f"v{version}"
    if tag != expected_tag:
        raise ValueError(
            f"release tag {tag!r} does not match project version {version}"
        )
    _changelog_entry(root, version)
    return version


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", required=True)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    try:
        version = validate_release_metadata(args.root, args.tag)
    except (OSError, KeyError, TypeError, ValueError) as error:
        print(f"Release metadata check failed: {error}")
        return 1
    print(f"Release metadata is valid for {version}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
