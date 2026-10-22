"""Bump and print fman's semantic version for the release workflow.

The version lives in ``src/build/settings/base.json``. Each release increments
its patch number, rolling over to the next minor version after patch 10.

Usage: ``python build_number.py [get|increment|decrement|label]``
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

PATCH_MAX = 10
_FALLBACK_VERSION = "0.0.0"
# tools/release/build_number.py -> project root is two parents up.
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_SETTINGS_FILE = _PROJECT_ROOT / "src" / "build" / "settings" / "base.json"
_VERSION_PATTERN = re.compile(r'("version"\s*:\s*")[^"]*(")')


def next_version(version: str) -> str:
    """Return the next version, rolling over after ``PATCH_MAX``."""
    segments = version.split(".")
    if len(segments) < 2 or any(not segment.isdecimal() for segment in segments):
        raise ValueError(f"invalid semantic version: {version!r}")

    numbers = [int(segment) for segment in segments]
    if numbers[-1] + 1 > PATCH_MAX:
        numbers[-2] += 1
        numbers[-1] = 0
    else:
        numbers[-1] += 1
    return ".".join(str(number) for number in numbers)


def version() -> str:
    if not _SETTINGS_FILE.exists():
        return _FALLBACK_VERSION
    data = json.loads(_SETTINGS_FILE.read_text(encoding="utf-8"))
    return str(data.get("version", _FALLBACK_VERSION))


def _write_version(value: str) -> None:
    contents = _SETTINGS_FILE.read_text(encoding="utf-8")
    updated, count = _VERSION_PATTERN.subn(rf'\g<1>{value}\g<2>', contents, count=1)
    if count != 1:
        raise ValueError(f"could not find version string in {_SETTINGS_FILE}")
    _SETTINGS_FILE.write_text(updated, encoding="utf-8")


def increment() -> str:
    value = next_version(version())
    _write_version(value)
    return value


def decrement() -> str:
    contents = subprocess.check_output(
        ["git", "show", "HEAD:src/build/settings/base.json"],
        cwd=_PROJECT_ROOT,
        text=True,
    )
    value = str(json.loads(contents).get("version", _FALLBACK_VERSION))
    _write_version(value)
    return value


def label() -> str:
    return version()


_COMMANDS = {
    "get": label,
    "increment": increment,
    "decrement": decrement,
    "label": label,
}


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    action = args[0] if args else "get"
    handler = _COMMANDS.get(action)
    if handler is None:
        print(f"usage: python build_number.py [{'|'.join(_COMMANDS)}]")
        return 2
    print(handler())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
