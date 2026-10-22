"""Tests for plain semantic release version handling."""

import unittest
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent / "release"))
import build_number


class NextVersionTest(unittest.TestCase):
    def test_patch_rollover(self):
        self.assertEqual(build_number.next_version("1.7.13"), "1.8.0")

    def test_increments_patch(self):
        self.assertEqual(build_number.next_version("1.8.0"), "1.8.1")

    def test_patch_maximum_is_included(self):
        self.assertEqual(build_number.next_version("1.8.9"), "1.8.10")

    def test_patch_maximum_rolls_over(self):
        self.assertEqual(build_number.next_version("1.8.10"), "1.9.0")


class IncrementTest(unittest.TestCase):
    def test_updates_only_version_and_preserves_formatting(self):
        original = (
            '{\n'
            '  "other": [1, 2],\n'
            '  "version": "1.8.9",\n'
            '  "nested": {"enabled": true}\n'
            '}\n'
        )
        expected = original.replace('"version": "1.8.9"', '"version": "1.8.10"')
        with tempfile.TemporaryDirectory(prefix="build-number-") as temporary:
            settings_file = Path(temporary) / "base.json"
            settings_file.write_text(original, encoding="utf-8")
            previous_settings_file = build_number._SETTINGS_FILE
            build_number._SETTINGS_FILE = settings_file
            try:
                self.assertEqual(build_number.increment(), "1.8.10")
            finally:
                build_number._SETTINGS_FILE = previous_settings_file
            self.assertEqual(settings_file.read_text(encoding="utf-8"), expected)


if __name__ == "__main__":
    unittest.main()
