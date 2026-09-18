# Security policy

## Scope

`drive-pdf-downloader` is a local automation tool: a Python script that drives a headless
browser against public or link-shared Google Drive pages. The realistic attack surface is
small, but worth stating.

### By design, this tool

* **never** asks for, stores or transmits your Google credentials or cookies;
* **never** reuses your browser profile — it launches a throwaway context;
* **never** writes outside `--out` and its own temporary files (`*.pdf.part`);
* **never** executes code from the pages it visits (it only evaluates its own small,
  hard-coded JS snippets in the page context);
* **never** phones home. There is no telemetry, no analytics, no update check.

### Out of scope

* **The security of the sites it visits.** It reads whatever the Drive viewer renders.
  Documents are rendered, not parsed, so a malicious PDF cannot exploit a PDF parser here —
  but it *is* loaded by your browser.
* **The documents you download.** They are images of untrusted content. Open them with the
  same caution you would apply to any downloaded file.

## Supported versions

Only the latest release is supported for security fixes.

| Version | Supported |
| --- | --- |
| 2.x | ✅ |
| 0.x – 1.x | ❌ (superseded, do not use) |

## Reporting a vulnerability

Please **do not** open a public issue for a security problem.

Open a [private security advisory](https://github.com/W24F2/drive-pdf-downloader/security/advisories/new)
or contact the maintainer via the address on their GitHub profile. Include:

1. what an attacker could achieve,
2. the smallest reproduction you can manage,
3. the affected version and platform,
4. whether you are willing to be credited.

**Response expectations:** acknowledgement within about 7 days; a fix or a documented
decision within 30. This is a volunteer project — no bug bounty, but credit in the
changelog if you want it.

## Hardening your own usage

If you run this in automation:

* keep the default low `--workers`; nothing here needs to be fast enough to look like abuse;
* run it as an unprivileged user, with `--out` pointing at a directory that user owns;
* never pass an untrusted folder id from an untrusted source — it decides what gets fetched;
* treat the output directory as untrusted input for whatever consumes it next.

## Dependency notes

Four runtime dependencies: `playwright`, `Pillow`, `img2pdf`, `pypdfium2`. Pinning to a
known-good lockfile in your own deployment is recommended; `requirements.txt` uses
compatible-release bounds so security patches can flow in.

Optionally, `python -m pip install pip-audit && pip-audit -r requirements.txt` to check for
known CVEs in your environment.
