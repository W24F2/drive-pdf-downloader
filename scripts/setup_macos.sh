#!/usr/bin/env bash
# ---------------------------------------------------------------------------
#  drive-pdf-downloader - macOS setup
#  Creates .venv, installs Python dependencies and the Playwright Chromium.
#
#  Usage:  ./scripts/setup_macos.sh
#          SKIP_BROWSER=1 ./scripts/setup_macos.sh   # reuse installed Chrome
# ---------------------------------------------------------------------------
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "drive-pdf-downloader setup (macOS)"
echo "project: $ROOT"

PYTHON="${PYTHON:-python3}"
if ! command -v "$PYTHON" >/dev/null 2>&1; then
    echo "python3 not found." >&2
    echo "Install it with:  brew install python    (or https://www.python.org/downloads/)" >&2
    exit 1
fi

if ! "$PYTHON" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 9) else 1)'; then
    echo "Python 3.9+ is required, but found: $("$PYTHON" -V 2>&1)" >&2
    exit 1
fi

if [ ! -d .venv ]; then
    echo "creating virtual environment in .venv ..."
    "$PYTHON" -m venv .venv
else
    echo "reusing existing .venv"
fi

PY="./.venv/bin/python"
"$PY" -m pip install --upgrade pip
"$PY" -m pip install -r requirements.txt

if [ "${SKIP_BROWSER:-0}" != "1" ]; then
    echo "installing Playwright Chromium (used for headless runs) ..."
    "$PY" -m playwright install chromium || \
        echo "warning: Chromium install failed - the tool will fall back to your system Chrome." >&2
fi

echo
echo "Setup complete."
echo "Run it with:  ./scripts/run_macos.sh"
