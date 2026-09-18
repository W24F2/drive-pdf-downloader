# How it works

This page documents the mechanism, because every step exists to fix a specific,
observed failure mode. If you are adapting this tool, read this first.

## The core idea

A PDF shared as **view only** cannot be downloaded through Drive's UI. But Drive's
preview viewer must still show you the document — and it does so by rendering each
page into an `<img>` whose `src` is a `blob:` URL minted in the page:

```html
<img src="blob:https://drive.google.com/2f4c…" width="1200" height="1697">
```

Those images are the document. Capture all of them, in order, and you have the PDF.

## Where the page images live

The important subtlety: **the blob images are in the top-level document**, not inside
the preview iframe. Drive also embeds a sandboxed iframe (with a reCAPTCHA when it
suspects automation), which is why a naïve `document.querySelectorAll` from the wrong
frame finds nothing. A page-level `page.evaluate(...)` sees them.

Verification step:

```js
document.querySelectorAll('img[src^="blob:"]').length   // → 3 initially, 56 after scrolling
```

## Why `fetch(blobUrl)` does not work

Tempting shortcut: `fetch()` each blob and read the bytes. It fails.

The blob is minted inside a **sandboxed, opaque-origin** context. Reading it from
another origin is blocked, and `fetch` of a `blob:` URL that isn't same-origin throws.
So the tool never fetches blobs — it lets the browser rasterise them:

* **Engine A** draws the `<img>` onto a `<canvas>` in-page and returns
  `canvas.toDataURL('image/jpeg')`. The canvas is not tainted for this case, because
  the image is same-origin to the document that owns the canvas.
* **Engine B** scrolls the `<img>` into view and takes a clipped screenshot of exactly
  its bounding box.

## Why pages must be scrolled before capture

Drive virtualises the document: only pages near the viewport are painted. A freshly
loaded 56-page PDF reports just 3 images. The tool therefore:

1. Parses the viewer's own indicator — `"Page 1 of 56"`, rendered as an editable
   `1 / 56` field — to learn the true total.
2. Scrolls the **viewer's inner scroll container** until `blob` image count ≥ total.

Scrolling the *window* does nothing (`window.scrollBy` is a no-op here): the viewer
lives in its own overflow container. The tool locates it by walking up from a page
image and picking the ancestor with the largest `scrollHeight - clientHeight`:

```js
let el = imgs[0].parentElement, best = null, max = 0;
while (el) {
    const d = el.scrollHeight - el.clientHeight;
    if (d > max) { max = d; best = el; }
    el = el.parentElement;
}
best.scrollTop += best.clientHeight * 0.9;
```

Observed geometry on a 56-page document: `scrollHeight ≈ 64 232`, `clientHeight ≈ 720`.

## Why the earlier versions produced black spots

Early versions re-encoded pages in Python:

```python
im = Image.open(io.BytesIO(raw))
im = im.convert("RGB")          # ← alpha channel dropped, becomes BLACK
```

The rendered page PNGs have **transparent margins**. Dropping alpha to RGB makes
`(0,0,0,0)` become `(0,0,0)` — opaque black. Any page with transparency therefore
arrives peppered with black rectangles.

The fix is to composite onto **white** instead. In-page:

```js
x.fillStyle = '#FFFFFF';
x.fillRect(0, 0, c.width, c.height);   // white underlay first
x.drawImage(img, 0, 0);
```

and in the Pillow fallback path:

```python
flat = Image.new("RGB", im.size, (255, 255, 255))
flat.paste(im, mask=im.split()[-1])
```

Verification: average luminance of output pages is ~248/255 with ≤0.4 % near-black
pixels (ordinary ink), versus blotchy dark regions before the fix.

## Why there is no jsPDF / Node.js dependency

The widely-shared console snippet builds the PDF in the browser with jsPDF. That
requires injecting a 1.2 MB library *into* a page that enforces a Trusted-Types policy
(`script.textContent` is rejected) and then capturing a browser download — a fragile
trio of CSP, Trusted Types and download-event handling.

Since Python can read a data URL perfectly well, the PDF is assembled in Python with
`img2pdf`, which performs **lossless image passthrough** (it embeds the JPEG bytes
directly — no re-encode, no quality loss, and it is fast). That removes Node.js, jsPDF,
CDN access, CSP interactions and download capture from the equation entirely.

## Why the writes are atomic

```python
part = out_path.with_suffix(".pdf.part")
part.write_bytes(data)
part.replace(out_path)
```

A crash or a `Ctrl-C` mid-run leaves `.part` files, never a truncated `.pdf` that looks
like a finished document.

## Verification

After the download pass, each PDF is reopened with `pypdfium2` and its page count
compared with the indicator captured during rendering:

```
OK       file.pdf  56 pages, 10.37 MB
SHORT    file.pdf  41/56 pages, 8.10 MB     ← triggers a repair pass
MISSING  file.pdf  (viewer said 28 pages)
```

Anything `SHORT`, `MISSING` or `UNREAD` is retried up to `--retries` times. The repair
loop stops early if a pass makes no progress, so a permanently broken file cannot spin
forever.

## Browser selection

Preferred order (all headless first, then headed):

1. Playwright's bundled Chromium (`python -m playwright install chromium`)
2. System Chrome / Chromium / Edge, auto-discovered per OS
3. Same two, **headed** — some sandboxed environments refuse headless pipes

Note that Chrome refuses `--remote-debugging-port` on its *default* profile directory,
which is why this tool launches a throwaway context instead of reusing your profile. The
upside: **no sign-in and no cookies are required** for link-shared files, so nothing of
yours is ever handed to the browser session.
