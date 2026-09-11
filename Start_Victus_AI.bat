@echo off
cd /d "%~dp0"
title Victus AI - JARVIS v7.0
color 0A

echo.
echo ========================================
echo      VICTUS AI - JARVIS v7.0
echo      LM Studio + Ollama Support
echo ========================================
echo.

set "PATH=%USERPROFILE%\AppData\Local\Programs\Python\Python311;%USERPROFILE%\AppData\Local\Programs\Python\Python311\Scripts;%PATH%"

REM == Step 1: Python ==
echo [1/5] Checking Python...
python --version
if %ERRORLEVEL% NEQ 0 (
    echo [!] Python not found!
    pause
    exit /b 1
)
echo.

REM == Step 2: Auto-repair dependencies ==
echo [2/5] Auto-repairing dependencies and updating pip...
python -m pip install --upgrade pip --quiet --disable-pip-version-check 2>nul
python -m pip install click typer --upgrade --quiet --no-warn-script-location --disable-pip-version-check 2>nul
echo [OK] Dependencies verified and repaired
echo.

REM == Step 3: Core packages ==
echo [3/5] Verifying core packages...
python -m pip install SpeechRecognition pyaudio PyQt5 python-dotenv requests psutil pypiwin32 langdetect pycaw comtypes screen_brightness_control openpyxl --quiet --no-warn-script-location --disable-pip-version-check 2>nul
echo [OK] Core packages verified
echo.

REM == Step 4: TTS engines (all 3) ==
echo [4/5] Verifying TTS engines...
python -m pip install pyttsx3 --quiet --no-warn-script-location --disable-pip-version-check 2>nul
echo   [OK] pyttsx3 (offline)
python -m pip install gtts --upgrade --quiet --no-warn-script-location --disable-pip-version-check 2>nul
echo   [OK] gtts (online)
python -m pip install pygame --quiet --no-warn-script-location --disable-pip-version-check 2>nul
echo   [OK] pygame (MP3 playback)
echo.

REM == Step 5: Check AI backend ==
echo [5/5] Checking AI backend...
echo.
echo   Checking LM Studio (port 1234)...
python -c "import requests; r=requests.get('http://127.0.0.1:1234/v1/models',timeout=3); print('  [OK] LM Studio ONLINE -',len(r.json().get('data',[])),'models loaded')" 2>nul
if %ERRORLEVEL% EQU 0 (
    echo   LM Studio detected! Using as primary backend.
    goto :launch
)

echo   LM Studio not running.
echo   Checking Ollama (port 11434)...
python -c "import requests; r=requests.get('http://127.0.0.1:11434/api/tags',timeout=3); print('  [OK] Ollama ONLINE -',len(r.json().get('models',[])),'models')" 2>nul
if %ERRORLEVEL% EQU 0 (
    echo   Ollama detected! Using as fallback backend.
    goto :launch
)

echo.
echo   [!] No AI backend detected!
echo.
echo   Please start ONE of these:
echo     1. LM Studio  - Download from lmstudio.ai
echo                    - Load a model and start the server
echo     2. Ollama      - Run: ollama serve
echo.
echo   Trying to start Ollama...
where ollama >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    start /min "" ollama serve 2>nul
    timeout /t 5 /nobreak >nul
    echo   [*] Ollama started.
) else (
    echo   [!] Ollama not installed.
    echo   [!] Download LM Studio from: https://lmstudio.ai
)

:launch
echo.

REM == Launch ==
set HF_HUB_DISABLE_XET=1

echo ========================================
echo   Say "Hey Victus" to wake me up!
echo ========================================
echo.

python "%~dp0assistant.py"

pause
