/* ===========================================================
   Pagebell · 翻页提醒器 网页版
   核心：一按即响两声提示（音色/频率/音量/声数可调）
   其余：沉浸隐藏、视觉涟漪、屏幕常亮、主题、迷你贴边
   =========================================================== */
(function () {
  'use strict';

  var $ = function (s) { return document.querySelector(s); };
  var $$ = function (s) { return Array.prototype.slice.call(document.querySelectorAll(s)); };

  var STORE_KEY = 'pagebell.v2';
  var isNative = false;   // 桌面应用模式（pywebview）

  var state = {
    voice: 'beep',
    freq: 880,
    volume: 70,
    beats: 2,
    idleSec: 2.5,
    opacity: 1,
    ripple: true,
    wakeLock: false,
    immerse: true,
    theme: 'light',
    mini: false
  };

  /* ---------------- 持久化 ---------------- */
  function load() {
    /* 载入需早于控件初始化 */
    try {
      var raw = localStorage.getItem(STORE_KEY) || localStorage.getItem('pagebell.v1');
      if (!raw) return;
      var d = JSON.parse(raw);
      var src = d.state || d;
      Object.keys(state).forEach(function (k) {
        if (src[k] !== undefined) state[k] = src[k];
      });
    } catch (e) { /* 忽略损坏数据 */ }
  }
  function save() {
    try { localStorage.setItem(STORE_KEY, JSON.stringify(state)); } catch (e) { /* 隐私模式静默 */ }
  }

  /* ---------------- 声音引擎 ---------------- */
  var AC = null;
  function ctx() {
    if (!AC) {
      var C = window.AudioContext || window.webkitAudioContext;
      if (!C) return null;
      AC = new C();
    }
    if (AC.state === 'suspended') AC.resume();
    return AC;
  }

  // 音色 → 音符序列 {f 频率倍率, d 时长, t 波形, g 增益, at 延迟}
  var VOICES = {
    beep: function () {
      return [{ f: 1, d: .10, t: 'sine', g: .9, at: 0 }];
    },
    bell: function () {
      return [
        { f: 1, d: .62, t: 'triangle', g: .55, at: 0 },
        { f: 2.01, d: .40, t: 'sine', g: .20, at: 0 },
        { f: 2.98, d: .26, t: 'sine', g: .08, at: 0 }
      ];
    },
    wood: function () {
      return [
        { f: .26, d: .11, t: 'square', g: .34, at: 0 },
        { f: .19, d: .16, t: 'sine', g: .40, at: 0 }
      ];
    },
    piano: function () {
      return [
        { f: 1, d: .95, t: 'sine', g: .48, at: 0 },
        { f: 2, d: .62, t: 'sine', g: .15, at: 0 },
        { f: 3, d: .40, t: 'sine', g: .07, at: 0 },
        { f: 4.02, d: .24, t: 'sine', g: .03, at: 0 }
      ];
    },
    chime: function () {
      return [
        { f: 1, d: .78, t: 'sine', g: .40, at: 0 },
        { f: 1.5, d: .58, t: 'sine', g: .18, at: .06 },
        { f: 2, d: .40, t: 'sine', g: .08, at: .12 }
      ];
    }
  };

  function playNote(freq, dur, type, gain, at) {
    var c = ctx();
    if (!c) return;
    var t0 = c.currentTime + (at || 0);
    var osc = c.createOscillator();
    var amp = c.createGain();
    osc.type = type || 'sine';
    osc.frequency.setValueAtTime(freq, t0);
    amp.gain.setValueAtTime(0.0001, t0);
    amp.gain.exponentialRampToValueAtTime(Math.max(gain, 0.0002), t0 + 0.012);
    amp.gain.exponentialRampToValueAtTime(0.0001, t0 + dur);
    osc.connect(amp);
    amp.connect(c.destination);
    osc.start(t0);
    osc.stop(t0 + dur + 0.05);
  }

  // 一次提醒：state.beats 声，声间隔 0.18s
  function chime() {
    var notes = (VOICES[state.voice] || VOICES.beep)();
    var gap = 0.18;
    for (var i = 0; i < state.beats; i++) {
      for (var j = 0; j < notes.length; j++) {
        var n = notes[j];
        playNote(state.freq * n.f, n.d, n.t, (state.volume / 100) * n.g, n.at + i * gap);
      }
    }
  }

  /* ---------------- 提醒 ---------------- */
  var btnRemind = $('#btnRemind');

  function remind() {
    chime();
    btnRemind.classList.remove('flash');
    void btnRemind.offsetWidth;
    btnRemind.classList.add('flash');
    if (state.ripple) ripple();
    var b = $('#breath');
    b.classList.remove('pulse');
    void b.offsetWidth;
    b.classList.add('pulse');
    poke();
  }

  function ripple() {
    var layer = $('#rippleLayer');
    var el = document.createElement('span');
    el.className = 'ripple';
    var r = $('#stage').getBoundingClientRect();
    el.style.left = (r.left + r.width / 2) + 'px';
    el.style.top = (r.top + r.height / 2) + 'px';
    layer.appendChild(el);
    setTimeout(function () { el.remove(); }, 1500);
  }

  /* ---------------- 窗口透明度 ---------------- */
  function applyOpacity() {
    if (isNative && IS_APP_SHELL) {
      // 桌面版：整窗真半透明交给窗口层，CSS 侧保持不透明避免叠加衰减
      document.documentElement.style.setProperty('--ui-opacity', '1');
      pushWindowState();
      return;
    }
    document.documentElement.style.setProperty('--ui-opacity', String(state.opacity));
  }

  /* ---------------- 沉浸隐藏 ---------------- */
  var idleTimer = null;
  function poke() {
    document.body.classList.remove('is-idle');
    clearTimeout(idleTimer);
    idleTimer = setTimeout(function () {
      if (state.immerse) document.body.classList.add('is-idle');
    }, state.idleSec * 1000);
  }

  ['mousemove', 'mousedown', 'wheel', 'touchstart', 'keydown', 'focus'].forEach(function (ev) {
    window.addEventListener(ev, poke, { passive: true });
  });
  document.addEventListener('visibilitychange', function () { if (!document.hidden) poke(); });

  /* ---------------- 屏幕常亮 ---------------- */
  var wakeRef = null;
  function requestWake() {
    if (!('wakeLock' in navigator)) return;
    navigator.wakeLock.request('screen').then(function (l) {
      wakeRef = l;
      l.addEventListener('release', function () { wakeRef = null; });
    }).catch(function () { /* 不支持则静默 */ });
  }
  function releaseWake() {
    if (wakeRef) { try { wakeRef.release(); } catch (e) {} wakeRef = null; }
  }

  /* ---------------- 控件 ---------------- */
  load(); // 必须早于任何控件初始化，否则 UI 与已存设置不同步

  function bindRange(id, key, fmt, after) {
    var el = $(id);
    var out = $(id.replace('rng', 'val'));
    el.value = state[key];
    out.textContent = fmt(state[key]);
    el.addEventListener('input', function () {
      state[key] = parseFloat(el.value);
      out.textContent = fmt(state[key]);
      if (after) after();
      save(); poke();
    });
  }

  bindRange('#rngFreq', 'freq', function (v) { return v + ' Hz'; });
  bindRange('#rngVol', 'volume', function (v) { return v + '%'; });
  bindRange('#rngBeats', 'beats', function (v) { return v + ' 声'; });
  bindRange('#rngIdle', 'idleSec', function (v) { return v + ' 秒'; }, poke);
  bindRange('#rngOpacity', 'opacity', function (v) { return Math.round(v * 100) + '%'; }, applyOpacity);

  $$('#voices .chip').forEach(function (c) {
    c.classList.toggle('is-on', c.dataset.voice === state.voice);
    c.addEventListener('click', function () {
      state.voice = c.dataset.voice;
      $$('#voices .chip').forEach(function (x) { x.classList.toggle('is-on', x === c); });
      chime();
      save(); poke();
    });
  });

  function bindSwitch(id, key, after) {
    var el = $(id);
    el.checked = !!state[key];
    el.addEventListener('change', function () {
      state[key] = el.checked;
      if (after) after();
      save(); poke();
    });
  }
  bindSwitch('#swRipple', 'ripple');
  bindSwitch('#swImmerse', 'immerse', poke);
  bindSwitch('#swWake', 'wakeLock', function () {
    if (state.wakeLock) { requestWake(); chime(); } else releaseWake();
  });

  btnRemind.addEventListener('click', remind);

  /* ---------------- 主题 ---------------- */
  function applyTheme() {
    document.body.dataset.theme = state.theme;
    document.documentElement.dataset.theme = state.theme;
    $('#btnTheme').textContent = state.theme === 'dark' ? '日间' : '夜间';
  }
  $('#btnTheme').addEventListener('click', function () {
    state.theme = state.theme === 'dark' ? 'light' : 'dark';
    applyTheme(); save(); poke();
    if (isNative) setTimeout(pushWindowState, 80);
  });

  /* ---------------- 迷你贴边（可拖动） ---------------- */
  function toggleMini(force) {
    state.mini = force === undefined ? !state.mini : force;
    document.body.classList.toggle('is-mini', state.mini);
    $('#btnMini').textContent = state.mini ? '展开' : '迷你';
    var st = $('#stage');
    st.style.left = ''; st.style.top = '';
    save(); poke();
    if (isNative) setTimeout(pushWindowState, 80);
  }
  $('#btnMini').addEventListener('click', function () { toggleMini(); });
  $('#btnUnfold').addEventListener('click', function () { toggleMini(false); });

  (function enableDrag() {
    var st = $('#stage');
    var dragging = false, sx = 0, sy = 0, ox = 0, oy = 0;
    st.addEventListener('mousedown', function (e) {
      if (!state.mini || e.target.closest('button, input, label')) return;
      dragging = true;
      var r = st.getBoundingClientRect();
      ox = r.left; oy = r.top; sx = e.clientX; sy = e.clientY;
      st.style.right = 'auto';
      st.style.left = ox + 'px';
      st.style.top = oy + 'px';
      e.preventDefault();
    });
    window.addEventListener('mousemove', function (e) {
      if (!dragging) return;
      st.style.left = (ox + e.clientX - sx) + 'px';
      st.style.top = (oy + e.clientY - sy) + 'px';
    });
    window.addEventListener('mouseup', function () { dragging = false; });
  })();

  /* ---------------- 全屏 ---------------- */
  $('#btnFull').addEventListener('click', function () {
    if (!document.fullscreenElement) {
      if (document.documentElement.requestFullscreen) document.documentElement.requestFullscreen();
    } else if (document.exitFullscreen) {
      document.exitFullscreen();
    }
    poke();
  });

  /* ---------------- 键盘 ---------------- */
  window.addEventListener('keydown', function (e) {
    var tag = (e.target.tagName || '').toLowerCase();
    if (tag === 'input' && e.target.type === 'range') return;

    if (e.code === 'Space') { e.preventDefault(); remind(); return; }
    var k = e.key.toLowerCase();
    if (k === 'f') { $('#btnFull').click(); return; }
    if (k === 'm') { toggleMini(); return; }
    if (k === 't') { $('#btnTheme').click(); return; }
    if (e.key === 'Escape' && document.fullscreenElement) { document.exitFullscreen(); }
  });

  /* ---------------- 首次交互解锁音频 ---------------- */
  var note = $('#audioNote');
  function unlockAudio() {
    ctx();
    note.classList.add('gone');
    window.removeEventListener('pointerdown', unlockAudio);
    window.removeEventListener('keydown', unlockAudio);
  }
  window.addEventListener('pointerdown', unlockAudio);
  window.addEventListener('keydown', unlockAudio);

  /* ---------------- 桌面应用模式（Electron 窗口） ---------------- */
  var shell = window.pagebell || null;                    // 桌面壳注入的接口
  var IS_APP_SHELL = !!shell || /(\?|&)app=1(&|$)/.test(location.search);
  var SHELL_PAD = 20;                                     // 与 main.js 的 PAD 一致（投影留白）

  function setPinUI(on) { $('#btnPin').classList.toggle('is-on', !!on); }

  /* 把卡片实际尺寸与透明度交给窗口，桌面版靠它贴合内容 */
  function pushWindowState(cmd) {
    if (cmd === 'quit') {
      if (shell) shell.quit();
      return;
    }
    if (!isNative || !shell) return;
    var st = $('#stage');
    var cssW = state.mini ? 214 : 622;
    var cssH = Math.ceil(st.getBoundingClientRect().height) || 320;
    shell.resize(cssW + SHELL_PAD * 2, cssH + SHELL_PAD * 2);
    shell.setAlpha(state.opacity);
  }

  function initNative() {
    if (isNative) return;
    isNative = true;
    document.body.classList.add('native');
    setPinUI(true);                 // 窗口创建时默认置顶
    applyOpacity();
    setTimeout(pushWindowState, 200);   // 首帧后按真实高度贴合窗口
    setTimeout(pushWindowState, 700);   // 字体就绪后再校准一次
  }

  $('#btnMin').addEventListener('click', function () {
    if (shell) shell.minimize();
  });

  $('#btnClose').addEventListener('click', function () { pushWindowState('quit'); });
  $('#btnPin').addEventListener('click', function () {
    if (shell) shell.toggleTop().then(setPinUI);
    else setPinUI(!$('#btnPin').classList.contains('is-on'));
  });

  if (IS_APP_SHELL) initNative();

  /* ---------------- 启动 ---------------- */
  if (IS_APP_SHELL) state.mini = false;   // 桌面版每次启动都以完整窗口打开
  applyTheme();
  applyOpacity();
  if (state.mini && !IS_APP_SHELL) toggleMini(true);
  if (state.wakeLock) requestWake();
  poke();
})();
