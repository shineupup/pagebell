@echo off
chcp 65001 >nul
title 翻页提醒器 · 打包

rem 双击本文件即可重新打包：会把最新界面装进程序，再编译成安装包
set ELECTRON_RUN_AS_NODE=
set NODE_OPTIONS=

set "PY=C:\Users\Administrator\.workbuddy\binaries\python\envs\default\Scripts\python.exe"
if not exist "%PY%" set "PY=python"

"%PY%" "%~dp0build.py"
echo.
echo 按任意键关闭...
pause >nul
