#!/usr/bin/env python3
"""Print a Markdown inventory of downloaded PDFs (used by CI job summaries).

    python scripts/ci_inventory.py downloads >> "$GITHUB_STEP_SUMMARY"
"""

from __future__ import annotations

import glob
import os
import sys
from pathlib import Path


def main() -> int:
    directory = Path(sys.argv[1] if len(sys.argv) > 1 else "downloads")
    files = sorted(glob.glob(str(directory / "*.pdf")))
    parts = sorted(glob.glob(str(directory / "*.pdf.part")))

    print("### Downloaded PDFs")
    print()
    if not files:
        print("_No PDFs were downloaded._")
        if parts:
            print()
            print(f"_{len(parts)} incomplete `.pdf.part` file(s) were left behind._")
        return 0

    try:
        import pypdfium2 as pdfium
    except ImportError:  # pragma: no cover - CI always installs it
        print(f"_{len(files)} file(s) (pypdfium2 unavailable, page counts skipped)_")
        return 0

    total_mb = 0.0
    total_pages = 0
    print("| file | pages | MB |")
    print("| --- | ---: | ---: |")
    for path in files:
        name = os.path.basename(path)
        mb = os.path.getsize(path) / 1048576
        total_mb += mb
        try:
            pages = len(pdfium.PdfDocument(path))
        except Exception as exc:
            print(f"| `{name}` | _unreadable: {exc}_ | {mb:.2f} |")
            continue
        total_pages += pages
        print(f"| `{name}` | {pages} | {mb:.2f} |")
    print(f"| **{len(files)} files** | **{total_pages}** | **{total_mb:.2f}** |")

    if parts:
        print()
        print(f"> ⚠️ {len(parts)} incomplete `.pdf.part` file(s) were left behind.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
