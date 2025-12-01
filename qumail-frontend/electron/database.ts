import Database from 'better-sqlite3'
import { app } from 'electron'
import { join } from 'path'
import * as fs from 'fs'

// Database instance
let db: Database.Database | null = null

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
  security_info?: string // JSON string
  encryption_metadata?: string // JSON string
  attachments?: string // JSON string
  timestamp: string
  synced_at?: string
  last_modified: string
  sync_status: 'synced' | 'pending_upload' | 'pending_download' | 'conflict'
}

export interface SyncQueueItem {
  id: number
  operation: 'create' | 'update' | 'delete' | 'mark_read' | 'mark_starred' | 'decrypt'
  email_id: string
  data?: string // JSON string
  created_at: string
  attempts: number
  last_error?: string
}

export interface DecryptedEmailCache {
  email_id: string
  flow_id?: string
  decrypted_body: string
  decrypted_html?: string
  security_info: string // JSON string
  cached_at: string
}

// Initialize database
export function initDatabase(): void {
  const userDataPath = app.getPath('userData')
  const dbPath = join(userDataPath, 'qumail_local.db')
  
  console.log('[Database] Initializing SQLite database at:', dbPath)
  
  // Ensure directory exists
  if (!fs.existsSync(userDataPath)) {
    fs.mkdirSync(userDataPath, { recursive: true })
  }
  
  // Open database (creates if doesn't exist)
  db = new Database(dbPath)
  
  // Enable WAL mode for better performance
  db.pragma('journal_mode = WAL')
  
  // Create tables
  createTables()
  
  console.log('[Database] Database initialized successfully')
}

function createTables(): void {
  if (!db) throw new Error('Database not initialized')
  
  // Emails table - primary local storage
  db.exec(`
    CREATE TABLE IF NOT EXISTS emails (
      id TEXT PRIMARY KEY,
      thread_id TEXT,
      gmail_message_id TEXT,
      subject TEXT,
      sender_email TEXT NOT NULL,
      sender_name TEXT,
      recipient_email TEXT,
      body TEXT,
      body_html TEXT,
      body_encrypted TEXT,
      snippet TEXT,
      folder TEXT DEFAULT 'inbox',
      is_read INTEGER DEFAULT 0,
      is_starred INTEGER DEFAULT 0,
      is_encrypted INTEGER DEFAULT 0,
      is_decrypted INTEGER DEFAULT 0,
      globally_decrypted INTEGER DEFAULT 0,
      security_level INTEGER,
      flow_id TEXT,
      algorithm TEXT,
      quantum_enhanced INTEGER DEFAULT 0,
      decrypted_content TEXT,
      decrypted_html TEXT,
      security_info TEXT,
      encryption_metadata TEXT,
      attachments TEXT,
      timestamp TEXT NOT NULL,
      synced_at TEXT,
      last_modified TEXT NOT NULL,
      sync_status TEXT DEFAULT 'synced'
    )
  `)
  
  // Create indexes for common queries
  db.exec(`CREATE INDEX IF NOT EXISTS idx_emails_folder ON emails(folder)`)
  db.exec(`CREATE INDEX IF NOT EXISTS idx_emails_timestamp ON emails(timestamp DESC)`)
  db.exec(`CREATE INDEX IF NOT EXISTS idx_emails_sync_status ON emails(sync_status)`)
  db.exec(`CREATE INDEX IF NOT EXISTS idx_emails_is_read ON emails(is_read)`)
  db.exec(`CREATE INDEX IF NOT EXISTS idx_emails_flow_id ON emails(flow_id)`)
  db.exec(`CREATE INDEX IF NOT EXISTS idx_emails_gmail_id ON emails(gmail_message_id)`)
  
  // Sync queue - operations pending upload
  db.exec(`
    CREATE TABLE IF NOT EXISTS sync_queue (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      operation TEXT NOT NULL,
      email_id TEXT NOT NULL,
      data TEXT,
      created_at TEXT NOT NULL,
      attempts INTEGER DEFAULT 0,
      last_error TEXT
    )
  `)
  
  // Decrypted content cache
  db.exec(`
    CREATE TABLE IF NOT EXISTS decrypted_cache (
      email_id TEXT PRIMARY KEY,
      flow_id TEXT,
      decrypted_body TEXT NOT NULL,
      decrypted_html TEXT,
      security_info TEXT,
      cached_at TEXT NOT NULL
    )
  `)
  
  // User settings
  db.exec(`
    CREATE TABLE IF NOT EXISTS settings (
      key TEXT PRIMARY KEY,
      value TEXT NOT NULL,
      updated_at TEXT NOT NULL
    )
  `)
  
  // Sync metadata
  db.exec(`
    CREATE TABLE IF NOT EXISTS sync_metadata (
      key TEXT PRIMARY KEY,
      value TEXT NOT NULL,
      updated_at TEXT NOT NULL
    )
  `)
  
  console.log('[Database] Tables created successfully')
}

// Close database
export function closeDatabase(): void {
  if (db) {
    db.close()
    db = null
    console.log('[Database] Database closed')
  }
}

// ==================== EMAIL OPERATIONS ====================

// Get all emails in a folder
export function getEmails(folder: string, limit: number = 100, offset: number = 0): LocalEmail[] {
  if (!db) throw new Error('Database not initialized')
  
  const stmt = db.prepare(`
    SELECT * FROM emails 
    WHERE folder = ? 
    ORDER BY timestamp DESC 
    LIMIT ? OFFSET ?
  `)
  
  return stmt.all(folder, limit, offset) as LocalEmail[]
}

// Get email by ID
export function getEmailById(id: string): LocalEmail | undefined {
  if (!db) throw new Error('Database not initialized')
  
  const stmt = db.prepare('SELECT * FROM emails WHERE id = ?')
  return stmt.get(id) as LocalEmail | undefined
}

// Get email by flow_id
export function getEmailByFlowId(flowId: string): LocalEmail | undefined {
  if (!db) throw new Error('Database not initialized')
  
  const stmt = db.prepare('SELECT * FROM emails WHERE flow_id = ?')
  return stmt.get(flowId) as LocalEmail | undefined
}

// Save or update email
export function saveEmail(email: Partial<LocalEmail>): void {
  if (!db) throw new Error('Database not initialized')
  
  const now = new Date().toISOString()
  
  const stmt = db.prepare(`
    INSERT OR REPLACE INTO emails (
      id, thread_id, gmail_message_id, subject, sender_email, sender_name,
      recipient_email, body, body_html, body_encrypted, snippet, folder,
      is_read, is_starred, is_encrypted, is_decrypted, globally_decrypted,
      security_level, flow_id, algorithm, quantum_enhanced,
      decrypted_content, decrypted_html, security_info, encryption_metadata,
      attachments, timestamp, synced_at, last_modified, sync_status
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `)
  
  stmt.run(
    email.id,
    email.thread_id || null,
    email.gmail_message_id || null,
    email.subject || '',
    email.sender_email || '',
    email.sender_name || null,
    email.recipient_email || null,
    email.body || null,
    email.body_html || null,
    email.body_encrypted || null,
    email.snippet || null,
    email.folder || 'inbox',
    email.is_read ? 1 : 0,
    email.is_starred ? 1 : 0,
    email.is_encrypted ? 1 : 0,
    email.is_decrypted ? 1 : 0,
    email.globally_decrypted ? 1 : 0,
    email.security_level || null,
    email.flow_id || null,
    email.algorithm || null,
    email.quantum_enhanced ? 1 : 0,
    email.decrypted_content || null,
    email.decrypted_html || null,
    email.security_info || null,
    email.encryption_metadata || null,
    email.attachments || null,
    email.timestamp || now,
    email.synced_at || null,
    now,
    email.sync_status || 'synced'
  )
}

// Save multiple emails (batch insert with transaction)
export function saveEmails(emails: Partial<LocalEmail>[]): void {
  if (!db) throw new Error('Database not initialized')
  
  const insertMany = db.transaction((emailList: Partial<LocalEmail>[]) => {
    for (const email of emailList) {
      saveEmail(email)
    }
  })
  
  insertMany(emails)
}

// Update email status
export function updateEmailStatus(id: string, updates: Partial<LocalEmail>): void {
  if (!db) throw new Error('Database not initialized')
  
  const now = new Date().toISOString()
  const fields: string[] = []
  const values: any[] = []
  
  if (updates.is_read !== undefined) {
    fields.push('is_read = ?')
    values.push(updates.is_read ? 1 : 0)
  }
  if (updates.is_starred !== undefined) {
    fields.push('is_starred = ?')
    values.push(updates.is_starred ? 1 : 0)
  }
  if (updates.is_decrypted !== undefined) {
    fields.push('is_decrypted = ?')
    values.push(updates.is_decrypted ? 1 : 0)
  }
  if (updates.globally_decrypted !== undefined) {
    fields.push('globally_decrypted = ?')
    values.push(updates.globally_decrypted ? 1 : 0)
  }
  if (updates.decrypted_content !== undefined) {
    fields.push('decrypted_content = ?')
    values.push(updates.decrypted_content)
  }
  if (updates.decrypted_html !== undefined) {
    fields.push('decrypted_html = ?')
    values.push(updates.decrypted_html)
  }
  if (updates.folder !== undefined) {
    fields.push('folder = ?')
    values.push(updates.folder)
  }
  if (updates.sync_status !== undefined) {
    fields.push('sync_status = ?')
    values.push(updates.sync_status)
  }
  
  fields.push('last_modified = ?')
  values.push(now)
  values.push(id)
  
  if (fields.length > 1) {
    const stmt = db.prepare(`UPDATE emails SET ${fields.join(', ')} WHERE id = ?`)
    stmt.run(...values)
  }
}

// Delete email
export function deleteEmail(id: string): void {
  if (!db) throw new Error('Database not initialized')
  
  const stmt = db.prepare('DELETE FROM emails WHERE id = ?')
  stmt.run(id)
}

// Get email counts by folder
export function getEmailCounts(): Record<string, number> {
  if (!db) throw new Error('Database not initialized')
  
  const stmt = db.prepare(`
    SELECT folder, COUNT(*) as count 
    FROM emails 
    GROUP BY folder
  `)
  
  const results = stmt.all() as { folder: string; count: number }[]
  const counts: Record<string, number> = {}
  
  for (const row of results) {
    counts[row.folder] = row.count
  }
  
  return counts
}

// Get unread counts by folder
export function getUnreadCounts(): Record<string, number> {
  if (!db) throw new Error('Database not initialized')
  
  const stmt = db.prepare(`
    SELECT folder, COUNT(*) as count 
    FROM emails 
    WHERE is_read = 0
    GROUP BY folder
  `)
  
  const results = stmt.all() as { folder: string; count: number }[]
  const counts: Record<string, number> = {}
  
  for (const row of results) {
    counts[row.folder] = row.count
  }
  
  return counts
}

// Search emails
export function searchEmails(query: string, folder?: string): LocalEmail[] {
  if (!db) throw new Error('Database not initialized')
  
  const searchTerm = `%${query}%`
  
  let sql = `
    SELECT * FROM emails 
    WHERE (subject LIKE ? OR sender_email LIKE ? OR sender_name LIKE ? OR body LIKE ? OR decrypted_content LIKE ?)
  `
  
  const params: any[] = [searchTerm, searchTerm, searchTerm, searchTerm, searchTerm]
  
  if (folder) {
    sql += ' AND folder = ?'
    params.push(folder)
  }
  
  sql += ' ORDER BY timestamp DESC LIMIT 100'
  
  const stmt = db.prepare(sql)
  return stmt.all(...params) as LocalEmail[]
}

// ==================== SYNC QUEUE OPERATIONS ====================

// Add to sync queue
export function addToSyncQueue(operation: SyncQueueItem['operation'], emailId: string, data?: any): void {
  if (!db) throw new Error('Database not initialized')
  
  const stmt = db.prepare(`
    INSERT INTO sync_queue (operation, email_id, data, created_at, attempts)
    VALUES (?, ?, ?, ?, 0)
  `)
  
  stmt.run(operation, emailId, data ? JSON.stringify(data) : null, new Date().toISOString())
}

// Get pending sync items
export function getPendingSyncItems(limit: number = 50): SyncQueueItem[] {
  if (!db) throw new Error('Database not initialized')
  
  const stmt = db.prepare(`
    SELECT * FROM sync_queue 
    WHERE attempts < 5
    ORDER BY created_at ASC 
    LIMIT ?
  `)
  
  return stmt.all(limit) as SyncQueueItem[]
}

// Mark sync item as completed (delete it)
export function completeSyncItem(id: number): void {
  if (!db) throw new Error('Database not initialized')
  
  const stmt = db.prepare('DELETE FROM sync_queue WHERE id = ?')
  stmt.run(id)
}

// Mark sync item as failed
export function failSyncItem(id: number, error: string): void {
  if (!db) throw new Error('Database not initialized')
  
  const stmt = db.prepare(`
    UPDATE sync_queue 
    SET attempts = attempts + 1, last_error = ?
    WHERE id = ?
  `)
  
  stmt.run(error, id)
}

// Get sync queue count
export function getSyncQueueCount(): number {
  if (!db) throw new Error('Database not initialized')
  
  const stmt = db.prepare('SELECT COUNT(*) as count FROM sync_queue WHERE attempts < 5')
  const result = stmt.get() as { count: number }
  return result?.count || 0
}

// ==================== DECRYPTED CACHE OPERATIONS ====================

// Get cached decrypted content
export function getCachedDecryption(emailId: string): DecryptedEmailCache | undefined {
  if (!db) throw new Error('Database not initialized')
  
  const stmt = db.prepare('SELECT * FROM decrypted_cache WHERE email_id = ?')
  return stmt.get(emailId) as DecryptedEmailCache | undefined
}

// Save decrypted content to cache
export function cacheDecryptedContent(cache: DecryptedEmailCache): void {
  if (!db) throw new Error('Database not initialized')
  
  const stmt = db.prepare(`
    INSERT OR REPLACE INTO decrypted_cache (email_id, flow_id, decrypted_body, decrypted_html, security_info, cached_at)
    VALUES (?, ?, ?, ?, ?, ?)
  `)
  
  stmt.run(
    cache.email_id,
    cache.flow_id || null,
    cache.decrypted_body,
    cache.decrypted_html || null,
    cache.security_info,
    cache.cached_at
  )
}

// ==================== SETTINGS OPERATIONS ====================

// Get setting
export function getSetting(key: string): string | undefined {
  if (!db) throw new Error('Database not initialized')
  
  const stmt = db.prepare('SELECT value FROM settings WHERE key = ?')
  const result = stmt.get(key) as { value: string } | undefined
  return result?.value
}

// Set setting
export function setSetting(key: string, value: string): void {
  if (!db) throw new Error('Database not initialized')
  
  const stmt = db.prepare(`
    INSERT OR REPLACE INTO settings (key, value, updated_at)
    VALUES (?, ?, ?)
  `)
  
  stmt.run(key, value, new Date().toISOString())
}

// ==================== SYNC METADATA OPERATIONS ====================

// Get last sync time
export function getLastSyncTime(): string | undefined {
  if (!db) throw new Error('Database not initialized')
  
  const stmt = db.prepare('SELECT value FROM sync_metadata WHERE key = ?')
  const result = stmt.get('last_sync') as { value: string } | undefined
  return result?.value
}

// Set last sync time
export function setLastSyncTime(time: string): void {
  if (!db) throw new Error('Database not initialized')
  
  const stmt = db.prepare(`
    INSERT OR REPLACE INTO sync_metadata (key, value, updated_at)
    VALUES ('last_sync', ?, ?)
  `)
  
  stmt.run(time, new Date().toISOString())
}

// Get emails that need syncing
export function getEmailsNeedingSync(): LocalEmail[] {
  if (!db) throw new Error('Database not initialized')
  
  const stmt = db.prepare(`
    SELECT * FROM emails 
    WHERE sync_status IN ('pending_upload', 'pending_download')
    ORDER BY last_modified DESC
  `)
  
  return stmt.all() as LocalEmail[]
}

// Clear all local data (for logout)
export function clearAllData(): void {
  if (!db) throw new Error('Database not initialized')
  
  db.exec('DELETE FROM emails')
  db.exec('DELETE FROM sync_queue')
  db.exec('DELETE FROM decrypted_cache')
  db.exec('DELETE FROM settings')
  db.exec('DELETE FROM sync_metadata')
  
  console.log('[Database] All local data cleared')
}

// Get database stats
export function getDatabaseStats(): {
  totalEmails: number
  decryptedEmails: number
  pendingSyncCount: number
  lastSync: string | undefined
} {
  if (!db) throw new Error('Database not initialized')
  
  const totalStmt = db.prepare('SELECT COUNT(*) as count FROM emails')
  const totalResult = totalStmt.get() as { count: number }
  
  const decryptedStmt = db.prepare('SELECT COUNT(*) as count FROM emails WHERE is_decrypted = 1')
  const decryptedResult = decryptedStmt.get() as { count: number }
  
  return {
    totalEmails: totalResult?.count || 0,
    decryptedEmails: decryptedResult?.count || 0,
    pendingSyncCount: getSyncQueueCount(),
    lastSync: getLastSyncTime()
  }
}
