#!/usr/bin/env bash
# ---------------------------------------------------------------------------
#  drive-pdf-downloader - run on macOS
#
#  Usage:  ./scripts/run_macos.sh                 # download the default folder
#          ./scripts/run_macos.sh --list
#          ./scripts/run_macos.sh --workers 4 --out ~/pdfs
#          ./scripts/run_macos.sh --quiet         # for launchd / cron
# ---------------------------------------------------------------------------
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="$ROOT/.venv/bin/python"

if [ ! -x "$PY" ]; then
    echo "Not set up yet. Run:  ./scripts/setup_macos.sh" >&2
    exit 1
fi

exec "$PY" "$ROOT/drive_pdf_downloader.py" "$@"
