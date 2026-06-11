@echo off
REM SurepriseAi – Update-Schleife beenden (Notfall)
REM Doppelklick wenn Auto-Update haengt.

set "LOG=%USERPROFILE%\Desktop\SurepriseAi-Update.log"
set "SETUP=%USERPROFILE%\Downloads\SurepriseAi-Setup.exe"
set "INSTDIR=%LOCALAPPDATA%\Programs\SurepriseAi"

echo [%date% %time%] === Notfall-Installer === >> "%LOG%"

:killloop
taskkill /IM SurepriseAi.exe /F /T >> "%LOG%" 2>&1
ping 127.0.0.1 -n 2 >nul
tasklist /FI "IMAGENAME eq SurepriseAi.exe" 2>nul | find /I "SurepriseAi.exe" >nul
if %ERRORLEVEL%==0 goto killloop

if not exist "%SETUP%" (
  echo Setup nicht gefunden: %SETUP%
  echo Bitte von GitHub Releases herunterladen.
  pause
  exit /b 1
)

echo Installiere...
"%SETUP%" /S
if errorlevel 1 (
  echo Silent fehlgeschlagen – starte Wizard...
  start "" "%SETUP%"
  exit /b 1
)

ping 127.0.0.1 -n 2 >nul
start "" "%INSTDIR%\SurepriseAi.exe"
echo Fertig. Log: %LOG%
timeout /t 5
