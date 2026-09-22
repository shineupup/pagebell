#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
翻页提醒器 · 一键打包
================================
把最新的界面文件（index.html / assets）同步进 Electron 程序目录，
再编译成 Windows 安装包（中文向导、可自选安装目录、自带卸载）。

用法：双击 build.bat，或者在本目录执行  python build.py
产物：安装包\翻页提醒器-<版本>-安装包.exe
"""
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
APP_NAME = '翻页提醒器'
APP_VER = '1.0.0'
PUBLISHER = 'Mayn'

# 已组装好的 Electron 运行时（含 resources\app）
SRC_APP = os.path.join(ROOT, 'dist', 'payload', 'Pagebell')
APP_RES = os.path.join(SRC_APP, 'resources', 'app')
ICON_DIR = os.path.join(ROOT, 'packer', 'build')
ICON_SETUP = os.path.join(ICON_DIR, 'icon_setup.ico')   # 安装包自己的图标
ICON_APP = os.path.join(ICON_DIR, 'icon_app.ico')       # 装完后应用/快捷方式/任务栏的图标
RCEDIT = (r'C:\Users\Administrator\AppData\Local\electron-builder\Cache'
          r'\winCodeSign\winCodeSign-2.6.0\rcedit-x64.exe')
OUT_DIR = os.path.join(ROOT, '安装包')
TMP_DIR = os.path.join(os.environ.get('TEMP', r'C:\Windows\Temp'), 'pbbuild')

# 本机 NSIS（electron-builder 缓存里那份，无需联网下载）
MAKENSIS = (r'C:\Users\Administrator\AppData\Local\electron-builder\Cache'
            r'\nsis\nsis-3.0.4.1-nsis-3.0.4.1\makensis.exe')

NSI = r'''Unicode true
SetCompressor /SOLID lzma
SetCompressorDictSize 64

!include "MUI2.nsh"
!include "FileFunc.nsh"
!include "LogicLib.nsh"

!define APP_NAME "@APP_NAME@"
!define APP_EXE "@APP_NAME@.exe"
!define APP_VER "@APP_VER@"
!define PUBLISHER "@PUBLISHER@"
!define REGKEY "Software\Pagebell"
!define UNKEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\Pagebell"
!define SRC "@SRC@"
!define ICON "@ICON@"

Name "${APP_NAME}"
OutFile "@OUTFILE@"
InstallDir "$LOCALAPPDATA\Programs\${APP_NAME}"
InstallDirRegKey HKCU "${REGKEY}" "InstallDir"
RequestExecutionLevel user
ShowInstDetails show
ShowUninstDetails show

Icon "${ICON}"
UninstallIcon "${ICON}"

VIProductVersion "@APP_VER@.0"
VIAddVersionKey /LANG=2052 "ProductName" "${APP_NAME}"
VIAddVersionKey /LANG=2052 "FileDescription" "${APP_NAME} 安装程序"
VIAddVersionKey /LANG=2052 "FileVersion" "${APP_VER}"
VIAddVersionKey /LANG=2052 "ProductVersion" "${APP_VER}"
VIAddVersionKey /LANG=2052 "CompanyName" "${PUBLISHER}"
VIAddVersionKey /LANG=2052 "LegalCopyright" "${PUBLISHER}"

!define MUI_ICON "${ICON}"
!define MUI_UNICON "${ICON}"
!define MUI_ABORTWARNING
!define MUI_WELCOMEPAGE_TITLE "欢迎安装 ${APP_NAME}"
!define MUI_WELCOMEPAGE_TEXT "安装向导将把 ${APP_NAME} 安装到你的电脑。$\r$\n$\r$\n· 无需管理员权限，不影响其他软件$\r$\n· 会创建桌面与开始菜单快捷方式$\r$\n· 自带卸载程序，可随时干净移除$\r$\n$\r$\n点击「下一步」继续。"
!define MUI_DIRECTORYPAGE_TEXT_TOP "请选择 ${APP_NAME} 的安装位置。$\r$\n$\r$\n你可以直接使用默认文件夹，也可以点「浏览」安装到其他磁盘或文件夹。"
!define MUI_DIRECTORYPAGE_TEXT_DESTDIR "安装到："
!define MUI_INSTFILESPAGE_COLORS "1B3A57 4D96FF"
!define MUI_FINISHPAGE_RUN "$INSTDIR\${APP_EXE}"
!define MUI_FINISHPAGE_RUN_TEXT "立即运行 ${APP_NAME}"
!define MUI_FINISHPAGE_TEXT "${APP_NAME} 已安装完成。$\r$\n$\r$\n桌面和开始菜单里都能找到它，卸载程序在开始菜单的 ${APP_NAME} 文件夹中。"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

!insertmacro MUI_LANGUAGE "SimpChinese"

Section "主程序" SEC_MAIN
  SectionIn RO
  SetOutPath "$INSTDIR"
  SetOverwrite on

  File "/oname=${APP_EXE}" "${SRC}\Pagebell.exe"
  File /r /x "Pagebell.exe" "${SRC}\*.*"

  CreateShortcut "$DESKTOP\${APP_NAME}.lnk" "$INSTDIR\${APP_EXE}" "" "$INSTDIR\${APP_EXE}" 0
  CreateDirectory "$SMPROGRAMS\${APP_NAME}"
  CreateShortcut "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk" "$INSTDIR\${APP_EXE}" "" "$INSTDIR\${APP_EXE}" 0

  WriteUninstaller "$INSTDIR\卸载 ${APP_NAME}.exe"
  CreateShortcut "$SMPROGRAMS\${APP_NAME}\卸载 ${APP_NAME}.lnk" "$INSTDIR\卸载 ${APP_NAME}.exe"

  WriteRegStr HKCU "${REGKEY}" "InstallDir" "$INSTDIR"
  WriteRegStr HKCU "${UNKEY}" "DisplayName" "${APP_NAME}"
  WriteRegStr HKCU "${UNKEY}" "DisplayVersion" "${APP_VER}"
  WriteRegStr HKCU "${UNKEY}" "Publisher" "${PUBLISHER}"
  WriteRegStr HKCU "${UNKEY}" "DisplayIcon" "$INSTDIR\${APP_EXE}"
  WriteRegStr HKCU "${UNKEY}" "InstallLocation" "$INSTDIR"
  WriteRegStr HKCU "${UNKEY}" "UninstallString" "$\"$INSTDIR\卸载 ${APP_NAME}.exe$\""
  WriteRegDWORD HKCU "${UNKEY}" "NoModify" 1
  WriteRegDWORD HKCU "${UNKEY}" "NoRepair" 1
  ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
  IntFmt $0 "0x%08X" $0
  WriteRegDWORD HKCU "${UNKEY}" "EstimatedSize" "$0"
SectionEnd

Section "Uninstall"
  Delete "$DESKTOP\${APP_NAME}.lnk"
  RMDir /r "$SMPROGRAMS\${APP_NAME}"

  MessageBox MB_YESNO|MB_ICONQUESTION "是否同时删除个人设置？$\r$\n$\r$\n包括音色、音量、透明度、累计统计等（选择「否」将保留，重装后仍在）。" /SD IDNO IDNO keep_settings
    RMDir /r "$APPDATA\pagebell"
  keep_settings:

  RMDir /r "$INSTDIR"
  DeleteRegKey HKCU "${REGKEY}"
  DeleteRegKey HKCU "${UNKEY}"
SectionEnd
'''


def log(msg):
    print(msg, flush=True)


def check_env():
    if not os.path.isfile(os.path.join(SRC_APP, 'Pagebell.exe')):
        log('缺少程序目录：%s' % SRC_APP)
        log('（这是 Electron 运行时，正常情况下不该丢；若真丢了需要重新组装一份）')
        return False
    if not os.path.isfile(MAKENSIS):
        log('找不到 NSIS 编译器：%s' % MAKENSIS)
        return False
    return True


def sync_web():
    """把界面文件同步进程序里的 resources\\app"""
    os.makedirs(os.path.join(APP_RES, 'assets'), exist_ok=True)
    shutil.copy2(os.path.join(ROOT, 'index.html'), os.path.join(APP_RES, 'index.html'))
    for f in ('style.css', 'app.js'):
        shutil.copy2(os.path.join(ROOT, 'assets', f),
                     os.path.join(APP_RES, 'assets', f))
    for f in ('main.js', 'preload.js'):
        shutil.copy2(os.path.join(ROOT, 'desktop', f), os.path.join(APP_RES, f))
    log('界面文件已同步 -> resources\\app')


def make_icon():
    """安装包图标（蓝青渐变 + 声波点）。已存在就不重画，方便直接替换 ico"""
    if os.path.isfile(ICON_SETUP):
        log('安装包图标已存在，沿用 %s' % ICON_SETUP)
        return
    try:
        from PIL import Image, ImageDraw, ImageFilter
    except ImportError:
        log('（未安装 Pillow，沿用现有图标）')
        return

    S = 1024
    A, B = (77, 150, 255), (46, 196, 182)

    def lerp(c1, c2, t):
        return tuple(round(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))

    grad = Image.new('RGBA', (S, S))
    px = grad.load()
    for y in range(S):
        for x in range(S):
            t = (x + y) / (2 * (S - 1))
            r, g, b = lerp(A, B, t)
            px[x, y] = (r, g, b, 255)

    mask = Image.new('L', (S, S), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, S - 1, S - 1),
                                           radius=int(S * 0.22), fill=255)
    img = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    img.paste(grad, (0, 0), mask)

    glow = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse(
        (int(S * -0.15), int(S * -0.25), int(S * 0.75), int(S * 0.55)),
        fill=(255, 255, 255, 62))
    glow = glow.filter(ImageFilter.GaussianBlur(S * 0.09))
    img = Image.alpha_composite(img, glow)
    m2 = Image.new('L', (S, S), 0)
    ImageDraw.Draw(m2).rounded_rectangle((0, 0, S - 1, S - 1),
                                         radius=int(S * 0.22), fill=255)
    img.putalpha(Image.composite(img.getchannel('A'),
                                 Image.new('L', (S, S), 0), m2))

    mark = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(mark)
    c = S / 2
    r0 = S * 0.115
    d.ellipse((c - r0, c - r0, c + r0, c + r0), fill=(255, 255, 255, 255))
    for r, w, alpha in ((S * 0.235, int(S * 0.042), 225),
                        (S * 0.345, int(S * 0.036), 130)):
        box = (c - r, c - r, c + r, c + r)
        d.arc(box, start=32, end=148, fill=(255, 255, 255, alpha), width=w)
        d.arc(box, start=212, end=328, fill=(255, 255, 255, alpha), width=w)
    img = Image.alpha_composite(img, mark)

    os.makedirs(ICON_DIR, exist_ok=True)
    img.save(ICON_SETUP, format='ICO',
             sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64),
                    (128, 128), (256, 256)])
    log('安装包图标已生成 -> %s' % ICON_SETUP)


def apply_exe_icon():
    """把应用图标写进 Electron 主程序：桌面/开始菜单快捷方式、任务栏都会用它"""
    exe = os.path.join(SRC_APP, 'Pagebell.exe')
    if not os.path.isfile(ICON_APP):
        log('（没有 icon_app.ico，跳过 exe 图标写入）')
        return False
    if not os.path.isfile(RCEDIT):
        log('（找不到 rcedit，跳过 exe 图标写入）')
        return False
    r = subprocess.run([RCEDIT, exe, '--set-icon', ICON_APP],
                       capture_output=True, text=True,
                       encoding='utf-8', errors='replace')
    if r.returncode == 0:
        log('应用图标已写入主程序（快捷方式/任务栏都会用它）')
        return True
    log('写图标失败：' + ((r.stderr or r.stdout or '').strip()[:200]))
    return False


def compile_nsis():
    """NSIS 命令行只喂 ASCII 路径最稳，所以脚本与输出先放临时目录"""
    os.makedirs(TMP_DIR, exist_ok=True)
    nsi_path = os.path.join(TMP_DIR, 'build.nsi')
    tmp_out = os.path.join(TMP_DIR, 'Pagebell-Setup-x64.exe')

    body = (NSI.replace('@APP_NAME@', APP_NAME)
               .replace('@APP_VER@', APP_VER)
               .replace('@PUBLISHER@', PUBLISHER)
               .replace('@SRC@', SRC_APP)
               .replace('@ICON@', ICON_SETUP)
               .replace('@OUTFILE@', tmp_out))
    with open(nsi_path, 'w', encoding='utf-8', newline='\r\n') as fh:
        fh.write(body)

    log('正在压缩打包（约 5 分钟，进度条跑完即完成）...')
    r = subprocess.run([MAKENSIS, '/INPUTCHARSET', 'UTF8', nsi_path],
                       capture_output=True, text=True,
                       encoding='utf-8', errors='replace')
    tail = (r.stdout or '').strip().splitlines()
    for line in tail[-6:]:
        log('  ' + line)
    if r.returncode != 0 or not os.path.isfile(tmp_out):
        log('编译失败' + ((r.stderr or '').strip()[:400]))
        return None

    os.makedirs(OUT_DIR, exist_ok=True)
    final = os.path.join(OUT_DIR, '%s-%s-安装包.exe' % (APP_NAME, APP_VER))
    shutil.copy2(tmp_out, final)          # copy2 直接覆盖，比 remove+move 稳
    log('安装包 -> %s  (%.1f MB)' % (final, os.path.getsize(final) / 1048576))
    return final


def main():
    log('=== %s 打包 ===' % APP_NAME)
    if not check_env():
        return 1
    sync_web()
    make_icon()
    apply_exe_icon()
    return 0 if compile_nsis() else 1


if __name__ == '__main__':
    sys.exit(main())
