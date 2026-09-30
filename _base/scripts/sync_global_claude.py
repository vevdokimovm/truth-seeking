#!/usr/bin/env python3
"""sync_global_claude.py — канон `.claude/{skills,agents,hooks}` живёт в base-repo
(git, история, диффы), но Claude Code видит `~/.claude/skills|agents/` и хуки из
`~/.claude/settings.json` ВСЕГДА и в ЛЮБОЙ репе, а `<репа>/.claude/...` — только
пока работаешь внутри этой репы (замер владельца, `97-claude-code-capabilities.md`
§6: «из 62 реп скиллы видны в 2» — раздача легла в `_base/`, на уровень ниже
видимого Claude Code пути).

🔴 ЗАКАЗ ВЛАДЕЛЬЦА 30.09.2026, дословно: «надо чтобы это всё было в одном месте
и один файл для ВСЕЙ СИСТЕМЫ, точно так же как мы делали со скилами агентами...
восстанови все хуки механизмы и тд для системы». Повод — 33 файла `.claude/`
физически пропали с диска (не через git) в этой же сессии; локальная копия
внутри одной репы не давала ни системного охвата, ни устойчивости к такой потере.

ЧТО ДЕЛАЕТ.
  1. Копирует `.claude/skills/` и `.claude/agents/` из base-repo в `~/.claude/`
     (перезаписывает — канон только один, глобальная копия одноразовая).
  2. Копирует `.claude/hooks/*.sh` в `~/.claude/hooks/`, сохраняя `+x`.
  3. Дописывает недостающие регистрации хуков в `~/.claude/settings.json` →
     `hooks` (PreToolUse/Stop/SessionStart) — идемпотентно, по совпадению
     команды: уже стоящая регистрация не дублируется.

ЧЕГО НЕ ДЕЛАЕТ. Не трогает project-local `.claude/settings.json` самой
base-repo — это отдельный ритуал (см. TODO в CHANGELOG при первом прогоне).
Не удаляет из `~/.claude/skills|agents/` то, чего больше нет в base-repo
(namespace `~/.claude/skills/` общий с плагинами Anthropic и чужими скиллами —
слепое удаление задело бы их).

ЗАПУСК
    sync_global_claude.py            синк + отчёт
    sync_global_claude.py --check    только сверка, код возврата ненулевой при расхождении
"""
from __future__ import annotations

import argparse
import filecmp
import json
import shutil
import stat
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOT_CLAUDE = REPO_ROOT / ".claude"
GLOBAL = Path.home() / ".claude"

HOOK_REGISTRATIONS = [
    ("PreToolUse", "Bash|Read|Glob|Grep|Edit|Write|MultiEdit|NotebookEdit",
     f'"{GLOBAL}/hooks/quarantine-guard.sh"', 10),
    ("PreToolUse", "Edit|Write|MultiEdit",
     f'"{GLOBAL}/hooks/protect-base-mirror.sh"', 10),
    ("Stop", None, f'"{GLOBAL}/hooks/ritual-gate.sh"', 60),
    ("Stop", None, f'"{GLOBAL}/hooks/task-hygiene.sh"', 15),
    ("SessionStart", None, f'"{GLOBAL}/hooks/watch-identity.sh"', 10),
    ("SessionStart", None, f'"{GLOBAL}/hooks/system-health.sh"', 60),
]

# 🔴 СКРИПТЫ НЕ КОПИРУЮТСЯ — на них ставится ССЫЛКА (`ARCH-001`, заказ владельца
# 29.09.2026: «все скрпитпы гейты механизмы скилы генты должны быть ГЛОБАЛЬНЫ»).
#
# Скиллы, агентов и хуки приходится класть в `~/.claude/` копией: Claude Code
# читает именно эти пути, иначе он их не видит. Скриптам этого не нужно —
# их зовут по пути, и копия принесла бы ровно ту болезнь, из-за которой всё
# и затевалось: вторая правда, расходящаяся с git молча. Ссылка всегда
# указывает на канон и не может отстать.
SCRIPTS_LINK = GLOBAL / "system"


def связать_скрипты(check_only: bool) -> str | None:
    """`~/.claude/system` → `base-repo/scripts`. Возвращает описание правки или None."""
    цель = REPO_ROOT / "scripts"
    if SCRIPTS_LINK.is_symlink() and SCRIPTS_LINK.resolve() == цель.resolve():
        return None
    if SCRIPTS_LINK.exists() and not SCRIPTS_LINK.is_symlink():
        return (f"🔴 {SCRIPTS_LINK} существует и НЕ является ссылкой — "
                f"не трогаю, разберись руками")
    if check_only:
        return f"нужно создать ссылку {SCRIPTS_LINK} → {цель}"
    if SCRIPTS_LINK.is_symlink():
        SCRIPTS_LINK.unlink()
    SCRIPTS_LINK.symlink_to(цель, target_is_directory=True)
    return f"ссылка создана: {SCRIPTS_LINK} → {цель}"


def синк_каталог(src: Path, dst: Path, dry: bool = False) -> list[str]:
    """Зеркалит src → dst (перезапись файлов, каталоги — по мере встречи).

    `dry=True` — только считает расхождение, ничего не пишет (для `--check`).
    """
    changed = []
    if not src.is_dir():
        return changed
    if not dry:
        dst.mkdir(parents=True, exist_ok=True)
    for item in src.rglob("*"):
        rel = item.relative_to(src)
        target = dst / rel
        if item.is_dir():
            if not dry:
                target.mkdir(parents=True, exist_ok=True)
            continue
        if not target.exists() or not filecmp.cmp(item, target, shallow=False):
            changed.append(str(rel))
            if not dry:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, target)
        if not dry and item.suffix == ".sh":
            target.chmod(target.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return changed


def обновить_settings(check_only: bool) -> list[str]:
    """Дописывает недостающие хук-регистрации в ~/.claude/settings.json."""
    settings_path = GLOBAL / "settings.json"
    data = json.loads(settings_path.read_text()) if settings_path.exists() else {}
    hooks = data.setdefault("hooks", {})
    added = []

    for event, matcher, command, timeout in HOOK_REGISTRATIONS:
        entries = hooks.setdefault(event, [])
        already = any(
            h.get("command") == command
            for block in entries
            for h in block.get("hooks", [])
        )
        if already:
            continue
        added.append(f"{event}: {command}")
        if check_only:
            continue
        block = {"hooks": [{"type": "command", "command": command, "timeout": timeout}]}
        if matcher:
            block = {"matcher": matcher, **block}
        entries.append(block)

    if added and not check_only:
        settings_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    return added


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--check", action="store_true")
    args = p.parse_args()

    print(f"Канон: {DOT_CLAUDE}")
    print(f"Цель:  {GLOBAL}\n")

    changed_skills = синк_каталог(DOT_CLAUDE / "skills", GLOBAL / "skills") if not args.check else []
    changed_agents = синк_каталог(DOT_CLAUDE / "agents", GLOBAL / "agents") if not args.check else []
    changed_hooks = синк_каталог(DOT_CLAUDE / "hooks", GLOBAL / "hooks") if not args.check else []
    added_registrations = обновить_settings(args.check)
    ссылка = связать_скрипты(args.check)

    print(f"skills/: {len(changed_skills)} файлов обновлено")
    print(f"agents/: {len(changed_agents)} файлов обновлено")
    print(f"hooks/:  {len(changed_hooks)} файлов обновлено")
    print(f"scripts: {ссылка or 'ссылка ~/.claude/system на месте'}")
    if added_registrations:
        print(f"settings.json: {'нужно дописать' if args.check else 'дописано'}:")
        for line in added_registrations:
            print(f"  · {line}")
    else:
        print("settings.json: все регистрации хуков уже на месте")

    if args.check:
        drift = bool(changed_skills or changed_agents or changed_hooks
                     or added_registrations or ссылка)
        return 1 if drift else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
