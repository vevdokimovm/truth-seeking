#!/usr/bin/env python3
"""efta_vad_probe.py — разобрать один спорный файл: речь или галлюцинация.

Повод (30.09.2026): на 5 минутах CCTV `EFTA00033407` прогон без VAD дал 20 слов,
с VAD — ноль. Ускорение ×50 ничего не стоит, если VAD выбросил настоящую речь,
и наоборот: 20 слов на тишине — типичная галлюцинация whisper, и тогда прав VAD.

Отвечает на это тремя вещами:
  · показывает сегменты прогона без VAD с таймкодами и длительностью;
  · гоняет VAD на порогах 0.5/0.3/0.2 — сколько речи он находит на каждом;
  · меряет реальный уровень звука (`volumedetect`) — есть ли там вообще сигнал.

    efta_vad_probe.py <EFTA-номер> --ds 8 [--seconds 300]
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path

from remotezip import RemoteZip

ITEM = "https://archive.org/download/data-set-8_20251228/"
MODEL = Path.home() / "Developer/whisper-models/ggml-large-v3-turbo-q5_0.bin"
VAD = (Path.home() / "Developer/whisper-models/whisper.cpp-1.9.4/models/"
       "ggml-silero-v5.1.2.bin")
CLI = "/usr/local/bin/whisper-cli"
MEDIA = {".mp4", ".m4a", ".mp3", ".avi", ".mov", ".m4v", ".opus", ".amr",
         ".wav", ".3gp", ".vob", ".ts", ".wmv"}


def zip_url(ds: int) -> str:
    name = "DataSet 09 - Incomplete.zip" if ds == 9 else f"DataSet {ds:02d}.zip"
    req = urllib.request.Request(ITEM + urllib.parse.quote(name), method="HEAD")
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.url


def fetch(ds: int, efta: str, dest_dir: Path) -> Path:
    url = zip_url(ds)
    with RemoteZip(url, timeout=120) as z:
        # у EFTA-номера есть однофамилец-PDF в IMAGES/ — брать только медиа
        hits = [i for i in z.infolist()
                if efta in i.filename and i.file_size > 0
                and Path(i.filename).suffix.lower() in MEDIA]
        if not hits:
            raise RuntimeError(f"{efta} не найден в DS{ds}")
        pick = hits[0]
        dest = dest_dir / Path(pick.filename).name
        print(f"  {pick.filename}: {pick.file_size / 1048576:.1f} МБ", flush=True)
        with z.open(pick.filename) as src, open(dest, "wb") as out:
            while chunk := src.read(1 << 20):
                out.write(chunk)
    return dest


def to_wav(src: Path, seconds: int) -> Path:
    wav = src.with_suffix(".16k.wav")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-t", str(seconds),
                    "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", str(wav)],
                   check=True, capture_output=True)
    return wav


def level(wav: Path) -> None:
    """Реальный уровень звука: тишина это или просто тихо."""
    r = subprocess.run(["ffmpeg", "-nostdin", "-v", "info", "-i", str(wav),
                        "-af", "volumedetect", "-f", "null", "-"],
                       capture_output=True, text=True)
    print("\n── уровень звука (ffmpeg volumedetect)")
    for line in r.stderr.splitlines():
        if any(k in line for k in ("mean_volume", "max_volume")):
            print("   " + line.split("] ")[-1])


def segments(wav: Path) -> None:
    """Сегменты прогона БЕЗ VAD — с таймкодами и длительностью."""
    out = wav.with_suffix(".probe")
    subprocess.run([CLI, "-m", str(MODEL), "-l", "en", "-f", str(wav),
                    "-oj", "-of", str(out), "-np"], capture_output=True, text=True)
    js = Path(f"{out}.json")
    if not js.is_file():
        print("   🔴 прогон без VAD не дал json")
        return
    data = json.loads(js.read_text(encoding="utf-8", errors="replace"))
    segs = data.get("transcription", [])
    print(f"\n── прогон без VAD: сегментов {len(segs)}")
    print("   таймкод            длит.  слов  текст")
    for s in segs:
        o = s.get("offsets", {})
        st, en = o.get("from", 0) / 1000, o.get("to", 0) / 1000
        text = s.get("text", "").strip()
        print(f"   {st:7.1f}–{en:7.1f} {en - st:6.1f}s {len(text.split()):5d}  {text[:70]}")


def vad_at(wav: Path, thr: float) -> None:
    """Сколько речи находит VAD на данном пороге."""
    out = wav.with_suffix(f".vad{thr}")
    r = subprocess.run([CLI, "-m", str(MODEL), "-l", "en", "-f", str(wav),
                        "--vad", "-vm", str(VAD), "-vt", str(thr),
                        "-oj", "-of", str(out)], capture_output=True, text=True)
    total = re.search(r"total duration of speech segments: ([\d.]+)", r.stderr)
    nseg = re.search(r"detected (\d+) speech segments", r.stderr)
    js = Path(f"{out}.json")
    words = 0
    if js.is_file():
        data = json.loads(js.read_text(encoding="utf-8", errors="replace"))
        words = len(" ".join(s["text"] for s in data.get("transcription", [])).split())
    print(f"   порог {thr}: сегментов {nseg.group(1) if nseg else 0:>3} · "
          f"речи {total.group(1) if total else '0.00':>7} с · слов {words}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("efta")
    ap.add_argument("--ds", type=int, default=8)
    ap.add_argument("--seconds", type=int, default=300)
    a = ap.parse_args()
    with tempfile.TemporaryDirectory(prefix="efta_probe_") as tmp:
        src = fetch(a.ds, a.efta, Path(tmp))
        wav = to_wav(src, a.seconds)
        level(wav)
        print("\n── VAD на разных порогах")
        for thr in (0.5, 0.3, 0.2):
            vad_at(wav, thr)
        segments(wav)
    return 0


if __name__ == "__main__":
    sys.exit(main())
