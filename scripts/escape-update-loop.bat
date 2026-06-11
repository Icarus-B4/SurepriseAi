@echo off
REM SurepriseAi – Update-Schleife beenden / manuell installieren
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
  pause
  exit /b 1
)

"%SETUP%" /S
echo [%date% %time%] NSIS exit=%ERRORLEVEL% >> "%LOG%"
if errorlevel 1 (
  start "" "%SETUP%"
  exit /b 1
)

ping 127.0.0.1 -n 2 >nul
cd /d "%INSTDIR%"
start "" /D "%INSTDIR%" "%INSTDIR%\SurepriseAi.exe"
ping 127.0.0.1 -n 3 >nul
tasklist /FI "IMAGENAME eq SurepriseAi.exe" 2>nul | find /I "SurepriseAi.exe" >nul
if %ERRORLEVEL% NEQ 0 (
  powershell -NoProfile -WindowStyle Hidden -Command "Start-Process -FilePath '%INSTDIR%\SurepriseAi.exe' -WorkingDirectory '%INSTDIR%'"
)
echo [%date% %time%] App neu gestartet >> "%LOG%"
timeout /t 3
