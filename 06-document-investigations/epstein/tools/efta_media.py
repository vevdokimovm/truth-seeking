#!/usr/bin/env python3
"""efta_media.py — stage E: audio/video from the remote dataset zips → speech notes.

Each media member is pulled from the archive.org zip into a temp file, passed to the
lab tool `_base/07-media-to-text-lab/tools/video_to_note.py` (whisper.cpp, speech with
timecodes), and the temp file is deleted. Frames are NOT extracted (`--no-frames`):
evidence video may show victims; describing people is out of scope (named loss).

    efta_media.py --ds 8 --out <dir> [--model large-v3-turbo-q5_0] [--limit N]
                  [--kind audio|video|all] [--min-voiced 20]
Resumable: members whose note exists are skipped.

Two cost guards, added 30.09.2026 after stage E measured 1.55x realtime on CCTV
video that yielded 238 words per hour of footage:
  * `--kind audio` runs the pure-audio members first (calls, dictaphone) — the
    dense speech in the corpus, hours of work instead of months;
  * every member is screened with ffmpeg `silencedetect` before whisper: a track
    that is silent end to end gets a note stating the measurement, not a model run.
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

from remotezip import RemoteZip

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[2] / "_base/07-media-to-text-lab/tools/video_to_note.py"
ITEM = "https://archive.org/download/data-set-8_20251228/"
MEDIA = {".mp4", ".m4a", ".mp3", ".avi", ".mov", ".m4v", ".opus", ".amr",
         ".wav", ".3gp", ".vob", ".ts", ".wmv"}
AUDIO = {".m4a", ".mp3", ".opus", ".amr", ".wav"}
SILENCE_DB = -35
SILENCE_MIN = 2.0
VAD_MODEL = Path.home() / ("Developer/whisper-models/whisper.cpp-1.9.4/models/"
                           "ggml-silero-v5.1.2.bin")
# Клише, которыми whisper отвечает на тишину и невнятную речь. Нормализуются
# до букв и пробелов, поэтому пунктуация и регистр здесь не нужны.
CLICHE = {
    "thank you", "thank you very much", "thanks for watching",
    "thank you for watching", "thanks", "bye", "you", "okay", "ok",
    "please subscribe", "subscribe to my channel", "the end",
    "продолжение следует", "спасибо", "спасибо за просмотр",
    "субтитры сделал dimatorzok", "редактор субтитров",
}


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


def duration(path: Path) -> float:
    """Length of the media file in seconds, 0.0 when ffprobe cannot tell."""
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "format=duration", "-of", "csv=p=0", str(path)],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def voiced_seconds(path: Path, total: float) -> float:
    """Seconds above the silence floor — the budget whisper would actually work on.

    Evidence video is mostly silent CCTV; running a 1.55x-realtime model over it
    buys nothing. `silencedetect` costs a decode pass and answers beforehand.
    """
    r = subprocess.run(
        ["ffmpeg", "-nostdin", "-v", "info", "-i", str(path), "-af",
         f"silencedetect=n={SILENCE_DB}dB:d={SILENCE_MIN}", "-f", "null", "-"],
        capture_output=True, text=True)
    silent = sum(float(line.split("silence_duration:")[1].split()[0])
                 for line in r.stderr.splitlines() if "silence_duration:" in line)
    return max(total - silent, 0.0)


def hallucination_warning(note_text: str) -> str:
    """Предупреждение, если расшифровка похожа на выдумку модели.

    Два признака, оба сняты с живых нот 30.09.2026:

    · **повтор одной строки.** На цифровой тишине whisper заполняет каждое
      30-секундное окно клише: 9 нот из 25 в первую ночь этапа E оказались
      119–121 сегментом «Thank you.» подряд. Причину закрывает VAD;
    · **только клише и ничего больше.** `EFTA01614407.amr` (13 с, сигнал есть:
      mean −39.8 dB, VAD нашёл 5 сегментов речи) дал один сегмент «Thank you.».
      Здесь VAD не помогает — он слышит активность, но не разборчивость,
      и на тихой невнятной речи модель выдаёт то же клише.

    Второй признак ловит короткие файлы, которые первый пропускает по порогу.
    """
    segs = [m.strip() for m in
            re.findall(r"^\*\*\d\d:\d\d(?::\d\d)?\*\* (.+?)\s*$", note_text, re.M)]
    if not segs:
        return ""
    if len(segs) >= 3:
        top, n = Counter(segs).most_common(1)[0]
        if n / len(segs) >= 0.8:
            return (f"\n---\n\n🔴 **Подозрение на галлюцинацию модели.** "
                    f"{n} из {len(segs)} сегментов — одна и та же строка "
                    f"«{top[:60]}». Так whisper заполняет тишину. Расшифровку "
                    f"читать как непроверенную, файл перепрогнать с `--vad` "
                    f"и сверить `ffmpeg volumedetect`.\n")
    norm = {re.sub(r"[^a-zа-яё ]", "", s.lower()).strip() for s in segs}
    if norm and norm <= CLICHE:
        return (f"\n---\n\n🟡 **Расшифровка состоит только из типового клише "
                f"whisper** («{segs[0][:50]}»). Так модель отвечает на тихую или "
                f"неразборчивую речь — содержанием файла это считать нельзя. "
                f"Проверить глазами: `efta_vad_probe.py <EFTA> --ds <N>`.\n")
    return ""


def no_speech_note(member: str, ds: int, voiced: float, total: float) -> str:
    """Note for a track that is silent end to end — a measurement, not a refusal."""
    return (f"# {Path(member).stem}\n\n> DOJ Epstein Library · Data Set {ds} · "
            f"`{member}`\n\n## Паспорт извлечения\n\n| | |\n|---|---|\n"
            f"| длительность | {total / 60:.1f} мин ({total:.0f} с) |\n"
            f"| звук выше порога тишины | **{voiced:.1f} с** "
            f"(ffmpeg silencedetect, порог {SILENCE_DB} dB, окно {SILENCE_MIN} с) |\n"
            f"| речь | **не распознавалась** — дорожка молчит, whisper не "
            f"запускался; это замер, не отказ инструмента |\n"
            f"| кадры | не извлекались (этика: видео-улики могут показывать "
            f"потерпевших) |\n| потеря | всё визуальное содержание; речь ниже "
            f"порога тишины, если она там есть |\n\n"
            f"Перепрогнать с другим порогом: `efta_media.py --ds {ds} "
            f"--min-voiced 0` после удаления этой ноты.\n")


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
    ap.add_argument("--kind", choices=["audio", "video", "all"], default="all")
    ap.add_argument("--min-voiced", type=float, default=20.0)
    ap.add_argument("--lang", default="en")
    ap.add_argument("--vad-model", type=Path, default=VAD_MODEL)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    url = zip_url(a.ds)
    with RemoteZip(url, timeout=120) as z:
        members = [(i.filename, i.file_size) for i in z.infolist()
                   if Path(i.filename).suffix.lower() in MEDIA]
    if a.kind != "all":
        want_audio = a.kind == "audio"
        members = [(m, s) for m, s in members
                   if (Path(m).suffix.lower() in AUDIO) == want_audio]
    todo = [m for m, _ in sorted(members, key=lambda x: x[1])
            if not (out / f"{Path(m).name}.md").exists()]
    if a.limit:
        todo = todo[:a.limit]
    print(f"DS{a.ds} [{a.kind}]: media={len(members)} todo={len(todo)}", flush=True)
    skipped = 0
    suspect = 0
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
                total = duration(src)
                voiced = voiced_seconds(src, total)
                if total >= a.min_voiced and voiced < a.min_voiced:
                    note.write_text(no_speech_note(member, a.ds, voiced, total),
                                    encoding="utf-8")
                    skipped += 1
                    continue
                r = subprocess.run(
                    [sys.executable, str(LAB), str(src), "--out", str(note),
                     "--model", a.model, "--lang", a.lang, "--no-frames",
                     *(["--vad-model", str(a.vad_model)] if a.vad_model else [])],
                    capture_output=True, text=True, timeout=6 * 3600)
                if r.returncode != 0 or not note.exists():
                    failed += 1
                    print(f"  FAIL {member}: {r.stderr[-300:]}", flush=True)
                else:
                    text = note.read_text(encoding="utf-8")
                    text = text.replace(str(src), member)
                    text = text.replace(
                        f"# {src.stem}",
                        f"# {src.stem}\n\n> DOJ Epstein Library · Data Set {a.ds} · "
                        f"`{member}` · кадры не извлекались (этика: видео-улики "
                        f"могут показывать потерпевших)", 1)
                    warn = hallucination_warning(text)
                    if warn:
                        text += warn
                        suspect += 1
                    note.write_text(text, encoding="utf-8")
            except Exception as e:
                failed += 1
                print(f"  FAIL {member}: {e!r}"[:300], flush=True)
            finally:
                src.unlink(missing_ok=True)
                # печать в finally, а не после: `continue` в ветке немого файла
                # её перескакивал, и на массиве CCTV (почти все молчат) лог
                # молчал целиком — прогон выглядел зависшим
                if n % 10 == 0 or n == len(todo):
                    print(f"  media {n}/{len(todo)} silent={skipped} "
                          f"suspect={suspect} failed={failed}", flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
