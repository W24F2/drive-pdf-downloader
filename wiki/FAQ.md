# FAQ

**Does this need my Google account or cookies?**
No. Link-shared ("anyone with the link") files render in the preview viewer anonymously.
The tool launches a throwaway browser context and never touches your profile, your
cookies, or your login. That is also why it works the same on a server with no Google
session. If a folder is *not* link-shared, this tool cannot list it — that is by design.

**Is this "bypassing" Google's protections?**
It reads pages the viewer renders for you anyway. It does not forge credentials, defeat
authentication, or solve CAPTCHAs. Whether that is acceptable for your use is a legal and
ethical question — see [Legal-and-Ethics](Legal-and-Ethics.md).

**Why are the pages images instead of real text?**
Because a view-only document is never released as a file. There is no text layer to
recover. Run `ocrmypdf` on the results if you need selectable text or search.

**Does the output keep the original quality?**
Yes, up to what the viewer serves. Engine A re-encodes as JPEG q=0.95 at the exact pixels
the viewer rendered; `img2pdf` embeds those bytes without further re-encoding. For
ordinary documents (equations, prose, diagrams) the result is visually identical. Engine B
is a screenshot and is slightly softer.

**How big are the files?**
~2–8 MB for a typical exam paper, up to ~12 MB for 80 pages. Images are inherently larger
than a text PDF.

**Can I download a whole Shared Drive, or subfolders?**
Subfolders are not recursed. Point `--folder` at each one, or run the tool in a loop.

**Can I keep the documents out of my git history?**
Yes — `.gitignore` already excludes `downloads/`, `*.pdf` and profile directories. Do not
remove those lines; committing other people's documents is exactly what this project must
not do.

**How fast is it?**
About 2–4 seconds per page, dominated by scrolling that forces Drive to render. A
19-document, 650-page folder took ~2 minutes with 2 workers and ~1 minute with 4.

**Why 2 workers by default instead of 8?**
Each worker is a fully rendered browser page consuming real memory and Drive bandwidth.
2 is polite and stable; 4 is a reasonable ceiling. Higher values mostly buy you throttling
and `SHORT` files.

**Can it handle password-protected or encrypted PDFs?**
No. Drive cannot preview those either.

**Does it work for presentations or Word docs?**
The mechanism generalises (Drive renders those too), but only `.pdf` rows are collected
here. Change the regex in `LIST_JS` if you want to experiment — just make sure the
rasterised pages still make sense.

**It says SHORT even though the document looks fine.**
Verify by hand: open the PDF and compare the last page with the viewer's last page. If page
counts differ, the document genuinely is missing pages — re-run. If the counts match, the
indicator parse picked up the wrong number; please open an issue with the log and the
document's indicator text.

**Which browsers are supported?**
Chrome, Chromium and Microsoft Edge, plus Playwright's bundled Chromium. Firefox is not
supported: its blob/origin behaviour differs and Drive's viewer is Chromium-targeted.

**Is there an API or library mode?**
`drive_pdf_downloader.py` is importable — `asyncio.run(amain(parse_args([...])))` gives you
full programmatic control. It is a single file with no local imports, so vendoring it is
trivial.
