@echo off
chcp 65001 >nul
echo ============================================
echo   每日待办 · 桌面便签 — 打包 exe
echo ============================================
echo.

:: 检查 Python 环境
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [错误] 未找到 Python，请先安装 Python 3.10+
    pause
    exit /b 1
)

:: 安装依赖
echo 正在安装依赖...
pip install -r requirements.txt

:: 打包
echo.
echo 正在打包为 exe...
pyinstaller build.spec --clean --noconfirm

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [成功] 打包完成！
    echo exe 位置: dist\DailyTodo.exe
    echo.
    echo 请将以下文件复制到目标目录：
    echo   - dist\DailyTodo.exe
    echo   - install.bat
    echo   - uninstall.bat
    echo   - config.json（首次运行自动生成）
) else (
    echo.
    echo [失败] 打包出错，请检查错误信息。
)

echo.
pause
