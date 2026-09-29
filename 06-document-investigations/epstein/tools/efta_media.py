#!/usr/bin/env python3
"""efta_media.py — stage E: audio/video from the remote dataset zips → speech notes.

Each media member is pulled from the archive.org zip into a temp file, passed to the
lab tool `_base/07-media-to-text-lab/tools/video_to_note.py` (whisper.cpp, speech with
timecodes), and the temp file is deleted. Frames are NOT extracted (`--no-frames`):
evidence video may show victims; describing people is out of scope (named loss).

    efta_media.py --ds 8 --out <dir> [--model large-v3-turbo-q5_0] [--limit N]
Resumable: members whose note exists are skipped.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request
from pathlib import Path

from remotezip import RemoteZip

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[2] / "_base/07-media-to-text-lab/tools/video_to_note.py"
ITEM = "https://archive.org/download/data-set-8_20251228/"
MEDIA = {".mp4", ".m4a", ".mp3", ".avi", ".mov", ".m4v", ".opus", ".amr",
         ".wav", ".3gp", ".vob", ".ts", ".wmv"}


def zip_url(ds: int) -> str:
    """Resolve the datanode URL of a dataset zip (redirects are slow to repeat)."""
    name = "DataSet 09 - Incomplete.zip" if ds == 9 else f"DataSet {ds:02d}.zip"
    req = urllib.request.Request(ITEM + urllib.parse.quote(name), method="HEAD")
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.url


def extract(url: str, member: str, dest: Path, tries: int = 5) -> None:
    """Stream one zip member to disk, retrying archive.org 5xx."""
    for i in range(tries):
        try:
            with RemoteZip(url, timeout=120) as z, z.open(member) as src, \
                    open(dest, "wb") as out:
                shutil.copyfileobj(src, out, 1 << 20)
            return
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(20 * (i + 1))


def audio_streams(path: Path) -> int:
    """Count audio streams: evidence video is often silent (CCTV, phone clips)."""
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a",
                        "-show_entries", "stream=index", "-of", "csv=p=0", str(path)],
                       capture_output=True, text=True)
    return len([x for x in r.stdout.split() if x.strip()])


def silent_note(member: str, ds: int, path: Path) -> str:
    """Note for media without an audio track — a fact, not a tool refusal."""
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "format=duration:stream=codec_type,codec_name,width,height",
                        "-of", "compact", str(path)], capture_output=True, text=True)
    return (f"# {Path(member).stem}\n\n> DOJ Epstein Library · Data Set {ds} · "
            f"`{member}`\n\n## Паспорт извлечения\n\n| | |\n|---|---|\n"
            f"| звуковая дорожка | **нет** (ffprobe: аудиопотоков 0) — речи нет по "
            f"факту, не отказ инструмента |\n| кадры | не извлекались (этика: "
            f"видео-улики могут показывать потерпевших) |\n| потеря | всё визуальное "
            f"содержание |\n\n```\n{r.stdout.strip()}\n```\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ds", type=int, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default="large-v3-turbo-q5_0")
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    url = zip_url(a.ds)
    with RemoteZip(url, timeout=120) as z:
        members = [i.filename for i in z.infolist()
                   if Path(i.filename).suffix.lower() in MEDIA]
    todo = [m for m in members if not (out / f"{Path(m).name}.md").exists()]
    if a.limit:
        todo = todo[:a.limit]
    print(f"DS{a.ds}: media={len(members)} todo={len(todo)}", flush=True)
    failed = 0
    with tempfile.TemporaryDirectory(prefix="efta_media_") as tmp:
        for n, member in enumerate(todo, 1):
            src = Path(tmp) / Path(member).name
            note = out / f"{Path(member).name}.md"
            try:
                extract(url, member, src)
                if audio_streams(src) == 0:
                    note.write_text(silent_note(member, a.ds, src), encoding="utf-8")
                    continue
                r = subprocess.run(
                    [sys.executable, str(LAB), str(src), "--out", str(note),
                     "--model", a.model, "--lang", "auto", "--no-frames"],
                    capture_output=True, text=True, timeout=6 * 3600)
                if r.returncode != 0 or not note.exists():
                    failed += 1
                    print(f"  FAIL {member}: {r.stderr[-300:]}", flush=True)
                else:
                    text = note.read_text(encoding="utf-8")
                    text = text.replace(str(src), member)
                    note.write_text(text.replace(
                        f"# {src.stem}",
                        f"# {src.stem}\n\n> DOJ Epstein Library · Data Set {a.ds} · "
                        f"`{member}` · кадры не извлекались (этика: видео-улики "
                        f"могут показывать потерпевших)", 1), encoding="utf-8")
            except Exception as e:
                failed += 1
                print(f"  FAIL {member}: {e!r}"[:300], flush=True)
            finally:
                src.unlink(missing_ok=True)
            if n % 10 == 0 or n == len(todo):
                print(f"  media {n}/{len(todo)} failed={failed}", flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
