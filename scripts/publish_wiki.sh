#!/usr/bin/env bash
# ---------------------------------------------------------------------------
#  Publish wiki/*.md to this repository's GitHub wiki.
#
#  Usage:  ./scripts/publish_wiki.sh                 # auto-detect from origin
#          ./scripts/publish_wiki.sh owner/repo
#
#  One-time prerequisite (a GitHub limitation, not ours): the wiki's git
#  storage does not exist until the *first* page is saved through the web UI.
#  This script detects that, tells you the exact link, and - if you are on a
#  terminal - waits for you to click it once and then publishes everything.
#
#  Exit codes:  0 published or already current
#               1 bad usage / missing wiki/ directory
#               3 the wiki still is not initialised (non-interactive run)
# ---------------------------------------------------------------------------
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO="${1:-}"

if [ -z "$REPO" ]; then
    REPO="$(git -C "$ROOT" remote get-url origin 2>/dev/null \
        | sed -E 's#(git@|https://)github\.com[:/]##; s#\.git$##')" || true
fi
if [ -z "$REPO" ]; then
    echo "usage: $0 owner/repo   (or add a git 'origin' remote)" >&2
    exit 1
fi

if [ ! -d "$ROOT/wiki" ]; then
    echo "no wiki/ directory in $ROOT" >&2
    exit 1
fi

WIKI_URL="https://github.com/${REPO}.wiki.git"
NEW_PAGE_URL="https://github.com/${REPO}/wiki"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "cloning ${WIKI_URL} ..."

if ! git clone --depth 1 "$WIKI_URL" "$TMP" 2>/dev/null; then
    cat >&2 <<EOF

  GitHub has not created the wiki storage yet.

  A wiki's ${REPO}.wiki.git repository is only born when its first page is
  saved through the web UI - there is no API for it, so no script can do this
  part. You only ever have to do it once.

    1. open  ${NEW_PAGE_URL}
    2. click  "Create the first page"
    3. type anything (it will be overwritten) and press  Save Page

EOF

    # Interactive: wait for the click instead of making the user re-run this.
    if [ -t 0 ]; then
        for _ in $(seq 1 12); do
            printf '  press Enter once the page is saved (or "q" to give up): '
            read -r reply || exit 3
            case "$reply" in
                q|Q) echo "  giving up - re-run this script when you are ready" >&2; exit 3 ;;
            esac
            if git clone --depth 1 "$WIKI_URL" "$TMP" 2>/dev/null; then
                echo "  wiki initialised - publishing all pages"
                break
            fi
            echo "  still not there, give GitHub a moment and press Enter again"
        done
        if [ ! -d "$TMP/.git" ]; then
            echo "  still unavailable - re-run this script later" >&2
            exit 3
        fi
    else
        echo "  re-run this script once the page is saved." >&2
        exit 3
    fi
fi

cp -v "$ROOT"/wiki/*.md "$TMP"/

cd "$TMP"
git add -A
if git diff --cached --quiet; then
    echo "wiki already up to date"
    exit 0
fi
git commit -m "docs: sync wiki from repo ($(date +%F))"
git push
echo
echo "Wiki published: https://github.com/${REPO}/wiki"
