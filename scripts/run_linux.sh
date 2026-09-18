#!/usr/bin/env bash
# ---------------------------------------------------------------------------
#  drive-pdf-downloader - run on Linux
#
#  Usage:  ./scripts/run_linux.sh                  # download the default folder
#          ./scripts/run_linux.sh --list
#          ./scripts/run_linux.sh --workers 4 --out ~/pdfs
#          ./scripts/run_linux.sh --quiet          # for cron / systemd timers
#
#  Headless is the default, so this works over SSH and in containers.
#  If no display is available and Chromium refuses to start, try:
#      xvfb-run -a ./scripts/run_linux.sh
# ---------------------------------------------------------------------------
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="$ROOT/.venv/bin/python"

if [ ! -x "$PY" ]; then
    echo "Not set up yet. Run:  ./scripts/setup_linux.sh" >&2
    exit 1
fi

exec "$PY" "$ROOT/drive_pdf_downloader.py" "$@"
