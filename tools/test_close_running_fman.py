"""Check that the Windows build closes only processes in its build folder."""

import os
import shutil
import subprocess
import tempfile
import threading
from pathlib import Path


SCRIPT = Path(__file__).with_name("close_running_fman.ps1")


def run_helper(directory, timeout_seconds):
    return subprocess.run(
        [
            "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
            "-File", str(SCRIPT), "-Directory", str(directory),
            "-TimeoutSeconds", str(timeout_seconds),
        ],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=30,
    )


def start_cmd(directory):
    executable = directory / "cmd.exe"
    shutil.copyfile(Path(os.environ["SystemRoot"]) / "System32" / "cmd.exe", executable)
    return subprocess.Popen(
        [str(executable), "/Q"],
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )


def stop_cmd(process):
    if process.poll() is None:
        process.terminate()
    process.wait(timeout=10)
    if process.stdin and not process.stdin.closed:
        process.stdin.close()


def check_close_running_fman():
    with tempfile.TemporaryDirectory(prefix="close-running-fman-") as temporary:
        directory = Path(temporary)

        result = run_helper(directory / "missing", 1)
        assert result.returncode == 0, result.stdout + result.stderr

        process = start_cmd(directory)
        try:
            result = run_helper(directory, 1)
            assert result.returncode == 1, result.stdout + result.stderr
            assert str(process.pid) in result.stdout + result.stderr
            assert process.poll() is None, "The helper must not kill a process"
        finally:
            stop_cmd(process)

        process = start_cmd(directory)
        close_stdin = threading.Timer(0.5, process.stdin.close)
        try:
            close_stdin.start()
            result = run_helper(directory, 10)
            assert result.returncode == 0, result.stdout + result.stderr
        finally:
            close_stdin.cancel()
            close_stdin.join()
            stop_cmd(process)


if __name__ == "__main__":
    check_close_running_fman()
    print("close running fman OK")
