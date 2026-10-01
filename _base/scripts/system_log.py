#!/usr/bin/env python3
"""system_log.py — единый журнал ВСЕЙ системы: кто, откуда, когда, зачем.

🔴 ЗАКАЗ ВЛАДЕЛЬЦА 30.09.2026, дословно: «вот именно поэтому я говорил внести
логи ВСЕЙ СИСТЕМЫ когда другая репа вносит изменения патчноуты в базу сама».

ПОВОД — ЖИВОЙ СЛУЧАЙ ТОГО ЖЕ ДНЯ. В базе параллельно работали три сессии.
Вахта, закрывавшая батч, обнаружила чужие незакоммиченные правки в
`07-media-to-text-lab` **только заглянув в `git status` глазами** — и лишь
поэтому не подписала чужой черновик своим релизом. Никакого механизма,
который сказал бы «в системе есть ещё одна рука», не существовало.

🔴 ЧЕМ ЭТО НЕ ЯВЛЯЕТСЯ — направление противоположное, и это главное:

    patch_notes.py   СВЕРХУ ВНИЗ: база объявляет обновления, наследники
                     читают и отмечаются `.infra-updates-read`
    system_log.py    СНИЗУ ВВЕРХ: каждая репа сама оставляет запись в базе —
                     кто изменил, где, когда, зачем

Оба нужны. Первый доставляет правила от родителя к детям; второй возвращает
факты от детей к родителю. Без второго родитель не знает, что происходит
в системе, которой он управляет.

РЕЖИМЫ
    --live              🔴 кто трогает систему ПРЯМО СЕЙЧАС: грязные деревья,
                        живые сессии, давность последней правки
    --scan [--days N]   добрать в журнал коммиты всех реп за N дней (по умолчанию 7)
    --record <репа>     одна запись по последнему коммиту репы (зовёт git-хук)
    --show [--days N]   показать журнал
    --install-hooks     поставить post-commit во все репы системы
    --selftest

🔴 ЧЕГО ЖУРНАЛ НЕ ВИДИТ
  · НЕЗАКОММИЧЕННОЕ прошлое: пока правка не в коммите, её «зачем» не записано
    нигде, и `--scan` её не увидит. Ровно этот зазор и породил случай 30.09 —
    закрывает его только `--live`, и то лишь на время, пока правка жива;
  · ПРИЧИНУ правки сверх заголовка коммита: если заголовок пустой по смыслу
    («fix»), журнал честно сохранит пустоту;
  · чьи руки: сессию git не знает. Автор коммита один на всю систему —
    владелец, поэтому различать вахты по автору нельзя.
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import subprocess
import sys
import time
from pathlib import Path

БАЗА = Path(__file__).resolve().parent.parent
РЕПЫ = БАЗА.parent
ЖУРНАЛ = БАЗА / "reports" / "system-log.tsv"
ПОЛЯ = ("время", "репа", "коммит", "ветка", "файлов", "добавлено", "удалено",
        "версия", "заголовок")
ХУК = """#!/bin/sh
# Единый журнал системы (base-repo/scripts/system_log.py). Никогда не роняет
# коммит: журнал — след, а не предусловие (71 §7ж).
python3 "%s/scripts/system_log.py" --record "$(basename "$(git rev-parse --show-toplevel)")" >/dev/null 2>&1 || true
"""


def гит(репа: Path, *арг: str) -> str:
    try:
        r = subprocess.run(["git", "-C", str(репа), *арг],
                           capture_output=True, text=True, timeout=30)
        return r.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def репы_системы() -> list[Path]:
    """Репы системы: каталог с `.git`. Знаменатель печатается всегда."""
    из = [д for д in sorted(РЕПЫ.iterdir())
          if д.is_dir() and (д / ".git").exists()]
    return из


def прочитать() -> list[dict[str, str]]:
    if not ЖУРНАЛ.is_file():
        return []
    строки = [с for с in ЖУРНАЛ.read_text(encoding="utf-8").splitlines() if с.strip()]
    if not строки:
        return []
    шапка = строки[0].split("\t")
    return [dict(zip(шапка, с.split("\t"))) for с in строки[1:]]


def дописать(записи: list[dict[str, str]]) -> int:
    """Append-only, без дублей по (репа, коммит). Возвращает число новых строк."""
    если_есть = {(з.get("репа"), з.get("коммит")) for з in прочитать()}
    новые = [з for з in записи if (з["репа"], з["коммит"]) not in если_есть]
    if not новые:
        return 0
    ЖУРНАЛ.parent.mkdir(parents=True, exist_ok=True)
    первый = not ЖУРНАЛ.is_file()
    with ЖУРНАЛ.open("a", encoding="utf-8") as ф:
        if первый:
            ф.write("\t".join(ПОЛЯ) + "\n")
        for з in sorted(новые, key=lambda з: з["время"]):
            ф.write("\t".join(з.get(п, "").replace("\t", " ") for п in ПОЛЯ) + "\n")
    return len(новые)


def запись(репа: Path, коммит: str) -> dict[str, str]:
    """Одна строка журнала по коммиту. Пустая клетка = не узнали, не ноль."""
    формат = гит(репа, "show", "-s", "--format=%cI%n%s", коммит)
    части = формат.splitlines()
    статистика = гит(репа, "show", "--numstat", "--format=", коммит).splitlines()
    файлов = добавлено = удалено = 0
    for с in статистика:
        к = с.split("\t")
        if len(к) == 3:
            файлов += 1
            добавлено += int(к[0]) if к[0].isdigit() else 0
            удалено += int(к[1]) if к[1].isdigit() else 0
    версия = ""
    ф = репа / "VERSION"
    if ф.is_file():
        версия = ф.read_text(encoding="utf-8").strip()
    return {
        "время": части[0] if части else "",
        "репа": репа.name,
        "коммит": коммит[:7],
        "ветка": гит(репа, "rev-parse", "--abbrev-ref", "HEAD"),
        "файлов": str(файлов),
        "добавлено": str(добавлено),
        "удалено": str(удалено),
        "версия": версия,
        "заголовок": части[1] if len(части) > 1 else "",
    }


def живое() -> int:
    """🔴 Кто трогает систему прямо сейчас — то, чего не хватило 30.09.2026."""
    код = subprocess.run(["pgrep", "-f", "claude --resume"],
                         capture_output=True, text=True)
    сессий = len([с for с in код.stdout.splitlines() if с.strip()])
    print(f"живых сессий: {сессий}" + (
        "  🟠 больше одной — `git add -A` в любом выпуске сгребёт чужое"
        if сессий > 1 else ""))

    все = репы_системы()
    грязных = 0
    тихие: list[tuple[str, int]] = []
    for репа in все:
        вывод = гит(репа, "status", "--porcelain")
        все_файлы = [с[2:].strip() for с in вывод.splitlines() if с.strip()]
        # 🔴 `_base/` ВЫНОСИТСЯ ИЗ СЧЁТА, И ЭТО НЕ КОСМЕТИКА. Раздача канона
        # переписывает зеркало правил в 57 наследниках, то есть после каждого
        # батча базы 57 реп становятся «грязными» по 500 файлов. Первый прогон
        # 30.09.2026 дал 59 реп из 70 — сигнал, кричащий на 59 репах, выключают
        # не разбираясь, и вместе с ним пропадёт единственный настоящий случай.
        # Механическая churn считается отдельно и не красит репу тревогой.
        файлы = [ф for ф in все_файлы if not ф.startswith("_base/")]
        зеркало = len(все_файлы) - len(файлы)
        if not файлы:
            if зеркало:
                тихие.append((репа.name, зеркало))
            continue
        грязных += 1
        свежесть = None
        for имя in файлы[:40]:
            п = репа / имя
            if п.is_file():
                возраст = (time.time() - п.stat().st_mtime) / 60
                свежесть = возраст if свежесть is None else min(свежесть, возраст)
        когда = f"{свежесть:.0f} мин назад" if свежесть is not None else "не определено"
        значок = "🔴" if свежесть is not None and свежесть < 15 else "🟡"
        неотправлено = гит(репа, "log", "--oneline", "@{u}..HEAD")
        хвост = f" · неотправленных коммитов: {len(неотправлено.splitlines())}" if неотправлено else ""
        зерк = f" · плюс зеркало правил: {зеркало}" if зеркало else ""
        print(f"{значок} {репа.name}: своей работы незакоммичено {len(файлы)} · "
              f"правка {когда}{хвост}{зерк}")

    print(f"\nреп на диске: {len(все)} · со своей незакоммиченной работой: {грязных} · "
          f"только зеркало правил после раздачи: {len(тихие)}")
    print("🔴 Свежая правка при живой второй сессии — не улика, а сигнал: "
          "в выпуск идти нельзя, пока не разобрано, чьё это.")
    return 0


def selftest() -> int:
    """Журнал обязан быть append-only и не плодить дублей по (репа, коммит)."""
    глобальный = ЖУРНАЛ
    try:
        import tempfile
        with tempfile.TemporaryDirectory() as д:
            globals()["ЖУРНАЛ"] = Path(д) / "log.tsv"
            з = {"время": "2026-09-30T10:00:00+02:00", "репа": "x", "коммит": "abc1234",
                 "ветка": "main", "файлов": "1", "добавлено": "2", "удалено": "0",
                 "версия": "1.0.0", "заголовок": "тест"}
            assert дописать([з]) == 1, "первая запись обязана лечь"
            assert дописать([з]) == 0, "дубль по (репа, коммит) обязан отсекаться"
            з2 = з | {"коммит": "def5678", "заголовок": "с\tтабуляцией"}
            assert дописать([з2]) == 1, "новый коммит обязан лечь"
            строки = прочитать()
            assert len(строки) == 2, f"строк обязано быть 2, стало {len(строки)}"
            assert "\t" not in строки[1]["заголовок"], "табуляция обязана вычищаться"
            assert строки[1]["заголовок"] == "с табуляцией"
    finally:
        globals()["ЖУРНАЛ"] = глобальный
    assert репы_системы(), "репы системы обязаны находиться"
    print("🟢 канарейка журнала: append-only держится, дубль по (репа, коммит) "
          "отсекается, табуляция в заголовке не рвёт колонки")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--scan", action="store_true")
    ap.add_argument("--record", metavar="РЕПА")
    ap.add_argument("--show", action="store_true")
    ap.add_argument("--install-hooks", action="store_true")
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    if a.selftest:
        return selftest()
    if a.live:
        return живое()

    if a.record:
        репа = РЕПЫ / a.record
        if not (репа / ".git").exists():
            return 0
        голова = гит(репа, "rev-parse", "HEAD")
        if голова:
            дописать([запись(репа, голова)])
        return 0

    if a.install_hooks:
        поставлено = 0
        for репа in репы_системы():
            каталог = Path(гит(репа, "rev-parse", "--git-path", "hooks") or "")
            цель = (репа / каталог) if not каталог.is_absolute() else каталог
            цель.mkdir(parents=True, exist_ok=True)
            ф = цель / "post-commit"
            если_есть = ф.read_text(encoding="utf-8") if ф.is_file() else ""
            if "system_log.py" in если_есть:
                continue
            ф.write_text((если_есть or "#!/bin/sh\n").rstrip("\n") + "\n"
                         + ХУК.split("\n", 1)[1] % БАЗА, encoding="utf-8")
            ф.chmod(0o755)
            поставлено += 1
        print(f"хуков поставлено: {поставлено} · реп всего: {len(репы_системы())}")
        return 0

    if a.scan:
        порог = (dt.datetime.now(dt.timezone.utc)
                 - dt.timedelta(days=a.days)).isoformat()
        собрано: list[dict[str, str]] = []
        for репа in репы_системы():
            for коммит in гит(репа, "log", f"--since={a.days}.days",
                              "--format=%H").splitlines():
                if коммит.strip():
                    собрано.append(запись(репа, коммит.strip()))
        новых = дописать(собрано)
        print(f"просмотрено реп: {len(репы_системы())} · коммитов за {a.days} дн.: "
              f"{len(собрано)} · новых строк в журнале: {новых} · порог: {порог[:10]}")

    записи = прочитать()
    if not записи:
        print("🟡 журнал пуст")
        return 0
    порог = (dt.date.today() - dt.timedelta(days=a.days)).isoformat()
    свежие = [з for з in записи if з.get("время", "")[:10] >= порог]
    print(f"\n── журнал системы: строк всего {len(записи)}, за {a.days} дн. {len(свежие)} ──")
    по_репам: dict[str, int] = {}
    for з in свежие:
        по_репам[з["репа"]] = по_репам.get(з["репа"], 0) + 1
    for репа, сколько in sorted(по_репам.items(), key=lambda п: -п[1]):
        print(f"  {сколько:3d}  {репа}")
    for з in свежие[-12:]:
        print(f"  {з['время'][:16]}  {з['репа'][:22]:22} {з['коммит']}  "
              f"файлов {з['файлов']:>3}  {з['заголовок'][:60]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
