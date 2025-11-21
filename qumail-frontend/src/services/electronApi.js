/**
 * Electron API wrapper for frontend
 * Provides seamless integration between React app and Electron native features
 */
// Check if running in Electron
export const isElectron = () => {
    return typeof window !== 'undefined' && typeof window.electronAPI !== 'undefined';
};
// Get Electron API (with fallback for web)
export const getElectronAPI = () => {
    if (isElectron()) {
        return window.electronAPI || null;
    }
    return null;
};
// Safe API call wrapper
export const callElectronAPI = async (apiCall, fallback) => {
    const api = getElectronAPI();
    if (api) {
        try {
            return await apiCall(api);
        }
        catch (error) {
            console.error('[Electron API Error]', error);
            return fallback;
        }
    }
    return fallback;
};
// Notification helper
export const showNotification = async (title, body, silent = false) => {
    if (isElectron()) {
        const api = getElectronAPI();
        await api?.showNotification({ title, body, silent });
    }
    else {
        // Fallback to web notifications
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification(title, { body, silent });
        }
    }
};
// File dialog helpers
export const openFileDialog = async (options) => {
    return callElectronAPI(api => api.showOpenDialog(options));
};
export const saveFileDialog = async (options) => {
    return callElectronAPI(api => api.showSaveDialog(options));
};
// Backend API request helper
export const makeBackendRequest = async (method, url, data, headers) => {
    if (isElectron()) {
        const api = getElectronAPI();
        if (api) {
            const result = await api.apiRequest({ method, url, data, headers });
            if (result.success) {
                return result.data;
            }
            else {
                throw new Error(result.error || 'Backend request failed');
            }
        }
    }
    // Fallback to direct HTTP (for web or dev mode)
    const backendUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    const response = await fetch(`${backendUrl}${url}`, {
        method,
        headers: {
            'Content-Type': 'application/json',
            ...headers,
        },
        body: data ? JSON.stringify(data) : undefined,
    });
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return response.json();
};
// App info helper
export const getAppInfo = async () => {
    return callElectronAPI(api => api.getAppInfo(), {
        version: '1.0.0',
        name: 'QuMail',
        platform: 'web',
        isDev: true,
    });
};
// Backend status helper
export const checkBackendStatus = async () => {
    const status = await callElectronAPI(api => api.getBackendStatus());
    return status?.online || false;
};
// External link helper
export const openExternalLink = async (url) => {
    if (isElectron()) {
        const api = getElectronAPI();
        await api?.openExternal(url);
    }
    else {
        window.open(url, '_blank', 'noopener,noreferrer');
    }
};
// File operations
export const readFile = async (filePath) => {
    const result = await callElectronAPI(api => api.readFile(filePath));
    return result?.success ? result.content || null : null;
};
export const writeFile = async (filePath, content) => {
    const result = await callElectronAPI(api => api.writeFile(filePath, content));
    return result?.success || false;
};
// Event listeners
export const onNewEmail = (callback) => {
    const api = getElectronAPI();
    api?.onNewEmail(callback);
};
export const onOpenSettings = (callback) => {
    const api = getElectronAPI();
    api?.onOpenSettings(callback);
};
export const removeElectronListener = (channel) => {
    const api = getElectronAPI();
    api?.removeAllListeners(channel);
};
export default {
    isElectron,
    getElectronAPI,
    callElectronAPI,
    showNotification,
    openFileDialog,
    saveFileDialog,
    makeBackendRequest,
    getAppInfo,
    checkBackendStatus,
    openExternalLink,
    readFile,
    writeFile,
    onNewEmail,
    onOpenSettings,
    removeElectronListener,
};
