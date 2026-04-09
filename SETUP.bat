@echo off
chcp 65001 >nul
title Robin - Ersteinrichtung

echo.
echo ================================================
echo   R O B I N - Ersteinrichtung
echo ================================================
echo.

:: Python pruefen
py -3.11 --version >nul 2>&1
if %errorlevel% neq 0 (
    python --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo [FEHLER] Python nicht gefunden!
        echo Bitte installiere Python 3.11 von https://python.org
        pause
        exit /b 1
    )
    set PY=python
) else (
    set PY=py -3.11
)

:: 1. Pakete installieren
echo [1/3] Installiere Python-Pakete...
%PY% -m pip install --upgrade pip
%PY% -m pip install -r "%~dp0requirements.txt"
echo.

:: 2. Ollama pruefen
echo [2/3] Pruefe Ollama...
ollama --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNUNG] Ollama nicht gefunden!
    echo Bitte installiere Ollama von https://ollama.com
    echo Danach: ollama pull llama3.2
) else (
    echo Ollama gefunden. Lade Modell...
)
echo.

:: 3. Piper Binary herunterladen
echo [3/3] Lade Piper TTS herunter...
if not exist "%~dp0piper" mkdir "%~dp0piper"
if not exist "%~dp0piper\piper\piper.exe" (
    echo   Lade piper.exe herunter ^(~30MB^)...
    %PY% -c "import urllib.request, zipfile, os; tmp=r'%~dp0piper\piper_win.zip'; urllib.request.urlretrieve('https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_windows_amd64.zip', tmp); print('  Entpacke...'); zipfile.ZipFile(tmp).extractall(r'%~dp0piper'); os.unlink(tmp); print('  piper.exe bereit!')"
) else (
    echo   piper.exe bereits vorhanden.
)

:: 4. Stimme herunterladen
if not exist "%~dp0piper-voice" mkdir "%~dp0piper-voice"
if not exist "%~dp0piper-voice\de_DE-thorsten-medium.onnx" (
    echo   Lade deutsche Stimme herunter ^(~63MB^)...
    %PY% -c "import urllib.request; urllib.request.urlretrieve('https://huggingface.co/rhasspy/piper-voices/resolve/main/de/de_DE/thorsten/medium/de_DE-thorsten-medium.onnx', r'%~dp0piper-voice\de_DE-thorsten-medium.onnx'); print('  Stimme heruntergeladen!')"
) else (
    echo   Stimme bereits vorhanden.
)
if not exist "%~dp0piper-voice\de_DE-thorsten-medium.onnx.json" (
    %PY% -c "import urllib.request; urllib.request.urlretrieve('https://huggingface.co/rhasspy/piper-voices/resolve/main/de/de_DE/thorsten/medium/de_DE-thorsten-medium.onnx.json', r'%~dp0piper-voice\de_DE-thorsten-medium.onnx.json'); print('  Stimm-Config heruntergeladen!')"
) else (
    echo   Stimm-Config bereits vorhanden.
)

echo.
echo ================================================
echo   Setup abgeschlossen!
echo.
echo   Starte Robin mit: START.bat
echo ================================================
echo.
pause
