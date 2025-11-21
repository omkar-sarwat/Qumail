import { contextBridge, ipcRenderer } from 'electron'

// Type definitions for the exposed API
export interface ElectronAPI {
  // Backend API
  apiRequest: (params: {
    method: string
    url: string
    data?: any
    headers?: Record<string, string>
  }) => Promise<{
    success: boolean
    data?: any
    error?: string
    status: number
  }>

  // App info
  getAppInfo: () => Promise<{
    version: string
    name: string
    platform: string
    isDev: boolean
  }>
  getAppVersion: () => Promise<string>

  // Window controls
  minimizeWindow: () => Promise<void>
  maximizeWindow: () => Promise<void>
  closeWindow: () => Promise<void>
  isMaximized: () => Promise<boolean>

  // OAuth
  getOAuthCallback: () => Promise<string | null>
  startOAuthFlow: (params: { authUrl: string; state: string }) => Promise<{ code: string; state: string }>

  // Notifications
  showNotification: (params: { title: string; body: string; silent?: boolean }) => Promise<boolean>

  // File dialogs
  showOpenDialog: (options?: any) => Promise<any>
  showSaveDialog: (options?: any) => Promise<any>

  // File operations
  readFile: (filePath: string) => Promise<{ success: boolean; content?: string; error?: string }>
  writeFile: (filePath: string, content: string) => Promise<{ success: boolean; error?: string }>

  // Backend status
  getBackendStatus: () => Promise<{ online: boolean; data?: any }>

  // External links
  openExternal: (url: string) => Promise<void>

  // Event listeners
  onMainProcessMessage: (callback: (message: string) => void) => void
  onNewEmail: (callback: () => void) => void
  onOpenSettings: (callback: () => void) => void
  removeAllListeners: (channel: string) => void
}

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
const electronAPI: ElectronAPI = {
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
  startOAuthFlow: (params: { authUrl: string; state: string }) => ipcRenderer.invoke('start-oauth-flow', params),

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
    ipcRenderer.on('main-process-message', (_, message) => callback(message))
  },
  onNewEmail: (callback) => {
    ipcRenderer.on('new-email', callback)
  },
  onOpenSettings: (callback) => {
    ipcRenderer.on('open-settings', callback)
  },
  removeAllListeners: (channel) => {
    ipcRenderer.removeAllListeners(channel)
  },
}

contextBridge.exposeInMainWorld('electronAPI', electronAPI)
