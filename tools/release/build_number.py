"""Self-contained build-number + release-label helper for the release workflow.

Manages the integer in ``build_version.txt`` at the project root, and prints the
``<version>_<build>`` label (version read from ``src/build/settings/base.json``,
fman's fbs settings file). The ``tools/build_*.bat`` and ``tools/version_get.bat``
wrappers call this.

Usage: ``python build_number.py [get|increment|decrement|label]``
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

BUILD_FILE_NAME = "build_version.txt"
# Counter = last shipped build; 0 = nothing shipped yet (bump-first, ship-next).
_DEFAULT_BUILD = 0
_FALLBACK_VERSION = "0.0.0"
# tools/release/build_number.py -> project root is two parents up.
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_SETTINGS_FILE = _PROJECT_ROOT / "src" / "build" / "settings" / "base.json"


def _build_file() -> Path:
    return _PROJECT_ROOT / BUILD_FILE_NAME


def read_build() -> int:
    path = _build_file()
    if not path.exists():
        return _DEFAULT_BUILD
    try:
        return int(path.read_text(encoding="utf-8").strip())
    except ValueError:
        return _DEFAULT_BUILD


def write_build(value: int) -> None:
    if value < 0:
        raise ValueError(f"build number must be >= 0, got {value}")
    _build_file().write_text(f"{value}\n", encoding="utf-8")


def increment() -> int:
    value = read_build() + 1
    write_build(value)
    return value


def decrement() -> int:
    value = max(0, read_build() - 1)
    write_build(value)
    return value


def version() -> str:
    if not _SETTINGS_FILE.exists():
        return _FALLBACK_VERSION
    data = json.loads(_SETTINGS_FILE.read_text(encoding="utf-8"))
    return str(data.get("version", _FALLBACK_VERSION))


def label() -> str:
    return f"{version()}_{read_build()}"


_COMMANDS = {
    "get": read_build,
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
