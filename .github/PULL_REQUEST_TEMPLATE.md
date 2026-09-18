## What this changes

<!-- One or two sentences. Link the issue it closes: "Closes #12". -->

## Why

<!-- The failure mode or need being addressed. If it is a bug fix, describe what broke. -->

## How it was tested

- [ ] `python -m py_compile drive_pdf_downloader.py`
- [ ] `python -m ruff check .`
- [ ] `python drive_pdf_downloader.py --help`
- [ ] `python drive_pdf_downloader.py --list`
- [ ] Real download: `python drive_pdf_downloader.py --only 2 --out /tmp/smoke`
      → page counts match the viewer for every file
- [ ] Windows / macOS / Linux (say which you actually ran)

## Checklist

- [ ] No documents, fixtures or profile data are added to the repository
- [ ] Verification is intact — an unverified PDF can still never be reported as success
- [ ] Defaults stay polite (concurrency, delays); no new credential handling
- [ ] `CHANGELOG.md` updated for user-visible changes
- [ ] Docs/README updated if behaviour or flags changed

## Notes for reviewers

<!-- Anything you are unsure about, or an alternative you rejected. -->
