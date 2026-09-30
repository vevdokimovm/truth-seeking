#!/usr/bin/env bash
# Этап E целиком: проверка машины → A/B-замер VAD → очередь (аудио, затем видео).
#
# Заведён 30.09.2026, повод — три сорванных дневных замера подряд: машина была
# занята (Ollama, своп 6.4 ГБ из 7), и коэффициент уходил за ×10. Замер обязан
# сниматься тогда же, когда идёт прогон, и той же машиной — иначе он не про неё.
#
#   run_stage_e.sh            → проверка + замер + аудио + видео
#   run_stage_e.sh --no-bench → без замера, сразу очередь
#   run_stage_e.sh --force    → игнорировать проверку машины (не рекомендуется)
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
PY="$HOME/epstein/.venv/bin/python"
LOG="$HOME/epstein/stageE.log"
BENCH=1; FORCE=0
for a in "$@"; do
  case "$a" in
    --no-bench) BENCH=0 ;;
    --force) FORCE=1 ;;
  esac
done

say() { echo "$(date '+%F %T') $*" | tee -a "$LOG"; }

# ── 1. свободна ли машина (METHOD-SPEECH §7а) ────────────────────────────────
# Мерим ДОСТУПНУЮ память, а не занятый своп: macOS держит своп занятым почти
# всегда, и порог по нему заворачивал прогон на здоровой машине. Душило whisper
# 30.09 не наличие свопа, а нехватка страниц — тогда было свободно 14 МБ.
pagesize=$(sysctl -n hw.pagesize)
free_mb=$(vm_stat | awk -v ps="$pagesize" '
  /Pages free/            {gsub(/\./,"",$3); f=$3}
  /Pages inactive/        {gsub(/\./,"",$3); i=$3}
  /Pages speculative/     {gsub(/\./,"",$3); s=$3}
  END {printf "%.0f", (f+i+s)*ps/1048576}')
load=$(uptime | sed 's/.*load averages*: *\([0-9.]*\).*/\1/')
swap=$(sysctl -n vm.swapusage | sed 's/total/своп/')
say "проверка машины: доступно ${free_mb}M · load ${load} · ${swap}"
if [ "$FORCE" -eq 0 ]; then
  if [ "${free_mb:-0}" -lt 1500 ]; then
    say "🔴 СТОП: доступно всего ${free_mb}M памяти. Прогон уйдёт в своп и станет втрое"
    say "   закрой тяжёлое (Ollama, браузер) или запусти с --force"
    exit 2
  fi
  if awk "BEGIN{exit !(${load:-0} > 20)}"; then
    say "🔴 СТОП: load average ${load} — машина занята. --force, если осознанно"
    exit 2
  fi
fi
say "машина свободна, работаем"

# ── 2. A/B-замер VAD на реальных файлах корпуса ──────────────────────────────
if [ "$BENCH" -eq 1 ]; then
  say "===== A/B-замер VAD (2 файла: аудио DS9 + 5 мин видео DS8) ====="
  "$PY" "$HERE/efta_bench.py" 2>&1 | tee -a "$LOG"
  say "===== замер окончен, числа в asr-timings.csv ====="
fi

# ── 3. очередь ───────────────────────────────────────────────────────────────
bash "$HERE/run_media.sh" audio video 2>&1 | tee -a "$LOG"
say "STAGE E: раннер завершился"
