@echo off
chcp 65001 >nul
title 翻页提醒器 · 预览

rem ============================================================
rem  免安装预览：直接用本机已有的 Electron 运行时启动窗口
rem  改了 index.html / assets 之后，双击这个就能看最新效果
rem  不需要打包、不需要安装
rem ============================================================

set ELECTRON_RUN_AS_NODE=
set NODE_OPTIONS=

set "EL=G:\自制网站_程序_\glitch-wolf\node_modules\electron\dist\electron.exe"

if not exist "%EL%" (
  echo.
  echo   找不到 Electron 运行时：
  echo     %EL%
  echo   请确认 G 盘（移动硬盘）已插好，再运行本文件。
  echo.
  pause
  exit /b 1
)

start "" "%EL%" "%~dp0desktop"
