# Automation

Everything here assumes a checkout with `.venv` set up (run the appropriate
`scripts/setup_*` script once).

Useful flags for unattended runs:

* `--quiet` — log only problems
* `--out DIR` — write somewhere specific (e.g. a dated folder)
* exit code `2` — "some files are short/missing", so your job can alert

---

## Windows — Task Scheduler

```powershell
schtasks /create /tn "DrivePDF" ^
  /tr "powershell -ExecutionPolicy Bypass -File C:\tools\drive-pdf-downloader\scripts\run_windows.ps1 -Quiet" ^
  /sc daily /st 03:00
```

Test it without waiting for 03:00:

```powershell
schtasks /run /tn "DrivePDF"
```

Output goes to the configured `--out` (`./downloads` by default). Change the schedule with
`schtasks /change`.

---

## macOS — launchd

`~/Library/LaunchAgents/com.me.drivepdf.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.me.drivepdf</string>
  <key>ProgramArguments</key>
  <array>
    <string>/Users/me/tools/drive-pdf-downloader/scripts/run_macos.sh</string>
    <string>--quiet</string>
  </array>
  <key>WorkingDirectory</key><string>/Users/me/tools/drive-pdf-downloader</string>
  <key>StartCalendarInterval</key>
  <dict><key>Hour</key><integer>3</integer><key>Minute</key><integer>0</integer></dict>
  <key>StandardOutPath</key><string>/tmp/drivepdf.log</string>
  <key>StandardErrorPath</key><string>/tmp/drivepdf.err</string>
</dict>
</plist>
```

```bash
launchctl load  ~/Library/LaunchAgents/com.me.drivepdf.plist
launchctl start com.me.drivepdf          # run now
launchctl unload ~/Library/LaunchAgents/com.me.drivepdf.plist
```

---

## Linux — cron

```bash
crontab -e
```

```cron
# every day at 03:00, into a dated folder, log rotated weekly
0 3 * * * cd /opt/drive-pdf-downloader && \
  ./.venv/bin/python drive_pdf_downloader.py --quiet \
  --out "/srv/archive/$(date +\%F)" >> /var/log/drivepdf.log 2>&1
```

Note the escaped `\%` — cron treats `%` specially.

## Linux — systemd timer

`/etc/systemd/system/drivepdf.service`:

```ini
[Unit]
Description=Archive Google Drive PDF folder
After=network-online.target

[Service]
Type=oneshot
User=archive
WorkingDirectory=/opt/drive-pdf-downloader
ExecStart=/opt/drive-pdf-downloader/.venv/bin/python drive_pdf_downloader.py --quiet --out /srv/archive
```

`/etc/systemd/system/drivepdf.timer`:

```ini
[Unit]
Description=Daily Drive PDF archive

[Timer]
OnCalendar=*-*-* 03:00:00
Persistent=true
RandomizedDelaySec=15m

[Install]
WantedBy=timers.target
```

```bash
sudo systemctl enable --now drivepdf.timer
systemctl list-timers drivepdf.timer       # confirm
journalctl -u drivepdf.service -n 50       # logs
```

`RandomizedDelaySec` is deliberate: it keeps a fleet of machines from hitting Drive at the
same second.

---

## GitHub Actions — no local machine at all

`.github/workflows/download.yml` ships with this repo.

1. Push the repo to GitHub.
2. **Actions → Download Google Drive PDFs → Run workflow.**
3. When it finishes, download the PDFs from the run's **Artifacts** section
   (retained 30 days).

The workflow:

* installs Python + dependencies + Playwright Chromium,
* runs the downloader with `--quiet --workers 4`,
* uploads `downloads/` as an artifact even when some files fail,
* fails the run if the exit code is `2`, so a broken archive is never silently "green".

To make it recurring, uncomment the `schedule:` block at the top of the workflow.

> ⚠️ **Before enabling a schedule on a public repo:** anyone can trigger a public
> workflow, and scheduled runs consume your Actions minutes on private repos. Point it at a
> folder you are entitled to archive, keep concurrency low, and prefer
> `workflow_dispatch` over `schedule` if the folder is private to you.

---

## CI on every push (three operating systems)

`.github/workflows/ci.yml` runs on Ubuntu, macOS and Windows and checks:

* byte-compilation (`python -m py_compile`),
* the CLI contract (`--help`, `--setup --help`),
* linting with `ruff` (config in `pyproject.toml`),
* that the module imports cleanly with all runtime dependencies installed.

It deliberately performs **no downloads** — CI should not hammer Drive.

---

## Publishing the wiki

`.github/workflows/publish-wiki.yml` mirrors the `wiki/` folder to the GitHub wiki whenever
anything under `wiki/**` is pushed, so the wiki can never drift from the versioned Markdown. It can
also be run by hand from **Actions → Publish wiki → Run workflow**.

**One-time prerequisite.** GitHub does not create the `<repo>.wiki.git` storage until the *first*
page is saved through the web UI, and there is no API that can do it. Every wiki-publishing tool has
the same limitation. Do this once:

1. open <https://github.com/W24F2/drive-pdf-downloader/wiki>
2. click **Create the first page**
3. type anything and press **Save Page**

From then on the workflow keeps it in sync — or run `./scripts/publish_wiki.sh`
(`.\scripts\publish_wiki.ps1` on Windows) locally, which prints that same link and waits for you to
click it before publishing every page in one go. The workflow reports a *warning*, not a failure,
while the wiki is still uninitialised.

---

## Monitoring your job

* Check exit code `2` — that means "finished, but something is incomplete".
* Pipe `--quiet` output to your alerting: it prints only `MISSING`/`SHORT`/`UNREAD`/`FAIL`
  lines plus the summary.
* Compare the number of PDFs in `downloads/` with what `--list` reports; a drop usually
  means the folder's sharing changed.

```bash
#!/usr/bin/env bash
set -euo pipefail
cd /opt/drive-pdf-downloader
if ! ./.venv/bin/python drive_pdf_downloader.py --quiet --out /srv/archive; then
  curl -fsS -m 10 -X POST "https://ntfy.sh/my-drivepdf-topic" \
    -d "Drive PDF archive failed - check /var/log/drivepdf.log"
fi
```
