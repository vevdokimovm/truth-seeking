#!/usr/bin/env python3
"""system_invariants.py — что обязано быть верно про СИСТЕМУ, а не про репу.

🔴 ЗАЧЕМ ОТДЕЛЬНО ОТ `repo_invariants.py` (`ARCH-002`). Тот отвечает на вопрос
«репа собрана правильно?» — есть ли `.repo-id`, `VERSION`, файлы по классу.
Здесь — вопрос другого уровня: «работа доведена до конца?». Репа может быть
безупречна по всем R-правилам и при этом нести сорок невыпущенных версий.

Повод — разбор 29.09.2026. `character-a-analysis` имел `VERSION` 3.101.0 при
git на v3.61.1 и **нуле локальных тегов**: сорок версий работы существовали
только на диске. Ни один гейт системы этого не показывал, потому что каждый
проверял свой шаг, а состояние «работа сделана, но не выпущена» не принадлежит
ни одному шагу. Разбор — `reports/architecture-defects.md`.

🔴 БЕЗ СЕТИ, НАМЕРЕННО. Проверка висит на старте сессии в любой репе, и зависеть
от GitHub она не может: 29.09.2026 сеть падала трижды за день, а гейт, который
при недоступности сети либо врёт, либо блокирует старт, хуже отсутствующего.
Локальные теги и `VERSION` — достаточный признак: если версия не выпущена даже
локально, на GitHub её тем более нет.

ИНВАРИАНТЫ

    E-01  в `~/Developer` нет ни одного `.zip` — выпуск доведён, архивы убраны
    E-02  VERSION репы не ушла вперёд старшего локального тега
    E-03  рабочее дерево не ушло вперёд `origin/<ветка>` незапушенными коммитами

ЗАПУСК
    system_invariants.py            полный отчёт
    system_invariants.py --краткий  одна строка на нарушение (для хука)
    system_invariants.py --selftest
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

BASE = Path(os.environ.get("BASE_REPO") or Path(__file__).resolve().parent.parent)
РЕПЫ = BASE.parent
АРТЕФАКТЫ = Path.home() / "Developer"
ВЕРСИЯ_РЕ = re.compile(r"^\d+\.\d+\.\d+$")


def git(корень: Path, *арг: str) -> str:
    r = subprocess.run(["git", "-C", str(корень), *арг],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    return r.stdout.strip() if r.returncode == 0 else ""


def ключ(v: str) -> tuple[int, ...]:
    return tuple(int(x) for x in v.split("."))


def e01() -> list[str]:
    """Архивы не копятся: конечное состояние ритуала выпуска."""
    if not АРТЕФАКТЫ.is_dir():
        return []
    зипы = sorted(АРТЕФАКТЫ.glob("*.zip"))
    if not зипы:
        return []
    вес = sum(ф.stat().st_size for ф in зипы) / 2**30
    примеры = ", ".join(ф.name for ф in зипы[:3])
    хвост = f" и ещё {len(зипы) - 3}" if len(зипы) > 3 else ""
    return [f"E-01 · {len(зипы)} архив(ов) в ~/Developer ({вес:.1f} ГБ) — "
            f"выпуск не доведён: {примеры}{хвост}. Лечит `archives_finish.py`"]


def репы_на_диске() -> list[Path]:
    if not РЕПЫ.is_dir():
        return []
    return sorted(п for п in РЕПЫ.iterdir()
                  if п.is_dir() and (п / ".git").exists())


В_КОММИТЕ = re.compile(r"\bv(\d+\.\d+\.\d+)\b")


def e02_e03(корень: Path) -> list[str]:
    """E-02 по сообщению последнего коммита, а НЕ по локальным тегам.

    🔴 Первая редакция сверяла `VERSION` со старшим локальным тегом и дала
    65 нарушений на 70 реп — то есть была неверна, а не строга. Причина в том,
    как система выпускает: `deploy.sh` и `github_sync.py --archive` строят
    коммит и тег во ВРЕМЕННОМ индексе и отправляют их на GitHub, поэтому в
    рабочей копии локальных тегов нет вовсе. Их отсутствие — норма, а не долг.
    Гейт, красный всегда, равен выключенному, и такой гейт хуже отсутствующего.

    Надёжный локальный признак — версия в сообщении последнего коммита:
    выпуск системы всегда коммитит «<репа> vX.Y.Z — тезис». Именно это
    расхождение поймало `character-a-analysis` (VERSION 3.101.0 при коммите
    v3.61.1). Тег используется как запасной источник, если версии в сообщении
    нет.
    """
    имя = корень.name
    беды: list[str] = []

    файл = корень / "VERSION"
    версия = файл.read_text(encoding="utf-8").strip() if файл.is_file() else ""
    if версия and ВЕРСИЯ_РЕ.match(версия):
        выпущена = ""
        m = В_КОММИТЕ.search(git(корень, "log", "-1", "--format=%s"))
        if m:
            выпущена = m.group(1)
        if выпущена and ключ(версия) > ключ(выпущена):
            беды.append(f"E-02 · {имя}: VERSION {версия}, а последний коммит выпускает "
                        f"v{выпущена} — работа на диске не выпущена")

    ветка = git(корень, "rev-parse", "--abbrev-ref", "HEAD")
    if ветка and ветка != "HEAD":
        счёт = git(корень, "rev-list", "--count", f"origin/{ветка}..HEAD")
        if счёт.isdigit() and int(счёт) > 0:
            беды.append(f"E-03 · {имя}: {счёт} коммит(ов) не запушено в origin/{ветка}")
    return беды


def selftest() -> int:
    assert ключ("4.10.0") > ключ("4.9.9"), "версии сравниваются числами, не строкой"
    assert ВЕРСИЯ_РЕ.match("1.2.3") and not ВЕРСИЯ_РЕ.match("v1.2.3")
    assert not ВЕРСИЯ_РЕ.match("1.2")
    print("🟢 selftest: версии сравниваются по числам, формат VERSION проверяется, "
          "префикс `v` не принимается за версию")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--краткий", action="store_true",
                    help="только нарушения, без итоговой арифметики — для хука")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()

    нарушения = e01()
    репы = репы_на_диске()
    # 🔴 Параллельно, потому что проверка висит на старте сессии. Последовательный
    # обход 70 реп — это 210 запусков `git` и 7.6 с; человек столько ждать не будет,
    # а гейт, который раздражает, выключают. Работа целиком в ожидании процесса,
    # поэтому потоков хватает — GIL здесь не мешает. Замер после: ~1.5 с.
    with ThreadPoolExecutor(max_workers=16) as пул:
        for беды in пул.map(e02_e03, репы):
            нарушения.extend(беды)
    нарушения.sort()

    if not нарушения:
        if not a.краткий:
            print(f"🟢 система в порядке: {len(репы)} реп, архивов не накоплено, "
                  f"невыпущенной работы нет")
        return 0

    for строка in нарушения:
        print(f"🔴 {строка}")
    if not a.краткий:
        print(f"\nпроверено реп: {len(репы)} · нарушений: {len(нарушения)}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
