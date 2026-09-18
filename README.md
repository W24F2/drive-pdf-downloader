# drive-pdf-downloader

**Download "view only" Google Drive PDFs as clean, complete, verified PDFs — on Windows, macOS and Linux.**

[![CI](https://github.com/W24F2/drive-pdf-downloader/actions/workflows/ci.yml/badge.svg)](https://github.com/W24F2/drive-pdf-downloader/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![Platforms](https://img.shields.io/badge/platforms-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)](#-quick-start)

When a PDF in Google Drive is shared as **view only**, Drive disables the download button — but your
browser still *renders* every page in the viewer. This tool automates that render: it drives a real
browser, waits for **every** page to paint, rasterises each page, and rebuilds a PDF you actually own.

No Node.js. No browser extension. No copy-pasting into DevTools. One command.

```console
$ python drive_pdf_downloader.py
[14:02:11] [drive] browser: bundled chromium, headless=True
[14:02:14] [drive] opening folder https://drive.google.com/drive/folders/1OhkZja...
[14:02:18] [drive] found 19 PDF(s)
[14:02:18] [drive] downloading 19 file(s), 2 worker(s) -> /home/you/drive-pdf-downloader/downloads
[14:02:36] [drive]   ok    PDF2026 Blacktown Boys High School - S2 - Trial  (56/56 pages, canvas)
[14:02:41] [drive]   ok    PDF2026 Caringbah High School - S2 - Trial - Questions  (32/32 pages, canvas)
...
[14:04:26] [drive] === verification ===
[14:04:26] [drive]   OK       PDF2026 Hurlstone Agricultural High School - S2 - Trial.pdf  80 pages, 12.24 MB
[14:04:26] [drive] verification: 19 good, 0 problem
[14:04:26] [drive] done - 19/19 PDFs saved to ./downloads
```

---

## Why this exists

The popular techniques for this problem are a DevTools console snippet that captures `blob:` images
into jsPDF, or scraping file ids out of the folder HTML. Both work, but both are brittle: they miss
pages that never rendered, they produce PDFs full of **black spots** (transparent page margins
flattened to black), they silently truncate documents, and they only work in one browser on one OS.

This project fixes all four:

| Problem | How this tool solves it |
| --- | --- |
| Missing / blank pages | Parses the viewer's own **"Page X of Y"** indicator, then scrolls the viewer's real scroll container until all *Y* pages have painted |
| **Black spots** | Each page is drawn onto a **white-filled** `<canvas>` before encoding, so transparency can never become black |
| Silent truncation | Every saved PDF is **re-opened and page-counted** (`pypdfium2`) and compared against the indicator; short files are automatically retried |
| Single-OS, single-browser | Cross-platform browser discovery + a fallback capture engine, so Windows, macOS and Linux all work headless |

---

## ✨ Features

- **Complete documents** — page count taken from the viewer indicator, not guessed.
- **No black spots** — white-composited page rasters.
- **Verified** — automatic post-download page-count verification with a repair pass.
- **Two capture engines** — in-page canvas (default) with an automatic screenshot fallback.
- **Concurrent** — async worker pool (default 2, tune with `--workers`).
- **Headless by default** — no window stealing focus; falls back to a visible window if needed.
- **Cross-platform** — auto-detects Chrome / Chromium / Edge on Windows, macOS and Linux; otherwise
  uses Playwright's own Chromium.
- **Self-installing** — `--setup` installs Python deps *and* the browser build.
- **Polite** — bounded concurrency, retry backoff, atomic `.part` → `.pdf` writes, no partial files.
- **Scriptable** — clean exit codes (`0` success, `1` no files, `2` unresolved), `--quiet` for cron/CI.
- **No Node.js, no jsPDF, no extensions** — pure Python.

---

## 🚀 Quick start

**Requirements:** Python **3.9+**, and a Chromium-based browser (Chrome, Chromium or Edge). Nothing else.

### Windows (PowerShell)

```powershell
git clone https://github.com/W24F2/drive-pdf-downloader.git
cd drive-pdf-downloader
.\scripts\setup_windows.ps1
.\scripts\run_windows.ps1
```

<sub>Prefer a double-click? Use `scripts\run_windows.bat` instead.</sub>

### macOS

```bash
git clone https://github.com/W24F2/drive-pdf-downloader.git
cd drive-pdf-downloader
./scripts/setup_macos.sh
./scripts/run_macos.sh
```

### Linux

```bash
git clone https://github.com/W24F2/drive-pdf-downloader.git
cd drive-pdf-downloader
./scripts/setup_linux.sh
./scripts/run_linux.sh
```

### Any OS, manually

```bash
python3 -m venv .venv
source .venv/bin/activate         # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
python -m playwright install chromium
python drive_pdf_downloader.py
```

Output lands in **`./downloads/`** as `<original name>.pdf`.

---

## 🧰 Usage

```console
python drive_pdf_downloader.py [options]
```

| Option | Default | Description |
| --- | --- | --- |
| `--folder URL\|ID` | bundled sample folder | Google Drive folder URL **or** bare folder id |
| `--out DIR` | `./downloads` | Where PDFs are written |
| `--workers N` | `2` | Concurrent downloads |
| `--retries N` | `2` | Repair passes for files that came out short |
| `--timeout SEC` | `600` | Per-file render budget |
| `--engine auto\|chromium\|chrome` | `auto` | Which browser to drive |
| `--headed` | off | Show the browser window (debugging) |
| `--only N` / `--one` | off | Only the first N files / just the first file |
| `--list` | off | List the PDFs found, then exit |
| `--setup` | off | Install Python deps + Playwright Chromium, then exit |
| `--quiet` | off | Print only problems (cron/CI friendly) |

### Common recipes

```bash
# See what's in a folder without downloading anything
python drive_pdf_downloader.py --folder 1OhkZjaNPP8InvTphuz-XaKGOly6NS-Iq --list

# Any other shared folder, into a custom directory
python drive_pdf_downloader.py --folder "https://drive.google.com/drive/folders/<ID>" --out ./pdfs

# Faster (heavier on Drive — be considerate)
python drive_pdf_downloader.py --workers 4

# Debug a stubborn document with a visible browser
python drive_pdf_downloader.py --one --headed
```

---

## 🔍 How it works

```text
folder listing ─▶ preview per file ─▶ parse "Page X of Y" ─▶ scroll to render all pages
                                                                       │
                          ┌────────────────────────────────────────────┘
                          ▼
        engine A: <canvas> (white fill) ──▶ JPEG data URL ─┐
        engine B: element screenshot ──▶ flatten on white ─┤ (fallback)
                                                           ▼
                              img2pdf assemble ──▶ .pdf.part ──▶ atomic rename
                                                           │
                                                           ▼
                            pypdfium2 page count  ==  "Page X of Y" ?  ──▶ repair pass
```

1. **List** — open the folder and collect every `*.pdf` row (`data-id`), no HTML id-scraping.
2. **Preview** — navigate to `drive.google.com/file/d/<id>/preview`. Link-shared files render
   **without sign-in**, so no cookies or Google account are needed.
3. **Count** — read the viewer's own page indicator (`Page 1 of 56`, shown as `1 / 56`).
4. **Render** — Drive virtualises pages, so they only paint once visible. The tool scrolls the
   viewer's *inner scroll container* (scrolling the window does nothing) until all pages exist.
5. **Capture** — engine **A** rasterises each page image onto a white canvas and returns a JPEG data
   URL; engine **B** falls back to a clipped screenshot flattened onto white in Pillow.
6. **Assemble** — `img2pdf` stitches the page rasters losslessly and the file is renamed into place
   atomically.
7. **Verify** — every PDF is reopened and page-counted; anything missing or short triggers a repair
   pass (up to `--retries`).

More detail, including the DOM specifics and why each step is necessary, is in the
**[wiki](https://github.com/W24F2/drive-pdf-downloader/wiki)** — see `wiki/` in this repo.

---

## 🤖 Automation

### Built-in installer

```bash
python drive_pdf_downloader.py --setup
```

### Cron / Task Scheduler / launchd

```bash
# Every day at 03:00, quiet, into a dated folder
0 3 * * * cd /opt/drive-pdf-downloader && \
  ./.venv/bin/python drive_pdf_downloader.py --quiet --out "./downloads/$(date +\%F)" >> run.log 2>&1
```

- **Windows:** `schtasks /create /tn "DrivePDF" /tr "powershell -File C:\path\to\scripts\run_windows.ps1 -Quiet" /sc daily /st 03:00`
- **macOS:** use a `launchd` plist calling `scripts/run_macos.sh`.

### 👉 GitHub Actions (no local machine needed)

`.github/workflows/download.yml` is included and ready to go:

1. **Actions → Download Google Drive PDFs → Run workflow**
2. It spins up Ubuntu, installs everything, downloads the folder, verifies every file, and uploads
   the PDFs as a **workflow artifact** (kept 30 days).
3. Optional weekly schedule is included (commented out) — uncomment to keep an archive fresh.

`--quiet` plus the `2` exit code makes it fail loudly if any document could not be retrieved intact.

---

## 🩺 Troubleshooting

| Symptom | Fix |
| --- | --- |
| `Could not launch a browser` | `python drive_pdf_downloader.py --setup`, or install Chrome/Chromium/Edge |
| `no PDF rows found` | The folder link isn't shared publicly, or the folder is empty |
| `SHORT  file.pdf  41/56 pages` | Usually a slow connection on a long document — re-run, or raise `--timeout`; the repair pass often fixes it on its own |
| `engine A unusable … TAINT` | Falls back to screenshots automatically; update your browser if it persists |
| Hang / no output on Linux | Run `python -m playwright install-deps chromium` (installs shared libraries) |
| Headless launch fails | The tool retries headed automatically; add `--headed` to force it |
| Text isn't selectable in the output | Expected: the pages are **images**, exactly as the viewer shows them. The original file is never released while it's view-only. Run OCR (e.g. `ocrmypdf`) if you need a text layer |

Full FAQ and diagnostics: **[wiki/Troubleshooting](wiki/Troubleshooting.md)**.

---

## 📁 Project layout

```text
drive-pdf-downloader/
├── drive_pdf_downloader.py      # the whole tool (single file, no local imports)
├── requirements.txt
├── pyproject.toml               # metadata + ruff config, installable as a CLI
├── scripts/
│   ├── setup_windows.ps1  run_windows.ps1  run_windows.bat
│   ├── setup_macos.sh     run_macos.sh
│   ├── setup_linux.sh     run_linux.sh
│   └── publish_wiki.sh    publish_wiki.ps1
├── wiki/                        # GitHub wiki pages (Home, Installation, …)
├── docs/                        # architecture notes
├── .github/workflows/           # ci.yml (3-OS matrix) + download.yml (manual/scheduled)
└── LICENSE
```

---

## ⚖️ Legal & ethical use

This tool exists for **archival and accessibility** — backing up documents you are legitimately
entitled to read, formatting material for offline study, or reading course material handed to you as
view-only. That is a real and common need.

**It is not a licence to redistribute.** By using it you agree that:

- you will only download material you have the right to access, and
- you are responsible for complying with copyright law, the terms of the material's owner, and
  [Google's Terms of Service](https://policies.google.com/terms).

A "view only" flag is a technical access control; bypassing it to read something you were granted
access to is one thing, redistributing someone else's work is another. The authors of this tool take
no responsibility for misuse. Keep `downloads/` out of version control (`.gitignore` already does
this) and never publish other people's documents.

---

## 🤝 Contributing

Issues and PRs are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md). Good first contributions:
report the DOM shape of a non-English Drive UI, or add a `chromium`-only Docker recipe.

## 📄 License

[MIT](LICENSE) © 2026 24F2
