@echo off
rem ---------------------------------------------------------------------------
rem  drive-pdf-downloader - double-click launcher for Windows.
rem  Requires scripts\setup_windows.ps1 to have been run once.
rem  Any arguments are forwarded to drive_pdf_downloader.py.
rem ---------------------------------------------------------------------------
setlocal
set "ROOT=%~dp0.."
set "PY=%ROOT%\.venv\Scripts\python.exe"

if not exist "%PY%" (
    echo.
    echo   Not set up yet.
    echo   Run this first:  powershell -ExecutionPolicy Bypass -File "%~dp0setup_windows.ps1"
    echo.
    pause
    exit /b 1
)

"%PY%" "%ROOT%\drive_pdf_downloader.py" %*
set "RC=%ERRORLEVEL%"

if not "%RC%"=="0" (
    echo.
    echo   Finished with exit code %RC%. Scroll up for details.
    pause
) else (
    echo.
    echo   Done. PDFs are in "%ROOT%\downloads".
    pause
)
exit /b %RC%
