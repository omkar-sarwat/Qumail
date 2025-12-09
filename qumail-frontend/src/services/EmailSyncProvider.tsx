/**
 * Email Sync Provider
 * 
 * React context provider that initializes email sync when user is authenticated.
 * Wrap this around components that need email sync functionality.
 */

import React, { createContext, useContext, useEffect, useState } from 'react'
import { useEmailSyncStore } from '../stores/emailSyncStore'
import { emailSyncService, SyncedEmail } from './emailSyncService'
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

  // Initialize sync when authenticated (even with 0 accounts, to set up listeners)
  useEffect(() => {
    if (isAuthenticated && !isInitialized) {
      console.log('🔄 EmailSyncProvider: Initializing sync service...')
      syncStore.initialize()
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

  const value: EmailSyncContextValue = {
    isInitialized,
    isSyncing: syncStore.activeSyncCount > 0,
    totalUnreadCount: syncStore.totalUnreadCount,
    getAllEmails: syncStore.getAllEmails,
    getAccountEmails: syncStore.getAccountEmails,
    refreshAll: async () => {
      const promises: Promise<void>[] = []
      syncStore.accountEmails.forEach((_, id) => {
        promises.push(syncStore.refreshAccount(id))
      })
      await Promise.all(promises)
    },
    refreshAccount: syncStore.refreshAccount,
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
