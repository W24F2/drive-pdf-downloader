#!/usr/bin/env bash
# ---------------------------------------------------------------------------
#  Publish wiki/*.md to this repository's GitHub wiki.
#
#  Usage:  ./scripts/publish_wiki.sh                 # auto-detect from origin
#          ./scripts/publish_wiki.sh owner/repo
#
#  Prerequisites:
#    * git push access to the wiki (i.e. to the repo)
#    * the wiki must be ENABLED once by hand: repo -> Settings -> Features -> Wikis,
#      then create any first page. GitHub only creates the .wiki.git repo after that.
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

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "cloning https://github.com/${REPO}.wiki.git ..."
if ! git clone --depth 1 "https://github.com/${REPO}.wiki.git" "$TMP" 2>/dev/null; then
    echo "Could not clone the wiki repo." >&2
    echo "Enable it first: GitHub repo -> Settings -> Features -> tick 'Wikis'," >&2
    echo "then open the Wiki tab and create a first page. Then re-run this script." >&2
    exit 1
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
