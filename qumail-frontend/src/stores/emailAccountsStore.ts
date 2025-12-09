import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface EmailAccountSettings {
  smtp_host: string
  smtp_port: number
  smtp_security: 'ssl' | 'starttls'
  imap_host: string
  imap_port: number
  imap_security: 'ssl' | 'starttls'
  protocol: 'imap' | 'pop3' | 'oauth'  // OAuth for Microsoft Graph API, IMAP/POP3 for others
}

export interface EmailAccount {
  id: string
  email: string
  displayName: string
  provider: string
  settings: EmailAccountSettings
  isActive: boolean
  isVerified: boolean
  lastSync?: string
  foldersToSync: string[]
  createdAt: string
  // OAuth-specific fields
  authType?: 'password' | 'oauth'
  oauthProvider?: 'google' | 'microsoft'
}

interface EmailAccountsState {
  accounts: EmailAccount[]
  activeAccountId: string | null
  isLoading: boolean
  error: string | null

  // Actions
  // Allow passing optional id to correlate with stored password
  addAccount: (account: Omit<EmailAccount, 'createdAt'> & { id?: string }) => EmailAccount
  removeAccount: (id: string) => void
  updateAccount: (id: string, updates: Partial<EmailAccount>) => void
  setActiveAccount: (id: string | null) => void
  getActiveAccount: () => EmailAccount | null
  getAccountByEmail: (email: string) => EmailAccount | undefined
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  clearAccounts: () => void
}

export const useEmailAccountsStore = create<EmailAccountsState>()(
  persist(
    (set, get) => ({
      accounts: [],
      activeAccountId: null,
      isLoading: false,
      error: null,

      addAccount: (account) => {
        // If account already has an ID (pre-generated), use it
        // Otherwise generate a new one
        const newAccount: EmailAccount = {
          ...account,
          id: (account as any).id || `acc_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
          createdAt: new Date().toISOString(),
        }
        set((state) => ({
          accounts: [...state.accounts, newAccount],
          activeAccountId: state.activeAccountId || newAccount.id,
        }))
        // Return the new account for reference
        return newAccount
      },

      removeAccount: (id) => {
        set((state) => {
          const newAccounts = state.accounts.filter((acc) => acc.id !== id)
          return {
            accounts: newAccounts,
            activeAccountId:
              state.activeAccountId === id
                ? newAccounts[0]?.id || null
                : state.activeAccountId,
          }
        })
      },

      updateAccount: (id, updates) => {
        set((state) => ({
          accounts: state.accounts.map((acc) =>
            acc.id === id ? { ...acc, ...updates } : acc
          ),
        }))
      },

      setActiveAccount: (id) => {
        set({ activeAccountId: id })
      },

      getActiveAccount: () => {
        const { accounts, activeAccountId } = get()
        return accounts.find((acc) => acc.id === activeAccountId) || null
      },

      getAccountByEmail: (email) => {
        return get().accounts.find((acc) => acc.email.toLowerCase() === email.toLowerCase())
      },

      setLoading: (loading) => set({ isLoading: loading }),
      setError: (error) => set({ error }),

      clearAccounts: () => {
        set({ accounts: [], activeAccountId: null })
      },
    }),
    {
      name: 'qumail-email-accounts',
    }
  )
)
