#!/usr/bin/env bash
# Stage E runner: media of every dataset → speech notes (efta_media.py, whisper).
#
# Two passes since 30.09.2026. Pass 1 takes the pure-audio members of every
# dataset (calls, dictaphone — the dense speech, ~118 files); pass 2 takes the
# video. Measured reason: an hour of CCTV costs 1.55x realtime and yields ~240
# words, so video must not hold up the audio.
#   run_media.sh            → audio pass, then video pass
#   run_media.sh audio      → audio only
#   run_media.sh video      → video only
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
PY="$HOME/epstein/.venv/bin/python"
if [ "$#" -gt 0 ]; then KINDS=("$@"); else KINDS=(audio video); fi

for kind in "${KINDS[@]}"; do
  echo "$(date '+%F %T') ===== PASS $kind ====="
  for n in 2 8 11 10 9; do
    case "$n" in 2|8) root="$HERE/../corpus" ;; *) root="$HOME/raw-originals/epstein-text" ;; esac
    out="$root/$(printf 'DS%02d' "$n")"
    for try in 1 2 3 4 5; do
      echo "$(date '+%F %T') media DS$n [$kind] try $try"
      "$PY" "$HERE/efta_media.py" --ds "$n" --out "$out" --kind "$kind" 2>&1 \
        | grep --line-buffered -v deprecat
      [ "${PIPESTATUS[0]}" -eq 0 ] && break
      sleep 60
    done
    echo "$(date '+%F %T') media DS$n [$kind] finished"
  done
done
echo "$(date '+%F %T') STAGE E DONE"
