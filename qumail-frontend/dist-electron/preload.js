"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
var electron_1 = require("electron");
// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
var electronAPI = {
    // Backend API proxy
    apiRequest: function (params) { return electron_1.ipcRenderer.invoke('api-request', params); },
    // App info
    getAppInfo: function () { return electron_1.ipcRenderer.invoke('get-app-info'); },
    getAppVersion: function () { return electron_1.ipcRenderer.invoke('get-app-version'); },
    // Window controls
    minimizeWindow: function () { return electron_1.ipcRenderer.invoke('minimize-window'); },
    maximizeWindow: function () { return electron_1.ipcRenderer.invoke('maximize-window'); },
    closeWindow: function () { return electron_1.ipcRenderer.invoke('close-window'); },
    isMaximized: function () { return electron_1.ipcRenderer.invoke('is-maximized'); },
    // OAuth
    getOAuthCallback: function () { return electron_1.ipcRenderer.invoke('get-oauth-callback'); },
    startOAuthFlow: function (params) { return electron_1.ipcRenderer.invoke('start-oauth-flow', params); },
    // Notifications
    showNotification: function (params) { return electron_1.ipcRenderer.invoke('show-notification', params); },
    // File dialogs
    showOpenDialog: function (options) { return electron_1.ipcRenderer.invoke('show-open-dialog', options); },
    showSaveDialog: function (options) { return electron_1.ipcRenderer.invoke('show-save-dialog', options); },
    // File operations
    readFile: function (filePath) { return electron_1.ipcRenderer.invoke('read-file', filePath); },
    writeFile: function (filePath, content) { return electron_1.ipcRenderer.invoke('write-file', filePath, content); },
    // Backend status
    getBackendStatus: function () { return electron_1.ipcRenderer.invoke('get-backend-status'); },
    // External links
    openExternal: function (url) { return electron_1.ipcRenderer.invoke('open-external', url); },
    // Event listeners
    onMainProcessMessage: function (callback) {
        electron_1.ipcRenderer.on('main-process-message', function (_, message) { return callback(message); });
    },
    onNewEmail: function (callback) {
        electron_1.ipcRenderer.on('new-email', callback);
    },
    onOpenSettings: function (callback) {
        electron_1.ipcRenderer.on('open-settings', callback);
    },
    removeAllListeners: function (channel) {
        electron_1.ipcRenderer.removeAllListeners(channel);
    },
};
electron_1.contextBridge.exposeInMainWorld('electronAPI', electronAPI);
