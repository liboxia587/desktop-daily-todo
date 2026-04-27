' run_silent.vbs — 无黑窗口启动 desktop-todo
' 双击或被快捷方式调用都不会弹 cmd 窗口

Set WshShell = CreateObject("WScript.Shell")
strScriptDir = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
strCmd = "pythonw """ & strScriptDir & "\main.py"""
WshShell.Run strCmd, 0, False
