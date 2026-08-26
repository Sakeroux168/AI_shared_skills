@echo off
setlocal EnableExtensions
chcp 65001 >nul
title AI_shared_skills 一键检查
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0doctor-windows.ps1" %*
set "AISS_EC=%ERRORLEVEL%"
echo.
echo 窗口可以关闭了。按任意键退出...
pause >nul
exit /b %AISS_EC%
