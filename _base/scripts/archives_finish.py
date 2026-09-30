#!/usr/bin/env python3
"""archives_finish.py — довести `~/Developer` до пустоты, а не измерить её.

🔴 ЗАЧЕМ ОТДЕЛЬНЫЙ ИНСТРУМЕНТ (`ARCH-002`, `ARCH-004`). Ритуал выпуска собран
из самостоятельных шагов, каждый из которых проверяет СЕБЯ и отчитывается
успехом. Конечное состояние ритуала — пустая `~/Developer` — не принадлежит
ни одному шагу, и потому не проверялось никем изнутри цепочки.

`archives_check.py` это состояние ИЗМЕРЯЕТ и ничего не делает. `github_sync.py
--archive` версию, чей тег уже на GitHub, ПРОПУСКАЕТ («как deploy.sh»). В итоге
версия, у которой тег есть, а релиза нет, не доводится никем: измеритель
говорит «не доведено», деплоер говорит «пропускаю», архив лежит вечно.
Замер 29.09.2026: так пережили все уборки `personal-finance-dss` v9.13.17,
.19, .20, .21 и `character-a-analysis` v3.91.0.

ЧТО ДЕЛАЕТ. Для каждого архива в папке — ровно один из четырёх исходов:

    релиз с ассетом есть   → сверить sha256 и удалить архив (расходится — оставить)
    тег есть, релиза нет   → создать релиз с этим архивом, сверить, удалить
    тега нет вовсе         → не трогать: это работа `github_sync.py --archive`
    GitHub не ответил      → остановиться вслух, НЕ гадать (`ARCH-003`)

🔴 УДАЛЕНИЕ ТОЛЬКО ПО sha256. Совпадение имени не доказывает ничего: 25.09.2026
архив `personal-finance-dss-v9.13.16.zip` назывался как ассет и отличался
содержимым. Такой архив остаётся на диске и называется в отчёте.

🔴 ОПИСАНИЕ РЕЛИЗА — ПАРСЕРОМ ДЕПЛОЙЕРА (`release_notes.py`) из CHANGELOG
самого архива, не отсебятиной (`PIT-209`).

ЗАПУСК
    archives_finish.py                довести всё, что можно довести
    archives_finish.py --dry          показать исход по каждому, ничего не делая
    archives_finish.py --selftest
"""
from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

БАЗА = Path(__file__).resolve().parent.parent
OWNER = "vevdokimovm"
РАЗБОР = re.compile(r"^(?P<репа>.+)-v(?P<версия>\d+\.\d+\.\d+)\.zip$")


def sha256(путь: Path) -> str:
    h = hashlib.sha256()
    with путь.open("rb") as fh:
        for кусок in iter(lambda: fh.read(1 << 20), b""):
            h.update(кусок)
    return h.hexdigest()


def gh(*арг: str) -> tuple[int, str, str]:
    r = subprocess.run(["gh", *арг], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return r.returncode, (r.stdout or "").strip(), (r.stderr or "").strip()


def нет_такого(stderr: str) -> bool:
    """404 — это ОТВЕТ («такого нет»), а не молчание. Разводить обязательно."""
    return "404" in stderr or "Not Found" in stderr


class НетСвязи(Exception):
    """GitHub не ответил — состояние неизвестно, действовать нельзя."""


def ассет(репа: str, версия: str, имя: str) -> str | None:
    """id ассета с этим именем, None — релиза или ассета нет. Молчание → НетСвязи."""
    код, вывод, ошибка = gh("api", f"repos/{OWNER}/{репа}/releases/tags/v{версия}",
                            "-q", f'.assets[] | select(.name=="{имя}") | .id')
    if код == 0:
        return вывод or None
    if нет_такого(ошибка):
        return None
    raise НетСвязи(ошибка.splitlines()[0] if ошибка else "причина не названа")


def релиз_есть(репа: str, версия: str) -> bool:
    код, вывод, ошибка = gh("api", f"repos/{OWNER}/{репа}/releases/tags/v{версия}",
                            "-q", ".id")
    if код == 0:
        return bool(вывод)
    if нет_такого(ошибка):
        return False
    raise НетСвязи(ошибка.splitlines()[0] if ошибка else "причина не названа")


def тег_есть(репа: str, версия: str) -> bool:
    код, вывод, ошибка = gh("api", f"repos/{OWNER}/{репа}/git/ref/tags/v{версия}",
                            "-q", ".ref")
    if код == 0:
        return bool(вывод)
    if нет_такого(ошибка):
        return False
    raise НетСвязи(ошибка.splitlines()[0] if ошибка else "причина не названа")


def сверить_и_убрать(репа: str, версия: str, архив: Path, ид: str) -> bool:
    """True — архив удалён. False — содержимое разошлось, архив оставлен."""
    with tempfile.TemporaryDirectory() as tmp:
        r = subprocess.run(["gh", "api", f"repos/{OWNER}/{репа}/releases/assets/{ид}",
                            "-H", "Accept: application/octet-stream"],
                           capture_output=True)
        if r.returncode != 0:
            raise НетСвязи("ассет не скачался для сверки")
        скачан = Path(tmp) / архив.name
        скачан.write_bytes(r.stdout)
        сошлось = sha256(скачан) == sha256(архив)
    if сошлось:
        архив.unlink()
    return сошлось


def описание(архив: Path, репа: str, версия: str, куда: Path) -> str:
    """Заголовок релиза; тело кладётся в `куда`. Парсер — деплойера."""
    with tempfile.TemporaryDirectory() as tmp:
        чейнджлог = Path(tmp) / "CHANGELOG.md"
        with zipfile.ZipFile(архив) as z:
            имена = [n for n in z.namelist() if n.endswith("CHANGELOG.md")
                     and "_base/" not in n]
            имена.sort(key=lambda n: n.count("/"))
            if not имена:
                raise RuntimeError("CHANGELOG в архиве не найден — описание брать неоткуда")
            чейнджлог.write_bytes(z.read(имена[0]))
        r = subprocess.run([sys.executable, str(БАЗА / "scripts/release_notes.py"),
                            версия, "--repo", репа, "--out", str(куда),
                            "--changelog", str(чейнджлог)],
                           capture_output=True, text=True, encoding="utf-8")
        строки = [л.strip() for л in r.stdout.splitlines() if л.strip()]
        if r.returncode != 0 or not строки:
            raise RuntimeError(f"парсер описания не дал заголовка: {r.stderr.strip()[:200]}")
        return строки[-1]


def довести(архив: Path, сухой: bool) -> str:
    """Один архив → строка исхода. Бросает НетСвязи, если GitHub промолчал."""
    m = РАЗБОР.match(архив.name)
    if not m:
        return f"🟡 {архив.name}: имя не по канону `43` — вердикт не выносится"
    репа, версия = m.group("репа"), m.group("версия")

    ид = ассет(репа, версия, архив.name)
    if ид:
        if сухой:
            return f"   {архив.name}: ассет есть — сверить sha256 и убрать"
        if сверить_и_убрать(репа, версия, архив, ид):
            return f"🟢 {архив.name}: sha256 сошёлся — архив удалён"
        return (f"🔴 {архив.name}: sha256 РАЗОШЁЛСЯ с ассетом — архив оставлен, "
                f"выпуск не соответствует диску")

    if not тег_есть(репа, версия):
        return (f"🟡 {архив.name}: тега нет — это работа `github_sync.py --archive`, "
                f"здесь не трогаю")

    if релиз_есть(репа, версия):
        return (f"🔴 {архив.name}: релиз есть, а ассета с этим именем в нём нет — "
                f"догрузить вручную, состояние нетипичное")

    if сухой:
        return f"   {архив.name}: тег есть, релиза нет — создать релиз с этим архивом"

    with tempfile.TemporaryDirectory() as tmp:
        заметки = Path(tmp) / "notes.md"
        заголовок = описание(архив, репа, версия, заметки)
        код, вывод, ошибка = gh("release", "create", f"v{версия}", str(архив),
                                "--repo", f"{OWNER}/{репа}", "--title", заголовок,
                                "--notes-file", str(заметки))
        if код != 0:
            raise НетСвязи(f"релиз не создан: {(ошибка or вывод)[:200]}")
    ид = ассет(репа, версия, архив.name)
    if not ид:
        return f"🔴 {архив.name}: релиз создан, ассет не виден — архив оставлен"
    if сверить_и_убрать(репа, версия, архив, ид):
        return f"🟢 {архив.name}: релиз создан, sha256 сошёлся — архив удалён"
    return f"🔴 {архив.name}: релиз создан, но sha256 разошёлся — архив оставлен"


def selftest() -> int:
    assert РАЗБОР.match("repo-v1.2.3.zip").group("версия") == "1.2.3"
    assert РАЗБОР.match("a-b-c-v10.0.1.zip").group("репа") == "a-b-c"
    assert not РАЗБОР.match("repo-v1.5.0.stale.zip")
    assert нет_такого('gh: Not Found (HTTP 404)')
    assert not нет_такого("net/http: TLS handshake timeout")
    print("🟢 selftest: имя разбирается, переименованный архив отсеивается, "
          "404 («такого нет») отличается от таймаута («не знаю»)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--папка", type=Path, default=Path.home() / "Developer")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.папка.is_dir():
        print(f"папки {a.папка} нет — доводить нечего")
        return 0

    зипы = sorted(a.папка.glob("*.zip"))
    if not зипы:
        print(f"🟢 {a.папка} пуста — конечное состояние ритуала достигнуто")
        return 0

    убрано, осталось, оборвалось = 0, [], False
    for архив in зипы:
        try:
            строка = довести(архив, a.dry)
        except НетСвязи as e:
            print(f"🔴 ОСТАНОВЛЕНО на {архив.name}: GitHub не ответил — "
                  f"состояние неизвестно, гадать нельзя.\n   {e}")
            оборвалось = True
            break
        except Exception as e:  # noqa: BLE001 — один архив не роняет проход
            строка = f"🔴 {архив.name}: {e}"
        print(строка)
        if строка.startswith("🟢"):
            убрано += 1
        else:
            осталось.append(архив.name)

    остаток = len(list(a.папка.glob("*.zip")))
    print(f"\nубрано: {убрано} · в папке осталось: {остаток}")
    if остаток:
        print("🔴 конечное состояние НЕ достигнуто — папка не пуста")
    return 1 if остаток or оборвалось else 0


if __name__ == "__main__":
    sys.exit(main())
