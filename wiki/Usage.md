# Usage

## Synopsis

```console
python drive_pdf_downloader.py [options]
```

Nothing here is interactive: it runs, logs, verifies, and exits with a status code.

## Options

| Option | Default | Description |
| --- | --- | --- |
| `--folder URL\|ID` | bundled sample folder | Google Drive folder URL, or a bare folder id |
| `--out DIR` | `./downloads` | Output directory (created if missing) |
| `--workers N` | `2` | Concurrent downloads. 2–4 is sensible; higher risks throttling |
| `--retries N` | `2` | Repair passes for files that came out short or missing |
| `--timeout SEC` | `600` | Per-file render budget for very long documents |
| `--engine auto\|chromium\|chrome` | `auto` | Which browser to drive |
| `--headed` | off | Show the browser window (debugging) |
| `--only N` | off | Process only the first N files |
| `--one` | off | Shorthand for `--only 1` |
| `--list` | off | List the PDFs found, then exit (no downloads) |
| `--setup` | off | Install Python deps + Playwright Chromium, then exit |
| `--quiet` | off | Print only problems — ideal for cron and CI |

## Output

```
downloads/
├── PDF2026 Blacktown Boys High School - S2 - Trial.pdf     56 pages, 10.37 MB
├── PDF2026 Caringbah High School - S2 - Trial - Questions.pdf
└── …
```

* File names are the folder's names with the `.pdf` extension removed and then the PDF
  rebuilt by this tool. Illegal path characters are replaced with `_`, and names are
  truncated at 120 characters so they stay valid on Windows.
* Verification reports real page counts read back from the saved files.
* A crash leaves `*.pdf.part` files, never a truncated `.pdf`.

## Exit codes

| Code | Meaning |
| --- | --- |
| `0` | Every file downloaded and verified |
| `1` | Nothing found (folder not public, or empty) |
| `2` | Finished, but some files are still short/missing after repairs |
| `130` | Interrupted with `Ctrl-C` |

Useful for automation: `python drive_pdf_downloader.py --quiet || notify-send "Drive pull failed"`.

## Recipes

```bash
# 1. Just look — what is in this folder?
python drive_pdf_downloader.py --list

# 2. A different folder, custom destination
python drive_pdf_downloader.py \
  --folder "https://drive.google.com/drive/folders/1OhkZjaNPP8InvTphuz-XaKGOly6NS-Iq" \
  --out ./pdfs

# 3. Faster
python drive_pdf_downloader.py --workers 4

# 4. One difficult document, with a visible browser
python drive_pdf_downloader.py --one --headed

# 5. Very long document (raise the render budget to 20 minutes)
python drive_pdf_downloader.py --timeout 1200 --one

# 6. Ignore Playwright's Chromium and use the Chrome I already have
python drive_pdf_downloader.py --engine chrome

# 7. Quiet run for a scheduled job
python drive_pdf_downloader.py --quiet --out "/srv/archive/$(date +%F)"
```

## Reading the log

```console
[14:02:18] [drive] downloading 19 file(s), 2 worker(s) -> …/downloads
[14:02:36] [drive]   ok    PDF2026 Blacktown…  (56/56 pages, canvas)     ← captured, engine A
[14:03:02] [drive]   ok    PDFcssa sol  (24/24 pages, screenshot)        ← engine B fallback used
[14:03:40] [drive]   FAIL  Some Doc  [SHORT] 12/30 pages                 ← will be repaired
[14:04:26] [drive] === verification ===
[14:04:26] [drive]   OK       PDFcssa.pdf  32 pages, 4.25 MB
[14:04:26] [drive] === repair pass 1/2: 1 file(s) ===                  ← automatic retry
[14:04:26] [drive] verification: 19 good, 0 problem
[14:04:26] [drive] done - 19/19 PDFs saved to …/downloads
```

Status labels you may see:

| Label | Meaning |
| --- | --- |
| `ok … (N/N pages, canvas)` | Captured with the in-page canvas engine |
| `ok … (N/N pages, screenshot)` | Canvas failed; the screenshot fallback worked |
| `FAIL … [NO_PAGES]` | The viewer never reported a page count |
| `FAIL … [NO_CAPTURE]` | Both engines produced nothing |
| `FAIL … [ERR]` | A browser/network error — the message says which |

## Performance

Measured on a 19-document folder (650 pages, 117 MB total):

| Workers | Wall clock |
| --- | --- |
| 2 (default) | ~2 min |
| 4 | ~1 min |
| 1 | ~4 min |

Roughly 2–4 seconds per page, dominated by the deliberate scrolling that forces Drive to
render. Raising `--workers` mostly helps folders with many short documents; a single
80-page document is bound by its own scroll time.
