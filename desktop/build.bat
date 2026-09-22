@echo off
rem 打包成独立可执行文件夹（可整个拷走 / 压缩分发）
rem 原理：复制本机 Electron 运行时 + 把页面装进 resources\app
chcp 65001 >nul
setlocal
cd /d "%~dp0"

set "SRC=%~dp0..\..\glitch-wolf\node_modules\electron\dist"
set "OUT=%~dp0..\dist\Pagebell"

if not exist "%SRC%\electron.exe" (
  echo [ERROR] Electron runtime not found: %SRC%
  echo         Install it once with:  npm i -D electron
  pause
  exit /b 1
)

echo 正在复制 Electron 运行时（约 280 MB）...
if exist "%OUT%" rmdir /s /q "%OUT%"
robocopy "%SRC%" "%OUT%" /E /NFL /NDL /NJH /NJS /NP >nul
if errorlevel 8 (
  echo [ERROR] copy failed
  pause
  exit /b 1
)

ren "%OUT%\electron.exe" "Pagebell.exe"
if not exist "%OUT%\resources\app" mkdir "%OUT%\resources\app"

copy /y "%~dp0package.json" "%OUT%\resources\app\" >nul
copy /y "%~dp0main.js"      "%OUT%\resources\app\" >nul
copy /y "%~dp0preload.js"   "%OUT%\resources\app\" >nul
copy /y "%~dp0..\index.html" "%OUT%\resources\app\" >nul
xcopy /e /i /y "%~dp0..\assets" "%OUT%\resources\app\assets" >nul

echo.
echo 打包完成： %OUT%
echo 双击 %OUT%\Pagebell.exe 即可运行；整个文件夹可压缩后分发。
echo.
pause
