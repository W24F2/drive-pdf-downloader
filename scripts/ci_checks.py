#!/usr/bin/env python3
"""Dependency-light assertions used by CI to protect the deterministic parts.

Run:  python scripts/ci_checks.py

These cover the behaviour that must not regress across platforms: name
preservation, folder-input validation and CLI parsing. The browser interaction is
deliberately not tested here (CI must not hammer Google Drive) - use
`python drive_pdf_downloader.py --only 2 --out /tmp/smoke` for that.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import drive_pdf_downloader as m  # noqa: E402  (path set up above)

# These checks print non-Latin test labels. On a legacy Windows console (cp1252)
# that used to abort the whole run with UnicodeEncodeError on the first one, so
# the very fix being tested here is applied first.
m.enable_utf8_output()

failures: list[str] = []


def check(label: str, condition: bool, detail: object = "") -> None:
    status = "ok  " if condition else "FAIL"
    print(f"  {status} {label}" + ("" if condition else f"  <- {detail!r}"))
    if not condition:
        failures.append(label)


def main() -> int:
    print("name sanitiser (fallback only)")
    check("strips .pdf", m.clean_name("x.pdf") == "x")
    check("replaces illegal characters", m.clean_name("a/b:c*d?.pdf") == "a_b_c_d_")
    check("never returns empty", m.clean_name("") == "document")
    check("truncates long names", len(m.clean_name("x" * 400)) <= 120)

    print("output_name preserves the original verbatim")
    verbatim = [
        "PDF2026 Blacktown Boys High School - S2 - Trial.pdf",
        "PDFcssa sol.pdf",
        "PDFindep 2026.pdf",
        "Report (Final) v2 - 2026.pdf",
        "Unicode 数学 - Ext 1.pdf",
        "dots.in.the.name.v1.2.pdf",
    ]
    for name in verbatim:
        out, why = m.output_name(name)
        check(f"verbatim: {name}", out == name and why is None, (out, why))
    check("adds a missing extension", m.output_name("no-extension") == ("no-extension.pdf", None))
    check("trims surrounding whitespace", m.output_name("  spaced.pdf  ")[0] == "spaced.pdf")

    # Regression guard: a legacy console codepage must not be able to abort a run
    # half way through, once the files are already on disk.
    print("console encoding")
    enc = getattr(sys.stdout, "encoding", None) or "utf-8"
    try:
        "数学 ✓".encode(enc)
        encodable = True
    except (UnicodeEncodeError, LookupError):
        encodable = False
    check("stdout can carry non-Latin file names", encodable, enc)

    print("output_name sanitises only when it must, and says why")
    out, why = m.output_name('a/b:c*d?e"f<g>h|i.pdf')
    check("reports a reason", bool(why), why)
    check("result has no illegal characters", not any(c in out for c in '<>:"/\\|?*'), out)
    long_out, long_why = m.output_name("y" * 300 + ".pdf")
    check("long name is shortened", len(long_out) <= m.MAX_NAME_LEN + 4, len(long_out))
    check("long name reports a reason", bool(long_why), long_why)
    # Reserved device names only matter on Windows: there it must be sanitised,
    # elsewhere the name is perfectly usable and must stay untouched.
    con_out, con_why = m.output_name("CON.pdf")
    if sys.platform.startswith("win"):
        check("reserved device name is sanitised on Windows", bool(con_why), con_why)
        check("reserved name no longer reserved", con_out.split(".")[0].upper() not in m.RESERVED_NAMES, con_out)
    else:
        check("reserved-name rule is Windows-only", con_why is None, con_why)

    print("folder inputs")
    fid = "1OhkZjaNPP8InvTphuz-XaKGOly6NS-Iq"
    check("full URL", m.resolve_folder_id(f"https://drive.google.com/drive/u/0/folders/{fid}") == fid)
    check("URL without /u/0", m.resolve_folder_id(f"https://drive.google.com/drive/folders/{fid}") == fid)
    check("URL with query string",
          m.resolve_folder_id(f"https://drive.google.com/drive/folders/{fid}?usp=sharing") == fid)
    check("bare id", m.resolve_folder_id(fid) == fid)

    for bad in [
        f"https://drive.google.com/file/d/{fid}/view",  # single file, not a folder
        "not a folder at all",
        "",
        "   ",
    ]:
        try:
            m.resolve_folder_id(bad)
            check(f"rejects {bad!r}", False, "no ValueError raised")
        except ValueError:
            check(f"rejects {bad!r}", True)

    print("CLI parsing")
    args = m.parse_args([])
    check("folder defaults to None (so it prompts)", args.folder is None)
    check("no_input defaults to False", args.no_input is False)
    check("workers default is polite (<= 4)", args.workers <= 4, args.workers)
    check("--one implies --only 1", m.parse_args(["--one"]).only == 1)
    check("--folder is honoured",
          m.parse_args(["--folder", fid]).folder == fid)
    check("--no-input is honoured", m.parse_args(["--no-input"]).no_input is True)
    check("--engine chrome", m.parse_args(["--engine", "chrome"]).engine == "chrome")
    check("--out is honoured", m.parse_args(["--out", "./x"]).out == "./x")

    print("browser discovery returns absolute-looking candidates")
    cands = m.chrome_candidates()
    check("candidates exist for this OS", len(cands) > 0, cands)
    check("no empty entries", all(c.strip() for c in cands))
    check("find_chrome returns None or a real path",
          m.find_chrome() is None or Path(m.find_chrome()).exists(),
          m.find_chrome())

    print()
    if failures:
        print(f"{len(failures)} check(s) FAILED: " + ", ".join(failures))
        return 1
    print("all checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
