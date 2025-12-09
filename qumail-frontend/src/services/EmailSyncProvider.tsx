/**
 * Email Sync Provider
 * 
 * React context provider that initializes email sync when user is authenticated.
 * Wrap this around components that need email sync functionality.
 */

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react'
import { useEmailSyncStore } from '../stores/emailSyncStore'
import { emailSyncService } from './emailSyncService'
import type { SyncedEmail } from '../stores/emailSyncStore'
import { useAuth } from '../context/AuthContext'

interface EmailSyncContextValue {
  isInitialized: boolean
  isSyncing: boolean
  totalUnreadCount: number
  getAllEmails: () => SyncedEmail[]
  getAccountEmails: (accountId: string) => SyncedEmail[]
  refreshAll: () => Promise<void>
  refreshAccount: (accountId: string) => Promise<void>
}

const EmailSyncContext = createContext<EmailSyncContextValue | null>(null)

export const EmailSyncProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useAuth()
  const syncStore = useEmailSyncStore()
  const [isInitialized, setIsInitialized] = useState(false)

  // Initialize sync when authenticated
  useEffect(() => {
    if (isAuthenticated && !isInitialized) {
      console.log('🔄 EmailSyncProvider: Email sync ready')
      setIsInitialized(true)
    }
  }, [isAuthenticated, isInitialized])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (isInitialized) {
        console.log('🧹 EmailSyncProvider: Cleaning up sync service')
        emailSyncService.destroy()
      }
    }
  }, [isInitialized])

  // Refresh all accounts using the emailSyncService
  const refreshAll = useCallback(async () => {
    const accountIds = Object.keys(syncStore.accountEmails)
    for (const accountId of accountIds) {
      const account = syncStore.accountEmails[accountId]
      if (account) {
        syncStore.setSyncStatus(accountId, 'syncing')
        try {
          await emailSyncService.startSync(accountId)
          syncStore.setSyncStatus(accountId, 'idle')
        } catch (error) {
          console.error(`Error syncing account ${accountId}:`, error)
          syncStore.setSyncStatus(accountId, 'error', String(error))
        }
      }
    }
  }, [syncStore])

  // Refresh single account
  const refreshAccount = useCallback(async (accountId: string) => {
    const account = syncStore.accountEmails[accountId]
    if (account) {
      syncStore.setSyncStatus(accountId, 'syncing')
      try {
        await emailSyncService.startSync(accountId)
        syncStore.setSyncStatus(accountId, 'idle')
      } catch (error) {
        console.error(`Error syncing account ${accountId}:`, error)
        syncStore.setSyncStatus(accountId, 'error', String(error))
      }
    }
  }, [syncStore])

  const value: EmailSyncContextValue = {
    isInitialized,
    isSyncing: syncStore.isSyncing,
    totalUnreadCount: syncStore.totalUnreadCount,
    getAllEmails: syncStore.getAllEmails,
    getAccountEmails: syncStore.getAccountEmails,
    refreshAll,
    refreshAccount,
  }

  return (
    <EmailSyncContext.Provider value={value}>
      {children}
    </EmailSyncContext.Provider>
  )
}

export const useEmailSync = () => {
  const context = useContext(EmailSyncContext)
  if (!context) {
    // Return safe defaults if used outside provider
    return {
      isInitialized: false,
      isSyncing: false,
      totalUnreadCount: 0,
      getAllEmails: () => [],
      getAccountEmails: () => [],
      refreshAll: async () => {},
      refreshAccount: async () => {},
    }
  }
  return context
}
