#!/usr/bin/env python3
"""efta_to_md.py — DOJ Epstein Library zip → one `.md` per EFTA document.

Extends `_base/07-media-to-text-lab/tools/docs_to_md.py` (text layer, note
passport) with what the lab lacks (its README §5): page-level OCR for scans.

Per page: text layer if present (>100 chars), else tesseract OCR at 300 dpi
with mean word confidence. Pages whose OCR is unreadable (photos of evidence,
blank placeholders) are recorded as "OCR refused", never as "empty page"
(`/media-to-text` §0). Media members are queued for stage E (whisper).

Run:
    efta_to_md.py --zip ds01.zip --ds 1 --out <dir> [--workers 8]
    efta_to_md.py --url https://.../DataSet%2011.zip --ds 11 --out <dir>
Resumable: documents whose `.md` exists are skipped.
"""
from __future__ import annotations

import argparse
import csv
import io
import os
import subprocess
import sys
import time
import zipfile
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import pymupdf

LAB = Path(__file__).resolve().parents[3] / "_base/07-media-to-text-lab/tools"
sys.path.insert(0, str(LAB))
from docs_to_md import from_xlsx  # noqa: E402  (lab extractor for spreadsheets)

TEXT_LAYER_MIN = 100
OCR_MIN_CONF = 55
OCR_MIN_WORDS = 8
MEDIA = {".mp4", ".m4a", ".mp3", ".avi", ".mov", ".m4v", ".opus", ".amr",
         ".wav", ".3gp", ".vob", ".ts", ".wmv"}
SHEETS = {".xlsx", ".xls", ".csv"}


class ZipSource:
    """Local zip or remote zip read through HTTP Range requests."""

    def __init__(self, zip_path: str | None, url: str | None) -> None:
        self.zip_path, self.url = zip_path, url

    def open(self) -> zipfile.ZipFile:
        if self.zip_path:
            return zipfile.ZipFile(self.zip_path)
        from remotezip import RemoteZip
        return RemoteZip(self.url)


def ocr_page(page: pymupdf.Page) -> tuple[str, float, int]:
    """OCR one page with tesseract; return text, mean confidence, word count."""
    png = page.get_pixmap(dpi=300, colorspace=pymupdf.csGRAY).tobytes("png")
    r = subprocess.run(["tesseract", "stdin", "stdout", "-l", "eng", "tsv"],
                       input=png, capture_output=True, timeout=300,
                       env={**os.environ, "OMP_THREAD_LIMIT": "1"})
    lines: dict[tuple, list[str]] = {}
    confs = []
    for row in csv.reader(io.StringIO(r.stdout.decode("utf-8", "replace")),
                          delimiter="\t", quoting=csv.QUOTE_NONE):
        if len(row) < 12 or row[0] != "5" or not row[11].strip():
            continue
        conf = float(row[10])
        if conf < 0:
            continue
        confs.append(conf)
        lines.setdefault((row[2], row[3], row[4]), []).append(row[11])
    text = "\n".join(" ".join(w) for w in lines.values())
    return text, (sum(confs) / len(confs) if confs else 0.0), len(confs)


def dark_share(page: pymupdf.Page) -> float:
    """Share of near-black pixels: DOJ redaction boxes show up as large black areas."""
    pix = page.get_pixmap(dpi=30, colorspace=pymupdf.csGRAY)
    s = pix.samples
    return sum(1 for b in s if b < 30) / max(len(s), 1)


def pdf_to_md(name: str, data: bytes, ds: int, source: str) -> tuple[str, dict]:
    """Build the note for one PDF; return markdown and passport stats."""
    efta = Path(name).stem
    doc = pymupdf.open(stream=data, filetype="pdf")
    parts, st = [], {"efta": efta, "ds": ds, "pages": doc.page_count,
                     "layer": 0, "ocr": 0, "redacted": 0, "refused": 0,
                     "conf_sum": 0.0}
    for i, page in enumerate(doc, 1):
        text = page.get_text().strip()
        if len(text) > TEXT_LAYER_MIN:
            st["layer"] += 1
            parts.append(f"### Стр. {i} · текстовый слой\n\n{text}")
            continue
        text, conf, words = ocr_page(page)
        if conf >= OCR_MIN_CONF and words >= OCR_MIN_WORDS:
            st["ocr"] += 1
            st["conf_sum"] += conf
            parts.append(f"### Стр. {i} · OCR, уверенность {conf:.0f}\n\n{text}")
        elif (dark := dark_share(page)) > 0.2:
            st["redacted"] += 1
            parts.append(f"### Стр. {i} · 🔲 зачернено\n\n_Чёрный блок на {dark:.0%} "
                         f"страницы — редактура DOJ. Распознано: {text or '—'}_")
        else:
            st["refused"] += 1
            parts.append(f"### Стр. {i} · 🔴 отказ OCR\n\n_Распознаваемого текста "
                         f"нет (слов {words}, уверенность {conf:.0f}) — вероятно фото "
                         f"или изображение. Это отказ инструмента, не пустая страница._")
    ocr_conf = st["conf_sum"] / st["ocr"] if st["ocr"] else 0
    md = f"""# {efta}

| паспорт | |
|---|---|
| документ | `{efta}` · DOJ Epstein Library · Data Set {ds} |
| источник | `{source}` → `{name}` |
| страниц | {st['pages']} |
| текстовый слой | {st['layer']} стр. |
| OCR (tesseract, 300 dpi) | {st['ocr']} стр., средняя уверенность {ocr_conf:.0f} |
| зачернено DOJ | {st['redacted']} стр. |
| отказ OCR | {st['refused']} стр. |
| режим | ⚠️ НЕ режим A: машинное извлечение, глазами не читано. Цитаты в синтезе сверяются с оригиналом по EFTA-номеру |
| потеря | изображения, почерк, вёрстка, зачернения не переносятся; OCR даёт ошибки распознавания |

{chr(10).join(parts)}
"""
    return md, st


def sheet_to_md(name: str, data: bytes, ds: int, source: str) -> str:
    """Spreadsheet members: xlsx via the lab extractor, csv verbatim."""
    ext = Path(name).suffix.lower()
    if ext == ".csv":
        text = data.decode("utf-8", "replace")
    else:
        tmp = Path(f"/tmp/efta_sheet_{Path(name).name}")
        tmp.write_bytes(data)
        text = from_xlsx(tmp)[0] if ext == ".xlsx" else "(xls: старый формат, не извлечён)"
        tmp.unlink()
    return (f"# {Path(name).stem}\n\n| | |\n|---|---|\n| источник | `{source}` → "
            f"`{name}` · Data Set {ds} |\n| метод | ячейки таблицы, без формул и формата |"
            f"\n\n```\n{text.strip()}\n```\n")


def read_retry(z: zipfile.ZipFile, name: str, tries: int = 4) -> bytes:
    """archive.org datanodes return sporadic 5xx; back off and retry."""
    for i in range(tries):
        try:
            return z.read(name)
        except Exception:
            if i == tries - 1:
                raise
            time.sleep(15 * (i + 1))
    raise RuntimeError("unreachable")


def work(src: ZipSource, names: list[str], ds: int, out: str, label: str) -> list[dict]:
    """Worker: process a chunk of zip members, write notes, return stats."""
    stats = []
    with src.open() as z:
        for name in names:
            ext = Path(name).suffix.lower()
            target = Path(out) / f"{Path(name).stem}.md"
            try:
                data = read_retry(z, name)
                if ext == ".pdf":
                    md, st = pdf_to_md(name, data, ds, label)
                    target.write_text(md, encoding="utf-8")
                    stats.append(st)
                elif ext in SHEETS:
                    target.write_text(sheet_to_md(name, data, ds, label), encoding="utf-8")
                    stats.append({"efta": Path(name).stem, "ds": ds, "pages": 0,
                                  "layer": 0, "ocr": 0, "redacted": 0, "refused": 0,
                                  "conf_sum": 0})
            except Exception as e:
                stats.append({"efta": Path(name).stem, "ds": ds, "error": repr(e)[:200]})
    return stats


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip")
    ap.add_argument("--url")
    ap.add_argument("--ds", type=int, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--chunk", type=int, default=25)
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    src = ZipSource(a.zip, a.url)
    label = Path(a.zip).name if a.zip else a.url.rsplit("/", 1)[-1]
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    with src.open() as z:
        members = [i.filename for i in z.infolist() if not i.is_dir()]
    media = [m for m in members if Path(m).suffix.lower() in MEDIA]
    todo = [m for m in members
            if Path(m).suffix.lower() in ({".pdf"} | SHEETS)
            and not (out / f"{Path(m).stem}.md").exists()]
    if a.limit:
        todo = todo[:a.limit]
    with open(out / "_media_queue.tsv", "w") as f:
        f.writelines(f"{a.ds}\t{m}\n" for m in media)
    print(f"DS{a.ds}: members={len(members)} todo={len(todo)} media={len(media)}",
          flush=True)

    chunks = [todo[i:i + a.chunk] for i in range(0, len(todo), a.chunk)]
    log = out / "_stats.tsv"
    new = not log.exists()
    done = errors = 0
    with open(log, "a") as f, ProcessPoolExecutor(a.workers) as ex:
        if new:
            f.write("efta\tds\tpages\tlayer\tocr\tredacted\trefused\tconf_sum\terror\n")
        futs = [ex.submit(work, src, c, a.ds, str(out), label) for c in chunks]
        for fut in as_completed(futs):
            for s in fut.result():
                errors += bool(s.get("error"))
                f.write("\t".join(str(s.get(k, "")) for k in
                        ("efta", "ds", "pages", "layer", "ocr", "redacted", "refused",
                         "conf_sum", "error")) + "\n")
            f.flush()
            done += 1
            if done % 10 == 0 or done == len(chunks):
                print(f"  chunks {done}/{len(chunks)}", flush=True)
    if errors:
        print(f"DS{a.ds}: {errors} documents failed, rerun to retry", flush=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
