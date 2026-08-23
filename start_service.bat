@echo off
setlocal EnableDelayedExpansion
title Manga AI Translator Studio — Turnkey Service Launcher

echo ======================================================================
echo   ⚡ Manga AI Translator Studio — Turnkey Service Launcher
echo ======================================================================
echo.

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

:: 1. Check Python Environment
echo [1/4] Checking Python 3.10+ installation...
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    where py >nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Python is not installed or not found in PATH.
        echo Please download and install Python 3.10+ from https://www.python.org/downloads/
        pause
        exit /b 1
    )
    set "SYS_PYTHON=py"
) else (
    set "SYS_PYTHON=python"
)

:: Check/Create Virtual Environment
if not exist "backend\venv\Scripts\python.exe" (
    echo [1/4] Creating virtual environment in backend\venv...
    %SYS_PYTHON% -m venv backend\venv
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to create Python virtual environment.
        pause
        exit /b 1
    )
    echo [1/4] Installing backend requirements...
    "backend\venv\Scripts\python.exe" -m pip install --upgrade pip
    "backend\venv\Scripts\pip.exe" install -r backend\requirements.txt
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to install backend dependencies.
        pause
        exit /b 1
    )
)
set "VENV_PYTHON=%SCRIPT_DIR%backend\venv\Scripts\python.exe"
echo [1/4] Python environment verified: %VENV_PYTHON%
echo.

:: 2. Check Node.js and Frontend Dependencies
echo [2/4] Checking Node.js and Frontend dependencies...
where node >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Node.js is not installed or not found in PATH.
    echo Please install Node.js 18+ from https://nodejs.org/
    pause
    exit /b 1
)

where npm >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] npm is not installed or not found in PATH.
    pause
    exit /b 1
)

if not exist "frontend\node_modules" (
    echo [2/4] Installing frontend npm packages (this may take a minute)...
    cd /d "%SCRIPT_DIR%frontend"
    call npm install
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to install frontend npm packages.
        cd /d "%SCRIPT_DIR%"
        pause
        exit /b 1
    )
    cd /d "%SCRIPT_DIR%"
)
echo [2/4] Frontend dependencies verified.
echo.

:: 3. Launch Backend and Frontend Services
echo [3/4] Launching FastAPI Backend on port 8000 and Next.js Frontend on port 3000...
start "Manga AI Translator - Backend (Port 8000)" /min cmd /c "cd /d \"%SCRIPT_DIR%backend\" && \"%VENV_PYTHON%\" server.py"
start "Manga AI Translator - Frontend (Port 3000)" /min cmd /c "cd /d \"%SCRIPT_DIR%frontend\" && npm run dev"
echo.

:: 4. Automated Healthcheck Polling via PowerShell
echo [4/4] Verifying services health status...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$backendOk = $false; $sw = [System.Diagnostics.Stopwatch]::StartNew();" ^
  "Write-Host '  -> Waiting for FastAPI Backend (http://localhost:8000/api/health)... ' -NoNewline;" ^
  "while ($sw.Elapsed.TotalSeconds -lt 45) {" ^
  "    try {" ^
  "        $res = Invoke-RestMethod -Uri 'http://localhost:8000/api/health' -TimeoutSec 2 -ErrorAction Stop;" ^
  "        if ($res.status -eq 'online' -or $res -ne $null) { $backendOk = $true; Write-Host '[ONLINE]' -ForegroundColor Green; break }" ^
  "    } catch { Start-Sleep -Milliseconds 500; Write-Host '.' -NoNewline }" ^
  "};" ^
  "if (-not $backendOk) { Write-Host ' [TIMEOUT/FAILED]' -ForegroundColor Red; exit 1 };" ^
  "$frontendOk = $false; $sw = [System.Diagnostics.Stopwatch]::StartNew();" ^
  "Write-Host '  -> Waiting for Next.js Web Studio (http://localhost:3000)... ' -NoNewline;" ^
  "while ($sw.Elapsed.TotalSeconds -lt 45) {" ^
  "    try {" ^
  "        $res = Invoke-WebRequest -Uri 'http://localhost:3000' -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop;" ^
  "        if ($res.StatusCode -eq 200 -or $res.StatusCode -eq 304) { $frontendOk = $true; Write-Host '[ONLINE]' -ForegroundColor Green; break }" ^
  "    } catch { Start-Sleep -Milliseconds 500; Write-Host '.' -NoNewline }" ^
  "};" ^
  "if (-not $frontendOk) { Write-Host ' [TIMEOUT/FAILED]' -ForegroundColor Red; exit 1 };"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [WARNING] One or more services timed out during startup health check.
    echo Please check the minimized backend and frontend console windows for error logs.
    echo.
) else (
    echo.
    echo ======================================================================
    echo   🚀 Manga AI Translator Studio is ONLINE and READY!
    echo ======================================================================
    echo   📡 FastAPI Backend API:   http://localhost:8000  (Docs: http://localhost:8000/docs)
    echo   🎨 Next.js Web Studio:    http://localhost:3000  (Reader & Dashboard)
    echo   📦 Chapter Storage:       backend\data\manga
    echo ======================================================================
    echo.
    echo Opening browser to http://localhost:3000...
    start http://localhost:3000
)

echo.
echo Press any key to close this launcher (background services will continue running)...
pause >nul
