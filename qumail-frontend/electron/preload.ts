import { contextBridge, ipcRenderer } from 'electron'

// Database response type
interface DbResponse<T = any> {
  success: boolean
  data?: T
  error?: string
}

// Local email type
interface LocalEmail {
  id: string
  thread_id?: string
  gmail_message_id?: string
  subject: string
  sender_email: string
  sender_name?: string
  recipient_email: string
  body?: string
  body_html?: string
  body_encrypted?: string
  snippet?: string
  folder: string
  is_read: boolean
  is_starred: boolean
  is_encrypted: boolean
  is_decrypted: boolean
  globally_decrypted: boolean
  security_level?: number
  flow_id?: string
  algorithm?: string
  quantum_enhanced: boolean
  decrypted_content?: string
  decrypted_html?: string
  security_info?: string
  encryption_metadata?: string
  attachments?: string
  timestamp: string
  synced_at?: string
  last_modified: string
  sync_status: 'synced' | 'pending_upload' | 'pending_download' | 'conflict'
}

interface SyncQueueItem {
  id: number
  operation: string
  email_id: string
  data?: string
  created_at: string
  attempts: number
  last_error?: string
}

interface DecryptedEmailCache {
  email_id: string
  flow_id?: string
  decrypted_body: string
  decrypted_html?: string
  security_info: string
  cached_at: string
}

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

  // ==================== LOCAL DATABASE API ====================
  db: {
    // Email operations
    getEmails: (folder: string, limit?: number, offset?: number) => Promise<DbResponse<LocalEmail[]>>
    getEmail: (id: string) => Promise<DbResponse<LocalEmail | undefined>>
    getEmailByFlowId: (flowId: string) => Promise<DbResponse<LocalEmail | undefined>>
    saveEmail: (email: Partial<LocalEmail>) => Promise<DbResponse>
    saveEmails: (emails: Partial<LocalEmail>[]) => Promise<DbResponse>
    updateEmail: (id: string, updates: Partial<LocalEmail>) => Promise<DbResponse>
    deleteEmail: (id: string) => Promise<DbResponse>
    getEmailCounts: () => Promise<DbResponse<Record<string, number>>>
    getUnreadCounts: () => Promise<DbResponse<Record<string, number>>>
    searchEmails: (query: string, folder?: string) => Promise<DbResponse<LocalEmail[]>>
    
    // Sync queue operations
    addToSyncQueue: (operation: string, emailId: string, data?: any) => Promise<DbResponse>
    getPendingSync: (limit?: number) => Promise<DbResponse<SyncQueueItem[]>>
    completeSyncItem: (id: number) => Promise<DbResponse>
    failSyncItem: (id: number, error: string) => Promise<DbResponse>
    getSyncQueueCount: () => Promise<DbResponse<number>>
    
    // Decryption cache
    getCachedDecryption: (emailId: string) => Promise<DbResponse<DecryptedEmailCache | undefined>>
    cacheDecryption: (cache: DecryptedEmailCache) => Promise<DbResponse>
    
    // Settings
    getSetting: (key: string) => Promise<DbResponse<string | undefined>>
    setSetting: (key: string, value: string) => Promise<DbResponse>
    
    // Sync metadata
    getLastSync: () => Promise<DbResponse<string | undefined>>
    setLastSync: (time: string) => Promise<DbResponse>
    
    // Stats and maintenance
    getStats: () => Promise<DbResponse<{
      totalEmails: number
      decryptedEmails: number
      pendingSyncCount: number
      lastSync: string | undefined
    }>>
    clearAll: () => Promise<DbResponse>
  }
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

  // ==================== LOCAL DATABASE API ====================
  db: {
    // Email operations
    getEmails: (folder, limit, offset) => ipcRenderer.invoke('db-get-emails', folder, limit, offset),
    getEmail: (id) => ipcRenderer.invoke('db-get-email', id),
    getEmailByFlowId: (flowId) => ipcRenderer.invoke('db-get-email-by-flow-id', flowId),
    saveEmail: (email) => ipcRenderer.invoke('db-save-email', email),
    saveEmails: (emails) => ipcRenderer.invoke('db-save-emails', emails),
    updateEmail: (id, updates) => ipcRenderer.invoke('db-update-email', id, updates),
    deleteEmail: (id) => ipcRenderer.invoke('db-delete-email', id),
    getEmailCounts: () => ipcRenderer.invoke('db-get-email-counts'),
    getUnreadCounts: () => ipcRenderer.invoke('db-get-unread-counts'),
    searchEmails: (query, folder) => ipcRenderer.invoke('db-search-emails', query, folder),
    
    // Sync queue operations
    addToSyncQueue: (operation, emailId, data) => ipcRenderer.invoke('db-add-to-sync-queue', operation, emailId, data),
    getPendingSync: (limit) => ipcRenderer.invoke('db-get-pending-sync', limit),
    completeSyncItem: (id) => ipcRenderer.invoke('db-complete-sync-item', id),
    failSyncItem: (id, error) => ipcRenderer.invoke('db-fail-sync-item', id, error),
    getSyncQueueCount: () => ipcRenderer.invoke('db-get-sync-queue-count'),
    
    // Decryption cache
    getCachedDecryption: (emailId) => ipcRenderer.invoke('db-get-cached-decryption', emailId),
    cacheDecryption: (cache) => ipcRenderer.invoke('db-cache-decryption', cache),
    
    // Settings
    getSetting: (key) => ipcRenderer.invoke('db-get-setting', key),
    setSetting: (key, value) => ipcRenderer.invoke('db-set-setting', key, value),
    
    // Sync metadata
    getLastSync: () => ipcRenderer.invoke('db-get-last-sync'),
    setLastSync: (time) => ipcRenderer.invoke('db-set-last-sync', time),
    
    // Stats and maintenance
    getStats: () => ipcRenderer.invoke('db-get-stats'),
    clearAll: () => ipcRenderer.invoke('db-clear-all'),
  },
}

contextBridge.exposeInMainWorld('electronAPI', electronAPI)
