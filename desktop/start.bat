@echo off
rem Pagebell Desktop launcher
rem 用本机已有的 Electron 运行时启动，不额外占磁盘
chcp 65001 >nul
setlocal
set ELECTRON_RUN_AS_NODE=
set "APP=%~dp0"
set "ELECTRON=%APP%..\..\glitch-wolf\node_modules\electron\dist\electron.exe"
if not exist "%ELECTRON%" set "ELECTRON=%APP%..\glitch-wolf\node_modules\electron\dist\electron.exe"
if not exist "%ELECTRON%" (
  echo [ERROR] Electron runtime not found.
  echo         Expected at: %APP%..\..\glitch-wolf\node_modules\electron\dist\electron.exe
  echo         Run "build.bat" first to create a standalone package.
  pause
  exit /b 1
)
start "" "%ELECTRON%" "%APP%."
