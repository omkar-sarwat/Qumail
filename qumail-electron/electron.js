const { app, BrowserWindow, ipcMain, protocol } = require('electron');
const path = require('path');
const isDev = process.argv.includes('--dev');
const api = require('./src/main/api');
const storage = require('./src/main/storage');
const { startGoogleOAuth } = require('./src/main/oauth');

let mainWindow;
let splashWindow;

function getRendererEntry() {
  if (isDev && process.env.VITE_DEV_SERVER_URL) {
    return process.env.VITE_DEV_SERVER_URL;
  }
  return path.join(__dirname, 'dist', 'renderer', 'index.html');
}

function createSplashWindow() {
  splashWindow = new BrowserWindow({
    width: 500,
    height: 400,
    transparent: true,
    frame: false,
    alwaysOnTop: true,
    resizable: false,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true
    }
  });

  splashWindow.loadFile(path.join(__dirname, 'splash.html'));
  splashWindow.center();
}

function createWindow() {
  // Create the browser window.
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 1024,
    minHeight: 700,
    show: false, // Don't show until ready
    fullscreen: true,
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

  // Wait for main window to be ready
  mainWindow.once('ready-to-show', () => {
    // Keep splash screen for at least 2.5 seconds to show animation
    setTimeout(() => {
      if (splashWindow) {
        splashWindow.close();
        splashWindow = null;
      }
      mainWindow.show();
      mainWindow.focus();
    }, 2500);
  });
}

app.whenReady().then(() => {
  protocol.registerSchemesAsPrivileged([{ scheme: 'qumail', privileges: { secure: true, standard: true } }]);
  
  createSplashWindow();
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
