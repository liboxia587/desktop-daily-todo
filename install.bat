@echo off
chcp 65001 >nul
echo ============================================
echo   每日待办 · 桌面便签 — 安装开机自启
echo ============================================
echo.

:: 获取当前脚本所在目录
set "APP_DIR=%~dp0"
set "EXE_PATH=%APP_DIR%DailyTodo.exe"
set "SHORTCUT_NAME=DailyTodo"
set "STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"

:: 检查 exe 是否存在
if not exist "%EXE_PATH%" (
    echo [错误] 未找到 DailyTodo.exe
    echo 请确保本脚本与 DailyTodo.exe 在同一目录下。
    pause
    exit /b 1
)

:: 使用 PowerShell 创建快捷方式到启动文件夹
echo 正在创建开机自启快捷方式...
powershell -NoProfile -Command ^
    "$ws = New-Object -ComObject WScript.Shell; ^
     $sc = $ws.CreateShortcut('%STARTUP_DIR%\%SHORTCUT_NAME%.lnk'); ^
     $sc.TargetPath = '%EXE_PATH%'; ^
     $sc.WorkingDirectory = '%APP_DIR%'; ^
     $sc.Description = '每日待办桌面便签'; ^
     $sc.Save()"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [成功] 开机自启已设置！
    echo 快捷方式位置: %STARTUP_DIR%\%SHORTCUT_NAME%.lnk
    echo.
    echo 现在启动应用...
    start "" "%EXE_PATH%"
) else (
    echo.
    echo [失败] 创建快捷方式时出错，请手动操作：
    echo   1. 按 Win+R，输入 shell:startup
    echo   2. 将 DailyTodo.exe 的快捷方式放入该文件夹
)

echo.
pause
