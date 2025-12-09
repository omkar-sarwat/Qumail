/**
 * Email Sync Store - Manages synced emails from external providers
 * Uses Record instead of Map for JSON serialization with localStorage persistence
 */

import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'

export interface SyncedEmail {
  id: string
  messageId: string
  subject: string
  from: string
  fromName?: string
  to: string
  date: string
  body: string
  bodyHtml?: string
  snippet?: string
  isRead: boolean
  hasAttachments: boolean
  labels?: string[]
  folder?: string
  provider: string
  accountId: string
}

export interface SyncedAccountEmails {
  accountId: string
  email: string
  provider: string
  emails: SyncedEmail[]
  lastSyncTime: string | null
  syncStatus: 'idle' | 'syncing' | 'error'
  errorMessage?: string
  unreadCount: number
}

export interface EmailSyncState {
  // Use Record instead of Map for JSON serialization
  accountEmails: Record<string, SyncedAccountEmails>
  totalUnreadCount: number
  isSyncing: boolean
  
  // Actions
  initializeAccount: (accountId: string, email: string, provider: string) => void
  setEmails: (accountId: string, emails: SyncedEmail[]) => void
  addEmails: (accountId: string, emails: SyncedEmail[]) => void
  markAsRead: (accountId: string, emailId: string) => void
  markAsUnread: (accountId: string, emailId: string) => void
  deleteEmail: (accountId: string, emailId: string) => void
  setSyncStatus: (accountId: string, status: 'idle' | 'syncing' | 'error', errorMessage?: string) => void
  updateLastSyncTime: (accountId: string) => void
  removeAccount: (accountId: string) => void
  clearAllEmails: () => void
  getAccountEmails: (accountId: string) => SyncedEmail[]
  getAllEmails: () => SyncedEmail[]
  getUnreadCount: (accountId: string) => number
  getTotalUnreadCount: () => number
}

export const useEmailSyncStore = create<EmailSyncState>()(
  persist(
    (set, get) => ({
      accountEmails: {},
      totalUnreadCount: 0,
      isSyncing: false,

      initializeAccount: (accountId: string, email: string, provider: string) => {
        console.log(`[EmailSyncStore] Initializing account: ${accountId} (${email}) - ${provider}`)
        set((state) => {
          // Don't reinitialize if already exists
          if (state.accountEmails[accountId]) {
            console.log(`[EmailSyncStore] Account ${accountId} already initialized`)
            return state
          }
          
          const newAccount: SyncedAccountEmails = {
            accountId,
            email,
            provider,
            emails: [],
            lastSyncTime: null,
            syncStatus: 'idle',
            unreadCount: 0
          }
          
          return {
            accountEmails: {
              ...state.accountEmails,
              [accountId]: newAccount
            }
          }
        })
      },

      setEmails: (accountId: string, emails: SyncedEmail[]) => {
        console.log(`[EmailSyncStore] Setting ${emails.length} emails for account: ${accountId}`)
        set((state) => {
          const account = state.accountEmails[accountId]
          if (!account) {
            console.warn(`[EmailSyncStore] Account ${accountId} not found`)
            return state
          }

          const unreadCount = emails.filter(e => !e.isRead).length
          const updatedAccount = {
            ...account,
            emails,
            unreadCount,
            lastSyncTime: new Date().toISOString(),
            syncStatus: 'idle' as const
          }

          const newAccountEmails = {
            ...state.accountEmails,
            [accountId]: updatedAccount
          }

          // Recalculate total unread
          let totalUnread = 0
          Object.values(newAccountEmails).forEach(acc => {
            totalUnread += acc.unreadCount
          })

          console.log(`[EmailSyncStore] Account ${accountId} now has ${emails.length} emails, ${unreadCount} unread`)

          return {
            accountEmails: newAccountEmails,
            totalUnreadCount: totalUnread
          }
        })
      },

      addEmails: (accountId: string, emails: SyncedEmail[]) => {
        console.log(`[EmailSyncStore] Adding ${emails.length} emails to account: ${accountId}`)
        set((state) => {
          const account = state.accountEmails[accountId]
          if (!account) {
            console.warn(`[EmailSyncStore] Account ${accountId} not found for adding emails`)
            return state
          }

          // Merge emails, avoiding duplicates by messageId
          const existingIds = new Set(account.emails.map(e => e.messageId))
          const newEmails = emails.filter(e => !existingIds.has(e.messageId))
          
          if (newEmails.length === 0) {
            console.log(`[EmailSyncStore] No new emails to add for account ${accountId}`)
            return state
          }

          const mergedEmails = [...account.emails, ...newEmails]
          const unreadCount = mergedEmails.filter(e => !e.isRead).length
          
          const updatedAccount = {
            ...account,
            emails: mergedEmails,
            unreadCount,
            lastSyncTime: new Date().toISOString()
          }

          const newAccountEmails = {
            ...state.accountEmails,
            [accountId]: updatedAccount
          }

          // Recalculate total unread
          let totalUnread = 0
          Object.values(newAccountEmails).forEach(acc => {
            totalUnread += acc.unreadCount
          })

          console.log(`[EmailSyncStore] Added ${newEmails.length} new emails to ${accountId}, total: ${mergedEmails.length}`)

          return {
            accountEmails: newAccountEmails,
            totalUnreadCount: totalUnread
          }
        })
      },

      markAsRead: (accountId: string, emailId: string) => {
        set((state) => {
          const account = state.accountEmails[accountId]
          if (!account) return state

          const updatedEmails = account.emails.map(email =>
            email.id === emailId ? { ...email, isRead: true } : email
          )
          const unreadCount = updatedEmails.filter(e => !e.isRead).length

          const updatedAccount = {
            ...account,
            emails: updatedEmails,
            unreadCount
          }

          const newAccountEmails = {
            ...state.accountEmails,
            [accountId]: updatedAccount
          }

          // Recalculate total unread
          let totalUnread = 0
          Object.values(newAccountEmails).forEach(acc => {
            totalUnread += acc.unreadCount
          })

          return {
            accountEmails: newAccountEmails,
            totalUnreadCount: totalUnread
          }
        })
      },

      markAsUnread: (accountId: string, emailId: string) => {
        set((state) => {
          const account = state.accountEmails[accountId]
          if (!account) return state

          const updatedEmails = account.emails.map(email =>
            email.id === emailId ? { ...email, isRead: false } : email
          )
          const unreadCount = updatedEmails.filter(e => !e.isRead).length

          const updatedAccount = {
            ...account,
            emails: updatedEmails,
            unreadCount
          }

          const newAccountEmails = {
            ...state.accountEmails,
            [accountId]: updatedAccount
          }

          // Recalculate total unread
          let totalUnread = 0
          Object.values(newAccountEmails).forEach(acc => {
            totalUnread += acc.unreadCount
          })

          return {
            accountEmails: newAccountEmails,
            totalUnreadCount: totalUnread
          }
        })
      },

      deleteEmail: (accountId: string, emailId: string) => {
        set((state) => {
          const account = state.accountEmails[accountId]
          if (!account) return state

          const updatedEmails = account.emails.filter(email => email.id !== emailId)
          const unreadCount = updatedEmails.filter(e => !e.isRead).length

          const updatedAccount = {
            ...account,
            emails: updatedEmails,
            unreadCount
          }

          const newAccountEmails = {
            ...state.accountEmails,
            [accountId]: updatedAccount
          }

          // Recalculate total unread
          let totalUnread = 0
          Object.values(newAccountEmails).forEach(acc => {
            totalUnread += acc.unreadCount
          })

          return {
            accountEmails: newAccountEmails,
            totalUnreadCount: totalUnread
          }
        })
      },

      setSyncStatus: (accountId: string, status: 'idle' | 'syncing' | 'error', errorMessage?: string) => {
        set((state) => {
          const account = state.accountEmails[accountId]
          if (!account) return state

          const updatedAccount = {
            ...account,
            syncStatus: status,
            errorMessage: errorMessage || undefined
          }

          return {
            accountEmails: {
              ...state.accountEmails,
              [accountId]: updatedAccount
            },
            isSyncing: status === 'syncing'
          }
        })
      },

      updateLastSyncTime: (accountId: string) => {
        set((state) => {
          const account = state.accountEmails[accountId]
          if (!account) return state

          const updatedAccount = {
            ...account,
            lastSyncTime: new Date().toISOString()
          }

          return {
            accountEmails: {
              ...state.accountEmails,
              [accountId]: updatedAccount
            }
          }
        })
      },

      removeAccount: (accountId: string) => {
        console.log(`[EmailSyncStore] Removing account: ${accountId}`)
        set((state) => {
          const newAccountEmails = { ...state.accountEmails }
          delete newAccountEmails[accountId]

          // Recalculate total unread
          let totalUnread = 0
          Object.values(newAccountEmails).forEach(acc => {
            totalUnread += acc.unreadCount
          })

          return {
            accountEmails: newAccountEmails,
            totalUnreadCount: totalUnread
          }
        })
      },

      clearAllEmails: () => {
        console.log('[EmailSyncStore] Clearing all emails')
        set({ accountEmails: {}, totalUnreadCount: 0 })
      },

      getAccountEmails: (accountId: string) => {
        const account = get().accountEmails[accountId]
        return account?.emails || []
      },

      getAllEmails: () => {
        const allEmails: SyncedEmail[] = []
        const accounts = get().accountEmails
        
        Object.values(accounts).forEach(account => {
          allEmails.push(...account.emails)
        })

        // Sort by date, newest first
        allEmails.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
        
        console.log(`[EmailSyncStore] getAllEmails returning ${allEmails.length} total emails`)
        return allEmails
      },

      getUnreadCount: (accountId: string) => {
        const account = get().accountEmails[accountId]
        return account?.unreadCount || 0
      },

      getTotalUnreadCount: () => {
        return get().totalUnreadCount
      }
    }),
    {
      name: 'qumail-synced-emails',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        accountEmails: state.accountEmails,
        totalUnreadCount: state.totalUnreadCount
      })
    }
  )
)

// Export hook for easier access
export const useSyncedEmails = (accountId?: string) => {
  const store = useEmailSyncStore()

  if (accountId) {
    return {
      emails: store.getAccountEmails(accountId),
      unreadCount: store.getUnreadCount(accountId),
      account: store.accountEmails[accountId]
    }
  }

  return {
    emails: store.getAllEmails(),
    unreadCount: store.totalUnreadCount,
    accounts: store.accountEmails
  }
}
