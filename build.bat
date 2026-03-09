@echo off
chcp 65001 >nul
echo ================================================
echo   AI 改写助手 — 打包工具
echo ================================================
echo.

:: 检查 PyInstaller
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [安装] PyInstaller 未找到，正在安装...
    pip install pyinstaller
)

:: 清理上次构建
if exist dist\AI改写助手.exe (
    echo [清理] 删除旧版本...
    del /f /q dist\AI改写助手.exe
)
if exist build (
    rmdir /s /q build
)

echo [开始] 正在打包，请稍候...
echo.

pyinstaller build.spec

echo.
if exist "dist\AI改写助手.exe" (
    echo ================================================
    echo   ✓ 打包成功！
    echo   输出路径：dist\AI改写助手.exe
    echo   文件大小：
    for %%A in ("dist\AI改写助手.exe") do echo     %%~zA 字节
    echo ================================================
    explorer dist
) else (
    echo   ✗ 打包失败，请查看上方错误信息
)

pause