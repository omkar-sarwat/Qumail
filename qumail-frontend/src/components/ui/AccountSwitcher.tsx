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
        className="flex items-center gap-2 px-3 py-2 text-sm text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors"
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
        className={`flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-gray-800 transition-colors ${
          compact ? '' : 'w-full'
        }`}
      >
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
          <span className="text-white text-sm font-medium">
            {activeAccount?.email.charAt(0).toUpperCase() || 'Q'}
          </span>
        </div>
        {!compact && (
          <>
            <div className="flex-1 text-left min-w-0">
              <p className="text-sm font-medium text-white truncate">
                {activeAccount?.displayName || activeAccount?.email.split('@')[0]}
              </p>
              <p className="text-xs text-gray-400 truncate">
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
              className="absolute left-0 right-0 top-full mt-2 bg-gray-900 border border-gray-700 rounded-xl shadow-xl z-50 overflow-hidden"
            >
              <div className="p-2 max-h-64 overflow-y-auto">
                {accounts.map((account) => (
                  <button
                    key={account.id}
                    onClick={() => {
                      setActiveAccount(account.id)
                      setIsOpen(false)
                    }}
                    className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
                      account.id === activeAccountId
                        ? 'bg-blue-500/20 text-white'
                        : 'hover:bg-gray-800 text-gray-300'
                    }`}
                  >
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center flex-shrink-0">
                      <span className="text-white text-sm font-medium">
                        {account.email.charAt(0).toUpperCase()}
                      </span>
                    </div>
                    <div className="flex-1 text-left min-w-0">
                      <p className="text-sm font-medium truncate">
                        {account.displayName || account.email.split('@')[0]}
                      </p>
                      <p className="text-xs text-gray-400 truncate">
                        {account.email}
                      </p>
                    </div>
                    {account.id === activeAccountId && (
                      <Check className="w-4 h-4 text-blue-400 flex-shrink-0" />
                    )}
                  </button>
                ))}
              </div>

              {/* Divider */}
              <div className="border-t border-gray-700" />

              {/* Settings link */}
              <div className="p-2">
                <button
                  onClick={() => {
                    setIsOpen(false)
                    onOpenSettings?.()
                  }}
                  className="w-full flex items-center gap-3 px-3 py-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors"
                >
                  <Settings className="w-4 h-4" />
                  <span className="text-sm">Manage Accounts</span>
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
