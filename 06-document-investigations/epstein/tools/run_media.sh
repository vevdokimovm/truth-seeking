#!/usr/bin/env bash
# Stage E runner: media of every dataset → speech notes (efta_media.py, whisper).
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
PY="$HOME/epstein/.venv/bin/python"
for n in 2 8 11 10 9; do
  case "$n" in 2|8) root="$HERE/../corpus" ;; *) root="$HOME/raw-originals/epstein-text" ;; esac
  out="$root/$(printf 'DS%02d' "$n")"
  for try in 1 2 3 4 5; do
    echo "$(date '+%F %T') media DS$n try $try"
    "$PY" "$HERE/efta_media.py" --ds "$n" --out "$out" 2>&1 | grep --line-buffered -v deprecat
    [ "${PIPESTATUS[0]}" -eq 0 ] && break
    sleep 60
  done
  echo "$(date '+%F %T') media DS$n finished"
done
echo "$(date '+%F %T') STAGE E DONE"
