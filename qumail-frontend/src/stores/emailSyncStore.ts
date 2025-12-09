/**
 * Email Sync Store
 * 
 * Zustand store for managing email sync state across all accounts.
 * Works in conjunction with emailSyncService to provide reactive state.
 */

import { create } from 'zustand'
import { emailSyncService, SyncedEmail, SyncEventType } from '../services/emailSyncService'

interface SyncedAccountEmails {
  accountId: string
  accountEmail: string
  provider: string
  emails: SyncedEmail[]
  lastSync: number
  isLoading: boolean
  error: string | null
}

interface EmailSyncState {
  // Per-account email data
  accountEmails: Map<string, SyncedAccountEmails>
  
  // Global state
  isInitialized: boolean
  totalUnreadCount: number
  activeSyncCount: number
  
  // Selected email for viewing
  selectedEmail: SyncedEmail | null
  selectedAccountId: string | null
  
  // Actions
  initialize: () => void
  getAccountEmails: (accountId: string) => SyncedEmail[]
  getAllEmails: () => SyncedEmail[]
  getUnreadCount: (accountId?: string) => number
  refreshAccount: (accountId: string) => Promise<void>
  selectEmail: (email: SyncedEmail | null, accountId: string | null) => void
  markAsRead: (accountId: string, emailId: string) => void
}

export const useEmailSyncStore = create<EmailSyncState>((set, get) => ({
  accountEmails: new Map(),
  isInitialized: false,
  totalUnreadCount: 0,
  activeSyncCount: 0,
  selectedEmail: null,
  selectedAccountId: null,

  initialize: () => {
    if (get().isInitialized) return

    console.log('📦 Initializing EmailSyncStore...')

    // Subscribe to sync events FIRST
    emailSyncService.subscribe((event: SyncEventType, data: any) => {
      switch (event) {
        case 'emails_fetched':
        case 'new_emails': {
          const { accountId, email: accountEmail, emails } = data
          
          set(state => {
            const newMap = new Map(state.accountEmails)
            const existing = newMap.get(accountId)
            
            if (event === 'new_emails' && existing) {
              // Prepend new emails
              newMap.set(accountId, {
                ...existing,
                emails: [...emails, ...existing.emails],
                lastSync: Date.now(),
                isLoading: false,
                error: null,
              })
            } else {
              // Replace all emails
              newMap.set(accountId, {
                accountId,
                accountEmail,
                provider: '',
                emails,
                lastSync: Date.now(),
                isLoading: false,
                error: null,
              })
            }

            // Calculate total unread
            let unreadCount = 0
            newMap.forEach(acc => {
              unreadCount += acc.emails.filter(e => !e.is_read).length
            })

            return {
              accountEmails: newMap,
              totalUnreadCount: unreadCount,
            }
          })
          break
        }

        case 'sync_error': {
          const { accountId, error } = data
          
          set(state => {
            const newMap = new Map(state.accountEmails)
            const existing = newMap.get(accountId)
            
            if (existing) {
              newMap.set(accountId, {
                ...existing,
                isLoading: false,
                error,
              })
            }

            return { accountEmails: newMap }
          })
          break
        }

        case 'sync_started': {
          const { accountId } = data
          
          set(state => {
            const newMap = new Map(state.accountEmails)
            const existing = newMap.get(accountId) || {
              accountId,
              accountEmail: '',
              provider: '',
              emails: [],
              lastSync: 0,
              isLoading: true,
              error: null,
            }
            
            newMap.set(accountId, {
              ...existing,
              isLoading: true,
              error: null,
            })

            return {
              accountEmails: newMap,
              activeSyncCount: state.activeSyncCount + 1,
            }
          })
          break
        }

        case 'sync_stopped': {
          set(state => ({
            activeSyncCount: Math.max(0, state.activeSyncCount - 1),
          }))
          break
        }
      }
    })

    // Initialize the sync service
    emailSyncService.initialize()

    set({ isInitialized: true })
    console.log('✅ EmailSyncStore initialized')
  },

  getAccountEmails: (accountId: string) => {
    const state = get().accountEmails.get(accountId)
    return state?.emails || []
  },

  getAllEmails: () => {
    const allEmails: SyncedEmail[] = []
    
    get().accountEmails.forEach(account => {
      allEmails.push(...account.emails)
    })

    // Sort by timestamp descending
    return allEmails.sort((a, b) => 
      new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    )
  },

  getUnreadCount: (accountId?: string) => {
    if (accountId) {
      const account = get().accountEmails.get(accountId)
      return account?.emails.filter(e => !e.is_read).length || 0
    }
    return get().totalUnreadCount
  },

  refreshAccount: async (accountId: string) => {
    set(state => {
      const newMap = new Map(state.accountEmails)
      const existing = newMap.get(accountId)
      
      if (existing) {
        newMap.set(accountId, {
          ...existing,
          isLoading: true,
          error: null,
        })
      }

      return { accountEmails: newMap }
    })

    try {
      await emailSyncService.refreshAccount(accountId)
    } catch (error) {
      // Error handled by sync service
    }
  },

  selectEmail: (email: SyncedEmail | null, accountId: string | null) => {
    set({
      selectedEmail: email,
      selectedAccountId: accountId,
    })

    // Auto-mark as read when selected
    if (email && accountId && !email.is_read) {
      get().markAsRead(accountId, email.id)
    }
  },

  markAsRead: (accountId: string, emailId: string) => {
    set(state => {
      const newMap = new Map(state.accountEmails)
      const account = newMap.get(accountId)
      
      if (account) {
        const updatedEmails = account.emails.map(e =>
          e.id === emailId ? { ...e, is_read: true } : e
        )
        
        newMap.set(accountId, {
          ...account,
          emails: updatedEmails,
        })

        // Recalculate unread count
        let unreadCount = 0
        newMap.forEach(acc => {
          unreadCount += acc.emails.filter(e => !e.is_read).length
        })

        return {
          accountEmails: newMap,
          totalUnreadCount: unreadCount,
        }
      }

      return state
    })
  },
}))

// Export hook for easier access
export const useSyncedEmails = (accountId?: string) => {
  const store = useEmailSyncStore()
  
  if (accountId) {
    return {
      emails: store.getAccountEmails(accountId),
      isLoading: store.accountEmails.get(accountId)?.isLoading || false,
      error: store.accountEmails.get(accountId)?.error || null,
      lastSync: store.accountEmails.get(accountId)?.lastSync || 0,
      unreadCount: store.getUnreadCount(accountId),
      refresh: () => store.refreshAccount(accountId),
    }
  }

  return {
    emails: store.getAllEmails(),
    isLoading: store.activeSyncCount > 0,
    error: null,
    lastSync: Date.now(),
    unreadCount: store.totalUnreadCount,
    refresh: async () => {
      const promises: Promise<void>[] = []
      store.accountEmails.forEach((_, id) => {
        promises.push(store.refreshAccount(id))
      })
      await Promise.all(promises)
    },
  }
}
