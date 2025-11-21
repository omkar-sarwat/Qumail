const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('qumail', {
  loadSession: () => ipcRenderer.invoke('session:load'),
  clearSession: () => ipcRenderer.invoke('session:clear'),
  loginWithGoogle: () => ipcRenderer.invoke('oauth:login'),
  sendEncryptedEmail: (payload) => ipcRenderer.invoke('messages:send', payload),
  getInbox: () => ipcRenderer.invoke('messages:inbox'),
  decryptEmail: (messageId) => ipcRenderer.invoke('messages:decrypt', messageId)
});
