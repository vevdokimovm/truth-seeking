#!/usr/bin/env python3
"""Index the downloaded EFTA corpus into SQLite FTS5 and search it locally.

Build:   python efta_index.py build --corpus ./corpus --db efta.db
Search:  python efta_index.py search --db efta.db --query "flight log"
Stats:   python efta_index.py stats --db efta.db

Requires: pip install pymupdf
PDFs with no text layer are flagged needs_ocr=1 -> run ocrmypdf on them
(see file 10, stage 3), then re-run build (re-indexes changed files only).
"""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

import fitz  # PyMuPDF

SCHEMA = """
CREATE TABLE IF NOT EXISTS docs(
    id INTEGER PRIMARY KEY,
    bates TEXT,
    dataset TEXT,
    path TEXT UNIQUE,
    mtime REAL,
    pages INTEGER,
    chars INTEGER,
    needs_ocr INTEGER
);
CREATE VIRTUAL TABLE IF NOT EXISTS docs_fts USING fts5(
    text, content='', tokenize='unicode61'
);
"""


def extract_text(path: Path) -> tuple[str, int]:
    with fitz.open(path) as pdf:
        text = "\n".join(page.get_text() for page in pdf)
        return text, pdf.page_count


def build(corpus: Path, db_path: Path) -> None:
    con = sqlite3.connect(db_path)
    con.executescript(SCHEMA)
    known = dict(con.execute("SELECT path, mtime FROM docs"))
    pdfs = sorted(corpus.rglob("*.pdf"))
    done = skipped = failed = 0
    for pdf in pdfs:
        key, mtime = str(pdf), pdf.stat().st_mtime
        if known.get(key) == mtime:
            skipped += 1
            continue
        try:
            text, pages = extract_text(pdf)
        except Exception as exc:
            print(f"  ! {pdf.name}: {exc}")
            failed += 1
            continue
        needs_ocr = int(len(text.strip()) < pages * 20)
        con.execute("DELETE FROM docs_fts WHERE rowid IN "
                    "(SELECT id FROM docs WHERE path = ?)", (key,))
        con.execute("DELETE FROM docs WHERE path = ?", (key,))
        cur = con.execute(
            "INSERT INTO docs(bates, dataset, path, mtime, pages, chars, "
            "needs_ocr) VALUES(?,?,?,?,?,?,?)",
            (pdf.stem, pdf.parent.name, key, mtime, pages,
             len(text), needs_ocr))
        con.execute("INSERT INTO docs_fts(rowid, text) VALUES(?, ?)",
                    (cur.lastrowid, text))
        done += 1
        if done % 200 == 0:
            con.commit()
            print(f"  indexed {done} (skipped {skipped}, failed {failed})")
    con.commit()
    total_ocr = con.execute(
        "SELECT COUNT(*) FROM docs WHERE needs_ocr = 1").fetchone()[0]
    print(f"Done: +{done} indexed, {skipped} unchanged, {failed} failed; "
          f"{total_ocr} docs flagged needs_ocr.")
    con.close()


def search(db_path: Path, query: str, limit: int) -> None:
    con = sqlite3.connect(db_path)
    rows = con.execute(
        "SELECT d.bates, d.dataset, snippet(docs_fts, 0, '[', ']', '…', 12) "
        "FROM docs_fts JOIN docs d ON d.id = docs_fts.rowid "
        "WHERE docs_fts MATCH ? ORDER BY rank LIMIT ?",
        (query, limit)).fetchall()
    for bates, dataset, snip in rows:
        print(f"{bates}  [{dataset}]  {snip}")
    print(f"\n{len(rows)} result(s) shown (limit {limit}).")
    con.close()


def stats(db_path: Path) -> None:
    con = sqlite3.connect(db_path)
    for row in con.execute(
            "SELECT dataset, COUNT(*), SUM(pages), SUM(needs_ocr) "
            "FROM docs GROUP BY dataset ORDER BY dataset"):
        print(f"{row[0]}: {row[1]} docs, {row[2]} pages, "
              f"{row[3]} need OCR")
    con.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["build", "search", "stats"])
    parser.add_argument("--corpus", default="corpus")
    parser.add_argument("--db", default="efta.db")
    parser.add_argument("--query", default="")
    parser.add_argument("--limit", type=int, default=25)
    args = parser.parse_args()

    if args.mode == "build":
        build(Path(args.corpus), Path(args.db))
    elif args.mode == "search":
        search(Path(args.db), args.query, args.limit)
    else:
        stats(Path(args.db))


if __name__ == "__main__":
    main()
