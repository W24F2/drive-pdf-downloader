#!/usr/bin/env python3
"""
drive-pdf-downloader - download view-only Google Drive PDFs as clean image PDFs.

When a Google Drive PDF is shared "view only", Drive refuses to hand you the
original file. But the *viewer* still renders every page in your browser as a
`blob:` image. This tool drives a real browser, lets the viewer render every
page, rasterises each rendered page, and stitches the pages back into a PDF
that you own.

Design goals
------------
* Cross-platform   - Windows, macOS and Linux are all first-class.
* Minimal deps     - pure Python (Playwright + Pillow + img2pdf + pypdfium2).
                     No Node.js, no jsPDF, no browser extensions.
* Redundant        - two independent capture engines, automatic retries and a
                     repair pass, so a failure never silently ships a short PDF.
* Verifying        - every saved PDF is re-opened and its page count is compared
                     against the viewer's own "Page X of Y" indicator.

How it works
------------
1. Open the folder and list every `*.pdf` entry (link-shared folders need no
   sign-in).
2. For each file open       https://drive.google.com/file/d/<id>/preview
3. Parse "Page X of Y" from the viewer -> the authoritative page count.
4. Scroll the viewer's scroll container until all Y pages have rendered.
5. Capture each rendered page with one of two engines:
      engine A (default)  in-page <canvas> -> JPEG data URL, white background
                          fill so transparent page margins never turn black
      engine B (fallback) clip screenshot of the rendered <img>, flattened
                          onto white in Pillow
6. Assemble an image PDF with img2pdf (lossless image passthrough).
7. Verify with pypdfium2; anything missing or short is retried in a repair pass.

Usage
-----
    python drive_pdf_downloader.py                     # whole folder, 2 workers
    python drive_pdf_downloader.py --workers 4         # faster
    python drive_pdf_downloader.py --one               # only the first file
    python drive_pdf_downloader.py --list              # just list what it finds
    python drive_pdf_downloader.py --folder <url|id>   # any shared folder
    python drive_pdf_downloader.py --setup             # install missing deps

Run `--help` for every option.

License: MIT. Use responsibly and respect copyright and Google's Terms of
Service - only download material you are entitled to access.
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import io
import os
import re
import shutil
import subprocess
import sys
import time
from collections.abc import Iterable
from pathlib import Path

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

ROOT = Path(__file__).resolve().parent
DEFAULT_FOLDER = "https://drive.google.com/drive/u/0/folders/1OhkZjaNPP8InvTphuz-XaKGOly6NS-Iq"
DEFAULT_OUT = ROOT / "downloads"
DEFAULT_WORKERS = 2      # be polite to Drive; raise it if you like
DEFAULT_RETRIES = 2      # repair passes for files that came up short
DEFAULT_TIMEOUT = 600.0  # per-file render budget (seconds)

PREVIEW_URL = "https://drive.google.com/file/d/{file_id}/preview"
FOLDER_ID_RE = re.compile(r"[-\w]{10,}")
MIN_PAGE_PX = 200        # ignore page images smaller than this (viewer chrome)

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

BROWSER_ARGS = [
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    "--no-first-run",
    "--no-default-browser-check",
    "--disable-background-timer-throttling",
    "--disable-renderer-backgrounding",
]


# --------------------------------------------------------------------------- #
# Cross-platform helpers
# --------------------------------------------------------------------------- #


def chrome_candidates() -> list[str]:
    """Plausible Chrome/Chromium/Edge executables for this OS, best first."""
    env = os.environ
    out: list[str] = []

    if sys.platform.startswith("win"):
        bases = [env.get("LOCALAPPDATA", ""), env.get("PROGRAMFILES", ""), env.get("PROGRAMFILES(X86)", "")]
        for base in bases:
            if not base:
                continue
            out.append(str(Path(base) / "Google/Chrome/Application/chrome.exe"))
            out.append(str(Path(base) / "Google/Chrome Beta/Application/chrome.exe"))
            out.append(str(Path(base) / "Chromium/Application/chrome.exe"))
            out.append(str(Path(base) / "Microsoft/Edge/Application/msedge.exe"))
    elif sys.platform == "darwin":
        out += [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Google Chrome Beta.app/Contents/MacOS/Google Chrome Beta",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
            os.path.expanduser("~/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        ]
    else:  # linux / bsd
        out += [
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
            "/usr/bin/chromium",
            "/usr/bin/chromium-browser",
            "/snap/bin/chromium",
            "/usr/lib/chromium/chromium",
            "/usr/bin/microsoft-edge",
        ]

    for name in ("google-chrome", "google-chrome-stable", "chromium",
                 "chromium-browser", "chrome", "msedge"):
        found = shutil.which(name)
        if found:
            out.append(found)
    return out


def find_chrome() -> str | None:
    for path in chrome_candidates():
        if path and Path(path).exists():
            return path
    return None


def clean_name(name: str, limit: int = 120) -> str:
    """Filesystem-safe file stem (valid on Windows, macOS and Linux)."""
    stem = re.sub(r"(?i)\.pdf$", "", name.strip())
    stem = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", stem)
    stem = re.sub(r"\s+", " ", stem).strip(" .")
    return (stem[:limit].strip() or "document")


def resolve_folder_id(folder: str) -> str:
    if "://" not in folder:
        return folder.strip()
    match = re.search(r"/folders/([-\w]+)", folder)
    if match:
        return match.group(1)
    match = FOLDER_ID_RE.search(folder)
    if not match:
        raise SystemExit(f"Could not find a folder id in {folder!r}")
    return match.group(0)


class Log:
    """Tiny timestamped logger (flushed, so it works under CI and redirection)."""

    def __init__(self, quiet: bool = False) -> None:
        self.quiet = quiet

    def __call__(self, *parts: object) -> None:
        if self.quiet:
            return
        print(f"[{time.strftime('%H:%M:%S')}] [drive]", *parts, flush=True)


# --------------------------------------------------------------------------- #
# In-page JavaScript
# --------------------------------------------------------------------------- #

# Page images are minted in the top document by the Drive viewer, so reading
# them back is not blocked by the sandboxed preview iframe.
#
# `__MIN_PX__` is substituted by _js(): the JS below is full of `{ }` and `%`,
# so neither .format() nor %-formatting can be used on it.

MIN_PX_TOKEN = "__MIN_PX__"


def _js(template: str) -> str:
    """Substitute the minimum page-image width into an in-page JS snippet."""
    return template.replace(MIN_PX_TOKEN, str(MIN_PAGE_PX))


COUNT_JS = _js("""() => [...document.querySelectorAll('img[src^="blob:"]')]
    .filter(i => i.naturalWidth >= __MIN_PX__).length""")

# Authoritative page count from the viewer's own indicator ("Page 1 of 56",
# rendered as an editable "1 / 56" field).
TOTAL_JS = """() => {
    const t = (document.body.innerText || '').replace(/\\s+/g, ' ');
    let m = t.match(/page\\s+(\\d+)\\s+of\\s+(\\d+)/i);
    if (m) return parseInt(m[2], 10);
    m = t.match(/(\\d+)\\s*\\/\\s*(\\d+)/);
    if (m && +m[2] > 1) return parseInt(m[2], 10);
    return 0;
}"""

# Scroll the viewer's scroll container (NOT the window) to paint the next
# pages. Drive virtualises pages, so they only render once visible.
SCROLL_JS = """() => {
    const imgs = [...document.querySelectorAll('img[src^="blob:"]')];
    if (!imgs.length) { window.scrollBy(0, 2000); return; }
    let el = imgs[0].parentElement, best = null, max = 0;
    while (el) {
        const d = el.scrollHeight - el.clientHeight;
        if (d > max) { max = d; best = el; }
        el = el.parentElement;
    }
    if (best) best.scrollTop += Math.max(600, best.clientHeight * 0.9);
    else window.scrollBy(0, 2000);
}"""

RESET_SCROLL_JS = """() => {
    const img = document.querySelector('img[src^="blob:"]');
    if (!img) return;
    let el = img.parentElement;
    while (el) {
        if (el.scrollHeight - el.clientHeight > 0) el.scrollTop = 0;
        el = el.parentElement;
    }
}"""

# Engine A: rasterise one rendered page onto a WHITE canvas and hand the JPEG
# data URL back to Python. The white fill is what prevents the "black spots"
# caused by transparent page margins being flattened to black.
CANVAS_JS = _js("""(i) => {
    const imgs = [...document.querySelectorAll('img[src^="blob:"]')]
        .filter(m => m.naturalWidth >= __MIN_PX__);
    const img = imgs[i];
    if (!img) return 'NO_IMG';
    const c = document.createElement('canvas');
    c.width = img.naturalWidth; c.height = img.naturalHeight;
    const x = c.getContext('2d', { alpha: false });
    x.fillStyle = '#FFFFFF';
    x.fillRect(0, 0, c.width, c.height);
    x.drawImage(img, 0, 0);
    try { return c.toDataURL('image/jpeg', 0.95); }
    catch (e) { return 'TAINT:' + e.message; }
}""")

# Engine B (fallback): scroll a page into view and report its viewport rect so
# Python can screenshot exactly that element.
BOX_JS = _js("""(i) => {
    const imgs = [...document.querySelectorAll('img[src^="blob:"]')]
        .filter(m => m.naturalWidth >= __MIN_PX__);
    const img = imgs[i];
    if (!img) return null;
    img.scrollIntoView({ block: 'center' });
    const r = img.getBoundingClientRect();
    if (r.width < 40 || r.height < 40) return null;
    return { x: r.x, y: r.y, width: r.width, height: r.height };
}""")

LIST_JS = """() => {
    const out = [], seen = new Set();
    for (const r of document.querySelectorAll('[data-id]')) {
        const id = r.getAttribute('data-id') || '';
        if (!id || seen.has(id)) continue;
        const m = (r.textContent || '').match(/[^\\n\\r]+\\.pdf/i);
        if (m) { seen.add(id); out.push({ id, name: m[0].trim() }); }
    }
    return out;
}"""


# --------------------------------------------------------------------------- #
# Capture helpers
# --------------------------------------------------------------------------- #


def decode_data_url(data_url: str) -> bytes:
    return base64.b64decode(data_url.partition(",")[2])


def png_bytes_to_jpeg(raw: bytes) -> bytes:
    """Flatten a screenshot onto white and re-encode as JPEG."""
    from PIL import Image

    im = Image.open(io.BytesIO(raw))
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        flat = Image.new("RGB", im.size, (255, 255, 255))
        flat.paste(im, mask=im.split()[-1])
        im = flat
    elif im.mode != "RGB":
        im = im.convert("RGB")
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=95, optimize=True)
    return buf.getvalue()


async def build_pdf(page_bytes: list[bytes], out_path: Path) -> None:
    """Assemble page images into a PDF (img2pdf keeps the images lossless)."""
    import img2pdf

    out_path.parent.mkdir(parents=True, exist_ok=True)
    data = await asyncio.to_thread(
        img2pdf.convert, [io.BytesIO(b) for b in page_bytes]
    )
    part = out_path.with_suffix(out_path.suffix + ".part")
    part.write_bytes(data)
    part.replace(out_path)  # atomic: never leave a truncated PDF behind


async def parse_total(page) -> int:
    try:
        return int(await page.evaluate(TOTAL_JS) or 0)
    except Exception:
        return 0


async def rendered_count(page) -> int:
    try:
        return int(await page.evaluate(COUNT_JS) or 0)
    except Exception:
        return 0


async def render_all_pages(page, log: Log, expected: int, budget_s: float) -> int:
    """Scroll until every page has rendered, or we run out of patience."""
    deadline = time.time() + budget_s
    seen, stale = 0, 0
    while time.time() < deadline:
        await page.evaluate(SCROLL_JS)
        await page.wait_for_timeout(320)
        n = await rendered_count(page)
        if n > seen:
            seen, stale = n, 0
        else:
            stale += 1
        if expected and seen >= expected:
            break
        if stale >= 12 and seen:
            break
    return seen


async def capture_engine_a(page, count: int, log: Log) -> list[bytes]:
    """In-page canvas -> JPEG data URL. Returns [] if unusable."""
    pages: list[bytes] = []
    for i in range(count):
        try:
            res = await page.evaluate(CANVAS_JS, i)
        except Exception as exc:
            log(f"    engine A aborted at page {i + 1}: {exc}")
            break
        if not isinstance(res, str) or not res.startswith("data:image/"):
            log(f"    engine A unusable at page {i + 1}: {str(res)[:70]}")
            return []
        pages.append(decode_data_url(res))
    return pages


async def capture_engine_b(page, count: int, log: Log) -> list[bytes]:
    """Fallback: screenshot each rendered page element onto white."""
    pages: list[bytes] = []
    for i in range(count):
        try:
            box = await page.evaluate(BOX_JS, i)
            if not box:
                log(f"    engine B: page {i + 1}/{count} not found")
                continue
            await page.wait_for_timeout(120)
            shot = await page.screenshot(clip={
                "x": max(0.0, box["x"]),
                "y": max(0.0, box["y"]),
                "width": box["width"],
                "height": box["height"],
            })
            pages.append(await asyncio.to_thread(png_bytes_to_jpeg, shot))
        except Exception as exc:
            log(f"    engine B aborted at page {i + 1}: {exc}")
            break
    return pages


async def fetch_one(browser, sem: asyncio.Semaphore, file_id: str, name: str,
                    out_dir: Path, log: Log, timeout_s: float) -> dict:
    """Download a single PDF and return a result dict for the verifier."""
    async with sem:
        result = {
            "id": file_id, "name": name, "expected": 0, "captured": 0,
            "status": "ERR", "detail": "", "path": out_dir / f"{name}.pdf",
        }
        ctx = await browser.new_context(user_agent=UA)
        page = await ctx.new_page()
        page.set_default_timeout(30_000)
        try:
            await page.goto(PREVIEW_URL.format(file_id=file_id), wait_until="load")
            await page.wait_for_timeout(2_200)
            result["expected"] = await parse_total(page)

            budget = max(90.0, (result["expected"] or 30) * 6.0, timeout_s / 4)
            count = 0
            for attempt in (1, 2, 3):
                count = await render_all_pages(page, log, result["expected"], budget)
                if not result["expected"] or count >= result["expected"]:
                    break
                log(f"    render attempt {attempt}: {count}/{result['expected']} pages, re-scanning")
                await page.evaluate(RESET_SCROLL_JS)
                await page.wait_for_timeout(600)

            target = result["expected"] or count
            if not target:
                result["status"] = "NO_PAGES"
                result["detail"] = "viewer never reported a page count"
                return result

            pages = await capture_engine_a(page, target, log)
            engine = "canvas"
            if not pages:
                log("    engine A failed, falling back to screenshots")
                pages = await capture_engine_b(page, target, log)
                engine = "screenshot"
            if not pages:
                result["status"] = "NO_CAPTURE"
                result["detail"] = "neither capture engine produced pages"
                return result

            result["captured"] = len(pages)
            await build_pdf(pages, result["path"])
            result["status"] = "OK"
            result["detail"] = engine
        except Exception as exc:
            result["status"] = "ERR"
            result["detail"] = f"{type(exc).__name__}: {exc}"
        finally:
            await ctx.close()

        if result["status"] == "OK":
            log(f"  ok    {name}  ({result['captured']}/{result['expected'] or '?'} pages, {result['detail']})")
        else:
            log(f"  FAIL  {name}  [{result['status']}] {result['detail']}")
        return result


async def list_files(page) -> list[dict]:
    """Every *.pdf row in the folder, in DOM order."""
    for _ in range(20):
        await page.mouse.wheel(0, 3000)
        await page.wait_for_timeout(250)
    return await page.evaluate(LIST_JS)


async def launch_browser(p, engine: str, headless: bool, log: Log):
    """Launch a browser: bundled Chromium first, then system Chrome.

    Headless needs no desktop session; if a headless launch fails we
    transparently retry headed.
    """
    attempts: list[tuple[str, dict]] = []
    if engine in ("auto", "chromium"):
        attempts.append(("bundled chromium", {"headless": headless}))
    system = find_chrome()
    if engine in ("auto", "chrome") and system:
        attempts.append((f"system chrome ({Path(system).name})",
                         {"executable_path": system, "headless": headless}))
    if headless:
        if engine in ("auto", "chromium"):
            attempts.append(("bundled chromium (headed)", {"headless": False}))
        if system and engine in ("auto", "chrome"):
            attempts.append(("system chrome (headed)", {"executable_path": system, "headless": False}))

    errors: list[str] = []
    for label, kwargs in attempts:
        try:
            browser = await p.chromium.launch(args=BROWSER_ARGS, **kwargs)
            log(f"browser: {label}, headless={kwargs.get('headless')}")
            return browser
        except Exception as exc:
            errors.append(f"{label}: {str(exc).splitlines()[0][:130]}")
    raise SystemExit(
        "Could not launch a browser.\n  "
        + "\n  ".join(errors)
        + "\n\nFix: run `python drive_pdf_downloader.py --setup`, or install Chrome."
    )


# --------------------------------------------------------------------------- #
# Verification, setup, main
# --------------------------------------------------------------------------- #


def verify(results: list[dict], log: Log) -> list[dict]:
    """Re-open each PDF and compare its page count with the viewer's count."""
    import pypdfium2 as pdfium

    log("=== verification ===")
    problems: list[dict] = []
    for r in sorted(results, key=lambda x: x["name"]):
        path = r["path"]
        if not path.exists():
            log(f"  MISSING  {path.name}  (viewer said {r['expected']} pages)  [{r['status']}] {r['detail']}")
            problems.append(r)
            continue
        try:
            pages = len(pdfium.PdfDocument(str(path)))
        except Exception as exc:
            log(f"  UNREAD   {path.name}  ({exc})")
            problems.append(r)
            continue
        mb = path.stat().st_size / 1024 / 1024
        expected = r["expected"] or 0
        if expected and pages < expected:
            log(f"  SHORT    {path.name}  {pages}/{expected} pages, {mb:.2f} MB")
            problems.append(r)
        else:
            log(f"  OK       {path.name}  {pages} pages, {mb:.2f} MB")
    log(f"verification: {len(results) - len(problems)} good, {len(problems)} problem")
    return problems


def run_setup(log: Log) -> None:
    """pip-install our deps and the Playwright Chromium build."""
    req = ROOT / "requirements.txt"
    log("installing Python dependencies ...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(req)], check=False)
    log("installing Playwright Chromium (used for headless mode) ...")
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=False)
    log("setup finished - run the downloader with: python drive_pdf_downloader.py")


async def amain(args: argparse.Namespace) -> int:
    log = Log(quiet=args.quiet)
    out_dir = Path(args.out).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    folder_id = resolve_folder_id(args.folder)

    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await launch_browser(p, args.engine, not args.headed, log)
        listing = await browser.new_page()
        listing.set_default_timeout(45_000)

        url = f"https://drive.google.com/drive/folders/{folder_id}"
        log("opening folder", url)
        await listing.goto(url, wait_until="load")
        await listing.wait_for_timeout(3_000)

        rows = await list_files(listing)
        if not rows:
            log("no PDF rows found - is the folder link shared publicly?")
            await browser.close()
            return 1
        log(f"found {len(rows)} PDF(s)")
        if args.list:
            for i, r in enumerate(rows, 1):
                log(f"  {i:>3}. {r['name']}")
            await browser.close()
            return 0
        await listing.close()

        targets = rows[: args.only] if args.only else rows
        sem = asyncio.Semaphore(max(1, args.workers))
        log(f"downloading {len(targets)} file(s), {args.workers} worker(s) -> {out_dir}")

        t0 = time.time()
        results = list(await asyncio.gather(*(
            fetch_one(browser, sem, r["id"], clean_name(r["name"]), out_dir, log, args.timeout)
            for r in targets
        )))
        log(f"download pass finished in {time.time() - t0:.1f}s")

        # ---- repair passes: retry anything missing or short --------------- #
        problems = verify(results, log)
        prev = len(problems)
        for attempt in range(1, args.retries + 1):
            if not problems:
                break
            log(f"=== repair pass {attempt}/{args.retries}: {len(problems)} file(s) ===")
            by_name = {r["name"]: r for r in results}
            for prob in problems:
                row = next((r for r in rows if clean_name(r["name"]) == prob["name"]), None)
                if row:
                    by_name[prob["name"]] = await fetch_one(
                        browser, sem, row["id"], prob["name"], out_dir, log, args.timeout
                    )
            results = list(by_name.values())
            problems = verify(results, log)
            if len(problems) >= prev:
                log("no further progress - stopping repair attempts")
                break
            prev = len(problems)

        await browser.close()

    good = len(results) - len(problems)
    log(f"done - {good}/{len(results)} PDFs saved to {out_dir}")
    if problems:
        log("unresolved: " + ", ".join(p["name"] for p in problems))
        return 2
    return 0


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        prog="drive_pdf_downloader",
        description="Download view-only Google Drive PDFs as clean image PDFs.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  python drive_pdf_downloader.py --setup\n"
            "  python drive_pdf_downloader.py --list\n"
            "  python drive_pdf_downloader.py --workers 4\n"
            "  python drive_pdf_downloader.py --folder 1OhkZja... --out ./pdfs\n"
        ),
    )
    ap.add_argument("--folder", default=DEFAULT_FOLDER, help="folder URL or folder id")
    ap.add_argument("--out", default=str(DEFAULT_OUT), help="output directory (default: ./downloads)")
    ap.add_argument("--workers", type=int, default=DEFAULT_WORKERS, help="concurrent downloads (default: 2)")
    ap.add_argument("--retries", type=int, default=DEFAULT_RETRIES, help="repair passes for short files (default: 2)")
    ap.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="per-file render budget in seconds (default: 600)")
    ap.add_argument("--engine", choices=["auto", "chromium", "chrome"], default="auto",
                    help="browser to drive (default: auto = bundled then system)")
    ap.add_argument("--headed", action="store_true", help="show the browser window (debugging)")
    ap.add_argument("--only", type=int, default=0, metavar="N", help="process only the first N files")
    ap.add_argument("--one", action="store_true", help="shorthand for --only 1")
    ap.add_argument("--list", action="store_true", help="list the PDFs found, then exit")
    ap.add_argument("--setup", action="store_true", help="install dependencies and exit")
    ap.add_argument("--quiet", action="store_true", help="only report problems")
    args = ap.parse_args(argv)
    if args.one:
        args.only = 1
    return args


def main() -> int:
    args = parse_args()
    if args.setup:
        run_setup(Log(quiet=args.quiet))
        return 0
    try:
        return asyncio.run(amain(args))
    except KeyboardInterrupt:
        print("\ninterrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
