// SQLite-based persistent database for Electron using sql.js (pure JS, no native build)
// Data survives app restarts

import initSqlJs, { Database as SqlJsDatabase } from 'sql.js'
import { app } from 'electron'
import path from 'path'
import fs from 'fs'

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

let db: SqlJsDatabase | null = null
let dbPath: string = ''
let saveTimeout: ReturnType<typeof setTimeout> | null = null

// Debounced save to disk
function scheduleSave(): void {
  if (saveTimeout) clearTimeout(saveTimeout)
  saveTimeout = setTimeout(() => {
    if (db && dbPath) {
      try {
        const data = db.export()
        fs.writeFileSync(dbPath, Buffer.from(data))
        console.log('[Database] Saved to disk')
      } catch (e) {
        console.error('[Database] Failed to save:', e)
      }
    }
  }, 1000) // Save after 1 second of no changes
}

// Initialize database with sql.js
export async function initDatabaseAsync(): Promise<void> {
  const userDataPath = app.getPath('userData')
  dbPath = path.join(userDataPath, 'qumail.db')
  console.log('[Database] Opening sql.js database at:', dbPath)

  const SQL = await initSqlJs()

  // Try to load existing database
  if (fs.existsSync(dbPath)) {
    try {
      const fileBuffer = fs.readFileSync(dbPath)
      db = new SQL.Database(fileBuffer)
      console.log('[Database] Loaded existing database')
    } catch (e) {
      console.warn('[Database] Failed to load existing db, creating new:', e)
      db = new SQL.Database()
    }
  } else {
    db = new SQL.Database()
  }

  // Create tables
  db.run(`
    CREATE TABLE IF NOT EXISTS emails (
      id TEXT PRIMARY KEY,
      thread_id TEXT,
      gmail_message_id TEXT,
      subject TEXT,
      sender_email TEXT,
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
      timestamp TEXT,
      synced_at TEXT,
      last_modified TEXT,
      sync_status TEXT DEFAULT 'synced'
    )
  `)

  db.run(`
    CREATE TABLE IF NOT EXISTS sync_queue (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      operation TEXT,
      email_id TEXT,
      data TEXT,
      created_at TEXT,
      attempts INTEGER DEFAULT 0,
      last_error TEXT
    )
  `)

  db.run(`
    CREATE TABLE IF NOT EXISTS decryption_cache (
      email_id TEXT PRIMARY KEY,
      flow_id TEXT,
      decrypted_body TEXT,
      decrypted_html TEXT,
      security_info TEXT,
      cached_at TEXT
    )
  `)

  db.run(`
    CREATE TABLE IF NOT EXISTS settings (
      key TEXT PRIMARY KEY,
      value TEXT
    )
  `)

  db.run(`CREATE INDEX IF NOT EXISTS idx_emails_folder ON emails(folder)`)
  db.run(`CREATE INDEX IF NOT EXISTS idx_emails_timestamp ON emails(timestamp)`)
  db.run(`CREATE INDEX IF NOT EXISTS idx_emails_flow_id ON emails(flow_id)`)

  scheduleSave()
  console.log('[Database] sql.js database initialized')
}

// Sync init wrapper for backward compatibility
export function initDatabase(): void {
  initDatabaseAsync().catch(e => console.error('[Database] Init failed:', e))
}

// Close database
export function closeDatabase(): void {
  if (saveTimeout) {
    clearTimeout(saveTimeout)
    saveTimeout = null
  }
  if (db && dbPath) {
    try {
      const data = db.export()
      fs.writeFileSync(dbPath, Buffer.from(data))
      console.log('[Database] Final save on close')
    } catch (e) {
      console.error('[Database] Failed to save on close:', e)
    }
    db.close()
    db = null
    console.log('[Database] sql.js database closed')
  }
}

// Helper to convert query result to array of objects
function queryToObjects(stmt: any): any[] {
  const results: any[] = []
  while (stmt.step()) {
    const row = stmt.getAsObject()
    results.push(row)
  }
  stmt.free()
  return results
}

// Get emails by folder
export function getEmails(folder: string, limit: number = 100, offset: number = 0): LocalEmail[] {
  if (!db) return []
  const sql = folder === 'all'
    ? 'SELECT * FROM emails ORDER BY timestamp DESC LIMIT ? OFFSET ?'
    : 'SELECT * FROM emails WHERE folder = ? ORDER BY timestamp DESC LIMIT ? OFFSET ?'
  const stmt = db.prepare(sql)
  if (folder === 'all') {
    stmt.bind([limit, offset])
  } else {
    stmt.bind([folder, limit, offset])
  }
  return queryToObjects(stmt).map(rowToEmail)
}

// Get email by ID
export function getEmailById(id: string): LocalEmail | undefined {
  if (!db) return undefined
  const stmt = db.prepare('SELECT * FROM emails WHERE id = ?')
  stmt.bind([id])
  const rows = queryToObjects(stmt)
  return rows.length > 0 ? rowToEmail(rows[0]) : undefined
}

// Get email by flow ID
export function getEmailByFlowId(flowId: string): LocalEmail | undefined {
  if (!db) return undefined
  const stmt = db.prepare('SELECT * FROM emails WHERE flow_id = ?')
  stmt.bind([flowId])
  const rows = queryToObjects(stmt)
  return rows.length > 0 ? rowToEmail(rows[0]) : undefined
}

// Save single email
export function saveEmail(email: LocalEmail): void {
  if (!db) return
  db.run(`
    INSERT OR REPLACE INTO emails (
      id, thread_id, gmail_message_id, subject, sender_email, sender_name,
      recipient_email, body, body_html, body_encrypted, snippet, folder,
      is_read, is_starred, is_encrypted, is_decrypted, globally_decrypted,
      security_level, flow_id, algorithm, quantum_enhanced, decrypted_content,
      decrypted_html, security_info, encryption_metadata, attachments,
      timestamp, synced_at, last_modified, sync_status
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `, [
    email.id, email.thread_id ?? null, email.gmail_message_id ?? null, email.subject,
    email.sender_email, email.sender_name ?? null, email.recipient_email,
    email.body ?? null, email.body_html ?? null, email.body_encrypted ?? null, email.snippet ?? null,
    email.folder, email.is_read ? 1 : 0, email.is_starred ? 1 : 0,
    email.is_encrypted ? 1 : 0, email.is_decrypted ? 1 : 0,
    email.globally_decrypted ? 1 : 0, email.security_level ?? null, email.flow_id ?? null,
    email.algorithm ?? null, email.quantum_enhanced ? 1 : 0, email.decrypted_content ?? null,
    email.decrypted_html ?? null, email.security_info ?? null, email.encryption_metadata ?? null,
    email.attachments ?? null, email.timestamp, email.synced_at ?? null,
    new Date().toISOString(), email.sync_status
  ])
  scheduleSave()
}

// Save multiple emails
export function saveEmails(emails: LocalEmail[]): void {
  if (!db) return
  for (const email of emails) {
    saveEmail(email)
  }
}

// Update email status
export function updateEmailStatus(id: string, updates: Partial<LocalEmail>): void {
  if (!db) return
  const sets: string[] = []
  const values: any[] = []
  for (const [key, val] of Object.entries(updates)) {
    sets.push(`${key} = ?`)
    values.push(typeof val === 'boolean' ? (val ? 1 : 0) : val)
  }
  sets.push('last_modified = ?')
  values.push(new Date().toISOString())
  values.push(id)
  db.run(`UPDATE emails SET ${sets.join(', ')} WHERE id = ?`, values)
  scheduleSave()
}

// Delete email
export function deleteEmail(id: string): void {
  if (!db) return
  db.run('DELETE FROM emails WHERE id = ?', [id])
  scheduleSave()
}

// Get email counts by folder
export function getEmailCounts(): Record<string, number> {
  if (!db) return {}
  const stmt = db.prepare('SELECT folder, COUNT(*) as cnt FROM emails GROUP BY folder')
  const rows = queryToObjects(stmt)
  const counts: Record<string, number> = {}
  for (const r of rows) counts[r.folder] = r.cnt
  return counts
}

// Get unread counts by folder
export function getUnreadCounts(): Record<string, number> {
  if (!db) return {}
  const stmt = db.prepare('SELECT folder, COUNT(*) as cnt FROM emails WHERE is_read = 0 GROUP BY folder')
  const rows = queryToObjects(stmt)
  const counts: Record<string, number> = {}
  for (const r of rows) counts[r.folder] = r.cnt
  return counts
}

// Search emails
export function searchEmails(query: string, folder?: string): LocalEmail[] {
  if (!db) return []
  const lowerQuery = `%${query.toLowerCase()}%`
  const sql = folder
    ? 'SELECT * FROM emails WHERE folder = ? AND (LOWER(subject) LIKE ? OR LOWER(sender_name) LIKE ? OR LOWER(sender_email) LIKE ? OR LOWER(snippet) LIKE ? OR LOWER(body) LIKE ?) ORDER BY timestamp DESC'
    : 'SELECT * FROM emails WHERE (LOWER(subject) LIKE ? OR LOWER(sender_name) LIKE ? OR LOWER(sender_email) LIKE ? OR LOWER(snippet) LIKE ? OR LOWER(body) LIKE ?) ORDER BY timestamp DESC'
  const stmt = db.prepare(sql)
  if (folder) {
    stmt.bind([folder, lowerQuery, lowerQuery, lowerQuery, lowerQuery, lowerQuery])
  } else {
    stmt.bind([lowerQuery, lowerQuery, lowerQuery, lowerQuery, lowerQuery])
  }
  return queryToObjects(stmt).map(rowToEmail)
}

// Sync queue operations
export function addToSyncQueue(operation: SyncQueueItem['operation'], emailId: string, data?: any): void {
  if (!db) return
  db.run('INSERT INTO sync_queue (operation, email_id, data, created_at, attempts) VALUES (?, ?, ?, ?, 0)',
    [operation, emailId, data ? JSON.stringify(data) : null, new Date().toISOString()])
  scheduleSave()
}

export function getPendingSyncItems(limit: number = 50): SyncQueueItem[] {
  if (!db) return []
  const stmt = db.prepare('SELECT * FROM sync_queue ORDER BY id LIMIT ?')
  stmt.bind([limit])
  return queryToObjects(stmt)
}

export function completeSyncItem(id: number): void {
  if (!db) return
  db.run('DELETE FROM sync_queue WHERE id = ?', [id])
  scheduleSave()
}

export function failSyncItem(id: number, error: string): void {
  if (!db) return
  db.run('UPDATE sync_queue SET attempts = attempts + 1, last_error = ? WHERE id = ?', [error, id])
  scheduleSave()
}

export function getSyncQueueCount(): number {
  if (!db) return 0
  const stmt = db.prepare('SELECT COUNT(*) as cnt FROM sync_queue')
  const rows = queryToObjects(stmt)
  return rows[0]?.cnt ?? 0
}

// Decryption cache operations
export function getCachedDecryption(emailId: string): DecryptedEmailCache | undefined {
  if (!db) return undefined
  const stmt = db.prepare('SELECT * FROM decryption_cache WHERE email_id = ?')
  stmt.bind([emailId])
  const rows = queryToObjects(stmt)
  return rows.length > 0 ? rows[0] : undefined
}

export function cacheDecryptedContent(cache: DecryptedEmailCache): void {
  if (!db) return
  db.run(`
    INSERT OR REPLACE INTO decryption_cache (email_id, flow_id, decrypted_body, decrypted_html, security_info, cached_at)
    VALUES (?, ?, ?, ?, ?, ?)
  `, [cache.email_id, cache.flow_id ?? null, cache.decrypted_body, cache.decrypted_html ?? null, cache.security_info, new Date().toISOString()])
  scheduleSave()
}

// Settings operations
export function getSetting(key: string): string | undefined {
  if (!db) return undefined
  const stmt = db.prepare('SELECT value FROM settings WHERE key = ?')
  stmt.bind([key])
  const rows = queryToObjects(stmt)
  return rows[0]?.value
}

export function setSetting(key: string, value: string): void {
  if (!db) return
  db.run('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', [key, value])
  scheduleSave()
}

// Sync time operations
export function getLastSyncTime(): string {
  return getSetting('last_sync') ?? ''
}

export function setLastSyncTime(time: string): void {
  setSetting('last_sync', time)
}

// Get database stats
export function getDatabaseStats(): { emails: number; syncQueue: number; cacheSize: number } {
  if (!db) return { emails: 0, syncQueue: 0, cacheSize: 0 }
  
  const emailsStmt = db.prepare('SELECT COUNT(*) as cnt FROM emails')
  const emailsRows = queryToObjects(emailsStmt)
  
  const syncStmt = db.prepare('SELECT COUNT(*) as cnt FROM sync_queue')
  const syncRows = queryToObjects(syncStmt)
  
  const cacheStmt = db.prepare('SELECT COUNT(*) as cnt FROM decryption_cache')
  const cacheRows = queryToObjects(cacheStmt)
  
  return {
    emails: emailsRows[0]?.cnt ?? 0,
    syncQueue: syncRows[0]?.cnt ?? 0,
    cacheSize: cacheRows[0]?.cnt ?? 0
  }
}

// Clear all data
export function clearAllData(): void {
  if (!db) return
  db.run('DELETE FROM emails')
  db.run('DELETE FROM sync_queue')
  db.run('DELETE FROM decryption_cache')
  db.run('DELETE FROM settings')
  scheduleSave()
  console.log('[Database] All data cleared')
}

// Helper: convert row to LocalEmail
function rowToEmail(row: any): LocalEmail {
  return {
    ...row,
    is_read: !!row.is_read,
    is_starred: !!row.is_starred,
    is_encrypted: !!row.is_encrypted,
    is_decrypted: !!row.is_decrypted,
    globally_decrypted: !!row.globally_decrypted,
    quantum_enhanced: !!row.quantum_enhanced,
  }
}
