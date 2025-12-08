/**
 * Hook to get active email account with credentials for API calls
 */

import { useCallback, useMemo } from 'react'
import { useEmailAccountsStore } from '../stores/emailAccountsStore'
import { getPassword } from '../utils/credentialStorage'

export interface ActiveAccountWithCredentials {
  id: string
  email: string
  password: string
  displayName: string
  provider: string
  settings: {
    smtp_host: string
    smtp_port: number
    smtp_security: string
    imap_host: string
    imap_port: number
    imap_security: string
    protocol: string
  }
  foldersToSync: string[]
}

export function useActiveEmailAccount() {
  const { accounts, activeAccountId, setActiveAccount } = useEmailAccountsStore()

  const activeAccount = useMemo(() => {
    return accounts.find((acc) => acc.id === activeAccountId) || null
  }, [accounts, activeAccountId])

  const getActiveAccountWithCredentials = useCallback((): ActiveAccountWithCredentials | null => {
    if (!activeAccount) return null

    const password = getPassword(activeAccount.id)
    if (!password) {
      console.warn(`No password found for account ${activeAccount.email}`)
      return null
    }

    return {
      id: activeAccount.id,
      email: activeAccount.email,
      password,
      displayName: activeAccount.displayName,
      provider: activeAccount.provider,
      settings: {
        smtp_host: activeAccount.settings.smtp_host,
        smtp_port: activeAccount.settings.smtp_port,
        smtp_security: activeAccount.settings.smtp_security,
        imap_host: activeAccount.settings.imap_host,
        imap_port: activeAccount.settings.imap_port,
        imap_security: activeAccount.settings.imap_security,
        protocol: activeAccount.settings.protocol,
      },
      foldersToSync: activeAccount.foldersToSync,
    }
  }, [activeAccount])

  const hasActiveAccount = useMemo(() => {
    return activeAccount !== null
  }, [activeAccount])

  const isGmailAccount = useMemo(() => {
    if (!activeAccount) return false
    return activeAccount.provider === 'Gmail' || activeAccount.email.endsWith('@gmail.com')
  }, [activeAccount])

  return {
    activeAccount,
    activeAccountId,
    accounts,
    hasActiveAccount,
    isGmailAccount,
    setActiveAccount,
    getActiveAccountWithCredentials,
  }
}
