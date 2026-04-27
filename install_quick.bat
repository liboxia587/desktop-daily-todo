@echo off
chcp 65001 >nul
echo ============================================
echo   每日待办 · 快速安装(Python 直跑版)
echo ============================================
echo.

set "APP_DIR=%~dp0"
set "VBS_PATH=%APP_DIR%run_silent.vbs"
set "SHORTCUT_NAME=DailyTodo"
set "STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"

if not exist "%VBS_PATH%" (
    echo [错误] 未找到 run_silent.vbs
    pause
    exit /b 1
)

echo 正在创建开机自启快捷方式...
powershell -NoProfile -Command ^
    "$ws = New-Object -ComObject WScript.Shell; ^
     $sc = $ws.CreateShortcut('%STARTUP_DIR%\%SHORTCUT_NAME%.lnk'); ^
     $sc.TargetPath = '%VBS_PATH%'; ^
     $sc.WorkingDirectory = '%APP_DIR%'; ^
     $sc.Description = '每日待办桌面便签'; ^
     $sc.Save()"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [成功] 开机自启已设置！
    echo 快捷方式: %STARTUP_DIR%\%SHORTCUT_NAME%.lnk
    echo.
    echo 现在启动应用...
    wscript "%VBS_PATH%"
    echo [完成] App 已在后台启动,看右上角桌面
) else (
    echo [失败] 请手动操作
)

echo.
pause
