#!/usr/bin/env python3
"""efta_page_png.py — render one page of an EFTA document from the remote zip.

    efta_page_png.py EFTA00008599 4 [--out DIR] [--dpi 110]

Used to check quotes by eye against the original (OCR is not trusted for citations).
Finds the zip member via the inventory listings in ~/epstein/manifest/dsNN_files.tsv.
"""
from __future__ import annotations

import argparse
import sys
import urllib.parse
import urllib.request
from pathlib import Path

import pymupdf
from remotezip import RemoteZip

MANIFEST = Path.home() / "epstein/manifest"
ITEM = "https://archive.org/download/data-set-8_20251228/"
ZIPS = {1: "DataSet 01.zip", 2: "DataSet 02.zip", 3: "DataSet 03.zip",
        4: "DataSet 04.zip", 5: "DataSet 05.zip", 6: "DataSet 06.zip",
        7: "DataSet 07.zip", 8: "DataSet 08.zip", 9: "DataSet 09 - Incomplete.zip",
        10: "DataSet 10.zip", 11: "DataSet 11.zip", 12: "DataSet 12.zip"}


def locate(efta: str) -> tuple[int, str]:
    """Return (dataset, zip member) for an EFTA number."""
    for tsv in sorted(MANIFEST.glob("ds*_files.tsv")):
        with open(tsv) as f:
            for line in f:
                if f"/{efta}.pdf\t" in line:
                    return int(tsv.name[2:4]), line.split("\t")[0]
    raise SystemExit(f"{efta}: not found in manifests")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("efta")
    ap.add_argument("page", type=int)
    ap.add_argument("--out", default="/private/tmp/efta-png")
    ap.add_argument("--dpi", type=int, default=110)
    a = ap.parse_args()
    ds, member = locate(a.efta)
    url = ITEM + urllib.parse.quote(ZIPS[ds])
    with urllib.request.urlopen(urllib.request.Request(url, method="HEAD"),
                                timeout=60) as r:
        url = r.url
    with RemoteZip(url, timeout=120) as z:
        doc = pymupdf.open(stream=z.read(member), filetype="pdf")
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{a.efta}_p{a.page}.png"
    doc[a.page - 1].get_pixmap(dpi=a.dpi).save(path)
    print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
