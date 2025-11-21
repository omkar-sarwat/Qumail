const { BrowserWindow, shell } = require('electron');
const axios = require('axios');
const config = require('../../config');

const apiBase = process.env.QUMAIL_API_BASE_URL || config.apiBaseUrl;
const BACKEND_BASE_URL = apiBase.replace(/\/api\/v1$/, '');

async function startGoogleOAuth() {
  const authWindow = new BrowserWindow({
    width: 500,
    height: 650,
    show: false,
    webPreferences: {
      nodeIntegration: false
    }
  });

  const params = new URLSearchParams({
    redirect_uri: process.env.QUMAIL_OAUTH_REDIRECT || config.oauthRedirect
  });
  const oauthUrl = `${BACKEND_BASE_URL}/api/v1/auth/google/init?${params.toString()}`;

  authWindow.loadURL(oauthUrl);
  authWindow.show();

  return new Promise((resolve, reject) => {
    const handleNavigation = async (url) => {
      if (!url.startsWith(params.get('redirect_uri'))) {
        return;
      }
      const code = new URL(url).searchParams.get('code');
      try {
        const response = await axios.post(`${BACKEND_BASE_URL}/api/v1/auth/google/callback`, { code });
        resolve(response.data);
      } catch (error) {
        reject(error);
      } finally {
        authWindow.destroy();
      }
    };

    authWindow.webContents.on('will-redirect', (_event, url) => handleNavigation(url));
    authWindow.webContents.on('did-navigate', (_event, url) => handleNavigation(url));
    authWindow.on('closed', () => reject(new Error('OAuth window closed')));
    authWindow.webContents.setWindowOpenHandler(({ url }) => {
      shell.openExternal(url);
      return { action: 'deny' };
    });
  });
}

module.exports = { startGoogleOAuth };
