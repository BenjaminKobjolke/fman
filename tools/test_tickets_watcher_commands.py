import re
import unittest
from pathlib import Path


TOOLS = Path(__file__).parent
COMMANDS = (
    "find_build_python.bat",
    "run_build_shutdown_tests.bat",
    "run_tests.bat",
    "unittest_with_timeout.bat",
    "update_windrop.bat",
)


class TicketsWatcherCommandsTest(unittest.TestCase):
    def test_scripts_do_not_wait_for_unsupported_prompts_or_windows(self):
        for name in COMMANDS:
            with self.subTest(name=name):
                script = (TOOLS / name).read_text(encoding="utf-8").lower()
                self.assertNotRegex(script, r"(?m)^\s*pause\s*(?:$|&)")
                self.assertNotRegex(script, r"(?m)^\s*start\s+(?!/wait\b)")

    def test_shutdown_tests_use_the_hang_timeout_wrapper(self):
        script = (TOOLS / "run_build_shutdown_tests.bat").read_text(encoding="utf-8")
        self.assertRegex(
            script,
            re.compile(
                r'call\s+"%~dp0unittest_with_timeout\.bat"\s+-v\s+'
                r'fman_unittest\.impl\.build_shutdown_test',
                re.IGNORECASE,
            ),
        )


if __name__ == "__main__":
    unittest.main()
