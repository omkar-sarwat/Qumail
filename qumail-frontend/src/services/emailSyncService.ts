/**
 * Email Sync Service
 * 
 * Handles automatic email fetching when accounts are added
 * and continuous polling for new emails.
 * 
 * Features:
 * - Auto-fetch last 30 emails when account is added
 * - Continuous polling every 30 seconds for new emails
 * - Per-account sync state tracking
 * - Multi-provider support (Gmail OAuth, IMAP, POP3)
 */

import { apiService } from './api'
import { useEmailAccountsStore } from '../stores/emailAccountsStore'
import { getPassword } from '../utils/credentialStorage'
import toast from 'react-hot-toast'

// Sync configuration
const SYNC_CONFIG = {
  initialFetchCount: 30,        // Fetch last 30 emails on account add
  pollInterval: 30000,          // Poll every 30 seconds
  maxEmailsPerPoll: 10,         // Check for max 10 new emails per poll
  retryDelay: 5000,             // Retry after 5 seconds on error
  maxRetries: 3,                // Max retries before stopping sync
}

// Email data type from backend
interface SyncedEmail {
  id: string
  message_id: string
  thread_id: string
  subject: string
  from_address: string
  from_name: string
  to_address: string
  to_name: string
  cc_address: string | null
  body_text: string
  body_html: string | null
  timestamp: string
  is_read: boolean
  has_attachments: boolean
  folder: string
}

// Sync state per account
interface AccountSyncState {
  accountId: string
  lastSyncTime: number
  lastMessageId: string | null
  emailCount: number
  isPolling: boolean
  errorCount: number
  emails: SyncedEmail[]
}

// Sync service event types
type SyncEventType = 'emails_fetched' | 'new_emails' | 'sync_error' | 'sync_started' | 'sync_stopped'
type SyncEventHandler = (event: SyncEventType, data: any) => void

class EmailSyncService {
  private syncStates: Map<string, AccountSyncState> = new Map()
  private pollTimers: Map<string, NodeJS.Timeout> = new Map()
  private eventHandlers: Set<SyncEventHandler> = new Set()
  private isInitialized = false

  /**
   * Initialize sync service and start syncing for all existing accounts
   */
  initialize() {
    if (this.isInitialized) return

    console.log('🔄 EmailSyncService initializing...')
    
    const store = useEmailAccountsStore.getState()
    const { accounts } = store
    
    // Start sync for all existing accounts
    accounts.forEach(account => {
      if (account.isVerified) {
        this.startSync(account.id)
      }
    })

    // Subscribe to account changes
    useEmailAccountsStore.subscribe((state, prevState) => {
      // Check for new accounts
      state.accounts.forEach(account => {
        if (!prevState.accounts.find(a => a.id === account.id)) {
          console.log(`📧 New account added: ${account.email}`)
          if (account.isVerified) {
            this.startSync(account.id)
          }
        }
      })

      // Check for removed accounts
      prevState.accounts.forEach(account => {
        if (!state.accounts.find(a => a.id === account.id)) {
          console.log(`🗑️ Account removed: ${account.email}`)
          this.stopSync(account.id)
        }
      })
    })

    this.isInitialized = true
    console.log('✅ EmailSyncService initialized')
  }

  /**
   * Subscribe to sync events
   */
  subscribe(handler: SyncEventHandler) {
    this.eventHandlers.add(handler)
    return () => this.eventHandlers.delete(handler)
  }

  /**
   * Emit sync event to all handlers
   */
  private emit(event: SyncEventType, data: any) {
    this.eventHandlers.forEach(handler => handler(event, data))
  }

  /**
   * Get account with credentials
   */
  private getAccountWithCredentials(accountId: string) {
    const store = useEmailAccountsStore.getState()
    const account = store.accounts.find(a => a.id === accountId)
    
    if (!account) return null
    
    const password = getPassword(account.id)
    if (!password) {
      console.warn(`No password found for account ${account.email}`)
      return null
    }

    return {
      email: account.email,
      password,
      provider: account.provider,
      settings: account.settings,
      foldersToSync: account.foldersToSync,
    }
  }

  /**
   * Start syncing for an account
   */
  async startSync(accountId: string) {
    const store = useEmailAccountsStore.getState()
    const account = store.accounts.find(a => a.id === accountId)
    
    if (!account) {
      console.error(`Account not found: ${accountId}`)
      return
    }

    // Initialize sync state
    if (!this.syncStates.has(accountId)) {
      this.syncStates.set(accountId, {
        accountId,
        lastSyncTime: 0,
        lastMessageId: null,
        emailCount: 0,
        isPolling: false,
        errorCount: 0,
        emails: [],
      })
    }

    const state = this.syncStates.get(accountId)!
    
    if (state.isPolling) {
      console.log(`Already syncing account: ${account.email}`)
      return
    }

    state.isPolling = true
    this.emit('sync_started', { accountId, email: account.email })
    
    console.log(`🚀 Starting sync for ${account.email}`)
    
    // Initial fetch of last 30 emails
    await this.fetchInitialEmails(accountId)
    
    // Start polling for new emails
    this.startPolling(accountId)
  }

  /**
   * Stop syncing for an account
   */
  stopSync(accountId: string) {
    const timer = this.pollTimers.get(accountId)
    if (timer) {
      clearInterval(timer)
      this.pollTimers.delete(accountId)
    }

    const state = this.syncStates.get(accountId)
    if (state) {
      state.isPolling = false
    }

    this.emit('sync_stopped', { accountId })
    console.log(`🛑 Stopped sync for account: ${accountId}`)
  }

  /**
   * Fetch initial 30 emails for account
   */
  private async fetchInitialEmails(accountId: string) {
    const account = this.getAccountWithCredentials(accountId)
    if (!account) return

    const state = this.syncStates.get(accountId)!
    
    console.log(`📥 Fetching initial ${SYNC_CONFIG.initialFetchCount} emails for ${account.email}`)
    
    try {
      const response = await apiService.fetchProviderEmails(account, {
        folder: 'INBOX',
        maxResults: SYNC_CONFIG.initialFetchCount,
        offset: 0,
      })

      const emails = response.emails || []
      state.emails = emails
      state.emailCount = emails.length
      state.lastSyncTime = Date.now()
      
      if (emails.length > 0) {
        state.lastMessageId = emails[0].message_id
      }

      console.log(`✅ Fetched ${emails.length} initial emails for ${account.email}`)
      
      // Show toast notification
      toast.success(`Synced ${emails.length} emails from ${account.email}`, {
        icon: '📧',
        duration: 3000,
      })

      this.emit('emails_fetched', {
        accountId,
        email: account.email,
        count: emails.length,
        emails,
        isInitial: true,
      })

      // Update last sync time in store
      useEmailAccountsStore.getState().updateAccount(accountId, {
        lastSync: new Date().toISOString(),
      })

      state.errorCount = 0
      
    } catch (error: any) {
      console.error(`❌ Failed to fetch emails for ${account.email}:`, error)
      state.errorCount++
      
      this.emit('sync_error', {
        accountId,
        email: account.email,
        error: error.message || 'Failed to fetch emails',
      })

      toast.error(`Failed to sync ${account.email}: ${error.response?.data?.detail || error.message}`)
    }
  }

  /**
   * Start polling for new emails
   */
  private startPolling(accountId: string) {
    // Clear existing timer if any
    const existingTimer = this.pollTimers.get(accountId)
    if (existingTimer) {
      clearInterval(existingTimer)
    }

    // Set up polling interval
    const timer = setInterval(() => {
      this.pollForNewEmails(accountId)
    }, SYNC_CONFIG.pollInterval)

    this.pollTimers.set(accountId, timer)
    
    const account = this.getAccountWithCredentials(accountId)
    console.log(`⏰ Started polling every ${SYNC_CONFIG.pollInterval/1000}s for ${account?.email}`)
  }

  /**
   * Poll for new emails
   */
  private async pollForNewEmails(accountId: string) {
    const account = this.getAccountWithCredentials(accountId)
    if (!account) {
      this.stopSync(accountId)
      return
    }

    const state = this.syncStates.get(accountId)
    if (!state || !state.isPolling) return

    // Check if max retries exceeded
    if (state.errorCount >= SYNC_CONFIG.maxRetries) {
      console.warn(`Max retries exceeded for ${account.email}, stopping sync`)
      this.stopSync(accountId)
      toast.error(`Sync stopped for ${account.email} due to repeated errors`)
      return
    }

    console.log(`🔄 Polling for new emails: ${account.email}`)

    try {
      // Fetch recent emails
      const response = await apiService.fetchProviderEmails(account, {
        folder: 'INBOX',
        maxResults: SYNC_CONFIG.maxEmailsPerPoll,
        offset: 0,
      })

      const newEmails = response.emails || []
      
      if (newEmails.length === 0) {
        console.log(`📭 No new emails for ${account.email}`)
        return
      }

      // Find emails newer than last sync
      const existingIds = new Set(state.emails.map(e => e.message_id))
      const trulyNewEmails = newEmails.filter(e => !existingIds.has(e.message_id))

      if (trulyNewEmails.length > 0) {
        console.log(`📬 ${trulyNewEmails.length} NEW emails for ${account.email}`)
        
        // Add new emails to the front of the list
        state.emails = [...trulyNewEmails, ...state.emails]
        state.emailCount = state.emails.length
        state.lastMessageId = trulyNewEmails[0].message_id
        
        // Show notification
        if (trulyNewEmails.length === 1) {
          toast(`New email from ${trulyNewEmails[0].from_name || trulyNewEmails[0].from_address}`, {
            icon: '📧',
            duration: 4000,
          })
        } else {
          toast(`${trulyNewEmails.length} new emails in ${account.email}`, {
            icon: '📧',
            duration: 4000,
          })
        }

        this.emit('new_emails', {
          accountId,
          email: account.email,
          count: trulyNewEmails.length,
          emails: trulyNewEmails,
        })

        // Play notification sound if available
        this.playNotificationSound()
      }

      state.lastSyncTime = Date.now()
      state.errorCount = 0

      // Update last sync time in store
      useEmailAccountsStore.getState().updateAccount(accountId, {
        lastSync: new Date().toISOString(),
      })

    } catch (error: any) {
      console.error(`❌ Poll failed for ${account.email}:`, error)
      state.errorCount++
      
      this.emit('sync_error', {
        accountId,
        email: account.email,
        error: error.message || 'Poll failed',
      })
    }
  }

  /**
   * Play notification sound
   */
  private playNotificationSound() {
    try {
      // Create a simple beep using Web Audio API
      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)()
      const oscillator = audioContext.createOscillator()
      const gainNode = audioContext.createGain()
      
      oscillator.connect(gainNode)
      gainNode.connect(audioContext.destination)
      
      oscillator.frequency.value = 800
      oscillator.type = 'sine'
      gainNode.gain.value = 0.1
      
      oscillator.start()
      oscillator.stop(audioContext.currentTime + 0.1)
    } catch (e) {
      // Audio not supported or blocked
    }
  }

  /**
   * Manually refresh emails for an account
   */
  async refreshAccount(accountId: string) {
    const account = this.getAccountWithCredentials(accountId)
    if (!account) return

    const state = this.syncStates.get(accountId)
    if (!state) return

    console.log(`🔄 Manual refresh for ${account.email}`)
    
    try {
      const response = await apiService.fetchProviderEmails(account, {
        folder: 'INBOX',
        maxResults: SYNC_CONFIG.initialFetchCount,
        offset: 0,
      })

      state.emails = response.emails || []
      state.emailCount = state.emails.length
      state.lastSyncTime = Date.now()
      state.errorCount = 0

      toast.success(`Refreshed ${state.emails.length} emails from ${account.email}`)

      this.emit('emails_fetched', {
        accountId,
        email: account.email,
        count: state.emails.length,
        emails: state.emails,
        isInitial: false,
      })

      return state.emails
      
    } catch (error: any) {
      console.error(`Refresh failed for ${account.email}:`, error)
      toast.error(`Failed to refresh: ${error.response?.data?.detail || error.message}`)
      throw error
    }
  }

  /**
   * Get sync state for an account
   */
  getSyncState(accountId: string): AccountSyncState | undefined {
    return this.syncStates.get(accountId)
  }

  /**
   * Get all synced emails for an account
   */
  getEmails(accountId: string): SyncedEmail[] {
    const state = this.syncStates.get(accountId)
    return state?.emails || []
  }

  /**
   * Get all synced emails across all accounts
   */
  getAllEmails(): { accountId: string; email: string; emails: SyncedEmail[] }[] {
    const result: { accountId: string; email: string; emails: SyncedEmail[] }[] = []
    
    this.syncStates.forEach((state, accountId) => {
      const account = useEmailAccountsStore.getState().accounts.find(a => a.id === accountId)
      if (account) {
        result.push({
          accountId,
          email: account.email,
          emails: state.emails,
        })
      }
    })

    return result
  }

  /**
   * Get total unread count across all accounts
   */
  getTotalUnreadCount(): number {
    let count = 0
    this.syncStates.forEach(state => {
      count += state.emails.filter(e => !e.is_read).length
    })
    return count
  }

  /**
   * Cleanup - stop all syncs
   */
  destroy() {
    console.log('🧹 Cleaning up EmailSyncService')
    this.pollTimers.forEach((timer) => {
      clearInterval(timer)
    })
    this.pollTimers.clear()
    this.syncStates.clear()
    this.eventHandlers.clear()
    this.isInitialized = false
  }
}

// Export singleton instance
export const emailSyncService = new EmailSyncService()

// Export types
export type { SyncedEmail, AccountSyncState, SyncEventType, SyncEventHandler }
