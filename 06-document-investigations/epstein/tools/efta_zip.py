#!/usr/bin/env python3
"""efta_zip.py — ОДИН способ ходить в удалённые zip DOJ Epstein Library.

🔴 Повод — `PIT-E` №4 (01.10.2026). Дефект «центральный каталог zip качается
заново на каждый файл» чинили дважды: сперва в `efta_to_md.py` (26.09, дало ×4
и отдельный пункт в CHANGELOG 1.5.0), потом заново в `efta_media.py` (01.10,
дало ×11 — до починки прогон давал 12 нот за 5 часов). Второй инструмент писался
рядом с первым и просто не получил исправление.

Модуль существует, чтобы третьего раза не было: любой новый инструмент, которому
нужен член удалённого архива, берёт `ZipSession` отсюда, а не пишет свой
`RemoteZip(url)` в цикле.

Что здесь важно по существу:
  · **одно соединение на прогон** — каталог DS10 это полмиллиона записей,
    перекачивать его ради файла в сотню килобайт нельзя;
  · **пересоздание сессии при обрыве** — archive.org рвёт соединения, и
    порванную сессию переиспользовать нельзя, иначе сыплются `SSLError`;
  · **ретраи на разрешении адреса** — HEAD к archive.org отвечает то 500,
    то таймаутом, и без повтора падает весь датасет.
"""
from __future__ import annotations

import shutil
import time
import urllib.parse
import urllib.request
from pathlib import Path

from remotezip import RemoteZip

ITEM = "https://archive.org/download/data-set-8_20251228/"


def zip_url(ds: int, tries: int = 5) -> str:
    """Адрес датанода для zip датасета, с ретраями на отказ archive.org."""
    name = "DataSet 09 - Incomplete.zip" if ds == 9 else f"DataSet {ds:02d}.zip"
    req = urllib.request.Request(ITEM + urllib.parse.quote(name), method="HEAD")
    for i in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.url
        except Exception as e:
            if i == tries - 1:
                raise
            print(f"  zip_url DS{ds} попытка {i + 1}: {e!r}"[:160], flush=True)
            time.sleep(15 * (i + 1))
    raise RuntimeError("unreachable")


class ZipSession:
    """Одно соединение с удалённым zip на весь прогон датасета."""

    def __init__(self, url: str) -> None:
        self.url = url
        self._zip: RemoteZip | None = None

    def _open(self) -> RemoteZip:
        if self._zip is None:
            self._zip = RemoteZip(self.url, timeout=120)
        return self._zip

    def close(self) -> None:
        if self._zip is not None:
            try:
                self._zip.close()
            except Exception:
                pass
            self._zip = None

    def names(self) -> list[tuple[str, int]]:
        """Имена и размеры членов архива — каталог читается один раз."""
        return [(i.filename, i.file_size) for i in self._open().infolist()]

    def extract(self, member: str, dest: Path, tries: int = 5) -> None:
        """Забрать один член на диск, пересоздавая сессию при сбое."""
        for i in range(tries):
            try:
                with self._open().open(member) as src, open(dest, "wb") as out:
                    shutil.copyfileobj(src, out, 1 << 20)
                return
            except Exception:
                self.close()
                if i == tries - 1:
                    raise
                time.sleep(20 * (i + 1))
