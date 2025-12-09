/**
 * Provider Email Inbox Component
 * 
 * Displays emails synced from all provider accounts (IMAP/POP3).
 * Shows emails with account labels, unread badges, and real-time sync status.
 */

import React, { useMemo, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Mail,
  RefreshCw,
  Paperclip,
  ChevronRight,
  Inbox,
  Loader2,
} from 'lucide-react'
import { useEmailSyncStore, SyncedEmail, SyncedAccountEmails } from '../../stores/emailSyncStore'
import { useEmailAccountsStore } from '../../stores/emailAccountsStore'
import { emailSyncService } from '../../services/emailSyncService'
import { getAvatarColor } from '../../utils/avatarColors'

interface ProviderEmailInboxProps {
  accountId?: string  // Optional: filter by specific account
  onEmailSelect?: (email: SyncedEmail, accountId: string) => void
}

export const ProviderEmailInbox: React.FC<ProviderEmailInboxProps> = ({
  accountId,
  onEmailSelect,
}) => {
  const syncStore = useEmailSyncStore()
  const accounts = useEmailAccountsStore(state => state.accounts)

  // Get emails based on filter
  const emails = useMemo(() => {
    if (accountId) {
      return syncStore.getAccountEmails(accountId)
    }
    return syncStore.getAllEmails()
  }, [accountId, syncStore.accountEmails])

  // Get unread count
  const unreadCount = useMemo(() => {
    if (accountId) {
      return syncStore.getUnreadCount(accountId)
    }
    return syncStore.totalUnreadCount
  }, [accountId, syncStore.accountEmails, syncStore.totalUnreadCount])

  // Check if any account is syncing
  const isSyncing = syncStore.isSyncing

  // Refresh handler
  const handleRefresh = useCallback(async () => {
    if (accountId) {
      syncStore.setSyncStatus(accountId, 'syncing')
      try {
        await emailSyncService.startSync(accountId)
        syncStore.setSyncStatus(accountId, 'idle')
      } catch (error) {
        console.error('Refresh error:', error)
        syncStore.setSyncStatus(accountId, 'error', String(error))
      }
    } else {
      // Refresh all accounts
      const accountIds = Object.keys(syncStore.accountEmails)
      for (const id of accountIds) {
        syncStore.setSyncStatus(id, 'syncing')
        try {
          await emailSyncService.startSync(id)
          syncStore.setSyncStatus(id, 'idle')
        } catch (error) {
          console.error(`Error syncing ${id}:`, error)
          syncStore.setSyncStatus(id, 'error', String(error))
        }
      }
    }
  }, [accountId, syncStore])

  // Group emails by account for display
  const groupedEmails = useMemo(() => {
    if (accountId) {
      const account = accounts.find(a => a.id === accountId)
      const accountData = syncStore.accountEmails[accountId]
      return [{
        accountId,
        accountEmail: accountData?.email || account?.email || '',
        provider: accountData?.provider || account?.provider || '',
        emails: emails,
      }]
    }

    const groups: Array<{ accountId: string; accountEmail: string; provider: string; emails: SyncedEmail[] }> = []
    
    // Get all emails from sync store (Record-based)
    Object.entries(syncStore.accountEmails).forEach(([id, data]: [string, SyncedAccountEmails]) => {
      groups.push({
        accountId: id,
        accountEmail: data.email,
        provider: data.provider,
        emails: data.emails,
      })
    })

    return groups
  }, [accountId, accounts, emails, syncStore.accountEmails])

  // Sort all emails by date
  const allEmailsSorted = useMemo(() => {
    const all: Array<{ email: SyncedEmail; accountId: string; accountEmail: string }> = []
    
    groupedEmails.forEach(group => {
      group.emails.forEach((email: SyncedEmail) => {
        all.push({
          email,
          accountId: group.accountId,
          accountEmail: group.accountEmail,
        })
      })
    })

    return all.sort((a, b) => 
      new Date(b.email.date).getTime() - new Date(a.email.date).getTime()
    )
  }, [groupedEmails])

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp)
    const now = new Date()
    
    const isToday = date.toDateString() === now.toDateString()
    const isYesterday = new Date(now.getTime() - 86400000).toDateString() === date.toDateString()
    
    if (isToday) {
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    } else if (isYesterday) {
      return 'Yesterday'
    } else {
      return date.toLocaleDateString([], { month: 'short', day: 'numeric' })
    }
  }

  const truncate = (text: string, maxLength: number) => {
    if (!text) return ''
    if (text.length <= maxLength) return text
    return text.substring(0, maxLength) + '...'
  }

  // Check for errors in any account
  const hasErrors = Object.values(syncStore.accountEmails).some((acc: SyncedAccountEmails) => acc.syncStatus === 'error')
  const errorAccounts = Object.values(syncStore.accountEmails).filter((acc: SyncedAccountEmails) => acc.syncStatus === 'error')

  // Count syncing accounts
  const activeSyncCount = Object.values(syncStore.accountEmails).filter((acc: SyncedAccountEmails) => acc.syncStatus === 'syncing').length

  // Empty state
  if (!isSyncing && allEmailsSorted.length === 0 && accounts.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-8 text-gray-400">
        <Inbox className="w-16 h-16 mb-4 opacity-50" />
        <h3 className="text-lg font-semibold text-gray-300 mb-2">No Email Accounts</h3>
        <p className="text-center text-sm">
          Add an email account in Settings to start receiving emails
        </p>
      </div>
    )
  }

  // Show credential error state
  if (!isSyncing && allEmailsSorted.length === 0 && accounts.length > 0 && hasErrors) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-8 text-gray-400">
        <Mail className="w-16 h-16 mb-4 opacity-50 text-yellow-500" />
        <h3 className="text-lg font-semibold text-yellow-400 mb-2">Credentials Expired</h3>
        <p className="text-center text-sm mb-2 max-w-md">
          Your saved passwords have expired (browser was closed). 
          Please go to Settings → Email Accounts to re-enter your passwords.
        </p>
        <div className="text-xs text-gray-500 mb-4">
          {errorAccounts.map((acc: SyncedAccountEmails) => (
            <div key={acc.accountId}>• {acc.email}</div>
          ))}
        </div>
        <button
          onClick={handleRefresh}
          className="flex items-center gap-2 px-4 py-2 bg-yellow-500/20 text-yellow-400 rounded-lg hover:bg-yellow-500/30 transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          Try Again
        </button>
      </div>
    )
  }

  if (!isSyncing && allEmailsSorted.length === 0 && accounts.length > 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-8 text-gray-400">
        <Mail className="w-16 h-16 mb-4 opacity-50" />
        <h3 className="text-lg font-semibold text-gray-300 mb-2">No Emails Yet</h3>
        <p className="text-center text-sm mb-4">
          Emails will appear here as they sync from your accounts
        </p>
        <button
          onClick={handleRefresh}
          className="flex items-center gap-2 px-4 py-2 bg-blue-500/20 text-blue-400 rounded-lg hover:bg-blue-500/30 transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full bg-gray-900/50">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-700/50">
        <div className="flex items-center gap-3">
          <h2 className="text-lg font-semibold text-white">Provider Inbox</h2>
          {unreadCount > 0 && (
            <span className="px-2 py-0.5 text-xs font-medium bg-blue-500 text-white rounded-full">
              {unreadCount} unread
            </span>
          )}
        </div>
        <button
          onClick={handleRefresh}
          disabled={isSyncing}
          className="p-2 text-gray-400 hover:text-white hover:bg-gray-700/50 rounded-lg transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-5 h-5 ${isSyncing ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Sync Status Bar */}
      {activeSyncCount > 0 && (
        <div className="flex items-center gap-2 px-4 py-2 bg-blue-500/10 border-b border-blue-500/20 text-blue-400 text-sm">
          <Loader2 className="w-4 h-4 animate-spin" />
          <span>Syncing {activeSyncCount} account{activeSyncCount > 1 ? 's' : ''}...</span>
        </div>
      )}

      {/* Email List */}
      <div className="flex-1 overflow-y-auto">
        <AnimatePresence>
          {allEmailsSorted.map(({ email, accountId: emailAccountId, accountEmail }, index) => {
            const avatarColor = getAvatarColor(email.from || email.fromName || '')
            const displayName = email.fromName || email.from?.split('@')[0] || 'Unknown'
            const initials = displayName.slice(0, 2).toUpperCase()

            return (
              <motion.div
                key={`${emailAccountId}-${email.id}`}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ delay: index * 0.02 }}
                onClick={() => onEmailSelect?.(email, emailAccountId)}
                className={`
                  flex items-start gap-3 px-4 py-3 border-b border-gray-700/30 cursor-pointer
                  hover:bg-gray-800/50 transition-colors
                  ${!email.isRead ? 'bg-gray-800/30' : ''}
                `}
              >
                {/* Avatar */}
                <div
                  className="w-10 h-10 rounded-full flex items-center justify-center text-white font-semibold text-sm flex-shrink-0"
                  style={{ backgroundColor: avatarColor }}
                >
                  {initials}
                </div>

                {/* Email Content */}
                <div className="flex-1 min-w-0">
                  {/* From & Time Row */}
                  <div className="flex items-center justify-between gap-2 mb-1">
                    <div className="flex items-center gap-2 min-w-0">
                      <span className={`font-medium truncate ${!email.isRead ? 'text-white' : 'text-gray-300'}`}>
                        {displayName}
                      </span>
                      {!email.isRead && (
                        <span className="w-2 h-2 rounded-full bg-blue-500 flex-shrink-0" />
                      )}
                    </div>
                    <span className="text-xs text-gray-500 flex-shrink-0">
                      {formatTimestamp(email.date)}
                    </span>
                  </div>

                  {/* Subject */}
                  <p className={`text-sm truncate mb-1 ${!email.isRead ? 'text-gray-200' : 'text-gray-400'}`}>
                    {email.subject || '(No subject)'}
                  </p>

                  {/* Preview & Account Badge */}
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-xs text-gray-500 truncate flex-1">
                      {truncate(email.snippet || email.body || '', 80)}
                    </p>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      {email.hasAttachments && (
                        <Paperclip className="w-3 h-3 text-gray-500" />
                      )}
                      <span className="text-xs px-2 py-0.5 bg-gray-700/50 text-gray-400 rounded-full">
                        {accountEmail.split('@')[0]}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Arrow */}
                <ChevronRight className="w-4 h-4 text-gray-600 flex-shrink-0 mt-3" />
              </motion.div>
            )
          })}
        </AnimatePresence>

        {/* Loading State */}
        {isSyncing && allEmailsSorted.length === 0 && (
          <div className="flex flex-col items-center justify-center py-12">
            <Loader2 className="w-8 h-8 text-blue-500 animate-spin mb-4" />
            <p className="text-gray-400">Loading emails...</p>
          </div>
        )}
      </div>

      {/* Account Summary Footer */}
      <div className="px-4 py-2 border-t border-gray-700/50 bg-gray-900/80">
        <div className="flex items-center justify-between text-xs text-gray-500">
          <span>{allEmailsSorted.length} emails from {accounts.length} account{accounts.length !== 1 ? 's' : ''}</span>
          <span>Auto-sync every 30s</span>
        </div>
      </div>
    </div>
  )
}

export default ProviderEmailInbox
