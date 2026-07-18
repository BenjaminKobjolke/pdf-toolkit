; FastFileViewer Installer Script (NSIS + Modern UI 2)
; Packages the GUI viewer only (dist\FastFileViewer onedir build) — no CLI tools.

!include "MUI2.nsh"
!include "FileFunc.nsh"
!include "LogicLib.nsh"

; Installer settings
Name "FastFileViewer"
Outfile "..\releases\windows\installer.exe"
InstallDir $PROGRAMFILES\FastFileViewer
RequestExecutionLevel admin
ShowInstDetails show

; Default installation section
Section "FastFileViewer (required)"

  SetOutPath $INSTDIR
  File /r "..\dist\FastFileViewer\*.*"

  ; Write the installation path into the registry
  WriteRegStr HKLM "Software\FastFileViewer" "Install_Dir" $INSTDIR

  ; Create the uninstaller
  WriteUninstaller "$INSTDIR\Uninstall.exe"

  ; Create shortcuts in the Start Menu Programs folder
  CreateDirectory $SMPROGRAMS\FastFileViewer
  CreateShortCut "$SMPROGRAMS\FastFileViewer\FastFileViewer.lnk" "$INSTDIR\FastFileViewer.exe"
  CreateShortCut "$SMPROGRAMS\FastFileViewer\Uninstall.lnk" "$INSTDIR\Uninstall.exe"

SectionEnd

; Uninstaller settings
Section "Uninstall"

  ; Remove the registry entries
  DeleteRegKey HKLM "Software\FastFileViewer"

  ; Remove the Start Menu shortcuts
  Delete "$SMPROGRAMS\FastFileViewer\FastFileViewer.lnk"
  Delete "$SMPROGRAMS\FastFileViewer\Uninstall.lnk"
  RMDir "$SMPROGRAMS\FastFileViewer"

  ; Remove the installed files
  RMDir /r "$INSTDIR"

SectionEnd

; Modern User Interface settings
!define MUI_WELCOMEPAGE_TITLE "Welcome to the FastFileViewer Setup Wizard"
!define MUI_WELCOMEPAGE_TEXT "This wizard will guide you through the installation of FastFileViewer.$\r$\n$\r$\nClick Next to continue or Cancel to exit the setup."
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!define MUI_FINISHPAGE_NOAUTOCLOSE
!define MUI_FINISHPAGE_TITLE "FastFileViewer Installation Completed"
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH
!insertmacro MUI_LANGUAGE "English"

; No version info in this file on purpose: the build bat renames the output
; to FastFileViewer_v<version>_<build>.exe using the project's version tools.
