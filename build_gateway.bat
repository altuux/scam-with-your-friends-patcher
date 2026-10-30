@echo off
setlocal
cd /d "%~dp0"

echo ========================================================
echo    Building SWYF-Gateway.exe with Nuitka (Standalone)
echo ========================================================
echo.

echo [*] Ensuring Nuitka and dependencies are installed...
python -m pip install --upgrade nuitka zstandard

echo.
echo [*] Compiling tools\cli.py into release\SWYF-Gateway.exe...
echo.

python -m nuitka --onefile --standalone --assume-yes-for-downloads --output-dir=release --output-filename=SWYF-Gateway.exe tools\cli.py

echo.
if exist "release\SWYF-Gateway.exe" (
    echo ========================================================
    echo  [SUCCESS] SWYF-Gateway.exe built successfully!
    echo  Location: release\SWYF-Gateway.exe
    echo ========================================================
) else (
    echo [-] Compilation failed. Please check the logs above.
)

pause
