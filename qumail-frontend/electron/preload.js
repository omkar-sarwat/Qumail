import { contextBridge, ipcRenderer } from 'electron';
// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
const electronAPI = {
    // Backend API proxy
    apiRequest: (params) => ipcRenderer.invoke('api-request', params),
    // App info
    getAppInfo: () => ipcRenderer.invoke('get-app-info'),
    getAppVersion: () => ipcRenderer.invoke('get-app-version'),
    // Window controls
    minimizeWindow: () => ipcRenderer.invoke('minimize-window'),
    maximizeWindow: () => ipcRenderer.invoke('maximize-window'),
    closeWindow: () => ipcRenderer.invoke('close-window'),
    isMaximized: () => ipcRenderer.invoke('is-maximized'),
    // OAuth
    getOAuthCallback: () => ipcRenderer.invoke('get-oauth-callback'),
    startOAuthFlow: (params) => ipcRenderer.invoke('start-oauth-flow', params),
    // Notifications
    showNotification: (params) => ipcRenderer.invoke('show-notification', params),
    // File dialogs
    showOpenDialog: (options) => ipcRenderer.invoke('show-open-dialog', options),
    showSaveDialog: (options) => ipcRenderer.invoke('show-save-dialog', options),
    // File operations
    readFile: (filePath) => ipcRenderer.invoke('read-file', filePath),
    writeFile: (filePath, content) => ipcRenderer.invoke('write-file', filePath, content),
    // Backend status
    getBackendStatus: () => ipcRenderer.invoke('get-backend-status'),
    // External links
    openExternal: (url) => ipcRenderer.invoke('open-external', url),
    // Event listeners
    onMainProcessMessage: (callback) => {
        ipcRenderer.on('main-process-message', (_, message) => callback(message));
    },
    onNewEmail: (callback) => {
        ipcRenderer.on('new-email', callback);
    },
    onOpenSettings: (callback) => {
        ipcRenderer.on('open-settings', callback);
    },
    removeAllListeners: (channel) => {
        ipcRenderer.removeAllListeners(channel);
    },
};
contextBridge.exposeInMainWorld('electronAPI', electronAPI);
