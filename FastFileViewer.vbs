' Windowless launcher for the pdf-toolkit GUI viewer, used as a file association.
'
' Why this exists: a .bat as a default PDF handler flashes a console window on
' every open, and the working directory is unpredictable (often system32), so
' the CWD-relative backup folder would land in a random place. This script:
'   1) sets the working directory to the opened PDF's own folder, so backups go
'      to <pdf folder>\backup\ next to the file, and
'   2) launches FastFileViewer.bat with a hidden window (no console flash).
' It reuses FastFileViewer.bat so the venv path and PYTHONPATH stay defined in one place.

Option Explicit

Dim shell, fso, projectRoot, bat, pdf, command
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

projectRoot = fso.GetParentFolderName(WScript.ScriptFullName)
bat = projectRoot & "\FastFileViewer.bat"

If WScript.Arguments.Count > 0 Then
    pdf = WScript.Arguments(0)
    ' Backups resolve against CWD; point it at the PDF's folder.
    shell.CurrentDirectory = fso.GetParentFolderName(pdf)
    command = """" & bat & """ """ & pdf & """"
Else
    command = """" & bat & """"
End If

' Window style 0 = hidden (no console flash); False = do not wait.
shell.Run command, 0, False
