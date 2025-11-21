// Types for Electron API exposed through preload script

export interface ElectronAPI {
  showNotification: (options: { title: string; body: string; silent?: boolean }) => Promise<boolean>
  showSaveDialog: (options?: any) => Promise<{ canceled: boolean; filePath?: string }>
  showOpenDialog: (options?: any) => Promise<{ canceled: boolean; filePaths?: string[] }>
  getAppVersion: () => Promise<string>
  openExternal: (url: string) => Promise<void>
  onMainProcessMessage: (callback: (message: string) => void) => void
  removeAllListeners: (channel: string) => void
}

declare global {
  interface Window {
    electronAPI: ElectronAPI
  }
}

export {}