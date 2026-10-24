"""Self-checks for building fman's platform app icons."""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent / "create_media"))
import build_app_icons


class BuildAppIconsTest(unittest.TestCase):
    def test_normalizes_source_pixels_before_resizing(self):
        with tempfile.TemporaryDirectory(
            prefix="build-app-icons-normalize-"
        ) as temporary:
            master = Path(temporary) / "master.png"
            source = Image.new("RGB", (3, 3), (0, 0, 0))
            source.putpixel((1, 1), (255, 255, 255))
            source.save(master)

            normalized_source = Image.new("RGB", (3, 3), (0, 0, 0))
            normalized_source.putpixel((1, 1), build_app_icons.NEON_GREEN)
            expected = normalized_source.resize((2, 2), build_app_icons.LANCZOS)
            with patch.object(build_app_icons, "MASTER_SIZE", 2):
                normalized = build_app_icons._normalize_master(master)

            self.assertEqual(list(normalized.getdata()), list(expected.getdata()))

    def test_builds_platform_sizes_and_normalizes_artwork(self):
        with tempfile.TemporaryDirectory(prefix="build-app-icons-") as temporary:
            root = Path(temporary)
            master = root / "master.png"
            icons = root / "icons"
            image = Image.new("RGB", (1024, 1024), (22, 187, 36))
            ImageDraw.Draw(image).rectangle((256, 256, 767, 767), fill=(4, 5, 6))
            image.save(master)

            self.assertEqual(
                build_app_icons.main(
                    ["--master", str(master), "--icons-dir", str(icons)]
                ),
                0,
            )

            expected = {
                "base": (16, 24, 32, 48, 64),
                "linux": (128, 256, 512, 1024),
                "mac": (128, 256, 512, 1024),
            }
            for platform, sizes in expected.items():
                for size in sizes:
                    path = icons / platform / f"{size}.png"
                    self.assertTrue(path.is_file(), path)
                    with Image.open(path) as generated:
                        self.assertEqual(generated.size, (size, size))

            with Image.open(icons / "linux" / "256.png") as linux_icon:
                self.assertEqual(linux_icon.getpixel((0, 0))[3], 0)
                self.assertEqual(linux_icon.getpixel((128, 128))[3], 255)

            with Image.open(icons / "mac" / "1024.png") as mac_icon:
                self.assertTrue(all(mac_icon.getpixel((x, y))[3] == 0 for x, y in (
                    *((x, 0) for x in range(1024)),
                    *((x, 89) for x in range(1024)),
                    *((0, y) for y in range(1024)),
                    *((89, y) for y in range(1024)),
                )))
                self.assertEqual(mac_icon.getpixel((512, 512))[3], 255)

            with Image.open(icons / "linux" / "1024.png") as full_size:
                opaque_colors = {
                    pixel[:3]
                    for pixel in full_size.getdata()
                    if pixel[3] == 255
                }
                self.assertLessEqual(opaque_colors, {(0, 255, 65), (0, 0, 0)})

            with Image.open(icons / "Icon.ico") as icon_file:
                self.assertEqual(
                    icon_file.info["sizes"],
                    {
                        (16, 16),
                        (24, 24),
                        (32, 32),
                        (48, 48),
                        (64, 64),
                        (128, 128),
                        (256, 256),
                    },
                )

    def test_missing_master_returns_nonzero(self):
        with tempfile.TemporaryDirectory(
            prefix="build-app-icons-missing-"
        ) as temporary:
            root = Path(temporary)
            self.assertNotEqual(
                build_app_icons.main([
                    "--master", str(root / "missing.png"),
                    "--icons-dir", str(root / "icons"),
                ]),
                0,
            )


if __name__ == "__main__":
    unittest.main()
