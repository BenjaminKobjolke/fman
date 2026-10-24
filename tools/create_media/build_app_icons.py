"""Build fman's platform icons from one committed master image.

Keeping the source artwork and platform-specific sizing in one script makes
the installer, application, and desktop environments use the same icon.
"""

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw


NEON_GREEN = (0x00, 0xFF, 0x41)
BASE_SIZES = (16, 24, 32, 48, 64)
LINUX_SIZES = (128, 256, 512, 1024)
MAC_SIZES = (128, 256, 512, 1024)
ICO_SIZES = (16, 24, 32, 48, 64, 128, 256)
MAC_MARGIN = 0.10
CORNER_RADIUS = 0.18
MASTER_SIZE = 1024
MASK_SCALE = 4
NEAR_BLACK_THRESHOLD = 48
LANCZOS = Image.Resampling.LANCZOS


def _arguments(argv=None):
    repository_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description="Build fman's platform app icons.")
    parser.add_argument(
        "--master",
        type=Path,
        default=Path(__file__).with_name("app_icon_master.png"),
        help=(
            "1024x1024 source artwork (default: app_icon_master.png beside this "
            "script)"
        ),
    )
    parser.add_argument(
        "--icons-dir",
        type=Path,
        default=repository_root / "src" / "main" / "icons",
        help=(
            "destination icon directory (default: this repository's "
            "src/main/icons)"
        ),
    )
    return parser.parse_args(argv)


def _normalize_master(master_path):
    with Image.open(master_path) as source:
        source = source.convert("RGB")
        pixels = source.load()
        for y in range(source.height):
            for x in range(source.width):
                red, green, blue = pixels[x, y]
                pixels[x, y] = (
                    (0, 0, 0)
                    if max(red, green, blue) <= NEAR_BLACK_THRESHOLD
                    else NEON_GREEN
                )
        if source.size != (MASTER_SIZE, MASTER_SIZE):
            source = source.resize((MASTER_SIZE, MASTER_SIZE), LANCZOS)
        return source


def _rounded_mask(size):
    scaled_size = size * MASK_SCALE
    mask = Image.new("L", (scaled_size, scaled_size), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        (0, 0, scaled_size - 1, scaled_size - 1),
        radius=round(scaled_size * CORNER_RADIUS),
        fill=255,
    )
    return mask.resize((size, size), LANCZOS)


def _masked_master(master):
    rgba = master.convert("RGBA")
    rgba.putalpha(_rounded_mask(MASTER_SIZE))
    return rgba


def _write_sizes(image, destination, sizes):
    destination.mkdir(parents=True, exist_ok=True)
    for size in sizes:
        # 16/24 px are plain downscales of the master; hand-tune those two if
        # the pane lines blur away at taskbar size.
        resized = image.resize((size, size), LANCZOS)
        resized.save(destination / f"{size}.png")


def _write_mac_sizes(image, destination):
    destination.mkdir(parents=True, exist_ok=True)
    for size in MAC_SIZES:
        art_size = round(size * (1 - 2 * MAC_MARGIN))
        art = image.resize((art_size, art_size), LANCZOS)
        canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        offset = ((size - art_size) // 2, (size - art_size) // 2)
        canvas.alpha_composite(art, offset)
        canvas.save(destination / f"{size}.png")


def build_icons(master_path, icons_dir):
    master = _normalize_master(master_path)
    masked = _masked_master(master)

    _write_sizes(masked, icons_dir / "base", BASE_SIZES)
    _write_sizes(masked, icons_dir / "linux", LINUX_SIZES)
    _write_mac_sizes(masked, icons_dir / "mac")
    masked.save(
        icons_dir / "Icon.ico",
        format="ICO",
        sizes=[(size, size) for size in ICO_SIZES],
    )


def main(argv=None):
    arguments = _arguments(argv)
    if not arguments.master.is_file():
        print(f"App icon master image not found: {arguments.master}", file=sys.stderr)
        return 1

    build_icons(arguments.master, arguments.icons_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
