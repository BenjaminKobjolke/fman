#!/bin/bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
RECORD="$ROOT_DIR/target/release_version.txt"
LABEL=${1:-}
if [[ -z "$LABEL" && -f "$RECORD" ]]; then
	LABEL=$(<"$RECORD")
fi
if [[ -z "$LABEL" ]]; then
	echo "ERROR: no completed Mac build recorded in $RECORD." >&2
	echo "Pass its label or run tools/build_mac.sh." >&2
	exit 1
fi

ASSET="$ROOT_DIR/target/fman.dmg"
NOTES="$ROOT_DIR/release_notes/$LABEL/en.json"
if [[ ! -f "$ASSET" ]]; then
	echo "ERROR: signed disk image not found: $ASSET" >&2
	exit 1
fi
if [[ ! -f "$NOTES" ]]; then
	echo "ERROR: release notes not found: $NOTES" >&2
	exit 1
fi
if ! git -C "$ROOT_DIR" ls-remote --exit-code --tags origin "refs/tags/$LABEL" >/dev/null; then
	echo "ERROR: tag $LABEL is not on origin. Commit, tag and push the Windows release first." >&2
	exit 1
fi

RELEASE_TOOL_DIR=${RELEASE_TOOL_DIR:-$HOME/GIT/BenjaminKobjolke/release-tool}
if [[ ! -d "$RELEASE_TOOL_DIR" ]]; then
	echo "ERROR: release-tool checkout not found at '$RELEASE_TOOL_DIR'; set RELEASE_TOOL_DIR" >&2
	exit 1
fi
ASSET_PATH=$(cd "$(dirname "$ASSET")" && pwd)/$(basename "$ASSET")
NOTES_PATH=$(cd "$(dirname "$NOTES")" && pwd)/$(basename "$NOTES")
cd "$RELEASE_TOOL_DIR"
# The title mirrors title_format in release_create.ini; keep the two in sync.
uv run python -m release_tool github-release "$LABEL" "$ASSET_PATH" \
	--repo BenjaminKobjolke/fman --notes-json "$NOTES_PATH" --title "fman $LABEL"
