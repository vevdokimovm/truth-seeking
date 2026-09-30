#!/bin/bash
# PreToolUse (Bash|Read|Glob|Grep|Edit|Write|MultiEdit|NotebookEdit) — ГЛОБАЛЬНЫЙ хук.
# Живёт в ~/.claude/, а не в одной репе — значит действует в КАЖДОЙ сессии Claude Code
# на этой машине, вне зависимости от того, какой проект открыт. Канон — здесь
# (base-repo/.claude/hooks/), активная копия раскатывается `scripts/sync_global_claude.py`.
#
# ЗАЧЕМ. Приказ владельца 29.09.2026: директория `~/Documents/NOT FOR CLAUDE` —
# абсолютная слепая зона (Claude никогда её не читает, не листит, не сканирует и не
# правит), и Claude никогда сам не выполняет команды сетевой/гео-разведки (внешний IP,
# шлюз, SSID Wi-Fi, VPN, маршруты). Расширено 30.09.2026 (Zero Trust): слепота к
# полному дампу окружения и к shell-конфигам — та же механика, тот же повод.
# Текстовый запрет агент обходит рассуждением, хук — нет. Тот же принцип, что у
# protect-base-mirror.sh в base-repo (00-infrastructure/69-agents-hooks-and-gates.md §4).
#
# Полный текст правил — `00-infrastructure/107-network-quarantine-and-recon-block.md`
# (карантин/разведка) и `~/.claude/CLAUDE.md` §«Zero Trust и Fail-Loud» (env-слепота —
# сама формулировка поведенческая, хук закрывает только механически ловимую часть).
#
# ГРАНИЦА. Ловит явные признаки: путь/паттерн/команда с «NOT FOR CLAUDE» и shell-rc
# файлы — для ЛЮБОГО инструмента; recon-утилиты и голый дамп окружения — только для
# Bash. Обычная сетевая работа (curl к API, docker, git remote) и точечное обращение
# к одной переменной (`echo $PATH`, `printenv NODE_ENV`) не задеты.
set -uo pipefail

input=$(cat)

# --- 1. Карантинный путь и shell-конфиги: блок для ЛЮБОГО инструмента ---
hit=$(printf '%s' "$input" | python3 -c '
import json, sys, os
try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)
ti = data.get("tool_input", {}) or {}
# Путь-поля: значение — путь по построению, голая фраза уже однозначна.
path_fields = ["file_path", "path", "pattern", "notebook_path", "glob"]
path_blob = " ".join(str(ti.get(f, "")) for f in path_fields if ti.get(f))
# `command` (Bash) — свободный текст: там же ходят commit-сообщения и прочая
# проза, которая может ОПИСЫВАТЬ карантин словами, не обращаться к нему.
# Нужен явный признак пути, не голая фраза (иначе хук блокирует собственную
# документацию — пойман на коммите 30.09.2026, где сообщение просто называло
# директорию по имени).
command_blob = str(ti.get("command", ""))
if "not for claude" in path_blob.lower() or "documents/not for claude" in command_blob.lower():
    print("quarantine")
    sys.exit(0)
RC_NAMES = {".zshrc", ".bash_profile", ".zprofile", ".bashrc", ".profile", ".zshenv", ".bash_login"}
for f in ("file_path", "path"):
    v = ti.get(f, "")
    if v and os.path.basename(str(v)) in RC_NAMES:
        print("rcfile")
        sys.exit(0)
' 2>/dev/null) || exit 0

if [ "$hit" = "quarantine" ]; then
  echo "Заблокировано: ~/Documents/NOT FOR CLAUDE — карантинная зона, Claude туда не заходит ни при каком инструменте." >&2
  echo "Правило: 00-CLAUDE-STOP.md → «Второе-кватро», 00-infrastructure/107-network-quarantine-and-recon-block.md." >&2
  exit 2
fi
if [ "$hit" = "rcfile" ]; then
  echo "Заблокировано: конфиг shell (.zshrc/.bash_profile и аналоги) — слепота к окружению, Zero Trust §2." >&2
  echo "Нужно для отладки конкретного скрипта — попроси владельца явно, тогда это точечный запрос, не общее чтение." >&2
  exit 2
fi

# --- 2. Сетевая/гео-разведка и голый дамп окружения: только для Bash ---
tool_name=$(printf '%s' "$input" | python3 -c '
import json, sys
try:
    print(json.load(sys.stdin).get("tool_name", ""))
except Exception:
    pass
' 2>/dev/null)

[ "$tool_name" != "Bash" ] && exit 0

command=$(printf '%s' "$input" | python3 -c '
import json, sys
try:
    print(json.load(sys.stdin).get("tool_input", {}).get("command", ""))
except Exception:
    pass
' 2>/dev/null)

[ -z "$command" ] && exit 0

# `git commit`/`git commit -m` не выполняет упомянутые в сообщении утилиты —
# это текст аргумента, не вызов. Без исключения хук блокирует собственную
# документацию (коммит, описывающий список recon-утилит, сам содержит их
# имена). Остальные проверки (карантинный путь, env/printenv/set) командой
# git commit не задеваются — там нет самих слов-триггеров в норме.
printf '%s' "$command" | grep -Eiq '(^|&&|;)\s*git\s+commit\b' && exit 0

if printf '%s' "$command" | grep -Eiq \
  '\<ifconfig\>|\<ipconfig\>|\<networksetup\>|SPNetworkDataType|\<netstat\>|\<scutil\>|\<wdutil\>|\<airport\>|\<arp\>[[:space:]]+-a|\<traceroute\>|\<tracert\>|\<mtr\>|\<mdutil\>|(curl|wget)[^|;&]*(ifconfig\.me|ipinfo\.io|icanhazip\.com|ipify\.org|checkip\.amazonaws\.com|wtfismyip\.com|myexternalip\.com|api64\.ipify)|(dig|nslookup|host)[^|;&]*myip\.opendns\.com|\<osascript\>[^|;&]*(administrator privileges|network setup|Wi-?Fi)'
then
  echo "Заблокировано: команда сетевой/гео-разведки запрещена приказом владельца 29.09.2026." >&2
  echo "IP, шлюз, SSID, VPN, внешняя локация — не в зоне доступа Claude ни при каком поводе." >&2
  echo "Правило: 00-CLAUDE-STOP.md → «Второе-кватро», 00-infrastructure/107-network-quarantine-and-recon-block.md." >&2
  exit 2
fi

# Голый env/printenv/set — полный дамп окружения (proxy/шлюз/токены могут утечь).
# `env VAR=x cmd`, `printenv PATH`, `export FOO=bar` — точечные, не дамп, пропускаются:
# после команды в этом же выражении обязан идти конец строки или труба/редирект.
if printf '%s' "$command" | grep -Eiq '(^|[;&|]|&&)\s*(env|printenv|set)\s*($|[;&|]|>|&&)'
then
  echo "Заблокировано: голый env/printenv/set выводит окружение целиком — Zero Trust §2 (слепота к окружению)." >&2
  echo "Нужна одна переменная — используй printenv <ИМЯ> или echo \$<ИМЯ>, это не запрещено." >&2
  exit 2
fi

exit 0
