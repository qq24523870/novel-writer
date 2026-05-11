@echo off
title AI Novel Writer - Mobile Test
echo.
echo ====================================================================
echo   AI Novel Writer - Mobile Test Tool
echo ====================================================================
echo.
echo This runs the mobile app on your PC for testing.
echo Close the app window when done.
echo.
echo [Need APK?]  See mobile\HOW_TO_BUILD_APK.txt
echo ====================================================================
echo.
pause

cd /d "%~dp0"
cd ..
set PYTHONPATH=%~dp0;%PYTHONPATH%
start /wait venv\Scripts\python.exe mobile\main.py
exit
