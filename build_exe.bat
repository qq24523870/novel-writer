@echo off
chcp 65001 >nul
echo ====================================================================
echo   AI小说创作助手 v1.0.0 - 一键打包脚本
echo   开发者: 青易 QQ:24523870
echo ====================================================================
echo.
echo   [注意] 打包需要5-10分钟，请耐心等待...
echo.

cd /d "%~dp0"

echo [1/4] 清理旧构建...
if exist "build" rd /s /q "build" 2>nul
if exist "dist" rd /s /q "dist" 2>nul
if exist "NovelWriter.spec" del /q "NovelWriter.spec" 2>nul
echo       清理完成

echo.
echo [2/4] 代码编译加密...
venv\Scripts\python.exe -m compileall -q -b core models utils ui
echo       已完成py编译保护

echo.
echo [3/4] 正在打包exe(请不要关闭此窗口)...
venv\Scripts\python.exe -m PyInstaller ^
    --noconfirm ^
    --onefile ^
    --windowed ^
    --name "AI小说创作助手" ^
    --add-data "config\default_config.json;config" ^
    --hidden-import openai ^
    --hidden-import loguru ^
    --hidden-import docx ^
    --hidden-import markdown ^
    --hidden-import lxml ^
    --hidden-import httpx ^
    --hidden-import tiktoken ^
    --hidden-import PySide6 ^
    --collect-submodules core ^
    --collect-submodules ui ^
    --collect-submodules models ^
    --collect-submodules utils ^
    main.py >nul 2>&1

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] 打包过程出错! 
    pause
    exit /b 1
)

echo.
echo [4/4] 完成...
if exist "dist\AI小说创作助手.exe" (
    echo ====================================================================
    echo   打包成功!
    echo   输出文件: dist\AI小说创作助手.exe
    echo   可直接将此exe文件复制到任何Windows电脑运行
    echo   首次运行时会在exe同目录自动创建data\目录
    echo ====================================================================
) else (
    echo [ERROR] 未找到生成的exe文件!
)

echo.
pause
