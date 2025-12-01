/**
 * Offline-First Service for QuMail
 * 
 * This service manages the local SQLite database for offline functionality
 * and syncs with MongoDB when online.
 * 
 * Architecture:
 * - Local SQLite database is the primary data source (instant access)
 * - When online, syncs with MongoDB backend
 * - All operations queue to sync when offline
 * - Preserves decrypted content for cross-device access
 */

// Types
export interface LocalEmail {
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

interface NetworkStatus {
  isOnline: boolean
  lastChecked: Date
}

// Check if running in Electron
const isElectron = (): boolean => {
  return !!(window as any).electronAPI?.db
}

// Get the electron API
const getElectronDB = () => {
  if (!isElectron()) {
    throw new Error('Not running in Electron - local database not available')
  }
  return (window as any).electronAPI.db
}

class OfflineService {
  private _isOnline: boolean = navigator.onLine
  private _syncInProgress: boolean = false
  private _listeners: Set<(status: NetworkStatus) => void> = new Set()
  private _syncInterval: ReturnType<typeof setInterval> | null = null

  constructor() {
    // Listen for online/offline events
    window.addEventListener('online', this.handleOnline)
    window.addEventListener('offline', this.handleOffline)
    
    // Initial status check
    this.checkNetworkStatus()
    
    // Start periodic sync when online
    this.startPeriodicSync()
  }

  // ==================== NETWORK STATUS ====================

  get isOnline(): boolean {
    return this._isOnline
  }

  get isElectronApp(): boolean {
    return isElectron()
  }

  private handleOnline = () => {
    console.log('🌐 Network: Online')
    this._isOnline = true
    this.notifyListeners()
    this.syncWithServer()
  }

  private handleOffline = () => {
    console.log('📴 Network: Offline')
    this._isOnline = false
    this.notifyListeners()
  }

  private async checkNetworkStatus(): Promise<void> {
    try {
      // Try to reach the backend
      const response = await fetch('https://qumail-backend-gwec.onrender.com/health', {
        method: 'GET',
        cache: 'no-store',
        signal: AbortSignal.timeout(5000)
      })
      this._isOnline = response.ok
    } catch {
      this._isOnline = navigator.onLine
    }
    this.notifyListeners()
  }

  addNetworkListener(callback: (status: NetworkStatus) => void): () => void {
    this._listeners.add(callback)
    // Immediately notify with current status
    callback({ isOnline: this._isOnline, lastChecked: new Date() })
    
    // Return unsubscribe function
    return () => {
      this._listeners.delete(callback)
    }
  }

  private notifyListeners(): void {
    const status: NetworkStatus = {
      isOnline: this._isOnline,
      lastChecked: new Date()
    }
    this._listeners.forEach(callback => callback(status))
  }

  // ==================== LOCAL DATABASE OPERATIONS ====================

  /**
   * Get emails from local database
   */
  async getLocalEmails(folder: string, limit: number = 100, offset: number = 0): Promise<LocalEmail[]> {
    if (!isElectron()) {
      console.warn('Not in Electron - skipping local DB')
      return []
    }

    try {
      const db = getElectronDB()
      const result = await db.getEmails(folder, limit, offset)
      
      if (result.success && result.data) {
        return result.data.map(this.normalizeLocalEmail)
      }
      
      return []
    } catch (error) {
      console.error('Failed to get local emails:', error)
      return []
    }
  }

  /**
   * Get a single email from local database
   */
  async getLocalEmail(id: string): Promise<LocalEmail | null> {
    if (!isElectron()) return null

    try {
      const db = getElectronDB()
      const result = await db.getEmail(id)
      
      if (result.success && result.data) {
        return this.normalizeLocalEmail(result.data)
      }
      
      return null
    } catch (error) {
      console.error('Failed to get local email:', error)
      return null
    }
  }

  /**
   * Save email to local database
   */
  async saveEmailLocally(email: Partial<LocalEmail>): Promise<boolean> {
    if (!isElectron()) return false

    try {
      const db = getElectronDB()
      const result = await db.saveEmail(email)
      return result.success
    } catch (error) {
      console.error('Failed to save email locally:', error)
      return false
    }
  }

  /**
   * Save multiple emails to local database
   */
  async saveEmailsLocally(emails: Partial<LocalEmail>[]): Promise<boolean> {
    if (!isElectron()) return false

    try {
      const db = getElectronDB()
      const result = await db.saveEmails(emails)
      return result.success
    } catch (error) {
      console.error('Failed to save emails locally:', error)
      return false
    }
  }

  /**
   * Update email in local database
   */
  async updateLocalEmail(id: string, updates: Partial<LocalEmail>): Promise<boolean> {
    if (!isElectron()) return false

    try {
      const db = getElectronDB()
      const result = await db.updateEmail(id, updates)
      
      // Add to sync queue if offline
      if (!this._isOnline && result.success) {
        await db.addToSyncQueue('update', id, updates)
      }
      
      return result.success
    } catch (error) {
      console.error('Failed to update local email:', error)
      return false
    }
  }

  /**
   * Mark email as read in local database
   */
  async markAsReadLocally(id: string, isRead: boolean = true): Promise<boolean> {
    if (!isElectron()) return false

    try {
      const db = getElectronDB()
      const result = await db.updateEmail(id, { is_read: isRead })
      
      // Add to sync queue
      if (result.success) {
        await db.addToSyncQueue('mark_read', id, { is_read: isRead })
      }
      
      return result.success
    } catch (error) {
      console.error('Failed to mark email as read locally:', error)
      return false
    }
  }

  /**
   * Mark email as starred in local database
   */
  async markAsStarredLocally(id: string, isStarred: boolean = true): Promise<boolean> {
    if (!isElectron()) return false

    try {
      const db = getElectronDB()
      const result = await db.updateEmail(id, { is_starred: isStarred })
      
      // Add to sync queue
      if (result.success) {
        await db.addToSyncQueue('mark_starred', id, { is_starred: isStarred })
      }
      
      return result.success
    } catch (error) {
      console.error('Failed to mark email as starred locally:', error)
      return false
    }
  }

  /**
   * Search emails in local database
   */
  async searchLocalEmails(query: string, folder?: string): Promise<LocalEmail[]> {
    if (!isElectron()) return []

    try {
      const db = getElectronDB()
      const result = await db.searchEmails(query, folder)
      
      if (result.success && result.data) {
        return result.data.map(this.normalizeLocalEmail)
      }
      
      return []
    } catch (error) {
      console.error('Failed to search local emails:', error)
      return []
    }
  }

  /**
   * Get email counts from local database
   */
  async getLocalEmailCounts(): Promise<Record<string, number>> {
    if (!isElectron()) return {}

    try {
      const db = getElectronDB()
      const result = await db.getEmailCounts()
      return result.success ? result.data : {}
    } catch (error) {
      console.error('Failed to get email counts:', error)
      return {}
    }
  }

  /**
   * Get unread counts from local database
   */
  async getLocalUnreadCounts(): Promise<Record<string, number>> {
    if (!isElectron()) return {}

    try {
      const db = getElectronDB()
      const result = await db.getUnreadCounts()
      return result.success ? result.data : {}
    } catch (error) {
      console.error('Failed to get unread counts:', error)
      return {}
    }
  }

  // ==================== DECRYPTION CACHE ====================

  /**
   * Get cached decrypted content
   */
  async getCachedDecryption(emailId: string): Promise<{
    decrypted_body: string
    decrypted_html?: string
    security_info: any
  } | null> {
    if (!isElectron()) return null

    try {
      const db = getElectronDB()
      const result = await db.getCachedDecryption(emailId)
      
      if (result.success && result.data) {
        return {
          decrypted_body: result.data.decrypted_body,
          decrypted_html: result.data.decrypted_html,
          security_info: result.data.security_info ? JSON.parse(result.data.security_info) : null
        }
      }
      
      return null
    } catch (error) {
      console.error('Failed to get cached decryption:', error)
      return null
    }
  }

  /**
   * Cache decrypted content
   */
  async cacheDecryption(
    emailId: string,
    flowId: string | undefined,
    decryptedBody: string,
    decryptedHtml: string | undefined,
    securityInfo: any
  ): Promise<boolean> {
    if (!isElectron()) return false

    try {
      const db = getElectronDB()
      const result = await db.cacheDecryption({
        email_id: emailId,
        flow_id: flowId,
        decrypted_body: decryptedBody,
        decrypted_html: decryptedHtml,
        security_info: JSON.stringify(securityInfo),
        cached_at: new Date().toISOString()
      })
      
      // Also update the email record
      if (result.success) {
        await db.updateEmail(emailId, {
          is_decrypted: true,
          globally_decrypted: true,
          decrypted_content: decryptedBody,
          decrypted_html: decryptedHtml,
          security_info: JSON.stringify(securityInfo)
        })
      }
      
      return result.success
    } catch (error) {
      console.error('Failed to cache decryption:', error)
      return false
    }
  }

  // ==================== SYNC OPERATIONS ====================

  /**
   * Sync local database with server
   */
  async syncWithServer(): Promise<void> {
    if (!isElectron() || !this._isOnline || this._syncInProgress) {
      return
    }

    this._syncInProgress = true
    console.log('🔄 Starting sync with server...')

    try {
      const db = getElectronDB()
      
      // 1. Process pending sync queue (upload local changes)
      await this.processSyncQueue()
      
      // 2. Update last sync time
      await db.setLastSync(new Date().toISOString())
      
      console.log('✅ Sync completed successfully')
    } catch (error) {
      console.error('❌ Sync failed:', error)
    } finally {
      this._syncInProgress = false
    }
  }

  /**
   * Process pending sync queue items
   */
  private async processSyncQueue(): Promise<void> {
    if (!isElectron()) return

    try {
      const db = getElectronDB()
      const pendingResult = await db.getPendingSync(50)
      
      if (!pendingResult.success || !pendingResult.data?.length) {
        return
      }

      console.log(`📤 Processing ${pendingResult.data.length} pending sync items...`)

      for (const item of pendingResult.data) {
        try {
          await this.processSyncItem(item)
          await db.completeSyncItem(item.id)
        } catch (error: any) {
          console.error(`Failed to sync item ${item.id}:`, error)
          await db.failSyncItem(item.id, error.message)
        }
      }
    } catch (error) {
      console.error('Failed to process sync queue:', error)
    }
  }

  /**
   * Process a single sync queue item
   */
  private async processSyncItem(item: any): Promise<void> {
    const data = item.data ? JSON.parse(item.data) : {}
    
    switch (item.operation) {
      case 'mark_read':
        await fetch(`https://qumail-backend-gwec.onrender.com/api/v1/emails/${item.email_id}/read`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('authToken')}`
          },
          body: JSON.stringify({ is_read: data.is_read })
        })
        break
        
      case 'mark_starred':
        await fetch(`https://qumail-backend-gwec.onrender.com/api/v1/emails/${item.email_id}/star`, {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('authToken')}`
          },
          body: JSON.stringify({ is_starred: data.is_starred })
        })
        break
        
      case 'delete':
        await fetch(`https://qumail-backend-gwec.onrender.com/api/v1/emails/${item.email_id}`, {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('authToken')}`
          }
        })
        break
        
      default:
        console.warn(`Unknown sync operation: ${item.operation}`)
    }
  }

  /**
   * Start periodic sync (every 30 seconds when online)
   */
  private startPeriodicSync(): void {
    if (this._syncInterval !== null) {
      clearInterval(this._syncInterval)
    }
    
    this._syncInterval = setInterval(() => {
      if (this._isOnline && !this._syncInProgress) {
        this.syncWithServer()
      }
    }, 30000) // 30 seconds
  }

  /**
   * Get sync queue count
   */
  async getPendingSyncCount(): Promise<number> {
    if (!isElectron()) return 0

    try {
      const db = getElectronDB()
      const result = await db.getSyncQueueCount()
      return result.success ? result.data : 0
    } catch (error) {
      console.error('Failed to get sync queue count:', error)
      return 0
    }
  }

  /**
   * Get database stats
   */
  async getDatabaseStats(): Promise<{
    totalEmails: number
    decryptedEmails: number
    pendingSyncCount: number
    lastSync: string | undefined
  } | null> {
    if (!isElectron()) return null

    try {
      const db = getElectronDB()
      const result = await db.getStats()
      return result.success ? result.data : null
    } catch (error) {
      console.error('Failed to get database stats:', error)
      return null
    }
  }

  // ==================== HELPERS ====================

  /**
   * Normalize a local email from SQLite format
   */
  private normalizeLocalEmail = (email: any): LocalEmail => {
    return {
      ...email,
      is_read: !!email.is_read,
      is_starred: !!email.is_starred,
      is_encrypted: !!email.is_encrypted,
      is_decrypted: !!email.is_decrypted,
      globally_decrypted: !!email.globally_decrypted,
      quantum_enhanced: !!email.quantum_enhanced,
      security_info: email.security_info ? 
        (typeof email.security_info === 'string' ? email.security_info : JSON.stringify(email.security_info)) 
        : undefined,
      encryption_metadata: email.encryption_metadata ?
        (typeof email.encryption_metadata === 'string' ? email.encryption_metadata : JSON.stringify(email.encryption_metadata))
        : undefined,
      attachments: email.attachments ?
        (typeof email.attachments === 'string' ? email.attachments : JSON.stringify(email.attachments))
        : undefined
    }
  }

  /**
   * Convert server email to local format
   */
  convertServerEmailToLocal(serverEmail: any): Partial<LocalEmail> {
    return {
      id: serverEmail.id || serverEmail.email_id || serverEmail.messageId,
      thread_id: serverEmail.threadId || serverEmail.thread_id,
      gmail_message_id: serverEmail.gmailMessageId || serverEmail.gmail_message_id,
      subject: serverEmail.subject || '',
      sender_email: serverEmail.sender_email || serverEmail.fromAddress || serverEmail.from || '',
      sender_name: serverEmail.sender_name || serverEmail.from_name || '',
      recipient_email: serverEmail.recipient_email || serverEmail.toAddress || serverEmail.to || '',
      body: serverEmail.body || serverEmail.bodyText || '',
      body_html: serverEmail.body_html || serverEmail.bodyHtml || '',
      body_encrypted: serverEmail.body_encrypted || serverEmail.bodyEncrypted || '',
      snippet: serverEmail.snippet || '',
      folder: serverEmail.folder || 'inbox',
      is_read: !!serverEmail.is_read || !!serverEmail.isRead,
      is_starred: !!serverEmail.is_starred || !!serverEmail.isStarred,
      is_encrypted: !!serverEmail.is_encrypted || !!serverEmail.isEncrypted || !!serverEmail.requires_decryption,
      is_decrypted: !!serverEmail.is_decrypted || !!serverEmail.isDecrypted,
      globally_decrypted: !!serverEmail.globally_decrypted || !!serverEmail.globallyDecrypted,
      security_level: serverEmail.security_level || serverEmail.securityLevel,
      flow_id: serverEmail.flow_id || serverEmail.flowId,
      algorithm: serverEmail.algorithm || serverEmail.security_info?.algorithm,
      quantum_enhanced: !!serverEmail.quantum_enhanced || !!serverEmail.security_info?.quantum_enhanced,
      decrypted_content: serverEmail.decrypted_content || serverEmail.decryptedContent,
      decrypted_html: serverEmail.decrypted_html || serverEmail.decryptedHtml,
      security_info: serverEmail.security_info ? JSON.stringify(serverEmail.security_info) : undefined,
      encryption_metadata: serverEmail.encryption_metadata ? JSON.stringify(serverEmail.encryption_metadata) : undefined,
      attachments: serverEmail.attachments ? JSON.stringify(serverEmail.attachments) : undefined,
      timestamp: serverEmail.timestamp || serverEmail.date || new Date().toISOString(),
      synced_at: new Date().toISOString(),
      last_modified: new Date().toISOString(),
      sync_status: 'synced'
    }
  }

  /**
   * Clear all local data (for logout)
   */
  async clearAllLocalData(): Promise<boolean> {
    if (!isElectron()) return false

    try {
      const db = getElectronDB()
      const result = await db.clearAll()
      return result.success
    } catch (error) {
      console.error('Failed to clear local data:', error)
      return false
    }
  }

  /**
   * Cleanup when service is destroyed
   */
  destroy(): void {
    window.removeEventListener('online', this.handleOnline)
    window.removeEventListener('offline', this.handleOffline)
    
    if (this._syncInterval !== null) {
      clearInterval(this._syncInterval)
      this._syncInterval = null
    }
    
    this._listeners.clear()
  }
}

// Singleton instance
export const offlineService = new OfflineService()
export default offlineService
