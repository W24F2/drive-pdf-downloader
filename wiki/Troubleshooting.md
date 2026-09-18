# Troubleshooting

## Diagnose first

```bash
python drive_pdf_downloader.py --list          # does it even see the folder?
python drive_pdf_downloader.py --one --headed  # watch one download happen
```

`--headed` with `--one` answers most questions in 30 seconds: you can literally see
whether the viewer loaded and whether pages painted.

---

## Browser problems

### `Could not launch a browser`

```
Could not launch a browser.
  bundled chromium: Executable doesn't exist at …/chrome-win/chrome.exe
  system chrome: no such file
```

Fix:

```bash
python -m playwright install chromium
# Linux only, needs root — installs Chromium's shared libraries:
sudo python -m playwright install-deps chromium
```

Or install Chrome / Chromium / Edge normally; the tool finds it automatically.

### Headless works but exits immediately, or hangs with no output

Some sandboxes and Chrome builds refuse headless pipes. The tool already retries headed
automatically — if it still fails, force it:

```bash
python drive_pdf_downloader.py --headed
```

On a machine with no display at all (SSH, bare container):

```bash
xvfb-run -a python drive_pdf_downloader.py
```

### `DevTools remote debugging requires a non-default data directory`

You upstreamed a version that launched the browser with *your* real Chrome profile. Chrome
forbids remote debugging against its default profile directory. This tool avoids it by
launching a throwaway browser context — no profile, no cookies, nothing of yours involved.
Nothing to fix; just use this version.

---

## Folder / listing problems

### `no PDF rows found`

In order of likelihood:

1. The folder isn't shared publicly — share it as *Anyone with the link → Viewer*.
   (Per-file sharing is not enough: the listing must be readable.)
2. The folder contains no `*.pdf` entries (subfolders are not recursed).
3. The link points at a *file* or a *shared drive* you cannot list.

Check with `--list`; if that prints nothing, the listing itself is the problem, not the
download.

### It only found some of the files

Long folders lazy-load. The tool scrolls the listing 20 times before reading it. If you
have hundreds of files, increase that loop in `list_files()`.

---

## Download problems

### `SHORT  file.pdf  41/56 pages`

The most common real failure. Causes: a slow connection between scrolls, or Drive
throttling a big document. Options:

```bash
python drive_pdf_downloader.py --one --timeout 1200      # more patience
python drive_pdf_downloader.py --workers 1               # less contention
python drive_pdf_downloader.py --headed                  # watch where it stalls
```

The repair pass usually resolves it on the second attempt by itself.

### `NO_PAGES` — the viewer never reported a page count

The preview did not finish loading (or hit a consent/CAPTCHA interstitial, common in
datacentre IP ranges). Run `--headed` and look. If you see a CAPTCHA, run from a normal
residential connection; do not try to solve CAPTCHAs automatically.

### `engine A unusable … TAINT`

`canvas.toDataURL()` was refused, so the tool switches to screenshots (engine B). If both
fail, update your browser: this happens when the page's origin handling changes.

### Black rectangles or spots on pages

You are running an old copy. In current versions every page is composited on white before
encoding; see [How-It-Works](How-It-Works.md#why-the-earlier-versions-produced-black-spots).

### Pages come out at low resolution

Engine B (screenshots) captures at CSS pixel size, so it is softer than engine A. If you
see `screenshot` in the log for a document that matters, re-run it alone and see whether
engine A succeeds:

```bash
python drive_pdf_downloader.py --one --headed
```

---

## Output problems

### The text isn't selectable / searchable

Expected, and unavoidable. A view-only document is never released as a file — you get what
the viewer renders, i.e. page images. Add a text layer afterwards:

```bash
ocrmypdf input.pdf output.pdf          # sudo apt install ocrmypdf
```

### A `.part` file is left behind

That is the atomic-write safety net: a `.pdf.part` means the write was interrupted and
that document is incomplete. Delete it and re-run.

### Filenames look truncated

Names are cut at 120 characters to stay well inside Windows' path limits. Rename them
afterwards if you care.

---

## Platform notes

| Platform | Note |
| --- | --- |
| **Windows** | Works headless with no display issues. If PowerShell refuses the setup script: `powershell -ExecutionPolicy Bypass -File .\scripts\setup_windows.ps1` |
| **macOS** | First run may prompt for network access — allow your terminal. Gatekeeper can quarantine a downloaded Chromium; `xattr -dr com.apple.quarantine ~/Library/Caches/ms-playwright` if launching fails |
| **Linux** | `python3-venv` is a separate package on Debian/Ubuntu. Chromium needs `playwright install-deps` (root) or an installed `google-chrome` |

---

## Still stuck?

Open an [issue](https://github.com/W24F2/drive-pdf-downloader/issues) with:

1. OS and version, `python -V`
2. The exact command you ran
3. **Full log output** (add `--headed` first if you can)
4. The page count the viewer shows for the file vs. the count you got
