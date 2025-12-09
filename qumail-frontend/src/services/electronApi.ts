/**
 * Electron API wrapper for frontend
 * Provides seamless integration between React app and Electron native features
 */

export interface ElectronAPI {
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
  getAppInfo: () => Promise<{
    version: string
    name: string
    platform: string
    isDev: boolean
  }>
  getAppVersion: () => Promise<string>
  minimizeWindow: () => Promise<void>
  maximizeWindow: () => Promise<void>
  closeWindow: () => Promise<void>
  isMaximized: () => Promise<boolean>
  getOAuthCallback: () => Promise<string | null>
  showNotification: (params: { title: string; body: string; silent?: boolean }) => Promise<boolean>
  showOpenDialog: (options?: any) => Promise<any>
  showSaveDialog: (options?: any) => Promise<any>
  readFile: (filePath: string) => Promise<{ success: boolean; content?: string; error?: string }>
  writeFile: (filePath: string, content: string) => Promise<{ success: boolean; error?: string }>
  getBackendStatus: () => Promise<{ online: boolean; data?: any }>
  openExternal: (url: string) => Promise<void>
  onMainProcessMessage: (callback: (message: string) => void) => void
  onNewEmail: (callback: () => void) => void
  onOpenSettings: (callback: () => void) => void
  removeAllListeners: (channel: string) => void
}

// Check if running in Electron
export const isElectron = (): boolean => {
  return typeof window !== 'undefined' && typeof window.electronAPI !== 'undefined'
}

// Get Electron API (with fallback for web)
export const getElectronAPI = (): ElectronAPI | null => {
  if (isElectron()) {
    return window.electronAPI || null
  }
  return null
}

// Safe API call wrapper
export const callElectronAPI = async <T = any>(
  apiCall: (api: ElectronAPI) => Promise<T>,
  fallback?: T
): Promise<T | undefined> => {
  const api = getElectronAPI()
  if (api) {
    try {
      return await apiCall(api)
    } catch (error) {
      console.error('[Electron API Error]', error)
      return fallback
    }
  }
  return fallback
}

// Notification helper
export const showNotification = async (title: string, body: string, silent = false): Promise<void> => {
  if (isElectron()) {
    const api = getElectronAPI()
    await api?.showNotification({ title, body, silent })
  } else {
    // Fallback to web notifications
    if ('Notification' in window && Notification.permission === 'granted') {
      new Notification(title, { body, silent })
    }
  }
}

// File dialog helpers
export const openFileDialog = async (options?: any): Promise<any> => {
  return callElectronAPI(api => api.showOpenDialog(options))
}

export const saveFileDialog = async (options?: any): Promise<any> => {
  return callElectronAPI(api => api.showSaveDialog(options))
}

// Backend API request helper
export const makeBackendRequest = async (
  method: string,
  url: string,
  data?: any,
  headers?: Record<string, string>
): Promise<any> => {
  if (isElectron()) {
    const api = getElectronAPI()
    if (api) {
      const result = await api.apiRequest({ method, url, data, headers })
      if (result.success) {
        return result.data
      } else {
        throw new Error(result.error || 'Backend request failed')
      }
    }
  }
  
  // Fallback to direct HTTP (for web or dev mode)
  const backendUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
  const response = await fetch(`${backendUrl}${url}`, {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...headers,
    },
    body: data ? JSON.stringify(data) : undefined,
  })
  
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`)
  }
  
  return response.json()
}

// App info helper
export const getAppInfo = async () => {
  return callElectronAPI(api => api.getAppInfo(), {
    version: '1.0.0',
    name: 'QuMail',
    platform: 'web',
    isDev: true,
  })
}

// Backend status helper
export const checkBackendStatus = async (): Promise<boolean> => {
  const status = await callElectronAPI(api => api.getBackendStatus())
  return status?.online || false
}

// External link helper
export const openExternalLink = async (url: string): Promise<void> => {
  if (isElectron()) {
    const api = getElectronAPI()
    await api?.openExternal(url)
  } else {
    window.open(url, '_blank', 'noopener,noreferrer')
  }
}

// File operations
export const readFile = async (filePath: string): Promise<string | null> => {
  const result = await callElectronAPI(api => api.readFile(filePath))
  return result?.success ? result.content || null : null
}

export const writeFile = async (filePath: string, content: string): Promise<boolean> => {
  const result = await callElectronAPI(api => api.writeFile(filePath, content))
  return result?.success || false
}

// Event listeners
export const onNewEmail = (callback: () => void): void => {
  const api = getElectronAPI()
  api?.onNewEmail(callback)
}

export const onOpenSettings = (callback: () => void): void => {
  const api = getElectronAPI()
  api?.onOpenSettings(callback)
}

export const removeElectronListener = (channel: string): void => {
  const api = getElectronAPI()
  api?.removeAllListeners(channel)
}

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
}
