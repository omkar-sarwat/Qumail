import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronDown, Check, Plus, Settings } from 'lucide-react'
import { useEmailAccountsStore } from '../../stores/emailAccountsStore'

interface AccountSwitcherProps {
  onOpenSettings?: () => void
  compact?: boolean
}

export const AccountSwitcher: React.FC<AccountSwitcherProps> = ({
  onOpenSettings,
  compact = false,
}) => {
  const [isOpen, setIsOpen] = useState(false)
  const { accounts, activeAccountId, setActiveAccount } = useEmailAccountsStore()

  const activeAccount = accounts.find((acc) => acc.id === activeAccountId)

  if (accounts.length === 0) {
    return (
      <button
        onClick={onOpenSettings}
        className="flex items-center gap-2 px-3 py-2 text-sm text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
      >
        <Plus className="w-4 h-4" />
        <span>Add Email Account</span>
      </button>
    )
  }

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`flex items-center gap-3 px-3 py-2.5 rounded-xl bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors ${
          compact ? '' : 'w-full'
        }`}
      >
        <div className="w-9 h-9 rounded-full bg-indigo-500 flex items-center justify-center flex-shrink-0">
          <span className="text-white text-sm font-semibold">
            {activeAccount?.email.charAt(0).toUpperCase() || 'Q'}
          </span>
        </div>
        {!compact && (
          <>
            <div className="flex-1 text-left min-w-0">
              <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                {activeAccount?.displayName || activeAccount?.email.split('@')[0]}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                {activeAccount?.email}
              </p>
            </div>
            <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
          </>
        )}
      </button>

      <AnimatePresence>
        {isOpen && (
          <>
            {/* Backdrop */}
            <div
              className="fixed inset-0 z-40"
              onClick={() => setIsOpen(false)}
            />

            {/* Dropdown */}
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.15 }}
              className="absolute left-0 right-0 top-full mt-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-lg z-50 overflow-hidden"
            >
              <div className="p-2 max-h-64 overflow-y-auto">
                {accounts.map((account) => (
                  <button
                    key={account.id}
                    onClick={() => {
                      setActiveAccount(account.id)
                      setIsOpen(false)
                    }}
                    className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors ${
                      account.id === activeAccountId
                        ? 'bg-indigo-50 dark:bg-indigo-900/20 text-gray-900 dark:text-white'
                        : 'hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300'
                    }`}
                  >
                    <div className="w-9 h-9 rounded-full bg-indigo-500 flex items-center justify-center flex-shrink-0">
                      <span className="text-white text-sm font-semibold">
                        {account.email.charAt(0).toUpperCase()}
                      </span>
                    </div>
                    <div className="flex-1 text-left min-w-0">
                      <p className="text-sm font-medium truncate">
                        {account.displayName || account.email.split('@')[0]}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                        {account.email}
                      </p>
                    </div>
                    {account.id === activeAccountId && (
                      <Check className="w-4 h-4 text-indigo-600 dark:text-indigo-400 flex-shrink-0" />
                    )}
                  </button>
                ))}
              </div>

              {/* Divider */}
              <div className="border-t border-gray-200 dark:border-gray-700" />

              {/* Settings link */}
              <div className="p-2">
                <button
                  onClick={() => {
                    setIsOpen(false)
                    onOpenSettings?.()
                  }}
                  className="w-full flex items-center gap-3 px-3 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                >
                  <Settings className="w-4 h-4" />
                  <span className="text-sm font-medium">Manage Accounts</span>
                </button>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  )
}

export default AccountSwitcher
