#!/bin/bash
set -euo pipefail

# Sign, notarize and staple one .app or .dmg via release-tool's mac-sign.
# Usage: sign_mac.sh <path> [mac-sign options]

if [[ $# -lt 1 ]]; then
    echo "ERROR: no app or dmg path given." >&2
    echo "Usage: sign_mac.sh <path> [mac-sign options]" >&2
    exit 1
fi
if [[ ! -e "$1" ]]; then
    echo "ERROR: app or dmg not found: $1" >&2
    exit 1
fi

file_path=$(cd "$(dirname "$1")" && pwd)/$(basename "$1")
release_tool_dir=${RELEASE_TOOL_DIR:-$HOME/GIT/BenjaminKobjolke/release-tool}
if [[ ! -d "$release_tool_dir" ]]; then
    echo "ERROR: release-tool checkout not found at '$release_tool_dir'; set RELEASE_TOOL_DIR" >&2
    exit 1
fi

cd "$release_tool_dir"
uv run python -m release_tool mac-sign "$file_path" "${@:2}"
echo "Signed: $file_path"
