#!/usr/bin/env python3
"""archives_check.py — архивы не копятся в `~/Developer`: выпущены и убраны.

🔴 ПРИКАЗ ВЛАДЕЛЬЦА 25.09.2026, дословно: «они должны выполнять работу деплой
скрипта и коммитить репы и удалять архивы затем».

ПОВОД. За сутки 23–24.09 в `~/Developer` скопилось **103 архива на 8.4 ГБ**
при 16 ГБ свободного места. Вахты собирали архив упаковщиком и не доводили
выпуск до конца: релиза нет, архив лежит. `deploy.sh` удалял опубликованный
архив по умолчанию с самого начала — а пути «изнутри вахты» этого не делали.

ЧТО ПРОВЕРЯЕТ. Для каждого архива в `~/Developer`:

    опубликован (тег + релиз + ассет сошёлся по имени) → 🔴 архив обязан быть удалён
    не опубликован, версия выше опубликованной        → 🟡 выпуск не доведён
    не опубликован, версия ниже опубликованной        → 🟡 промежуточный, решает владелец

🔴 ЧЕГО НЕ ЛОВИТ. Не сверяет sha256 ассета с архивом (это делают `publish.py`
и `github_sync.py` в момент удаления) — здесь только факт публикации, иначе
проверка читала бы гигабайты на каждом ходу. Не знает, идёт ли выпуск прямо
сейчас: архив, собранный минуту назад, выглядит как забытый.

ЗАПУСК
    archives_check.py            сводка + что делать с каждым
    archives_check.py --selftest
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

РАЗБОР = re.compile(r"^(?P<репа>.+)-v(?P<версия>\d+\.\d+\.\d+)\.zip$")
OWNER = "vevdokimovm"


def версия_ключ(v: str) -> tuple[int, ...]:
    return tuple(int(x) for x in v.split("."))


def релизы(репа: str) -> dict[str, set[str]]:
    """{версия: {имена ассетов}} по всем релизам репы; пусто, если gh недоступен."""
    r = subprocess.run(["gh", "api", "--paginate",
                        f"repos/{OWNER}/{репа}/releases?per_page=100",
                        "-q", '.[] | "\\(.tag_name)\\t\\([.assets[].name] | join(","))"'],
                       capture_output=True, text=True)
    из = {}
    for строка in r.stdout.splitlines():
        тег, _, ассеты = строка.partition("\t")
        из[тег.lstrip("v")] = {a for a in ассеты.split(",") if a}
    return из


def разобрать(папка: Path) -> list[tuple[str, str, Path]]:
    найдено = []
    for ф in sorted(папка.glob("*.zip")):
        m = РАЗБОР.match(ф.name)
        if m:
            найдено.append((m.group("репа"), m.group("версия"), ф))
    return найдено


def проверить(папка: Path) -> tuple[list[str], list[str]]:
    провалы: list[str] = []
    предупреждения: list[str] = []
    по_репам: dict[str, dict[str, set[str]]] = {}
    for репа, версия, ф in разобрать(папка):
        if репа not in по_репам:
            по_репам[репа] = релизы(репа)
        опубликованные = по_репам[репа]
        if ф.name in опубликованные.get(версия, set()):
            # 🔴 Совпало ИМЯ, а не содержимое: 25.09.2026 архив pfd v9.13.16 был
            # пересобран вахтой заново и отличался от ассета по sha256. Поэтому
            # здесь не «удали», а «сверь и убери» — сверку делают инструменты.
            провалы.append(f"{ф.name}: релиз с ассетом этого имени есть — архив пора убрать. "
                           f"Сверку sha256 и удаление делают publish.py / github_sync.py; "
                           f"если содержимое разошлось, они оставят архив и скажут об этом")
            continue
        старшая = max((версия_ключ(v) for v in опубликованные), default=(0, 0, 0))
        моя = версия_ключ(версия)
        if моя > старшая:
            что = "выпуск не доведён — релиза нет"
        elif моя == старшая:
            что = "релиз этой версии есть, но ассета с таким именем в нём нет — догрузить"
        else:
            что = (f"ниже опубликованной v{'.'.join(map(str, старшая))} — "
                   "промежуточный, решает владелец")
        предупреждения.append(f"{ф.name}: {что}")
    return провалы, предупреждения


def selftest() -> int:
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        (d / "repo-v1.2.3.zip").write_bytes(b"x")
        (d / "repo-v1.2.4.zip").write_bytes(b"x")
        (d / "мусор.zip").write_bytes(b"x")
        разобранные = разобрать(d)
        assert len(разобранные) == 2, разобранные
        assert разобранные[0][0] == "repo" and разобранные[0][1] == "1.2.3"
        assert версия_ключ("4.10.0") > версия_ключ("4.9.9")
    print("🟢 selftest: имя архива разбирается на репу и версию, посторонний zip "
          "игнорируется, версии сравниваются по числам, а не строкой")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--папка", type=Path, default=Path.home() / "Developer")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.папка.is_dir():
        print(f"папки {a.папка} нет — архивов не накоплено")
        return 0
    провалы, предупреждения = проверить(a.папка)
    for п in провалы:
        print(f"🔴 {п}")
    for п in предупреждения:
        print(f"🟡 {п}")
    всего = len(разобрать(a.папка))
    print(f"\nархивов в {a.папка}: {всего} · опубликованы и не убраны: {len(провалы)} "
          f"· выпуск не доведён или промежуточные: {len(предупреждения)}")
    return 1 if провалы else 0


if __name__ == "__main__":
    sys.exit(main())
