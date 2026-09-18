---
name: Bug report
about: Something downloaded wrong, or did not download at all
title: "[bug] "
labels: bug
assignees: ""
---

## What happened

<!-- A clear description. If pages are missing, say how many. -->

## What you expected

<!-- e.g. "56-page PDF matching the Drive viewer" -->

## Page counts

| | Count |
| --- | --- |
| Pages the Drive viewer shows (`x / y` indicator) | |
| Pages the written PDF has | |

## Your command

```console
# paste the exact command
python drive_pdf_downloader.py ...
```

## Log output

<!-- Full output. Re-run with --headed --one if you can spare 30 seconds. -->

```
paste here
```

## Environment

| | |
| --- | --- |
| OS and version | <!-- e.g. Windows 11 23H2 / macOS 14.5 / Ubuntu 24.04 --> |
| Python (`python -V`) | |
| Installed version | <!-- `python -c "import drive_pdf_downloader"` or the release tag --> |
| Browser used | <!-- from the "browser:" log line: bundled chromium or system chrome --> |
| `--workers` value | |

## Checklist

- [ ] I ran `python drive_pdf_downloader.py --list` and it found the files
- [ ] I tried `--one --headed` and watched it
- [ ] The output PDF actually has a wrong page count (not just slow)
- [ ] I am not attaching the downloaded document itself
