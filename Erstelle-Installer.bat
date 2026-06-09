@echo off
title SurepriseAi – Setup.exe erstellen
echo.
echo  SurepriseAi Setup (NSIS – wie Hermes Desktop)
echo  ==============================================
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0build\build.ps1" -Installer
echo.
if exist "%~dp0dist\SurepriseAi-Setup.exe" (
    echo  Fertig: dist\SurepriseAi-Setup.exe
    echo  Diese Datei an Nutzer weitergeben – Doppelklick zum Installieren.
) else (
    echo  Setup.exe nicht erstellt. Siehe Fehlermeldung oben.
)
echo.
pause
