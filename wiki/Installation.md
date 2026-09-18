# Installation

## Requirements

| | |
| --- | --- |
| **Python** | 3.9 or newer (`python -V`) |
| **Browser** | Chrome, Chromium, Edge — or let Playwright install its own Chromium |
| **OS** | Windows 10+, macOS 11+, or any modern Linux |
| **Disk** | ~400 MB for Playwright's Chromium (skip if you use system Chrome) |

No Node.js. No browser extension. No Google account.

## The easy path (recommended)

### Windows

```powershell
git clone https://github.com/W24F2/drive-pdf-downloader.git
cd drive-pdf-downloader
.\scripts\setup_windows.ps1
.\scripts\run_windows.ps1
```

If PowerShell blocks the script:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_windows.ps1
```

Double-click users: run `scripts\run_windows.bat` after setup (it pauses so you can read
the output).

### macOS

```bash
git clone https://github.com/W24F2/drive-pdf-downloader.git
cd drive-pdf-downloader
./scripts/setup_macos.sh
./scripts/run_macos.sh
```

No Python? `brew install python`.

### Linux

```bash
git clone https://github.com/W24F2/drive-pdf-downloader.git
cd drive-pdf-downloader
./scripts/setup_linux.sh
./scripts/run_linux.sh
```

Missing Python? `sudo apt install python3 python3-venv` (Debian/Ubuntu),
`sudo dnf install python3` (Fedora), `sudo pacman -S python` (Arch).

## Manual installation

```bash
git clone https://github.com/W24F2/drive-pdf-downloader.git
cd drive-pdf-downloader

python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m playwright install chromium        # optional if you have Chrome

python drive_pdf_downloader.py
```

## Self-installing

The tool can bootstrap its own dependencies:

```bash
python drive_pdf_downloader.py --setup
```

That runs `pip install -r requirements.txt` and `playwright install chromium`.
Use it from a fresh checkout when you do not want the helper scripts.

## Reusing an existing browser

Playwright's Chromium download is ~400 MB. If Chrome/Chromium/Edge is already installed,
skip it:

```bash
SKIP_BROWSER=1 ./scripts/setup_linux.sh      # macOS script accepts this too
```

```powershell
.\scripts\setup_windows.ps1 -SkipBrowser
```

The tool discovers browsers automatically on all three platforms, including
`google-chrome`, `chromium`, `chromium-browser`, `google-chrome-stable`, Microsoft Edge,
and the usual install paths.

## Installing as a command

The package is installable, which gives you a `drive-pdf-downloader` entry point:

```bash
python -m pip install .
drive-pdf-downloader --help
```

## Containers / CI

Playwright's official image already has the browser and system libraries:

```dockerfile
FROM mcr.microsoft.com/playwright/python:v1.47.0-jammy
WORKDIR /app
COPY requirements.txt ./
RUN pip install -r requirements.txt
COPY drive_pdf_downloader.py ./
CMD ["python", "drive_pdf_downloader.py", "--quiet", "--out", "/out"]
```

```bash
docker build -t drive-pdf-downloader .
docker run --rm -v "$PWD/out:/out" drive-pdf-downloader
```

Headless works with no display. If a bare (non-Playwright) image complains about missing
libraries, run `python -m playwright install-deps chromium` with root, or prefix the run
with `xvfb-run -a`.

## Uninstalling

```bash
rm -rf .venv downloads            # PowerShell: Remove-Item -Recurse -Force .venv, downloads
```
