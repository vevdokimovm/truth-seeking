#!/usr/bin/env python3
"""efta_telemetry.py — periodic telemetry of the Epstein corpus pipeline for later tuning.

Every --interval seconds appends one row to `telemetry/telemetry.csv` and writes
human-readable events to `telemetry/events.md` whenever something changes:
stage progress and rate, stalls, process deaths, reboots, CPU throttling, load,
memory, disk, power, VPN/route/proxy, archive.org latency and HTTP status,
error counts in stage logs.

    efta_telemetry.py [--interval 300]
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "telemetry"
RAW = Path.home() / "raw-originals/epstein-text"
CORPUS = HERE.parent / "corpus"
LOGS = {"B": Path.home() / "epstein/stageB.log", "E": Path.home() / "epstein/stageE.log"}
PROBE = "https://archive.org/download/data-set-8_20251228/DataSet%2011.zip"
MEDIA_RE = re.compile(r"\.(mp4|m4a|mp3|avi|mov|m4v|opus|amr|wav|3gp|vob|ts|wmv)\.md$")
FIELDS = ["ts", "uptime_min", "b_docs", "b_rate_min", "e_notes", "e_rate_h",
          "runner_b", "runner_e", "tesseract_n", "whisper_n", "our_cpu_pct",
          "load1", "cpu_speed_limit", "mem_free_mb", "swap_used_mb", "disk_free_gb",
          "power", "route_if", "proxy_on", "utun_n", "ia_code", "ia_connect_s",
          "ia_ttfb_s", "b_err", "e_fail", "b_retry", "e_retry"]


def sh(cmd: list[str], timeout: int = 60) -> str:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout).stdout
    except Exception:
        return ""


class Probe:
    """Collects one telemetry sample."""

    def count_b(self) -> int:
        d = RAW / "DS11"
        return sum(1 for e in os.scandir(d) if e.name.startswith("EFTA")) if d.exists() else 0

    def count_e(self) -> int:
        n = 0
        for root in (CORPUS, RAW):
            for d in root.glob("DS*"):
                n += sum(1 for e in os.scandir(d) if MEDIA_RE.search(e.name))
        return n

    def procs(self) -> dict:
        ps = sh(["ps", "-Ao", "pcpu=,command="])
        rows = [(float(l.split(None, 1)[0]), l.split(None, 1)[1]) for l in ps.splitlines()
                if l.strip() and len(l.split(None, 1)) == 2]
        ours = [c for c, cmd in rows if "tesseract" in cmd or "whisper-cli" in cmd
                or "epstein/.venv" in cmd]
        return {"runner_b": int(any("run_stage.sh" in c for _, c in rows)),
                "runner_e": int(any("run_media.sh" in c for _, c in rows)),
                "tesseract_n": sum("tesseract" in c for _, c in rows),
                "whisper_n": sum("whisper-cli" in c for _, c in rows),
                "our_cpu_pct": round(sum(ours))}

    def system(self) -> dict:
        boot = re.search(r"sec = (\d+)", sh(["sysctl", "-n", "kern.boottime"]))
        therm = re.search(r"CPU_Speed_Limit\s*=\s*(\d+)", sh(["pmset", "-g", "therm"]))
        vm = sh(["vm_stat"])
        page = 4096
        free = sum(int(m) for m in re.findall(
            r"Pages (?:free|inactive|speculative):\s+(\d+)", vm)) * page // 2**20
        swap = re.search(r"used = ([\d.]+)M", sh(["sysctl", "-n", "vm.swapusage"]))
        batt = sh(["pmset", "-g", "batt"])
        route = re.search(r"interface: (\S+)", sh(["route", "-n", "get", "default"]))
        proxy = sh(["scutil", "--proxy"])
        return {"uptime_min": int((time.time() - int(boot.group(1))) / 60) if boot else "",
                "load1": os.getloadavg()[0].__round__(2),
                "cpu_speed_limit": therm.group(1) if therm else "",
                "mem_free_mb": free,
                "swap_used_mb": round(float(swap.group(1))) if swap else "",
                "disk_free_gb": round(shutil.disk_usage(Path.home()).free / 1e9, 1),
                "power": "AC" if "AC Power" in batt else "battery",
                "route_if": route.group(1) if route else "none",
                "proxy_on": int(bool(re.search(r"(HTTPS?|SOCKS)Enable : 1", proxy))),
                "utun_n": sh(["ifconfig", "-l"]).count("utun")}

    def archive(self) -> dict:
        out = sh(["curl", "-s", "-o", "/dev/null", "-I", "-L", "-m", "40", "-w",
                  "%{http_code} %{time_connect} %{time_starttransfer}", PROBE], 60).split()
        return dict(zip(["ia_code", "ia_connect_s", "ia_ttfb_s"],
                        out if len(out) == 3 else ["000", "", ""]))

    def logs(self) -> dict:
        def grep(path: Path, pat: str) -> int:
            return len(re.findall(pat, path.read_text(errors="replace"))) if path.exists() else 0
        return {"b_err": grep(LOGS["B"], r"Traceback|documents failed"),
                "e_fail": grep(LOGS["E"], r"  FAIL "),
                "b_retry": grep(LOGS["B"], r" try [2-5] "),
                "e_retry": grep(LOGS["E"], r" try [2-5]")}


class Telemetry:
    """Writes samples and change events."""

    WATCH = {"runner_b": "раннер этапа B", "runner_e": "раннер этапа E",
             "power": "питание", "route_if": "интерфейс маршрута по умолчанию (VPN)",
             "proxy_on": "системный прокси", "ia_code": "HTTP-код archive.org"}

    def __init__(self) -> None:
        OUT.mkdir(parents=True, exist_ok=True)
        self.csv = OUT / "telemetry.csv"
        self.events = OUT / "events.md"
        if not self.events.exists():
            self.events.write_text("# Журнал событий конвейера Epstein\n\n"
                                   "> Пишется `tools/efta_telemetry.py` автоматически "
                                   "при любом изменении состояния. Ручные записи — "
                                   "с пометкой ✍️.\n\n", encoding="utf-8")
        self.prev: dict | None = None

    def event(self, text: str) -> None:
        with open(self.events, "a", encoding="utf-8") as f:
            f.write(f"- **{datetime.now():%Y-%m-%d %H:%M}** — {text}\n")

    def sample(self) -> dict:
        p = Probe()
        row = {"ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
               "b_docs": p.count_b(), "e_notes": p.count_e(),
               **p.procs(), **p.system(), **p.archive(), **p.logs()}
        prev, now = self.prev, time.time()
        if prev:
            mins = (now - prev["_t"]) / 60
            row["b_rate_min"] = round((row["b_docs"] - prev["b_docs"]) / mins, 1)
            row["e_rate_h"] = round((row["e_notes"] - prev["e_notes"]) / mins * 60, 1)
        row["_t"] = now
        return row

    def diff(self, row: dict) -> None:
        prev = self.prev
        if prev is None:
            self.event(f"телеметрия запущена · B {row['b_docs']} док. · E {row['e_notes']} "
                       f"медиа · маршрут {row['route_if']} · CPU limit "
                       f"{row['cpu_speed_limit']}% · диск {row['disk_free_gb']} ГБ")
            return
        if isinstance(row["uptime_min"], int) and isinstance(prev["uptime_min"], int) \
                and row["uptime_min"] < prev["uptime_min"]:
            self.event("🔴 **перезагрузка мака** — фоновые этапы остановлены")
        for k, name in self.WATCH.items():
            if str(row[k]) != str(prev[k]):
                self.event(f"{name}: `{prev[k]}` → `{row[k]}`")
        if row["cpu_speed_limit"] and prev["cpu_speed_limit"] and \
                abs(int(row["cpu_speed_limit"]) - int(prev["cpu_speed_limit"])) > 15:
            self.event(f"троттлинг CPU: лимит частоты {prev['cpu_speed_limit']}% → "
                       f"{row['cpu_speed_limit']}%")
        for k, name in (("b_err", "ошибки B"), ("e_fail", "сбои E"),
                        ("b_retry", "перезапуски B"), ("e_retry", "перезапуски E")):
            if row[k] > prev[k]:
                self.event(f"{name}: +{row[k] - prev[k]} (всего {row[k]})")
        if row["runner_b"] and row.get("b_rate_min") == 0:
            self.event("⚠️ этап B: ноль новых документов за интервал (возможное зависание)")
        if row["ia_ttfb_s"] and prev["ia_ttfb_s"] and \
                float(row["ia_ttfb_s"]) > 3 * max(float(prev["ia_ttfb_s"]), 0.5):
            self.event(f"archive.org: время ответа {prev['ia_ttfb_s']} → {row['ia_ttfb_s']} с")
        if row["disk_free_gb"] < 10 <= prev["disk_free_gb"]:
            self.event(f"🔴 диск: свободно меньше 10 ГБ ({row['disk_free_gb']})")

    def run(self, interval: int) -> None:
        new = not self.csv.exists()
        while True:
            row = self.sample()
            self.diff(row)
            with open(self.csv, "a", newline="") as f:
                w = csv.DictWriter(f, FIELDS, extrasaction="ignore")
                if new:
                    w.writeheader()
                    new = False
                w.writerow(row)
            self.prev = row
            time.sleep(interval)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--interval", type=int, default=300)
    Telemetry().run(ap.parse_args().interval)
