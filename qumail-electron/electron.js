const { app, BrowserWindow, ipcMain, protocol } = require('electron');
const path = require('path');
const isDev = process.argv.includes('--dev');
const api = require('./src/main/api');
const storage = require('./src/main/storage');
const { startGoogleOAuth } = require('./src/main/oauth');

let mainWindow;

function getRendererEntry() {
  if (isDev && process.env.VITE_DEV_SERVER_URL) {
    return process.env.VITE_DEV_SERVER_URL;
  }
  return path.join(__dirname, 'dist', 'renderer', 'index.html');
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 1024,
    minHeight: 700,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    }
  });

  const rendererEntry = getRendererEntry();
  if (rendererEntry.startsWith('http')) {
    mainWindow.loadURL(rendererEntry);
  } else {
    mainWindow.loadFile(rendererEntry);
  }

  if (isDev) {
    mainWindow.webContents.openDevTools();
  }
}

app.whenReady().then(() => {
  protocol.registerSchemesAsPrivileged([{ scheme: 'qumail', privileges: { secure: true, standard: true } }]);
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

ipcMain.handle('session:load', () => {
  return storage.loadSession();
});

ipcMain.handle('session:clear', () => {
  storage.clearSession();
  return true;
});

ipcMain.handle('oauth:login', async () => {
  const session = await startGoogleOAuth();
  if (session?.user && session?.jwt) {
    storage.saveSession(session.user, session.jwt);
  }
  return session;
});

ipcMain.handle('messages:send', async (_event, payload) => {
  return api.sendEncryptedEmail(payload.to, payload.subject, payload.body, payload.securityLevel);
});

ipcMain.handle('messages:inbox', async () => {
  return api.getInbox();
});

ipcMain.handle('messages:decrypt', async (_event, messageId) => {
  return api.decryptEmail(messageId);
});
