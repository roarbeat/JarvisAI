@echo off
chcp 65001 >nul
title R O B I N - System Terminal
cd /d "%~dp0"

echo ==================================================
echo   R O B I N - Lokaler KI-Sprachassistent
echo ==================================================
echo.

:: Ollama im Hintergrund starten, falls nicht aktiv
tasklist /FI "IMAGENAME eq ollama.exe" 2>NUL | find /I "ollama.exe" >NUL
if errorlevel 1 (
    echo  [System] Starte Ollama-Server im Hintergrund...
    start /min ollama serve
    timeout /t 3 /nobreak >nul
) else (
    echo  [System] Ollama-Server laeuft bereits.
)

:: Python suchen
set PYTHON=
where py >nul 2>&1 && set PYTHON=py
where python >nul 2>&1 && if "%PYTHON%"=="" set PYTHON=python
where python3 >nul 2>&1 && if "%PYTHON%"=="" set PYTHON=python3

if "%PYTHON%"=="" (
    echo.
    echo  [FEHLER] Python nicht gefunden! 
    echo  Bitte stelle sicher, dass Python installiert und im PATH ist.
    pause
    exit /b 1
)

echo  [System] Nutze Python-Umgebung: %PYTHON%
echo  [System] Lade neuronale Netze und starte Robin...
echo ==================================================
echo.

:: Robin starten
%PYTHON% jarvis.py

echo.
echo ==================================================
echo  Robin wurde beendet.
echo ==================================================
pause