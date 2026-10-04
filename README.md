# drive-pdf-downloader

**Download view-only Google Drive PDFs as complete, verified PDFs.**

When a PDF in Google Drive is shared as *view only*, the download button is disabled. This tool opens the PDF in Playwright, waits for every page to render, and exports a clean PDF you can actually keep.

## Quick Start

```bash
# 1. Clone
git clone https://github.com/W24F2/drive-pdf-downloader
cd drive-pdf-downloader

# 2. Install
python -m pip install -r requirements.txt
python -m playwright install chromium  # first time only

# 3. Run
python drive_pdf_downloader.py
# → prompts for folder URL, saves PDFs to ./downloads/
```

## Usage

```
python drive_pdf_downloader.py --folder <URL|ID> --out ./downloads --workers 2
```

Options:
- `--folder` / `-f` : Google Drive folder URL or ID (default prompts)
- `--out`  / `-o`   : Output directory (default: ./downloads)
- `--workers` / `-w`: Concurrent downloads, 1-4 (default: 2)
- `--one`          : Process first file only (testing)
- `--list`         : List PDFs in folder, don't download
- `--setup`        : Install deps and exit

## Why this exists

Google Drive's viewer renders every page as a blob image. This tool:
- Reads **Page X of Y** from the viewer to get the true page count
- Captures every page as a screenshot
- Assembles a verified PDF via img2pdf
- Verifies final page count with pypdfium2 and retries if short

## Requirements

- Python 3.9+
- Chromium (installed via Playwright)
- No Node.js, no browser extensions

## Dependencies

```
playwright>=1.44
Pillow>=10.2
img2pdf>=0.5
pypdfium2>=4.30
```

## Important

This is for downloading files you have legal access to. The tool respects your authentication cookies and only downloads documents you can already view. Use responsibly and per Google's Terms of Service.

## License

MIT — see [LICENSE](LICENSE)

*Questions or issues: https://github.com/W24F2/drive-pdf-downloader/issues*
