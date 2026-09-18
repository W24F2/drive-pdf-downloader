# Contributing

Thanks for wanting to help. This is a small, single-file tool, so contributions stay
focused and easy to review.

## Ground rules

1. **Be honest about failures.** If a change makes a previously-working case worse, say so
   in the PR. Silent regressions in page completeness are the one thing this project cannot
   tolerate.
2. **Never commit documents.** `downloads/`, `*.pdf` and profile directories are gitignored
   for a reason. Do not add sample PDFs sourced from the internet; if you need a fixture,
   generate one.
3. **Respect the target.** No changes that increase request volume, defeat rate limits,
   solve CAPTCHAs, or reach into private resources. Concurrency defaults stay low.

## Setting up a dev environment

```bash
git clone https://github.com/W24F2/drive-pdf-downloader.git
cd drive-pdf-downloader
# Windows: .\scripts\setup_windows.ps1
# macOS:   ./scripts/setup_macos.sh
# Linux:   ./scripts/setup_linux.sh
python -m pip install ruff
```

## Before you push

```bash
python -m py_compile drive_pdf_downloader.py     # must be clean
python -m ruff check .                           # config lives in pyproject.toml
python drive_pdf_downloader.py --help            # CLI must still parse
python drive_pdf_downloader.py --list            # listing must still work
python drive_pdf_downloader.py --only 2 --out /tmp/smoke   # real end-to-end
```

CI runs the first three on Linux, macOS and Windows across Python 3.9 and 3.12.

## What makes a good PR

| Area | Examples |
| --- | --- |
| **Robustness** | A third capture engine, better stall detection, smarter scroll heuristics |
| **Portability** | Browser discovery for a distro/OS we miss, better headless fallbacks |
| **Diagnostics** | Clearer failure labels, a `--doctor` mode that reports what it can see |
| **Docs** | Translation of the wiki, screenshots, a Dockerfile recipe |
| **Speed** | Lower wall-clock without raising request pressure |

## What will be declined

* Anything that redistributes third-party documents (fixtures, archives, links to dumps).
* Features that weaken the verification step — shipping an unverified PDF silently is the
  bug this project exists to fix.
* Large refactors of the browser-driving code without a matching fixture or a clear
  reproduction of the problem being solved.

## Reporting bugs

Use the issue template. The three fields that matter most:

1. `python -V`, OS, and whether Playwright's Chromium or system Chrome was used,
2. the exact command,
3. the page count the viewer shows versus what you got, plus the full log (`--headed` if you
   can spare a minute).

## Code style

* Standard library + the four declared dependencies. No new runtime dependency without a
  strong justification.
* Keep it one importable module; helper code goes in `scripts/`.
* Prefer explicit failure over silent fallback — if pages are missing, the run must end with
  a non-zero exit code.
* Comments explain *why* (usually *which failure mode* a line prevents). The wiki holds the
  long-form explanation; the code holds the reason.

## Commit messages

Conventional-ish and specific:

```
fix: detect scroll container via largest scrollHeight, not first overflow parent
feat: add --engine chrome to skip the Playwright Chromium download
docs: explain why blob fetches are blocked by origin
```

## Releases

1. Bump `version` in `pyproject.toml` and add a `CHANGELOG.md` entry.
2. Tag: `git tag -a v2.0.1 -m "v2.0.1" && git push --tags`.
3. Create a GitHub release from the tag, pasting the changelog section.
