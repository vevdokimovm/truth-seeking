#!/usr/bin/env python3
"""efta_bench.py — A/B-замер VAD на РЕАЛЬНЫХ файлах корпуса, с записью в реестр.

Отвечает на два вопроса, которые нельзя решить синтетикой:
  · **скорость** — во сколько раз VAD ускоряет прогон на этом железе сегодня;
  · **качество** — не срезает ли VAD речь; сравнивается текст обоих прогонов.

Тексты НЕ печатаются: в корпусе возможны имена потерпевших. В вывод идут только
метрики, расшифровки остаются в файлах рядом.

Результат дописывается в `_base/07-media-to-text-lab/asr-timings.csv`, с `loadavg`
и признаком конкуренции — замер под чужой нагрузкой обязан быть помечен
(METHOD-SPEECH §7а).
"""
from __future__ import annotations

import csv
import datetime
import difflib
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request
from pathlib import Path

from remotezip import RemoteZip

HERE = Path(__file__).resolve().parent
TIMINGS = HERE.parents[2] / "_base/07-media-to-text-lab/asr-timings.csv"
ITEM = "https://archive.org/download/data-set-8_20251228/"
MODEL = Path.home() / "Developer/whisper-models/ggml-large-v3-turbo-q5_0.bin"
VAD = (Path.home() / "Developer/whisper-models/whisper.cpp-1.9.4/models/"
       "ggml-silero-v5.1.2.bin")
CLI = "/usr/local/bin/whisper-cli"
VIDEO_SECONDS = 300


def zip_url(ds: int) -> str:
    """Datanode-адрес zip датасета (редиректы дорого повторять)."""
    name = "DataSet 09 - Incomplete.zip" if ds == 9 else f"DataSet {ds:02d}.zip"
    req = urllib.request.Request(ITEM + urllib.parse.quote(name), method="HEAD")
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.url


def loadavg() -> float:
    return os.getloadavg()[0]


def grab(ds: int, suffixes: set[str], max_bytes: int, dest_dir: Path) -> Path:
    """Взять из zip самый крупный член подходящего типа в пределах лимита."""
    url = zip_url(ds)
    with RemoteZip(url, timeout=120) as z:
        cands = [i for i in z.infolist()
                 if Path(i.filename).suffix.lower() in suffixes
                 and 0 < i.file_size <= max_bytes]
        if not cands:
            raise RuntimeError(f"DS{ds}: подходящих файлов нет")
        pick = max(cands, key=lambda i: i.file_size)
        dest = dest_dir / Path(pick.filename).name
        print(f"  беру {dest.name}: {pick.file_size / 1048576:.1f} МБ", flush=True)
        with z.open(pick.filename) as src, open(dest, "wb") as out:
            while chunk := src.read(1 << 20):
                out.write(chunk)
    return dest


def to_wav(src: Path, seconds: int | None = None) -> Path:
    wav = src.with_suffix(".16k.wav")
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", str(src)]
    if seconds:
        cmd += ["-t", str(seconds)]
    cmd += ["-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", str(wav)]
    subprocess.run(cmd, check=True, capture_output=True)
    return wav


def duration(path: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "format=duration", "-of", "csv=p=0", str(path)],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def transcribe(wav: Path, tag: str, vad: bool) -> tuple[float, list[str]]:
    out = wav.with_suffix(f".{tag}")
    cmd = [CLI, "-m", str(MODEL), "-l", "en", "-f", str(wav), "-oj", "-of", str(out)]
    if vad:
        cmd += ["--vad", "-vm", str(VAD)]
    t0 = time.time()
    r = subprocess.run(cmd, capture_output=True, text=True)
    wall = time.time() - t0
    js = out.with_suffix(".json")
    if not js.is_file():
        print(f"  🔴 {tag} не дал результата: {r.stderr[-200:]}", flush=True)
        return wall, []
    data = json.loads(js.read_text(encoding="utf-8", errors="replace"))
    return wall, " ".join(s["text"] for s in data.get("transcription", [])).split()


def record(source: str, kind: str, dur: float, wall: float, note: str) -> None:
    with open(TIMINGS, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([
            datetime.date.today().isoformat(), source, kind, f"{dur:.0f}",
            "large-v3-turbo-q5_0", "4", f"{wall:.0f}",
            f"{wall / dur:.2f}" if dur else "", f"{loadavg():.0f}", "1",
            "efta_bench.py", note])


def one(name: str, wav: Path, kind: str) -> None:
    dur = duration(wav)
    if dur <= 0:
        print(f"  🔴 {name}: ffprobe не прочитал длительность", flush=True)
        return
    wa, worda = transcribe(wav, "novad", False)
    wb, wordb = transcribe(wav, "vad", True)
    sim = difflib.SequenceMatcher(None, worda, wordb).ratio() if worda or wordb else 1.0
    print(f"\n=== {name} · {dur / 60:.1f} мин звука ===", flush=True)
    print(f"  без VAD : {wa:6.0f} с · {len(worda):5d} слов · ×{wa / dur:.2f}", flush=True)
    print(f"  с VAD   : {wb:6.0f} с · {len(wordb):5d} слов · ×{wb / dur:.2f}", flush=True)
    if wb > 0:
        print(f"  ускорение ×{wa / wb:.2f} · совпадение текста {sim * 100:.1f}% "
              f"· слов {len(wordb) - len(worda):+d}", flush=True)
    record(name, kind, dur, wa, "A/B без VAD")
    record(name, kind, dur, wb,
           f"A/B с VAD: ускорение x{wa / wb:.2f}, совпадение {sim * 100:.1f}%, "
           f"слов {len(wordb) - len(worda):+d}")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="efta_bench_") as tmp:
        work = Path(tmp)
        try:
            print("① АУДИО DS9", flush=True)
            au = grab(9, {".m4a", ".mp3", ".wav"}, 3_000_000, work)
            one(au.name, to_wav(au), "audio")
        except Exception as e:
            print(f"  🔴 аудио-часть не вышла: {e!r}"[:200], flush=True)
        try:
            print(f"\n② ВИДЕО DS8, первые {VIDEO_SECONDS // 60} мин", flush=True)
            vi = grab(8, {".mp4"}, 20_000_000, work)
            one(f"{vi.name} ({VIDEO_SECONDS // 60} мин)",
                to_wav(vi, seconds=VIDEO_SECONDS), "video")
        except Exception as e:
            print(f"  🔴 видео-часть не вышла: {e!r}"[:200], flush=True)
    print(f"\nзаписано в {TIMINGS}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
