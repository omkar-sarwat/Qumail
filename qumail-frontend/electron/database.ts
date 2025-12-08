// In-memory database replacement (no SQLite dependency)
// All data is stored in memory - persists during session only

// Types for database operations
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

export interface SyncQueueItem {
  id: number
  operation: 'create' | 'update' | 'delete' | 'mark_read' | 'mark_starred' | 'decrypt'
  email_id: string
  data?: string
  created_at: string
  attempts: number
  last_error?: string
}

export interface DecryptedEmailCache {
  email_id: string
  flow_id?: string
  decrypted_body: string
  decrypted_html?: string
  security_info: string
  cached_at: string
}

// In-memory storage
const store = {
  emails: new Map<string, LocalEmail>(),
  syncQueue: new Map<number, SyncQueueItem>(),
  decryptionCache: new Map<string, DecryptedEmailCache>(),
  settings: new Map<string, string>(),
  syncQueueIdCounter: 1,
  lastSyncTime: '',
}

// Initialize database (no-op for in-memory)
export function initDatabase(): void {
  console.log('[Database] Using in-memory storage (no SQLite)')
  console.log('[Database] In-memory database initialized')
}

// Close database (no-op for in-memory)
export function closeDatabase(): void {
  console.log('[Database] Closing in-memory storage')
}

// Get emails by folder
export function getEmails(folder: string, limit: number = 100, offset: number = 0): LocalEmail[] {
  const emails = Array.from(store.emails.values())
    .filter(e => folder === 'all' || e.folder === folder)
    .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
    .slice(offset, offset + limit)
  return emails
}

// Get email by ID
export function getEmailById(id: string): LocalEmail | undefined {
  return store.emails.get(id)
}

// Get email by flow ID
export function getEmailByFlowId(flowId: string): LocalEmail | undefined {
  return Array.from(store.emails.values()).find(e => e.flow_id === flowId)
}

// Save single email
export function saveEmail(email: LocalEmail): void {
  email.last_modified = new Date().toISOString()
  store.emails.set(email.id, email)
}

// Save multiple emails
export function saveEmails(emails: LocalEmail[]): void {
  const now = new Date().toISOString()
  for (const email of emails) {
    email.last_modified = now
    store.emails.set(email.id, email)
  }
}

// Update email status
export function updateEmailStatus(id: string, updates: Partial<LocalEmail>): void {
  const email = store.emails.get(id)
  if (email) {
    Object.assign(email, updates, { last_modified: new Date().toISOString() })
    store.emails.set(id, email)
  }
}

// Delete email
export function deleteEmail(id: string): void {
  store.emails.delete(id)
}

// Get email counts by folder
export function getEmailCounts(): Record<string, number> {
  const counts: Record<string, number> = {}
  const emails = Array.from(store.emails.values())
  for (const email of emails) {
    counts[email.folder] = (counts[email.folder] || 0) + 1
  }
  return counts
}

// Get unread counts by folder
export function getUnreadCounts(): Record<string, number> {
  const counts: Record<string, number> = {}
  const emails = Array.from(store.emails.values())
  for (const email of emails) {
    if (!email.is_read) {
      counts[email.folder] = (counts[email.folder] || 0) + 1
    }
  }
  return counts
}

// Search emails
export function searchEmails(query: string, folder?: string): LocalEmail[] {
  const lowerQuery = query.toLowerCase()
  return Array.from(store.emails.values())
    .filter(e => {
      if (folder && e.folder !== folder) return false
      return (
        e.subject?.toLowerCase().includes(lowerQuery) ||
        e.sender_name?.toLowerCase().includes(lowerQuery) ||
        e.sender_email?.toLowerCase().includes(lowerQuery) ||
        e.snippet?.toLowerCase().includes(lowerQuery) ||
        e.body?.toLowerCase().includes(lowerQuery)
      )
    })
    .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
}

// Sync queue operations
export function addToSyncQueue(operation: SyncQueueItem['operation'], emailId: string, data?: any): void {
  const item: SyncQueueItem = {
    id: store.syncQueueIdCounter++,
    operation,
    email_id: emailId,
    data: data ? JSON.stringify(data) : undefined,
    created_at: new Date().toISOString(),
    attempts: 0,
  }
  store.syncQueue.set(item.id, item)
}

export function getPendingSyncItems(limit: number = 50): SyncQueueItem[] {
  return Array.from(store.syncQueue.values())
    .sort((a, b) => a.id - b.id)
    .slice(0, limit)
}

export function completeSyncItem(id: number): void {
  store.syncQueue.delete(id)
}

export function failSyncItem(id: number, error: string): void {
  const item = store.syncQueue.get(id)
  if (item) {
    item.attempts++
    item.last_error = error
    store.syncQueue.set(id, item)
  }
}

export function getSyncQueueCount(): number {
  return store.syncQueue.size
}

// Decryption cache operations
export function getCachedDecryption(emailId: string): DecryptedEmailCache | undefined {
  return store.decryptionCache.get(emailId)
}

export function cacheDecryptedContent(cache: DecryptedEmailCache): void {
  cache.cached_at = new Date().toISOString()
  store.decryptionCache.set(cache.email_id, cache)
}

// Settings operations
export function getSetting(key: string): string | undefined {
  return store.settings.get(key)
}

export function setSetting(key: string, value: string): void {
  store.settings.set(key, value)
}

// Sync time operations
export function getLastSyncTime(): string {
  return store.lastSyncTime
}

export function setLastSyncTime(time: string): void {
  store.lastSyncTime = time
}

// Get database stats
export function getDatabaseStats(): { emails: number; syncQueue: number; cacheSize: number } {
  return {
    emails: store.emails.size,
    syncQueue: store.syncQueue.size,
    cacheSize: store.decryptionCache.size,
  }
}

// Clear all data
export function clearAllData(): void {
  store.emails.clear()
  store.syncQueue.clear()
  store.decryptionCache.clear()
  store.settings.clear()
  store.lastSyncTime = ''
  console.log('[Database] All data cleared')
}
