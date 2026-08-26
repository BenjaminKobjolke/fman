"""Join the recorded theme stills into the README's themes GIF.

Demo 2 writes one PNG per installed theme, named after it, and no video at all
(``"formats": []`` in fman.json) - so the command palette it uses to switch
themes never reaches the recording. This script turns those stills into a GIF
that holds each theme for a couple of seconds.

The theme list is never written down: the inputs are whatever PNGs the demo
left behind, sorted by name - which is the order ``themes.list_themes``
returns, so a new theme shows up in the GIF by being recorded.

    python tools/create_media/build_themes.py
"""

import subprocess
import sys
import tempfile
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parents[2]
STILLS_DIR = REPO_DIR / 'media' / 'demos' / 'themes'
OUTPUT_FILE = STILLS_DIR / 'themes.gif'
# Seconds each theme is on screen. Kept in step with THEME_HOLD_S in
# src/main/python/fman/impl/demo_scripts.py, which is how long the recording
# itself dwells on a theme.
HOLD_SECONDS = 2.0
# The stills are the full 1280x800 window; a GIF that wide would be several
# megabytes for a README image nobody views at 1:1.
GIF_WIDTH = 960


def stills():
    result = sorted(STILLS_DIR.glob('*.png'))
    if not result:
        raise SystemExit(
            'No stills in %s - record them first with: '
            'tools\\demo_themes_record.bat' % STILLS_DIR
        )
    return result


def write_concat_list(path, images):
    """An ffmpeg concat-demuxer list holding each still for HOLD_SECONDS.

    A list file rather than one ``-i`` per image because theme names contain
    spaces. Paths are absolute and forward-slashed: the demuxer resolves a
    relative entry against the list file's own directory (not the working
    directory), and it reads a backslash as an escape character. The last
    entry is repeated because it ignores the final ``duration``.
    """
    lines = []
    for image in images:
        lines.append("file '%s'" % image.as_posix())
        lines.append('duration %s' % HOLD_SECONDS)
    lines.append("file '%s'" % images[-1].as_posix())
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def filter_graph():
    # fps is the reciprocal of the hold, so each still becomes exactly one GIF
    # frame carrying the whole delay - 11 frames instead of 11 x fps copies of
    # the same picture. palettegen/paletteuse because a GIF's default 216-color
    # web palette turns a theme's background into visible banding, which is the
    # one thing this GIF exists to show.
    return (
        'fps=%s,scale=%d:-2:flags=lanczos,split[a][b];'
        '[a]palettegen=stats_mode=diff[p];[b][p]paletteuse'
        % (1 / HOLD_SECONDS, GIF_WIDTH)
    )


def main():
    images = stills()
    with tempfile.TemporaryDirectory() as work_dir:
        list_file = Path(work_dir) / 'stills.txt'
        write_concat_list(list_file, images)
        command = [
            'ffmpeg', '-y',
            '-f', 'concat', '-safe', '0', '-i', str(list_file),
            '-filter_complex', filter_graph(),
            # The concat list repeats its last entry, which would otherwise
            # leave the final theme on screen for two holds instead of one.
            '-t', str(len(images) * HOLD_SECONDS),
            '-loop', '0',
            str(OUTPUT_FILE),
        ]
        print('Joining %d themes: %s' % (
            len(images), ', '.join(image.stem for image in images)
        ))
        result = subprocess.run(command)
    if result.returncode:
        return result.returncode
    print('Wrote %s (%.1f MB)' % (
        OUTPUT_FILE, OUTPUT_FILE.stat().st_size / 1024 / 1024
    ))
    return 0


if __name__ == '__main__':
    sys.exit(main())
