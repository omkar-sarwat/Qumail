/**
 * Provider Email Inbox Component
 * 
 * Displays emails synced from all provider accounts (IMAP/POP3).
 * Shows emails with account labels, unread badges, and real-time sync status.
 */

import React, { useEffect, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Mail,
  RefreshCw,
  Paperclip,
  ChevronRight,
  Inbox,
  Loader2,
} from 'lucide-react'
import { useEmailSyncStore, useSyncedEmails } from '../../stores/emailSyncStore'
import { useEmailAccountsStore } from '../../stores/emailAccountsStore'
import { SyncedEmail } from '../../services/emailSyncService'
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
  const { emails, isLoading, unreadCount, refresh } = useSyncedEmails(accountId)

  // Initialize sync store if not done yet
  useEffect(() => {
    if (!syncStore.isInitialized && accounts.length > 0) {
      syncStore.initialize()
    }
  }, [accounts.length, syncStore.isInitialized])

  // Group emails by account
  const groupedEmails = useMemo(() => {
    if (accountId) {
      const account = accounts.find(a => a.id === accountId)
      return [{
        accountId,
        accountEmail: account?.email || '',
        provider: account?.provider || '',
        emails,
      }]
    }

    const groups: Map<string, { accountEmail: string; provider: string; emails: SyncedEmail[] }> = new Map()
    
    // Get all emails from sync store
    syncStore.accountEmails.forEach((data, id) => {
      groups.set(id, {
        accountEmail: data.accountEmail,
        provider: data.provider,
        emails: data.emails,
      })
    })

    return Array.from(groups.entries()).map(([id, data]) => ({
      accountId: id,
      ...data,
    }))
  }, [accountId, accounts, emails, syncStore.accountEmails])

  // Sort all emails by timestamp
  const allEmailsSorted = useMemo(() => {
    const all: Array<{ email: SyncedEmail; accountId: string; accountEmail: string }> = []
    
    groupedEmails.forEach(group => {
      group.emails.forEach(email => {
        all.push({
          email,
          accountId: group.accountId,
          accountEmail: group.accountEmail,
        })
      })
    })

    return all.sort((a, b) => 
      new Date(b.email.timestamp).getTime() - new Date(a.email.timestamp).getTime()
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
  const hasErrors = Array.from(syncStore.accountEmails.values()).some(acc => acc.error)
  const errorAccounts = Array.from(syncStore.accountEmails.values()).filter(acc => acc.error)

  // Empty state
  if (!isLoading && allEmailsSorted.length === 0 && accounts.length === 0) {
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
  if (!isLoading && allEmailsSorted.length === 0 && accounts.length > 0 && hasErrors) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-8 text-gray-400">
        <Mail className="w-16 h-16 mb-4 opacity-50 text-yellow-500" />
        <h3 className="text-lg font-semibold text-yellow-400 mb-2">Credentials Expired</h3>
        <p className="text-center text-sm mb-2 max-w-md">
          Your saved passwords have expired (browser was closed). 
          Please go to Settings → Email Accounts to re-enter your passwords.
        </p>
        <div className="text-xs text-gray-500 mb-4">
          {errorAccounts.map(acc => (
            <div key={acc.accountId}>• {acc.accountEmail}</div>
          ))}
        </div>
        <button
          onClick={() => refresh()}
          className="flex items-center gap-2 px-4 py-2 bg-yellow-500/20 text-yellow-400 rounded-lg hover:bg-yellow-500/30 transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          Try Again
        </button>
      </div>
    )
  }

  if (!isLoading && allEmailsSorted.length === 0 && accounts.length > 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-8 text-gray-400">
        <Mail className="w-16 h-16 mb-4 opacity-50" />
        <h3 className="text-lg font-semibold text-gray-300 mb-2">No Emails Yet</h3>
        <p className="text-center text-sm mb-4">
          Emails will appear here as they sync from your accounts
        </p>
        <button
          onClick={() => refresh()}
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
          onClick={() => refresh()}
          disabled={isLoading}
          className="p-2 text-gray-400 hover:text-white hover:bg-gray-700/50 rounded-lg transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-5 h-5 ${isLoading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Sync Status Bar */}
      {syncStore.activeSyncCount > 0 && (
        <div className="flex items-center gap-2 px-4 py-2 bg-blue-500/10 border-b border-blue-500/20 text-blue-400 text-sm">
          <Loader2 className="w-4 h-4 animate-spin" />
          <span>Syncing {syncStore.activeSyncCount} account{syncStore.activeSyncCount > 1 ? 's' : ''}...</span>
        </div>
      )}

      {/* Email List */}
      <div className="flex-1 overflow-y-auto">
        <AnimatePresence>
          {allEmailsSorted.map(({ email, accountId, accountEmail }, index) => {
            const avatarColor = getAvatarColor(email.from_address || email.from_name)
            const initials = (email.from_name || email.from_address.split('@')[0])
              .slice(0, 2)
              .toUpperCase()

            return (
              <motion.div
                key={`${accountId}-${email.id}`}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ delay: index * 0.02 }}
                onClick={() => onEmailSelect?.(email, accountId)}
                className={`
                  flex items-start gap-3 px-4 py-3 border-b border-gray-700/30 cursor-pointer
                  hover:bg-gray-800/50 transition-colors
                  ${!email.is_read ? 'bg-gray-800/30' : ''}
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
                      <span className={`font-medium truncate ${!email.is_read ? 'text-white' : 'text-gray-300'}`}>
                        {email.from_name || email.from_address.split('@')[0]}
                      </span>
                      {!email.is_read && (
                        <span className="w-2 h-2 rounded-full bg-blue-500 flex-shrink-0" />
                      )}
                    </div>
                    <span className="text-xs text-gray-500 flex-shrink-0">
                      {formatTimestamp(email.timestamp)}
                    </span>
                  </div>

                  {/* Subject */}
                  <p className={`text-sm truncate mb-1 ${!email.is_read ? 'text-gray-200' : 'text-gray-400'}`}>
                    {email.subject || '(No subject)'}
                  </p>

                  {/* Preview & Account Badge */}
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-xs text-gray-500 truncate flex-1">
                      {truncate(email.body_text || '', 80)}
                    </p>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      {email.has_attachments && (
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
        {isLoading && allEmailsSorted.length === 0 && (
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
