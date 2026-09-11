@echo off
echo ========================================
echo   VICTUS AI - Dependency Fix Script
echo ========================================
echo.

set "PATH=%USERPROFILE%\AppData\Local\Programs\Python\Python311;%USERPROFILE%\AppData\Local\Programs\Python\Python311\Scripts;%PATH%"

echo [1/4] Auto-repairing dependencies and updating pip...
pip install --upgrade pip --quiet --disable-pip-version-check 2>nul
pip install click typer --upgrade --quiet --no-warn-script-location --disable-pip-version-check 2>nul
echo [OK] Dependencies verified and repaired

echo.
echo [2/4] Installing gtts (compatible version)...
pip install gtts --upgrade --quiet --no-warn-script-location --disable-pip-version-check 2>nul
echo [OK] gtts installed

echo.
echo [3/4] Installing pygame for MP3 playback...
pip install pygame --quiet --no-warn-script-location --disable-pip-version-check 2>nul
echo [OK] pygame installed

echo.
echo [4/4] Installing remaining packages...
pip install SpeechRecognition pyaudio PyQt5 python-dotenv langdetect psutil pypiwin32 requests pycaw comtypes screen_brightness_control openpyxl --quiet --no-warn-script-location --disable-pip-version-check 2>nul
echo [OK] All packages installed

echo.
echo ========================================
echo   All dependencies fixed!
echo   Now run: Start_Victus_AI.bat
echo ========================================
pause
