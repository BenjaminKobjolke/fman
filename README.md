# fman

A cross-platform dual-pane file manager.

## Web help system

A searchable, mobile-friendly reference of all keyboard shortcuts lives in its own
repo: [fman-web-help-system](https://github.com/BenjaminKobjolke/fman-web-help-system).
It regenerates its data from this repo's source; point its `fman_repo_dir` config at
a local fman checkout.

## Development instructions

fman currently uses Python 3.14.

Install the requirements for your operating system. For example:

    pip install -Ur requirements/mac.txt       # macOS
    pip install -Ur requirements/ubuntu.txt    # Ubuntu/Debian
    pip install -Ur requirements/arch.txt      # Arch Linux
    pip install -Ur requirements/fedora.txt    # Fedora
    pip install -Ur requirements/windows.txt   # Windows

Then you can use `python build.py` to run, compile etc. fman. For example:

    python build.py run

Call `python build.py` without arguments to see a list of available commands.
This uses [fman build system](https://build-system.fman.io/).

You can run automated tests with `python build.py test`. On Windows, this
requires Developer Mode (Settings -> System -> Advanced) to be enabled, or some
tests related to symlinks will fail.
