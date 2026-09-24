"""Inventory of the DOJ Epstein Library datasets on archive.org without downloading.

Reads each zip's content listing (archive.org zip view) and the Opticon .OPT
load file (one line per page) to get exact file, size and page counts.
"""
import csv
import html
import re
import sys
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

ITEM = "data-set-8_20251228"
ZIPS = {
    1: "DataSet 01.zip", 2: "DataSet 02.zip", 3: "DataSet 03.zip",
    4: "DataSet 04.zip", 5: "DataSet 05.zip", 6: "DataSet 06.zip",
    7: "DataSet 07.zip", 8: "DataSet 08.zip", 9: "DataSet 09 - Incomplete.zip",
    10: "DataSet 10.zip", 11: "DataSet 11.zip", 12: "DataSet 12.zip",
}
ROW = re.compile(r'<a href="(//archive\.org/download/[^"]+)">([^<]+)</a>.*?<td id="size">(\d+)')
OUT = Path(__file__).parent / "manifest"


def fetch(url: str, timeout: int = 600) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "efta-inventory/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def zip_url(n: int) -> str:
    return f"https://archive.org/download/{ITEM}/{urllib.parse.quote(ZIPS[n])}/"


def inventory(n: int) -> dict:
    page = fetch(zip_url(n))
    rows = [(html.unescape(p), int(s)) for _, p, s in ROW.findall(page)]
    with open(OUT / f"ds{n:02d}_files.tsv", "w") as f:
        for p, s in rows:
            f.write(f"{p}\t{s}\n")
    exts = Counter(Path(p).suffix.lower() or "(none)" for p, _ in rows)
    pages = 0
    for p, _ in rows:
        if p.upper().endswith(".OPT"):
            opt = fetch(zip_url(n) + urllib.parse.quote(p, safe=""))
            pages += sum(1 for line in opt.splitlines() if line.strip())
    return {
        "dataset": n,
        "files": len(rows),
        "bytes": sum(s for _, s in rows),
        "pages_opt": pages,
        "exts": ";".join(f"{e}:{c}" for e, c in exts.most_common()),
    }


def main() -> int:
    OUT.mkdir(exist_ok=True)
    sets = [int(a) for a in sys.argv[1:]] or list(ZIPS)
    with open(OUT / "inventory.csv", "a", newline="") as f:
        w = csv.DictWriter(f, ["dataset", "files", "bytes", "pages_opt", "exts"])
        if f.tell() == 0:
            w.writeheader()
        for n in sets:
            try:
                row = inventory(n)
            except Exception as e:
                print(f"DS{n}: ERROR {e}", flush=True)
                continue
            w.writerow(row)
            f.flush()
            print(row, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
