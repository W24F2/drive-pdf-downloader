# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-09-18

The first public release, after a long debugging session against a real 19-document,
650-page folder. Everything below was driven by an observed failure.

### Added

- **Page-count verification** — every saved PDF is reopened with `pypdfium2` and its page
  count compared against the viewer's `Page X of Y` indicator; `SHORT`/`MISSING`/`UNREAD`
  files are reported and retried.
- **Repair passes** (`--retries`, default 2) with early stop when a pass makes no progress.
- **Two capture engines** — in-page `<canvas>` → JPEG data URL (default) with an automatic
  clipped-screenshot fallback.
- **Cross-platform browser discovery** — Chrome, Chrome Beta, Chromium, Edge and Playwright's
  bundled Chromium, on Windows / macOS / Linux, including `shutil.which` fallbacks.
- **Headless by default** with transparent headed fallback.
- **Concurrent** async worker pool (`--workers`, default 2).
- **Atomic writes** — pages are written to `*.pdf.part` and renamed, so an interrupted run
  never leaves a truncated PDF.
- **CLI**: `--folder`, `--out`, `--workers`, `--retries`, `--timeout`, `--engine`, `--headed`,
  `--only`, `--one`, `--list`, `--setup`, `--quiet`.
- **Meaningful exit codes** — `0` complete, `1` nothing found, `2` incomplete, `130`
  interrupted.
- Setup and run scripts for Windows (PowerShell + `.bat`), macOS and Linux.
- GitHub Actions: a 3-OS / 2-Python CI matrix, and a manual or scheduled download workflow
  that uploads the PDFs as an artifact.
- Wiki (7 pages) plus publisher scripts for macOS/Linux and Windows.
- GitHub templates, `pyproject.toml` with ruff config, `.gitattributes`, `.editorconfig`.

### Fixed

- **Transparent page margins turning black.** Rendered pages have an alpha channel; the old
  `Image.convert("RGB")` turned `(0,0,0,0)` into opaque black, littering pages with black
  spots. Pages are now composited onto **white** before encoding. Verified: average page
  luminance ~248/255, ≤0.4 % near-black pixels (ordinary ink).
- **Pages silently missing.** Drive virtualises pages, so a fresh 56-page document initially
  has only 3 rendered images. The tool now parses the page indicator and scrolls until every
  page has painted.
- **Scrolling that did nothing.** `mouse.wheel`/`window.scrollBy` do not move the viewer — it
  scrolls an inner container. The correct container is now found by walking up from a page
  image to the ancestor with the largest `scrollHeight - clientHeight`.
- **Blob fetches failing.** `fetch(blobUrl)` is blocked because the viewer mints blobs in a
  sandboxed, opaque-origin context. Pages are now read via canvas / screenshot instead.
- **Playwright async download capture.** `dl_info.value` is a coroutine in the async API and
  must be awaited; the unawaited version made every save raise `AttributeError` while the run
  still reported success. Capture no longer depends on the download event at all.

### Removed

- Node.js, jsPDF, CDN script injection, Trusted-Types workarounds and browser-download
  capture. The PDF is assembled in Python with `img2pdf` (lossless image passthrough).
- Reusing the user's Chrome profile (Chrome refuses remote debugging on its default profile).
  Link-shared files need no sign-in, so no session data is involved.

### Notes

- Output PDFs are image-based, exactly as the viewer renders them; text is not selectable.
  Run `ocrmypdf` if you need a text layer.
- Measured on the reference folder: 19 files, 650 pages, 117 MB — ~2 min at 2 workers,
  ~1 min at 4.

## [0.1.0] - 2026-09-18

- Initial prototype: DevTools console snippet capturing `blob:` images into jsPDF, plus a
  Puppeteer folder walker. Superseded by 2.0.0.
