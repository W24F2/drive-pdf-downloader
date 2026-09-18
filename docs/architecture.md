# Architecture

Reference notes for maintainers. User-facing explanation lives in the
[wiki › How it works](../wiki/How-It-Works.md).

## Shape of the program

One importable module, `drive_pdf_downloader.py`, with no local imports so it can be
vendored as a single file. Everything is `async` except the CPU-bound image work, which is
pushed to threads with `asyncio.to_thread`.

```
main()
└── asyncio.run(amain(args))
    ├── launch_browser()          # headless-first cascade, 2 engines × headed/headless
    ├── list_files()              # folder listing → [{id, name}]
    ├── asyncio.gather(           # bounded by asyncio.Semaphore(workers)
    │     fetch_one() × N
    │   )
    └── verify() → repair loop    # fetch_one() again for short/missing files
```

### `fetch_one()` — the unit of work

Each worker owns a fresh `BrowserContext` (not just a page), so cookies, storage and any
intermediate state from one document cannot leak into another.

```
new_context → goto(preview) → parse_total() → render_all_pages()
    → capture_engine_a()  ─┐
    → capture_engine_b()  ─┴─► build_pdf()  → atomic rename
```

Time budget: `max(90, expected_pages × 6, timeout/4)` seconds for the render loop, plus up
to three independent render attempts before giving up. A long document is therefore never
failed simply because it is long.

### Concurrency model

* `asyncio.Semaphore(workers)` bounds simultaneous documents (default 2).
* Playwright is single-threaded internally but multiplexes many pages over one browser
  process, so one `browser` is shared, with a context per document.
* Retry/repair work reuses the same semaphore, so a repair pass cannot exceed the
  configured concurrency either.

### Why the JS lives in constants

`COUNT_JS`, `TOTAL_JS`, `SCROLL_JS`, `RESET_SCROLL_JS`, `CANVAS_JS`, `BOX_JS`, `LIST_JS` are
module-level strings. They are tiny, reviewed, and injected via `page.evaluate(code, arg)` —
never `eval` of page content. Keeping them as constants makes them greppable and diffable.

`MIN_PAGE_PX` (200) is interpolated into four of them. It exists because Drive's own UI
contains small blob images (thumbnails, icons); filtering by `naturalWidth` is what makes
"page N" mean the same thing in every engine.

## Failure taxonomy

| Status | Raised when | Retried? |
| --- | --- | --- |
| `OK` | Pages captured and written | — |
| `SHORT` | Saved page count < indicator (caught by `verify`) | ✅ |
| `MISSING` | Expected file absent (caught by `verify`) | ✅ |
| `UNREAD` | Saved PDF will not open | ✅ |
| `NO_PAGES` | Viewer never reported a page count | ✅ (via repair) |
| `NO_CAPTURE` | Both engines returned zero pages | ✅ (via repair) |
| `ERR` | Exception; `detail` carries `Type: message` | ✅ (via repair) |

`verify()` is the single source of truth for success: it reopens what is actually on disk
rather than trusting what the capture step claimed. The repair loop stops as soon as a pass
fails to reduce the problem count, which guarantees termination.

## Adding a third capture engine

1. Write the JS as a constant returning either a data URL string or a DOM rect.
2. Add a `capture_engine_c(page, count, log) -> list[bytes]` following the existing
   signatures: return `[]` on any unusable condition so the caller can fall through.
3. Chain it in `fetch_one()`: `a or b or c`.
4. Log which engine won — `verify()` output and the README table rely on that string.

## Testing approach

There are no unit tests for the browser interaction, because the DOM it depends on belongs
to Google and changes without notice. Instead:

* CI tests the **deterministic** parts: `clean_name`, `resolve_folder_id`, `chrome_candidates`,
  CLI parsing, import health (3 OS × 2 Python versions).
* A real end-to-end check is a documented manual step:
  `python drive_pdf_downloader.py --only 2 --out /tmp/smoke`, then confirm the printed page
  counts match the viewer.
* If you want a fixture-based test, **generate** a PDF rather than downloading one, and keep
  it out of the repository (see `.gitignore`).

## Deliberate non-features

* **No profile/cookie support.** Chrome refuses remote debugging on its default profile, and
  link-shared files need no session. Supporting credentials would add a large attack surface
  for a use case the tool does not need.
* **No recursion into subfolders.** Listing semantics differ per share type, and a recursive
  crawl multiplies request volume — the opposite of the tool's "be polite" stance.
* **No CAPTCHA handling.** If Drive challenges the session, the correct behaviour is to fail
  and tell the user, not to escalate.
