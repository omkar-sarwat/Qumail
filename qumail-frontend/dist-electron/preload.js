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
    // ==================== LOCAL DATABASE API ====================
    db: {
        // Email operations
        getEmails: function (folder, limit, offset) { return electron_1.ipcRenderer.invoke('db-get-emails', folder, limit, offset); },
        getEmail: function (id) { return electron_1.ipcRenderer.invoke('db-get-email', id); },
        getEmailByFlowId: function (flowId) { return electron_1.ipcRenderer.invoke('db-get-email-by-flow-id', flowId); },
        saveEmail: function (email) { return electron_1.ipcRenderer.invoke('db-save-email', email); },
        saveEmails: function (emails) { return electron_1.ipcRenderer.invoke('db-save-emails', emails); },
        updateEmail: function (id, updates) { return electron_1.ipcRenderer.invoke('db-update-email', id, updates); },
        deleteEmail: function (id) { return electron_1.ipcRenderer.invoke('db-delete-email', id); },
        getEmailCounts: function () { return electron_1.ipcRenderer.invoke('db-get-email-counts'); },
        getUnreadCounts: function () { return electron_1.ipcRenderer.invoke('db-get-unread-counts'); },
        searchEmails: function (query, folder) { return electron_1.ipcRenderer.invoke('db-search-emails', query, folder); },
        // Sync queue operations
        addToSyncQueue: function (operation, emailId, data) { return electron_1.ipcRenderer.invoke('db-add-to-sync-queue', operation, emailId, data); },
        getPendingSync: function (limit) { return electron_1.ipcRenderer.invoke('db-get-pending-sync', limit); },
        completeSyncItem: function (id) { return electron_1.ipcRenderer.invoke('db-complete-sync-item', id); },
        failSyncItem: function (id, error) { return electron_1.ipcRenderer.invoke('db-fail-sync-item', id, error); },
        getSyncQueueCount: function () { return electron_1.ipcRenderer.invoke('db-get-sync-queue-count'); },
        // Decryption cache
        getCachedDecryption: function (emailId) { return electron_1.ipcRenderer.invoke('db-get-cached-decryption', emailId); },
        cacheDecryption: function (cache) { return electron_1.ipcRenderer.invoke('db-cache-decryption', cache); },
        // Settings
        getSetting: function (key) { return electron_1.ipcRenderer.invoke('db-get-setting', key); },
        setSetting: function (key, value) { return electron_1.ipcRenderer.invoke('db-set-setting', key, value); },
        // Sync metadata
        getLastSync: function () { return electron_1.ipcRenderer.invoke('db-get-last-sync'); },
        setLastSync: function (time) { return electron_1.ipcRenderer.invoke('db-set-last-sync', time); },
        // Stats and maintenance
        getStats: function () { return electron_1.ipcRenderer.invoke('db-get-stats'); },
        clearAll: function () { return electron_1.ipcRenderer.invoke('db-clear-all'); },
    },
};
electron_1.contextBridge.exposeInMainWorld('electronAPI', electronAPI);
