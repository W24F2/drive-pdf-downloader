# drive-pdf-downloader wiki

Welcome. This wiki is the long-form companion to the [README](../README.md).

## Pages

| Page | What's in it |
| --- | --- |
| **[Installation](Installation.md)** | Windows, macOS, Linux and Docker-style setups, plus the manual path |
| **[Usage](Usage.md)** | Every CLI flag, recipes, exit codes, output layout |
| **[How-It-Works](How-It-Works.md)** | The viewer DOM, why pages must be scrolled, why transparency caused black spots |
| **[Automation](Automation.md)** | cron, launchd, Task Scheduler, GitHub Actions, systemd timers |
| **[Troubleshooting](Troubleshooting.md)** | Every error you are likely to hit, and the fix |
| **[FAQ](FAQ.md)** | Sign-in, OCR, quality, speed, ethics of "view only" |
| **[Legal-and-Ethics](Legal-and-Ethics.md)** | What this tool is for, and what it is not |

## TL;DR

```bash
git clone https://github.com/W24F2/drive-pdf-downloader.git
cd drive-pdf-downloader
# Windows:  .\scripts\setup_windows.ps1    then  .\scripts\run_windows.ps1
# macOS:    ./scripts/setup_macos.sh       then  ./scripts/run_macos.sh
# Linux:    ./scripts/setup_linux.sh       then  ./scripts/run_linux.sh
```

PDFs land in `./downloads/`, each one page-count-verified against the viewer.
