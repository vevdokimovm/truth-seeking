#!/usr/bin/env python3
"""efta_netplot.py — render telemetry/network.csv into a self-contained HTML dashboard.

Stdlib only (no matplotlib): Python embeds the rows as JSON, inline JS draws SVG
small multiples on a shared time axis with hover crosshair, VPN reconnect markers,
KPI tiles, Spearman correlations and an hourly table view.

    efta_netplot.py [--csv telemetry/network.csv] [--out telemetry/network.html]
"""
from __future__ import annotations

import argparse
import csv
import json
import statistics as st
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
TELEMETRY = HERE.parent / "telemetry"
NUMERIC = ["ia_kbps", "cf_kbps", "ia_ttfb_s", "dns_ms", "wifi_snr", "wifi_tx_mbps",
           "en0_rx_kbps", "tun_rx_kbps", "docs_done"]


class NetReport:
    """Loads network.csv, derives rates and summaries, writes the HTML page."""

    def __init__(self, path: Path) -> None:
        self.rows = list(csv.DictReader(open(path, encoding="utf-8")))
        self.t = [datetime.fromisoformat(r["ts"]) for r in self.rows]
        self.cols = {k: [self._num(r.get(k, "")) for r in self.rows] for k in NUMERIC}
        self.cols["docs_min"] = self._docs_rate()
        self.cols["ia_ok"] = [v if r["ia_code"] in ("200", "206") else None
                              for v, r in zip(self.cols["ia_kbps"], self.rows)]

    @staticmethod
    def _num(s: str) -> float | None:
        try:
            return float(s)
        except ValueError:
            return None

    def _docs_rate(self) -> list[float | None]:
        d = self.cols["docs_done"]
        out: list[float | None] = [None]
        for i in range(1, len(d)):
            mins = (self.t[i] - self.t[i - 1]).total_seconds() / 60
            cur, prev = d[i], d[i - 1]
            ok = cur is not None and prev is not None and mins > 0
            out.append(round((cur - prev) / mins, 1) if ok else None)
        return out

    @staticmethod
    def _spearman(a: list, b: list) -> tuple[float, int]:
        pairs = [(x, y) for x, y in zip(a, b) if x is not None and y is not None]

        def rank(v: list[float]) -> list[float]:
            order = sorted(range(len(v)), key=v.__getitem__)
            r = [0.0] * len(v)
            i = 0
            while i < len(order):
                j = i
                while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                    j += 1
                for k in range(i, j + 1):
                    r[order[k]] = (i + j) / 2
                i = j + 1
            return r

        if len(pairs) < 10:
            return float("nan"), len(pairs)
        ra, rb = rank([p[0] for p in pairs]), rank([p[1] for p in pairs])
        return round(st.correlation(ra, rb), 2), len(pairs)

    def _grouped(self, key_of) -> list[list]:
        """Medians per group of rows (VPN server, uplink network, ...)."""
        c, groups = self.cols, {}
        for i, r in enumerate(self.rows):
            groups.setdefault(key_of(r), []).append(i)
        out = []
        for key, idx in groups.items():
            def sm(k: str) -> float | str:
                v = [c[k][i] for i in idx if c[k][i] is not None]
                return round(st.median(v), 1) if v else "—"
            fail = sum(self.rows[i]["ia_code"] not in ("200", "206") for i in idx)
            span = f"{self.rows[idx[0]]['ts'][5:16]} – {self.rows[idx[-1]]['ts'][11:16]}"
            out.append([key, span, len(idx), sm("ia_ok"), sm("cf_kbps"),
                        sm("tun_rx_kbps"), sm("docs_min"), sm("ia_ttfb_s"), fail])
        return out

    def summary(self) -> dict:
        c = self.cols

        def med(k: str) -> float:
            v: list[float] = [x for x in c[k] if x is not None]
            return round(st.median(v), 1) if v else 0

        reconnects = [r["ts"] for i, r in enumerate(self.rows)
                      if i and r["route_if"] != self.rows[i - 1]["route_if"]]
        fails = sum(r["ia_code"] not in ("200", "206") for r in self.rows)
        corr = {name: self._spearman(c[a], c["docs_min"]) for name, a in
                (("туннель, КБ/с", "tun_rx_kbps"), ("проба archive.org", "ia_ok"),
                 ("проба Cloudflare", "cf_kbps"), ("TTFB archive.org", "ia_ttfb_s"),
                 ("Wi-Fi SNR", "wifi_snr"))}
        hours: dict[str, list[int]] = {}
        for i, t in enumerate(self.t):
            hours.setdefault(t.strftime("%d.%m %H:00"), []).append(i)
        hourly = []
        for h, idx in hours.items():
            def hm(k: str) -> float | str:
                v = [c[k][i] for i in idx if c[k][i] is not None]
                return round(st.median(v), 1) if v else "—"
            hourly.append([h, len(idx), hm("ia_ok"), hm("cf_kbps"), hm("tun_rx_kbps"),
                           hm("docs_min"), hm("ia_ttfb_s"), hm("dns_ms")])
        by_server = self._grouped(lambda r: f"{r.get('vpn_server') or 'не записан'} · "
                                           f"{r.get('vpn_net') or '—'}")
        by_uplink = self._grouped(lambda r: f"{r.get('net_kind') or 'не записан'} · {r.get('wifi_ssid') or ''} · "
                                           f"{r.get('isp_org') or '—'} · "
                                           f"{r.get('gw_mac') or '—'}")
        return {"span": [self.rows[0]["ts"], self.rows[-1]["ts"]], "n": len(self.rows),
                "servers": by_server, "uplinks": by_uplink,

                "ia_med": med("ia_ok"), "cf_med": med("cf_kbps"),
                "tun_med": med("tun_rx_kbps"), "docs_med": med("docs_min"),
                "ttfb_med": med("ia_ttfb_s"), "reconnects": reconnects,
                "ia_fail": fails, "corr": {k: list(v) for k, v in corr.items()},
                "hourly": hourly}

    def write(self, out: Path) -> None:
        data = {"ts": [r["ts"] for r in self.rows],
                "route": [r["route_if"] for r in self.rows],
                "cols": self.cols, "sum": self.summary()}
        tpl = (HERE / "efta_netplot.html").read_text(encoding="utf-8")
        out.write_text(tpl.replace("/*__DATA__*/null", json.dumps(data, ensure_ascii=False)),
                       encoding="utf-8")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", type=Path, default=TELEMETRY / "network.csv")
    ap.add_argument("--out", type=Path, default=TELEMETRY / "network.html")
    a = ap.parse_args()
    NetReport(a.csv).write(a.out)
    print(a.out)
