#!/usr/bin/env python3
"""close_batch.py — ритуал закрытия батча одной командой.

ЗАДАЧА `ROADMAP.md` §P0 п.1: «оптимизация скорости без потери качества». Узкое место
измерено и названо там же: **не чтение, а закрытие батча** — ритуал стоит примерно
столько же, сколько проход по малой репе.

ИЗ ЧЕГО СКЛАДЫВАЛАСЬ ЦЕНА. Ритуал — десять шагов в пяти файлах, и каждый требовал
отдельного вызова:

    revision_check → VERSION → секция CHANGELOG → WATCHLOG §0 → WATCHLOG §3
    (+ подрезка до ровно 10) → readme_status_gate --fix → описание в README
    → pack_release → ScheduleWakeup

Замер этой сессии: **7 версий**, то есть ритуал исполнялся семь раз по 5–7 вызовов.

🔴 ЧТО ИМЕННО ОПТИМИЗИРУЕТСЯ — И ЧТО НЕТ. Механика раскладки одного текста по пяти
местам автоматизируется полностью. **Содержание не автоматизируется вовсе**: что
написать в CHANGELOG, какую строку дать журналу и витрине — суждение вахты. Скрипт
берёт готовый текст и разносит его; он не пишет его за вахту.

Это та же граница, что у `capture.py` (`20-knowledge-capture-protocol.md` §4.4):
машина снимает механику, вахта отвечает за суждение. Инструмент, который взялся бы
сочинять changelog, был бы хуже отсутствия инструмента (`71` §7г-бис).

ПОЧЕМУ ГЕЙТ ОСТАЁТСЯ ВНУТРИ, А НЕ РЯДОМ. «Без потери качества» в задаче — не пожелание:
`revision_check.py` запускается **первым**, и при DRIFT ритуал не начинается вовсе.
Иначе оптимизация свелась бы к пропуску проверки, что уже случалось (`PIT-116`:
инструмент существовал и работал, его просто никто не запускал).

ЗАПУСК:
    close_batch.py --minor --title "..." --body FILE --log "..." --readme "..."
    close_batch.py --version 2.58.0 --title "..." --body-stdin --log "..." --readme "..."
    close_batch.py --root ../mission-control --minor --title "..." ...

    --minor / --patch / --major   как поднять версию (по умолчанию --minor)
    --root ПУТЬ                   закрыть батч другой репы (по умолчанию — сама база)
    --no-pack                     не собирать архив
    --dry                         показать, что будет сделано

🔴 ОБОБЩЕНО НА `--root` 28.08.2026 (`PIT-153`). До этого скрипт умел закрывать
только `base-repo` — для остальных 57 реп тот же десятишаговый ритуал делался
вручную, и это стоило дважды не замеченного дрейфа (README STATUS не обновлялся
10 батчей подряд, `WATCHLOG` §0 дорастал обратно за потолок). Инструменты
(`revision_check.py`, `readme_status_gate.py`, `pack_release.py`) всегда
вызываются из `base-repo/scripts/` (`BASE_SCRIPTS`, self-locating) — REPO это
только целевая репа, чьи файлы правятся. Формат `WATCHLOG.md` §0/§3 у разных
реп слегка расходится (есть репы без маркера-дефиса перед «Версия:», с другим
заголовком §3) — оба паттерна ниже терпимы к обоим вариантам, а не только
к тому, что исторически сложился в `base-repo`.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

BASE_SCRIPTS = Path(__file__).resolve().parent
REPO = BASE_SCRIPTS.parent  # переопределяется в main() по --root
TODAY = date.today().isoformat()


def run(*cmd: str) -> tuple[int, str]:
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=BASE_SCRIPTS.parent)
    return r.returncode, (r.stdout + r.stderr)


def base_script(name: str) -> str:
    return str(BASE_SCRIPTS / name)


def bump(v: str, kind: str) -> str:
    a, b, c = (v.strip().split(".") + ["0", "0", "0"])[:3]
    if kind == "major":
        return f"{int(a)+1}.0.0"
    if kind == "patch":
        return f"{a}.{b}.{int(c)+1}"
    return f"{a}.{int(b)+1}.0"


def write_changelog(version: str, title: str, body: str, kind: str, dry: bool) -> None:
    """Секция вставляется сразу после заголовка `# CHANGELOG...` файла.

    Заголовок не сверяется дословно (`PIT-153`) — у разных реп разный текст
    («история инфраструктуры» у базы, `mission-control`` у планировщика и т.д.),
    жёсткая строка работала только для базы. Ищется первая строка `# ` и первая
    пустая строка после неё — секция вставляется сразу за ней.
    """
    p = REPO / "CHANGELOG.md"
    tag = {"major": "MAJOR", "patch": "PATCH"}.get(kind, "MINOR")
    section = f"## [{version}] — {TODAY} — {title} ({tag})\n\n{body.rstrip()}\n\n"
    t = p.read_text(encoding="utf-8")
    if dry:
        print(f"  [dry] CHANGELOG += секция [{version}] ({len(body)} знаков)")
        return
    lines = t.split("\n")
    if not lines or not lines[0].startswith("# "):
        sys.exit("🔴 CHANGELOG.md: первая строка не начинается с «# » — формат не распознан")
    insert_at = 1
    while insert_at < len(lines) and lines[insert_at].strip() == "":
        insert_at += 1
    new_lines = lines[:insert_at] + [""] + section.rstrip("\n").split("\n") + lines[insert_at:]
    p.write_text("\n".join(new_lines), encoding="utf-8")


def write_watchlog(version: str, log_line: str, dry: bool) -> None:
    """§0 — текущая точка; §3 — запись сверху и подрезка до РОВНО десяти.

    Подрезка обязательна: правило «§3 хранит ровно 10» не исполнялось 32 версии
    подряд, потому что опиралось на ручную дисциплину (`WATCHLOG` шапка).
    """
    p = REPO / "WATCHLOG.md"
    t = p.read_text(encoding="utf-8")
    # 🔴 PIT-148: deploy.sh/bump_repo.py читают строго `**Версия:**`, а строка §0
    # ходовой формы — «- **Версия:** X.Y.Z · **Дата:** ГГГГ-ММ-ДД · **Вахта:** N
    # (текущая точка: vX.Y.Z)». Прежний паттерн искал отдельную строку
    # `- **Текущая точка: v...**`, которой в этом формате нет — правка молча
    # не находила совпадения, и §0 отставал от VERSION (тот же класс дефекта,
    # что PIT-148 уже чинил один раз в другом месте).
    # 🔴 PIT-153: не у всех реп строка §0 начинается с «- » (mission-control,
    # например, не ставит маркер списка) — префикс необязателен, а не жёстко
    # «- ». Раньше нулевая раздача сюда молча роняла всю функцию для этих реп.
    line_re = re.compile(
        r"(- )?\*\*Версия:\*\* [\d.]+ · \*\*Дата:\*\* \d{4}-\d{2}-\d{2} · "
        r"\*\*Вахта:\*\* (\S+)([^\n]*)"
    )
    m = line_re.search(t)
    if m:
        prefix, vahta, rest = m.group(1) or "", m.group(2), m.group(3)
        rest = re.sub(r"текущая точка: v[\d.]+", f"текущая точка: v{version}", rest)
        new_line = (f"{prefix}**Версия:** {version} · **Дата:** {date.today().isoformat()} "
                    f"· **Вахта:** {vahta}{rest}")
        t = t[:m.start()] + new_line + t[m.end():]
    else:
        print("  ! строка §0 «Где стоим» не найдена по канону — версия там не обновлена",
              file=sys.stderr)
    # 🔴 PIT-153: §3 не у всех реп — маркированный список («- **ДАТА** — vX: …»),
    # как у базы. У `mission-control`, например, это markdown-таблица
    # («| Версия | Дата | Вахта | Что сделано |»). Форсировать один алгоритм на
    # оба формата рискованно — вместо этого функция распознаёт формат и либо
    # правит список сама (как раньше), либо честно пропускает таблицу и просит
    # вахту дописать строку руками, а не молча портит структуру.
    anchor_m = re.search(r"^## §3\.[^\n]*\n", t, re.MULTILINE)
    if not anchor_m:
        print("  ! §3 не найден — журнал не тронут", file=sys.stderr)
        return
    after_anchor = t[anchor_m.end():].lstrip("\n")
    if after_anchor.lstrip().startswith("|"):
        print(f"  ! §3 — таблица, не список: допиши строку `{version}` в неё вручную "
              f"(лог: «{log_line.strip()}»)", file=sys.stderr)
        if dry:
            print(f"  [dry] WATCHLOG §0 → v{version}; §3 — таблица, не тронута")
        else:
            p.write_text(t, encoding="utf-8")
        return
    anchor = anchor_m.group(0)
    entry = f"- **{TODAY}** — v{version}: {log_line.strip()}\n\n"
    head, tail = t[:anchor_m.end()], t[anchor_m.end():]
    t = head + entry + tail.lstrip("\n")
    s = t.index(entry)
    e_m = re.search(r"\n## §\d+\.", t[s:])
    e = s + e_m.start() if e_m else len(t)
    items = re.split(r"\n(?=- \*\*20)", t[s:e].strip("\n"))
    dropped = max(0, len(items) - 10)
    t = t[:s] + "\n".join(items[:10]) + "\n" + t[e:]
    if dry:
        print(f"  [dry] WATCHLOG §0 → v{version}; §3 += запись, подрезано {dropped}")
        return
    p.write_text(t, encoding="utf-8")
    if dropped:
        print(f"  · §3 подрезан: убрано {dropped} (уходит в CHANGELOG, не в git)")


def write_readme(version: str, line: str, dry: bool) -> None:
    # 🔴 В сухом прогоне НЕ звать `--fix`: он пишет в README на самом деле.
    # В первой редакции спасло лишь то, что VERSION в dry не поднимается и гейт
    # не находил расхождения — то есть безопасность держалась на случайности,
    # а не на устройстве. `--dry` обязан не менять ничего по построению.
    if dry:
        print("  [dry] README: статус и описание были бы проставлены")
        return
    code, out = run(sys.executable, base_script("readme_status_gate.py"), "--root", str(REPO), "--fix")
    p = REPO / "README.md"
    t = p.read_text(encoding="utf-8")
    pat = re.compile(rf"(> \*\*Сейчас:\*\* `v{re.escape(version)}` · {TODAY} · )[^\n]*")
    if not pat.search(t):
        print("  ! блок статуса README не найден — описание не проставлено", file=sys.stderr)
        return
    if dry:
        print("  [dry] README: описание статуса заменено")
        return
    p.write_text(pat.sub(lambda m: m.group(1) + line.strip(), t, count=1), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--title", required=True, help="заголовок секции CHANGELOG")
    ap.add_argument("--body", help="файл с телом секции")
    ap.add_argument("--body-stdin", action="store_true")
    ap.add_argument("--log", required=True, help="строка для WATCHLOG §3")
    ap.add_argument("--readme", required=True, help="описание для блока статуса README")
    ap.add_argument("--version", help="явная версия; иначе поднимается сама")
    ap.add_argument("--root", help="путь к репе, чей батч закрывается (по умолчанию — база)")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--minor", action="store_true")
    g.add_argument("--patch", action="store_true")
    g.add_argument("--major", action="store_true")
    ap.add_argument("--no-pack", action="store_true")
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()

    global REPO
    if a.root:
        REPO = Path(a.root).expanduser().resolve()
        if not REPO.is_dir():
            sys.exit(f"🔴 --root {REPO}: не каталог")

    # 🔴 Защита от подстановки shell. `--log "…\`health-vault\`…"` в zsh превращается
    # в подстановку команды: обратные кавычки съедаются вместе с содержимым, и в журнал
    # уходит «ревизия :» вместо «ревизия `health-vault`». Поймано 22.08.2026 на v2.61.0.
    # Проверка здесь, а не в памяти вахты: строка приходит уже испорченной, и заметить
    # это можно только по следу — пустой паре разделителей.
    for name, val in (("--log", a.log), ("--readme", a.readme)):
        if "**:" in val.replace(" ", "") or "` `" in val or "**  " in val:
            print(f"  ! {name}: похоже на съеденную shell-подстановку — проверь обратные кавычки",
                  file=sys.stderr)
        if val.count("`") % 2:
            sys.exit(f"🔴 {name}: непарная обратная кавычка — строка испорчена shell. "
                     f"Передавай через файл или экранируй.")

    body = sys.stdin.read() if a.body_stdin else (
        Path(a.body).read_text(encoding="utf-8") if a.body else "")
    if not body.strip():
        sys.exit("пустое тело секции — нечего записывать в CHANGELOG")

    # 🔴 ПРОВЕРКА РАЗМЕРА БАТЧА (`PIT-128`). За сессию 22.08.2026 база прошла 12 версий,
    # и владелец увидел в загрузках стену одинаковых архивов: «ты делаешь версии как
    # будто это новые репы». Содержательных изменений было втрое меньше — версией
    # закрывался удобный момент остановки, а не законченная работа.
    #
    # Цена невидима изнутри: каждый отдельный ритуал дёшев, дорога их сумма.
    # Поэтому предупреждение здесь, где решение принимается, а не в документе.
    if len(body.strip()) < 400:
        print("  ! тело секции короче 400 знаков — возможно, батч закрывается рано.")
        print("    Правило PIT-128: версия закрывает ЗАКОНЧЕННУЮ работу. Если секцию")
        print("    нельзя назвать одним предложением без союза «и» — работа не одна,")
        print("    а если она умещается в пару строк — она, вероятно, ещё не закончена.")

    # 🔴 ГЕЙТ ПЕРВЫМ. Оптимизация не имеет права начинаться с пропуска проверки.
    print("── гейт до начала ритуала")
    code, out = run(sys.executable, base_script("revision_check.py"), "--root", str(REPO))
    if code != 0:
        print(out[-1500:])
        sys.exit("🔴 гейт DRIFT — батч не закрывается. Сначала починить.")
    print("  · CLEAN")

    kind = "major" if a.major else "patch" if a.patch else "minor"
    cur = (REPO / "VERSION").read_text().strip()
    new = a.version or bump(cur, kind)
    print(f"── версия {cur} → {new}")

    write_changelog(new, a.title, body, kind, a.dry)
    if not a.dry:
        (REPO / "VERSION").write_text(new + "\n", encoding="utf-8")
    write_watchlog(new, a.log, a.dry)
    write_readme(new, a.readme, a.dry)

    print("── гейт после правок")
    code, out = run(sys.executable, base_script("revision_check.py"), "--root", str(REPO))
    print("  · " + ("CLEAN" if code == 0 else "🔴 DRIFT:\n" + out[-1200:]))
    if code != 0:
        sys.exit("ритуал оставил репу в DRIFT — разобрать до сборки архива")

    if not a.no_pack and not a.dry:
        code, out = run(sys.executable, base_script("pack_release.py"), str(REPO))
        print("── " + (out.strip().splitlines() or ["архив не собран"])[0])

    # 🔴 Напоминание о раздаче — по ПОРОГУ, а не после каждого батча.
    # Замер 22–23.08.2026: база прошла 23 версии за сессию, раздача делалась трижды
    # вручную и каждый раз по случайному поводу. Порог 5 минорных взят из
    # `ADR-004` §5 правило 1: раздача повторяется раз в несколько батчей, иначе
    # либо зеркала отстают, либо ритуал дорожает вдвое.
    try:
        repos = REPO.parent
        cn = int(new.split(".")[1])
        lag = 0
        for d in repos.iterdir():
            f = d / "_base" / "BASE_VERSION"
            if d.is_dir() and f.is_file():
                v = f.read_text(encoding="utf-8").strip().split(".")
                if len(v) > 1 and v[0] == new.split(".")[0] and cn - int(v[1]) > 5:
                    lag += 1
        if lag:
            print(f"\n  🔴 зеркал отстало больше чем на 5 минорных: {lag}")
            print(f"     Раздать:  LOCAL=1 bash {REPO.parent}/"
                  "mission-control/scripts/sync-base.sh")
    except Exception:
        pass

    print(f"\n✅ батч v{new} закрыт. Дальше — ScheduleWakeup, а не отчёт (скилла auto §2б).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
