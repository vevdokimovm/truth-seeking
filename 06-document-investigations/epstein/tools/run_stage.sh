#!/usr/bin/env bash
# Stage runner: stream each dataset zip from archive.org through efta_to_md.py.
#   run_stage.sh A   → DS 1-8,12 into the repo (corpus/DSNN)
#   run_stage.sh B|C|D → DS 11|10|9 into ~/raw-originals/epstein-text/DSNN
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
PY="$HOME/epstein/.venv/bin/python"
ITEM="https://archive.org/download/data-set-8_20251228"
zipname() {
  case "$1" in
    9) echo "DataSet%2009%20-%20Incomplete.zip" ;;
    *) printf 'DataSet%%20%02d.zip' "$1" ;;
  esac
}

case "${1:-}" in
  A) SETS=(5 6 7 12 3 4 2 1 8); ROOT="$HERE/../corpus" ;;
  B) SETS=(11); ROOT="$HOME/raw-originals/epstein-text" ;;
  C) SETS=(10); ROOT="$HOME/raw-originals/epstein-text" ;;
  D) SETS=(9);  ROOT="$HOME/raw-originals/epstein-text" ;;
  *) echo "usage: $0 A|B|C|D"; exit 1 ;;
esac

for n in "${SETS[@]}"; do
  out="$ROOT/$(printf 'DS%02d' "$n")"
  for try in 1 2 3 4 5; do
    url=$(curl -sIL -o /dev/null -w '%{url_effective}' "$ITEM/$(zipname "$n")")
    echo "$(date '+%F %T') DS$n try $try $url"
    "$PY" "$HERE/efta_to_md.py" --url "$url" --ds "$n" --out "$out" 2>&1 \
      | grep --line-buffered -v deprecat
    [ "${PIPESTATUS[0]}" -eq 0 ] && break
    sleep 60
  done
  echo "$(date '+%F %T') DS$n finished"
done
echo "$(date '+%F %T') STAGE $1 DONE"
