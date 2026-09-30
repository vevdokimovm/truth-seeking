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
swap_used=$(sysctl -n vm.swapusage | sed 's/.*used = \([0-9.]*\)M.*/\1/')
swap_tot=$(sysctl -n vm.swapusage | sed 's/total = \([0-9.]*\)M.*/\1/')
load=$(uptime | sed 's/.*load averages*: *\([0-9.]*\).*/\1/')
say "проверка машины: своп ${swap_used}M из ${swap_tot}M · load ${load}"
if [ "$FORCE" -eq 0 ]; then
  if awk "BEGIN{exit !(${swap_used:-0} > ${swap_tot:-1} * 0.7)}"; then
    say "🔴 СТОП: своп занят больше чем на 70%. Замер будет ложным, прогон — втрое"
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
