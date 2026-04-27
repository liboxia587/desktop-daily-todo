@echo off
chcp 65001 >nul
echo ============================================
echo   每日待办 · 桌面便签 — 移除开机自启
echo ============================================
echo.

set "SHORTCUT_NAME=DailyTodo"
set "STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "SHORTCUT_PATH=%STARTUP_DIR%\%SHORTCUT_NAME%.lnk"

:: 先结束正在运行的进程
echo 正在关闭运行中的程序...
taskkill /f /im DailyTodo.exe >nul 2>&1

:: 删除启动文件夹中的快捷方式
if exist "%SHORTCUT_PATH%" (
    del "%SHORTCUT_PATH%"
    echo [成功] 已移除开机自启快捷方式。
) else (
    echo [提示] 未找到开机自启快捷方式，可能已经移除。
)

echo.
echo 注意：本脚本仅移除开机自启，不会删除程序文件和待办数据。
echo 如需完全删除，请手动删除本目录。
echo.
pause
