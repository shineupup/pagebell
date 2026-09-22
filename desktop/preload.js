// 暴露给页面的窗口接口（window.pagebell）
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('pagebell', {
  app: true,
  resize: function (w, h) { ipcRenderer.send('pb:size', w, h); },
  setAlpha: function (v) { ipcRenderer.send('pb:alpha', v); },
  toggleTop: function () { return ipcRenderer.invoke('pb:top'); },
  minimize: function () { ipcRenderer.send('pb:min'); },
  quit: function () { ipcRenderer.send('pb:quit'); }
});
