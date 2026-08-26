"""Join the recorded tour chapters into the README's feature-tour MP4.

Each chapter is recorded separately (the recorder keeps every frame in RAM, so
one 2.5-minute take would need gigabytes), then this script burns a caption
over the first seconds of each and concatenates them in one ffmpeg pass.

Chapter order comes from fman.json - the same file the recording tool reads -
so a new chapter only has to be added there and given a caption below.

    python tools/create_media/build_tour.py
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parents[2]
CONFIG_FILE = Path(__file__).with_name('fman.json')
CHAPTER_PREFIX = 'tour-'
OUTPUT_FILE = REPO_DIR / 'media' / 'demos' / 'tour' / 'feature-tour.mp4'
FONT_FILE = 'C:/Windows/Fonts/segoeui.ttf'
# How long each chapter's caption stays on screen. It titles the chapter
# rather than narrating it, so it leaves before it can cover the UI.
CAPTION_SECONDS = 5.0

CAPTIONS = {
    'tour-a-panes':
        'Two panes, one keyboard  \u00b7  select, copy, filter, sort',
    'tour-b-organize':
        'Organize without leaving the keyboard  \u00b7  F7 new folder, '
        'F6 move, Shift+F6 rename',
    'tour-c-viewers':
        'Preview inside the pane  \u00b7  images and text, zoom, edit, save',
    'tour-d-video':
        'Video plays in the pane  \u00b7  and previews in the other one',
    'tour-e-archives':
        'Archives are just folders  \u00b7  pack, step inside, copy out',
}


def chapters():
    """The tour chapters from fman.json, in recording order."""
    demos = json.loads(CONFIG_FILE.read_text(encoding='utf-8'))['demos']
    tour = sorted(
        (d for d in demos if d['name'].startswith(CHAPTER_PREFIX)),
        key=lambda d: d['id']
    )
    if not tour:
        raise SystemExit('No %s* demos in %s' % (CHAPTER_PREFIX, CONFIG_FILE))
    missing = [d['name'] for d in tour if d['name'] not in CAPTIONS]
    if missing:
        raise SystemExit('No caption for: %s' % ', '.join(missing))
    return tour


def clip_of(chapter):
    path = REPO_DIR / 'media' / 'demos' / chapter['name'] / 'demo.mp4'
    if not path.is_file():
        raise SystemExit(
            'Missing %s - record it first with: '
            'tools\\demos_record.bat --demo %s' % (path, chapter['id'])
        )
    return path


def filter_graph(count):
    """Scale, caption and concatenate every input into one stream.

    Captions come from caption<i>.txt files rather than a literal ``text=``:
    ffmpeg's filter syntax treats commas, colons and quotes as separators, and
    ``textfile`` sidesteps escaping all of them. The files are read from the
    working directory, which is why ffmpeg runs there - a Windows absolute
    path would need its drive colon escaped again.

    The scale/setsar is not cosmetic: chapters captured on different runs can
    differ by a pixel, and concat rejects mismatched inputs.
    """
    font = FONT_FILE.replace(':', r'\:')
    steps = []
    for i in range(count):
        steps.append(
            "[%d:v]scale=1280:-2,setsar=1,"
            "drawtext=fontfile='%s':textfile=caption%d.txt:"
            "fontsize=30:fontcolor=white:box=1:boxcolor=black@0.65:"
            "boxborderw=18:x=(w-text_w)/2:y=h-text_h-56:"
            "enable='lte(t\\,%s)'[v%d]" % (i, font, i, CAPTION_SECONDS, i)
        )
    inputs = ''.join('[v%d]' % i for i in range(count))
    steps.append('%sconcat=n=%d:v=1:a=0[out]' % (inputs, count))
    return ';'.join(steps)


def main():
    tour = chapters()
    clips = [clip_of(chapter) for chapter in tour]
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as work_dir:
        for i, chapter in enumerate(tour):
            caption = Path(work_dir) / ('caption%d.txt' % i)
            caption.write_text(CAPTIONS[chapter['name']], encoding='utf-8')
        command = ['ffmpeg', '-y']
        for clip in clips:
            command += ['-i', str(clip)]
        command += [
            '-filter_complex', filter_graph(len(clips)),
            '-map', '[out]',
            '-c:v', 'libx264', '-crf', '26', '-preset', 'slow',
            '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
            str(OUTPUT_FILE),
        ]
        print('Joining %d chapters: %s' % (
            len(clips), ', '.join(c['name'] for c in tour)
        ))
        result = subprocess.run(command, cwd=work_dir)
    if result.returncode:
        return result.returncode
    print('Wrote %s (%.1f MB)' % (
        OUTPUT_FILE, OUTPUT_FILE.stat().st_size / 1024 / 1024
    ))
    return 0


if __name__ == '__main__':
    sys.exit(main())
