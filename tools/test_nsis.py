#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证 NSIS 安装包：
  1) 走完向导（下一步 / 安装 / 完成）
  2) 在目录页把安装路径改成自定义目录，确认"可选安装位置"真的生效
  3) 检查自定义目录、桌面快捷方式、开始菜单
用法: python test_nsis.py <安装包路径> <自定义安装目录>
"""
import ctypes
import ctypes.wintypes as wt
import os
import subprocess
import sys
import time

user32 = ctypes.windll.user32
EnumProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wt.HWND, wt.LPARAM)

EXE = sys.argv[1] if len(sys.argv) > 1 else \
    r'G:\自制网站_程序_\pagebell-web\dist\nsis\翻页提醒器-1.0.0-安装包.exe'
CUSTOM = sys.argv[2] if len(sys.argv) > 2 else r'G:\PagebellTest'
LOG = r'G:\自制网站_程序_\pagebell-web\dist\_nsis_test.txt'

lines = []


def log(*a):
    s = ' '.join(str(x) for x in a)
    lines.append(s)
    print(s, flush=True)


def text_of(h):
    n = user32.GetWindowTextLengthW(h)
    if not n:
        return ''
    b = ctypes.create_unicode_buffer(n + 1)
    user32.GetWindowTextW(h, b, n + 1)
    return b.value


def class_of(h):
    b = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(h, b, 256)
    return b.value


def top_windows():
    res = []

    def cb(h, l):
        if user32.IsWindowVisible(h):
            res.append(h)
        return True
    user32.EnumWindows(EnumProc(cb), 0)
    return res


def children(h):
    res = []

    def cb(c, l):
        res.append(c)
        return True
    user32.EnumChildWindows(h, EnumProc(cb), 0)
    return res


def click(h, wait=1.6):
    user32.SendMessageW(h, 0x00F5, 0, 0)   # BM_CLICK
    time.sleep(wait)


def set_dir(edit_h, path):
    """直接把目录页里的输入框改成自定义路径（等价于用户手动输入/浏览选择）"""
    buf = ctypes.create_unicode_buffer(path)
    user32.SendMessageW(edit_h, 0x000C, 0, ctypes.cast(buf, ctypes.c_void_p))
    time.sleep(0.4)


def main():
    log('=== NSIS 安装包验证 ===')
    log('package:', EXE, '%.1f MB' % (os.path.getsize(EXE) / 1048576))
    log('目标自定义目录:', CUSTOM)

    if os.path.isdir(CUSTOM):
        subprocess.run(['rd', '/s', '/q', CUSTOM], shell=True)
        time.sleep(1)

    p = subprocess.Popen([EXE], cwd=os.path.dirname(EXE))
    log('launched pid', p.pid)

    clicked = set()
    dir_set = False
    deadline = time.time() + 240

    while time.time() < deadline:
        time.sleep(1.2)
        if p.poll() is not None:
            log('installer exited, code =', p.returncode)
            break

        for h in top_windows():
            title = text_of(h)
            if '翻页提醒器' not in title and '安装' not in title:
                continue
            for c in children(h):
                cls = class_of(c).lower()
                txt = text_of(c)
                key = (h, c)

                # 目录页：把输入框（默认安装路径）改成自定义目录
                if cls.startswith('edit') and not dir_set and len(txt.strip()) > 3:
                    log('  目录框原值:', txt)
                    set_dir(c, CUSTOM)
                    dir_set = True
                    log('  已改为自定义目录:', CUSTOM)
                    continue

                if not txt:
                    continue
                low = txt.replace('&', '')
                for kw, label in (('更多信息', 'smartscreen-more'),
                                  ('仍要运行', 'smartscreen-run'),
                                  ('下一步', 'next'),
                                  ('我接受', 'accept'),
                                  ('安装', 'install'),
                                  ('完成', 'finish')):
                    if kw in low and key not in clicked:
                        if label == 'install' and '卸载' in low:
                            continue
                        click(c)
                        clicked.add(key)
                        log('  点击:', txt)
                        break
        time.sleep(0.5)

    # 收尾：等进程结束
    try:
        p.wait(timeout=60)
        log('final exit code =', p.returncode)
    except Exception:
        log('进程仍未退出，强制结束')
        p.kill()

    time.sleep(3)
    log('--- 结果 ---')
    log('自定义目录存在:', os.path.isdir(CUSTOM))
    if os.path.isdir(CUSTOM):
        n = size = 0
        for root, dirs, files in os.walk(CUSTOM):
            for f in files:
                n += 1
                size += os.path.getsize(os.path.join(root, f))
        log('  文件数:', n, '  大小: %.1f MB' % (size / 1048576))
        exe = os.path.join(CUSTOM, '翻页提醒器.exe')
        log('  主程序存在:', os.path.isfile(exe))
        if not os.path.isfile(exe):
            log('  目录内容:', os.listdir(CUSTOM)[:10])
    log('桌面快捷方式:', os.path.isfile(
        os.path.join(os.path.expanduser('~'), 'Desktop', '翻页提醒器.lnk')))
    smdir = os.path.join(os.environ.get('APPDATA', ''), 'Microsoft', 'Windows',
                         'Start Menu', 'Programs')
    ents = [x for x in os.listdir(smdir) if '翻页' in x] if os.path.isdir(smdir) else []
    log('开始菜单项:', ents)

    with open(LOG, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(lines))
    return 0


if __name__ == '__main__':
    sys.exit(main())
