// Pagebell Desktop · Electron 主进程
// 无边框 + 透明窗口：只有卡片本身可见，没有网页背景
const { app, BrowserWindow, ipcMain, screen } = require('electron');
const path = require('path');
const fs = require('fs');

const APP_DIR = __dirname;
const PAD = 20;                 // 卡片外留白，用来放投影
const WIDE = [622, 340];        // 完整尺寸（CSS 像素）
const MINI = [214, 96];         // 迷你尺寸

// 开发时页面在上一级目录，打包后与 main.js 同级
function resolveIndex() {
  const local = path.join(APP_DIR, 'index.html');
  return fs.existsSync(local) ? local : path.join(APP_DIR, '..', 'index.html');
}

let win = null;

// 把窗口拉回屏幕内。
// ring = PAD：允许透明留白溢出屏幕，这样卡片仍能贴边；但卡片本体一定留在屏内，
// 顶部拖动条永远不会跑到屏幕外（否则窗口就再也拖不动了）。
function clampToWorkArea(b, ring) {
  const d = screen.getDisplayNearestPoint({
    x: Math.round(b.x + b.width / 2),
    y: Math.round(b.y + b.height / 2),
  });
  const wa = d.workArea;
  const r = ring === undefined ? 0 : ring;

  let x = b.x;
  let y = b.y;

  if (b.width >= wa.width + r * 2) {
    x = wa.x;
  } else {
    x = Math.min(Math.max(x, wa.x - r), wa.x + wa.width - b.width + r);
  }

  if (b.height >= wa.height + r * 2) {
    y = wa.y;
  } else {
    y = Math.min(Math.max(y, wa.y - r), wa.y + wa.height - b.height + r);
  }

  return {
    x: Math.round(x),
    y: Math.round(y),
    width: Math.round(b.width),
    height: Math.round(b.height),
  };
}

// 缩放窗口时保持中心不动，迷你/展开不会跳到别处；
// 但缩放后必须把窗口按回屏幕内，且尺寸没变化时不动它（避免拖到边上后一碰控件就弹回来）
function resizeKeepCenter(w, h) {
  if (!win) return;
  const b = win.getBounds();
  const nw = Math.round(w);
  const nh = Math.round(h);
  if (b.width === nw && b.height === nh) return;   // 尺寸没变，位置交给用户

  const cx = b.x + b.width / 2;
  const cy = b.y + b.height / 2;
  const next = clampToWorkArea({
    x: cx - nw / 2,
    y: cy - nh / 2,
    width: nw,
    height: nh,
  }, PAD);
  win.setBounds(next);
}

function createWindow() {
  // 任务栏 / 窗口图标（预览时用 desktop\icon.ico，打包后 exe 自带图标）
  const ico = path.join(APP_DIR, 'icon.ico');

  win = new BrowserWindow({
    icon: fs.existsSync(ico) ? ico : undefined,
    width: WIDE[0] + PAD * 2,
    height: WIDE[1] + PAD * 2,
    frame: false,
    transparent: true,
    backgroundColor: '#00000000',
    resizable: false,
    maximizable: false,
    fullscreenable: false,
    alwaysOnTop: true,
    hasShadow: false,
    show: false,
    title: '翻页提醒器',
    webPreferences: {
      preload: path.join(APP_DIR, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      backgroundThrottling: false,
    },
  });

  win.setMenuBarVisibility(false);
  win.loadFile(resolveIndex(), { query: { app: '1' } });
  win.once('ready-to-show', function () { win.show(); });

  // 调试：PB_DEBUG=1 时把页面控制台与加载状态打到 stdout
  if (process.env.PB_DEBUG) {
    win.webContents.on('did-finish-load', function () { console.log('[main] page loaded'); });
    win.webContents.on('did-fail-load', function (e, code, desc) {
      console.log('[main] load failed', code, desc);
    });
    win.webContents.on('console-message', function (e, level, message) {
      var msg = (level && typeof level === 'object') ? level.message : message;
      console.log('[page]', msg);
    });
  }

  // 调试：PB_SHOT=xxx.png 时截取窗口内容后退出（用于检查布局与透明背景）
  if (process.env.PB_SHOT) {
    // 截屏前压掉「静止隐藏」的淡出，否则 2.2s 时正好卡在淡出动画里
    const NO_IDLE = "document.body.classList.remove('is-idle');" +
      "var s=document.createElement('style');" +
      "s.textContent='body.is-idle .stage{opacity:1!important;transform:none!important;" +
      "filter:none!important;transition:none!important;pointer-events:auto!important}';" +
      "document.head.appendChild(s);";
    win.webContents.once('did-finish-load', function () {
      setTimeout(function () {
        win.webContents.executeJavaScript(NO_IDLE);
        win.webContents.capturePage().then(function (img) {
          require('fs').writeFileSync(process.env.PB_SHOT, img.toPNG());
          console.log('[main] shot saved:', process.env.PB_SHOT);
          if (!process.env.PB_SHOT_MINI) { app.quit(); return; }
          win.webContents.executeJavaScript("document.getElementById('btnMini').click()");
          setTimeout(function () {
            win.webContents.executeJavaScript(NO_IDLE);
            win.webContents.capturePage().then(function (img2) {
              require('fs').writeFileSync(process.env.PB_SHOT_MINI, img2.toPNG());
              console.log('[main] mini shot saved:', process.env.PB_SHOT_MINI);
              app.quit();
            });
          }, 1200);
        });
      }, 2200);
    });
  }

  // 居中（多显示器时以当前屏幕工作区为基准）
  const wa = screen.getPrimaryDisplay().workArea;
  const b = win.getBounds();
  win.setPosition(
    Math.round(wa.x + (wa.width - b.width) / 2),
    Math.round(wa.y + (wa.height - b.height) / 2)
  );

  win.on('closed', function () { win = null; });

  // 调试：PB_TEST_CLAMP=1 时直接批量验证贴边展开（几何回归）
  if (process.env.PB_TEST_CLAMP) {
    win.once('ready-to-show', function () {
      const wa = screen.getPrimaryDisplay().workArea;
      const mini = { width: MINI[0] + PAD * 2, height: MINI[1] + PAD * 2 };
      const full = { width: WIDE[0] + PAD * 2, height: WIDE[1] + PAD * 2 };
      const cases = [
        { name: '顶边(上半出界)', x: wa.x + 40, y: wa.y - 60 },
        { name: '右上角', x: wa.x + wa.width - 60, y: wa.y - 60 },
        { name: '右下角(小窗完全出界)', x: wa.x + wa.width - 60, y: wa.y + wa.height - 40 },
        { name: '正常居中', x: wa.x + 300, y: wa.y + 300 },
      ];
      cases.forEach(function (c) {
        win.setBounds({ x: c.x, y: c.y, width: mini.width, height: mini.height });
        resizeKeepCenter(full.width, full.height);
        const a = win.getBounds();
        const ok = a.x >= wa.x - PAD &&
                   a.y + PAD >= wa.y &&
                   a.x + a.width <= wa.x + wa.width + PAD &&
                   a.y + a.height <= wa.y + wa.height + PAD;
        console.log('[t]', c.name, '->', a.x + ',' + a.y, ok ? 'OK' : 'FAIL');
      });
      app.quit();
    });
  }
}

app.whenReady().then(function () {
  createWindow();

  // 页面报告尺寸（已含 PAD），窗口自己保持中心
  ipcMain.on('pb:size', function (e, w, h) {
    if (process.env.PB_DEBUG) console.log('[main] size ->', w, h);
    resizeKeepCenter(w, h);
  });

  // 整窗透明度
  ipcMain.on('pb:alpha', function (e, v) {
    if (!win) return;
    const val = Math.max(0.2, Math.min(1, Number(v) || 1));
    win.setOpacity(val);
  });

  // 置顶开关
  ipcMain.handle('pb:top', function () {
    if (!win) return false;
    const next = !win.isAlwaysOnTop();
    win.setAlwaysOnTop(next);
    return next;
  });

  // 最小化
  ipcMain.on('pb:min', function () {
    if (!win) return;
    win.minimize();
  });

  // 退出
  ipcMain.on('pb:quit', function () {
    app.quit();
  });
});

app.on('window-all-closed', function () { app.quit(); });
