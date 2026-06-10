; SurepriseAi – NSIS Installer (Hermes Desktop: electron-builder → NSIS)
; oneClick: false, allowToChangeInstallationDirectory: true, perMachine: false

!include "MUI2.nsh"

!ifndef APP_VERSION
  !define APP_VERSION "0.1.1"
!endif

!define APP_NAME "SurepriseAi"
!define APP_PUBLISHER "SurepriseAi"
!define APP_EXE "SurepriseAi.exe"
!define APP_URL "https://github.com/Icarus-B4/SurepriseAi"

InstallDir "$LOCALAPPDATA\Programs\${APP_NAME}"
InstallDirRegKey HKCU "Software\${APP_PUBLISHER}\${APP_NAME}" "InstallPath"
RequestExecutionLevel user

Name "${APP_NAME} ${APP_VERSION}"
OutFile "..\dist\SurepriseAi-Setup.exe"
Unicode True

!define MUI_ABORTWARNING
!define MUI_ICON "assets\app_icon.ico"
!define MUI_UNICON "assets\app_icon.ico"
!define MUI_WELCOMEPAGE_TITLE "Willkommen bei ${APP_NAME}"
!define MUI_WELCOMEPAGE_TEXT "Installiert ${APP_NAME} – Voice-Dictation für Windows (lokal & privat).$\r$\n$\r$\nKlicken Sie auf Weiter."
!define MUI_FINISHPAGE_RUN "$INSTDIR\${APP_EXE}"
!define MUI_FINISHPAGE_RUN_TEXT "${APP_NAME} starten"
!define MUI_FINISHPAGE_SHOWLINK
!define MUI_FINISHPAGE_LINK "GitHub-Projektseite"
!define MUI_FINISHPAGE_LINK_LOCATION "${APP_URL}"
!define MUI_COMPONENTS_DESCRIPTION_STUFF
!define MUI_COMPONENTSPAGE_SMALLDESC "Wählen Sie optionale Einträge."

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "..\LICENSE"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "German"

LangString DESC_SecMain ${LANG_GERMAN} "SurepriseAi-Anwendung (erforderlich)."
LangString DESC_SecDesktop ${LANG_GERMAN} "Verknüpfung auf dem Desktop erstellen."
LangString DESC_SecAutostart ${LANG_GERMAN} "SurepriseAi beim Windows-Start im Tray starten."

Function .onInit
  ReadRegStr $0 HKCU "Software\${APP_PUBLISHER}\${APP_NAME}" "InstallPath"
  StrCmp $0 "" +2 0
    StrCpy $INSTDIR $0

  ; Stilles Update: optionale Komponenten wie zuvor beibehalten
  IfSilent 0 silent_done
    IfFileExists "$DESKTOP\${APP_NAME}.lnk" 0 +2
      SectionSetFlags ${SecDesktop} ${SF_SELECTED}
    ReadRegStr $1 HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "${APP_NAME}"
    StrCmp $1 "" silent_done 0
      SectionSetFlags ${SecAutostart} ${SF_SELECTED}
  silent_done:
FunctionEnd

Function .onInstSuccess
  ; Nach stillem Auto-Update die neue Version starten
  IfSilent 0 +2
    Exec '"$INSTDIR\${APP_EXE}"'
FunctionEnd

Function un.onInit
  MessageBox MB_ICONQUESTION|MB_YESNO|MB_DEFBUTTON2 \
    "Möchten Sie ${APP_NAME} vollständig deinstallieren?" IDYES +2
  Abort
FunctionEnd

Section "!Hauptprogramm" SecMain
  SectionIn RO
  SetOutPath "$INSTDIR"
  File /r "..\dist\SurepriseAi\*.*"
  File "assets\app_icon.ico"
  Rename "$INSTDIR\app_icon.ico" "$INSTDIR\SurepriseAi.ico"

  WriteUninstaller "$INSTDIR\Uninstall.exe"

  CreateDirectory "$SMPROGRAMS\${APP_NAME}"
  CreateShortCut "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk" \
    "$INSTDIR\${APP_EXE}" "" "$INSTDIR\SurepriseAi.ico"
  CreateShortCut "$SMPROGRAMS\${APP_NAME}\Deinstallieren.lnk" \
    "$INSTDIR\Uninstall.exe"

  WriteRegStr HKCU "Software\${APP_PUBLISHER}\${APP_NAME}" "InstallPath" "$INSTDIR"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" \
    "DisplayName" "${APP_NAME}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" \
    "UninstallString" "$INSTDIR\Uninstall.exe"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" \
    "DisplayIcon" "$INSTDIR\SurepriseAi.ico"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" \
    "Publisher" "${APP_PUBLISHER}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" \
    "DisplayVersion" "${APP_VERSION}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" \
    "URLInfoAbout" "${APP_URL}"
SectionEnd

Section "Desktop-Verknüpfung" SecDesktop
  CreateShortCut "$DESKTOP\${APP_NAME}.lnk" "$INSTDIR\${APP_EXE}" "" "$INSTDIR\SurepriseAi.ico"
SectionEnd

Section "Mit Windows starten" SecAutostart
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Run" \
    "${APP_NAME}" '"$INSTDIR\${APP_EXE}"'
SectionEnd

!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
  !insertmacro MUI_DESCRIPTION_TEXT ${SecMain} $(DESC_SecMain)
  !insertmacro MUI_DESCRIPTION_TEXT ${SecDesktop} $(DESC_SecDesktop)
  !insertmacro MUI_DESCRIPTION_TEXT ${SecAutostart} $(DESC_SecAutostart)
!insertmacro MUI_FUNCTION_DESCRIPTION_END

Section "Uninstall"
  DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Run\${APP_NAME}"
  Delete "$DESKTOP\${APP_NAME}.lnk"
  RMDir /r "$SMPROGRAMS\${APP_NAME}"
  RMDir /r "$INSTDIR"
  DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}"
  DeleteRegKey HKCU "Software\${APP_PUBLISHER}\${APP_NAME}"
SectionEnd
