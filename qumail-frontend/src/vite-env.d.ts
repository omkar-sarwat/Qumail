/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string
  readonly VITE_APP_VERSION: string
  readonly VITE_APP_NAME: string
  readonly VITE_GOOGLE_CLIENT_ID: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

// Electron API types
interface ElectronAPI {
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

interface Window {
  electronAPI?: ElectronAPI
}