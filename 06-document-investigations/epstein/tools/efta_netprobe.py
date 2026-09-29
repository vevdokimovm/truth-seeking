#!/usr/bin/env python3
"""efta_netprobe.py — network telemetry for later charts: Wi-Fi, VPN, proxy, real throughput.

Every --interval seconds appends one row to `telemetry/network.csv`:
Wi-Fi link (RSSI, noise, tx rate, channel), default route interface (VPN tunnel id —
a change means a reconnect), system proxy, DNS time, real download speed from
archive.org and Cloudflare (1 MB each), byte rates on en0 and on the active tunnel
from interface counters, and pipeline progress for correlation.

    efta_netprobe.py [--interval 120]
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import socket
import subprocess
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "telemetry" / "network.csv"
RAW = Path.home() / "raw-originals/epstein-text"
IA = "https://dn720805.ca.archive.org/0/items/data-set-8_20251228/DataSet%2011.zip"
CF = "https://speed.cloudflare.com/__down?bytes=1000000"
FIELDS = ["ts", "route_if", "vpn_reconnect", "proxy_on", "wifi_rssi", "wifi_noise",
          "wifi_snr", "wifi_tx_mbps", "wifi_channel", "dns_ms", "ia_kbps", "ia_code",
          "ia_ttfb_s", "cf_kbps", "cf_code", "en0_rx_kbps", "en0_tx_kbps",
          "tun_rx_kbps", "tun_tx_kbps", "docs_done"]


def sh(cmd: list[str], timeout: int = 60) -> str:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout).stdout
    except Exception:
        return ""


class NetProbe:
    """One network sample; keeps previous counters for rates."""

    def __init__(self) -> None:
        self.prev_counters: dict[str, tuple[int, int]] = {}
        self.prev_t = 0.0
        self.prev_if = ""

    def wifi(self) -> dict:
        info = sh(["system_profiler", "SPAirPortDataType"], 30)
        cur = info.split("Current Network Information:", 1)[-1][:1500] \
            if "Current Network Information:" in info else ""
        sn = re.search(r"Signal / Noise: (-?\d+) dBm / (-?\d+) dBm", cur)
        tx = re.search(r"Transmit Rate: (\d+)", cur)
        ch = re.search(r"Channel: (\d+)", cur)
        rssi, noise = (int(sn.group(1)), int(sn.group(2))) if sn else ("", "")
        return {"wifi_rssi": rssi, "wifi_noise": noise,
                "wifi_snr": rssi - noise if sn else "",
                "wifi_tx_mbps": tx.group(1) if tx else "",
                "wifi_channel": ch.group(1) if ch else ""}

    def counters(self) -> dict[str, tuple[int, int]]:
        """Interface -> (ibytes, obytes) from netstat -ib (link-level rows)."""
        out: dict[str, tuple[int, int]] = {}
        for line in sh(["netstat", "-ib"]).splitlines()[1:]:
            p = line.split()
            if len(p) >= 10 and "<Link#" in p[2] and p[0] not in out:
                try:
                    out[p[0]] = (int(p[-5]), int(p[-2]))
                except ValueError:
                    pass
        return out

    def speed(self, url: str, rng: bool) -> tuple[str, str, str]:
        args = ["curl", "-s", "-o", "/dev/null", "-m", "40", "-w",
                "%{speed_download} %{http_code} %{time_starttransfer}"]
        if rng:
            args += ["-r", "0-999999"]
        out = sh(args + [url], 60).split()
        if len(out) != 3:
            return "0", "000", ""
        return str(round(float(out[0]) / 1024, 1)), out[1], out[2]

    def dns_ms(self) -> str:
        t = time.time()
        try:
            socket.getaddrinfo(f"probe{int(t)}.archive.org", 443)
        except Exception:
            pass
        return str(round((time.time() - t) * 1000))

    def sample(self) -> dict:
        route = re.search(r"interface: (\S+)", sh(["route", "-n", "get", "default"]))
        rif = route.group(1) if route else "none"
        proxy = sh(["scutil", "--proxy"])
        now, cnt = time.time(), self.counters()
        row = {"ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "route_if": rif,
               "vpn_reconnect": int(bool(self.prev_if) and rif != self.prev_if),
               "proxy_on": int(bool(re.search(r"(HTTPS?|SOCKS)Enable : 1", proxy))),
               "dns_ms": self.dns_ms(), **self.wifi()}
        row["ia_kbps"], row["ia_code"], row["ia_ttfb_s"] = self.speed(IA, True)
        row["cf_kbps"], row["cf_code"], _ = self.speed(CF, False)
        if self.prev_counters:
            dt = now - self.prev_t
            for key, iface in (("en0", "en0"), ("tun", rif)):
                if iface in cnt and iface in self.prev_counters:
                    rx = (cnt[iface][0] - self.prev_counters[iface][0]) / dt / 1024
                    tx = (cnt[iface][1] - self.prev_counters[iface][1]) / dt / 1024
                    row[f"{key}_rx_kbps"], row[f"{key}_tx_kbps"] = round(rx, 1), round(tx, 1)
        row["docs_done"] = sum(
            sum(1 for e in os.scandir(d) if e.name.startswith("EFTA"))
            for d in RAW.glob("DS*") if d.is_dir())
        self.prev_counters, self.prev_t, self.prev_if = cnt, now, rif
        return row

    def run(self, interval: int) -> None:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        new = not OUT.exists()
        while True:
            start = time.time()
            row = self.sample()
            with open(OUT, "a", newline="") as f:
                w = csv.DictWriter(f, FIELDS, extrasaction="ignore")
                if new:
                    w.writeheader()
                    new = False
                w.writerow(row)
            time.sleep(max(10, interval - (time.time() - start)))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--interval", type=int, default=120)
    NetProbe().run(ap.parse_args().interval)
