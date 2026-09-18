#!/usr/bin/env bash
# ---------------------------------------------------------------------------
#  drive-pdf-downloader - Linux setup
#  Creates .venv, installs Python dependencies and the Playwright Chromium
#  (plus the shared libraries Chromium needs on Debian/Ubuntu-style distros).
#
#  Usage:  ./scripts/setup_linux.sh
#          SKIP_BROWSER=1 ./scripts/setup_linux.sh   # reuse installed Chrome
#
#  Needs sudo for the Chromium system libraries - the script will tell you the
#  single command to run if it cannot do it itself.
# ---------------------------------------------------------------------------
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "drive-pdf-downloader setup (Linux)"
echo "project: $ROOT"

PYTHON="${PYTHON:-python3}"
if ! command -v "$PYTHON" >/dev/null 2>&1; then
    echo "python3 not found. Install it with one of:" >&2
    echo "  sudo apt install python3 python3-venv    # Debian/Ubuntu" >&2
    echo "  sudo dnf install python3                  # Fedora" >&2
    echo "  sudo pacman -S python                     # Arch" >&2
    exit 1
fi

if ! "$PYTHON" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 9) else 1)'; then
    echo "Python 3.9+ is required, but found: $("$PYTHON" -V 2>&1)" >&2
    exit 1
fi

if ! "$PYTHON" -c 'import venv' >/dev/null 2>&1; then
    echo "The python3-venv module is missing." >&2
    echo "  sudo apt install python3-venv" >&2
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
    if ! "$PY" -m playwright install chromium; then
        echo "warning: Chromium download failed - the tool will fall back to system Chrome." >&2
    fi

    # Chromium needs a pile of shared libraries. Playwright can install them,
    # but it needs root; try, and print the command if it cannot.
    if ! "$PY" -m playwright install-deps chromium 2>/dev/null; then
        echo
        echo "note: system libraries for Chromium were not installed."
        echo "      If the browser fails to start, run:"
        echo "        sudo $PY -m playwright install-deps chromium"
        echo "      (or make sure google-chrome / chromium is already installed)"
    fi
fi

echo
echo "Setup complete."
echo "Run it with:  ./scripts/run_linux.sh"
