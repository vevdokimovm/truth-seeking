#!/usr/bin/env python3
"""efta_search.py — page-level full-text index over the EFTA `.md` notes.

    efta_search.py build                 index new/changed notes (incremental)
    efta_search.py q 'mossad NEAR blackmail' [--limit 30]
    efta_search.py count 'term'          hits per dataset
    efta_search.py page EFTA00008599 4   print one page

Sources: repo `corpus/DSNN` and `~/raw-originals/epstein-text/DSNN`.
The database lives outside the repo: `~/raw-originals/epstein-text/efta.db`.
FTS5 query syntax: "exact phrase", AND/OR/NOT, NEAR(a b, 10), prefix*.
"""
from __future__ import annotations

import argparse
import re
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOTS = [HERE.parent / "corpus", Path.home() / "raw-originals/epstein-text"]
DB = Path.home() / "raw-originals/epstein-text/efta.db"
PAGE = re.compile(r"^### Стр\. (\d+) · (.+)$", re.M)


class Index:
    """SQLite FTS5 index with one row per document page."""

    def __init__(self, path: Path = DB) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS docs(efta TEXT PRIMARY KEY, ds INT, mtime REAL);
            CREATE VIRTUAL TABLE IF NOT EXISTS pages USING fts5(
                efta UNINDEXED, ds UNINDEXED, page UNINDEXED, kind UNINDEXED, body,
                tokenize='porter unicode61');
        """)

    def build(self) -> None:
        """Index notes that are new or modified since the last build."""
        known = dict(self.db.execute("SELECT efta, mtime FROM docs"))
        added = 0
        for root in ROOTS:
            for f in sorted(root.glob("DS*/EFTA*.md")):
                mtime = f.stat().st_mtime
                if known.get(f.stem) == mtime:
                    continue
                ds = int(f.parent.name[2:])
                self.db.execute("DELETE FROM pages WHERE efta=?", (f.stem,))
                text = f.read_text(encoding="utf-8")
                marks = list(PAGE.finditer(text))
                if not marks:
                    self.db.execute("INSERT INTO pages VALUES(?,?,?,?,?)",
                                    (f.stem, ds, 0, "таблица", text))
                for i, m in enumerate(marks):
                    end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
                    self.db.execute("INSERT INTO pages VALUES(?,?,?,?,?)",
                                    (f.stem, ds, int(m.group(1)), m.group(2),
                                     text[m.end():end].strip()))
                self.db.execute("INSERT OR REPLACE INTO docs VALUES(?,?,?)",
                                (f.stem, ds, mtime))
                added += 1
                if added % 500 == 0:
                    self.db.commit()
        self.db.commit()
        total = self.db.execute("SELECT count(*) FROM docs").fetchone()[0]
        print(f"indexed +{added}, total documents {total}")

    def query(self, q: str, limit: int) -> None:
        """Print matching pages with a highlighted snippet."""
        rows = self.db.execute(
            "SELECT efta, ds, page, kind, snippet(pages, 4, '«', '»', ' … ', 24) "
            "FROM pages WHERE pages MATCH ? ORDER BY rank LIMIT ?", (q, limit))
        n = 0
        for efta, ds, page, kind, snip in rows:
            n += 1
            print(f"{efta} p{page} DS{ds} [{kind[:22]}]\n    {snip.replace(chr(10), ' ')}")
        print(f"-- {n} shown")

    def count(self, q: str) -> None:
        """Print hit counts (pages, documents) per dataset."""
        for ds, pages, docs in self.db.execute(
                "SELECT ds, count(*), count(DISTINCT efta) FROM pages "
                "WHERE pages MATCH ? GROUP BY ds ORDER BY ds", (q,)):
            print(f"DS{ds}: {pages} pages in {docs} documents")

    def page(self, efta: str, page: int) -> None:
        """Print one page body."""
        for kind, body in self.db.execute(
                "SELECT kind, body FROM pages WHERE efta=? AND page=?", (efta, page)):
            print(f"{efta} p{page} [{kind}]\n{body}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["build", "q", "count", "page"])
    ap.add_argument("arg", nargs="*")
    ap.add_argument("--limit", type=int, default=30)
    a = ap.parse_args()
    idx = Index()
    if a.cmd == "build":
        idx.build()
    elif a.cmd == "q":
        idx.query(" ".join(a.arg), a.limit)
    elif a.cmd == "count":
        idx.count(" ".join(a.arg))
    else:
        idx.page(a.arg[0], int(a.arg[1]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
