import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Mail,
  Plus,
  Trash2,
  Check,
  X,
  Loader2,
  Settings,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  AlertCircle,
  CheckCircle,
  Folder,
} from 'lucide-react'
import toast from 'react-hot-toast'
import { apiService } from '../../services/api'
import { useEmailAccountsStore, EmailAccountSettings } from '../../stores/emailAccountsStore'
import { storePassword, removePassword } from '../../utils/credentialStorage'
import { emailSyncService } from '../../services/emailSyncService'

interface AddAccountFormData {
  email: string
  password: string
  displayName: string
  provider: string
  settings: EmailAccountSettings
  foldersToSync: string[]
}

const initialFormData: AddAccountFormData = {
  email: '',
  password: '',
  displayName: '',
  provider: '',
  settings: {
    smtp_host: '',
    smtp_port: 587,
    smtp_security: 'starttls',
    imap_host: '',
    imap_port: 993,
    imap_security: 'ssl',
    protocol: 'imap',
  },
  foldersToSync: ['INBOX', 'Sent'],
}

export const EmailAccountsSettings: React.FC = () => {
  const { accounts, activeAccountId, addAccount, removeAccount, setActiveAccount } = useEmailAccountsStore()
  
  const [showAddForm, setShowAddForm] = useState(false)
  const [formData, setFormData] = useState<AddAccountFormData>(initialFormData)
  const [isDetecting, setIsDetecting] = useState(false)
  const [isTesting, setIsTesting] = useState(false)
  const [testResults, setTestResults] = useState<{ imap: string | null; smtp: string | null }>({ imap: null, smtp: null })
  const [availableFolders, setAvailableFolders] = useState<string[]>([])
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [expandedAccount, setExpandedAccount] = useState<string | null>(null)

  // Detect provider when email changes
  const handleEmailChange = async (email: string) => {
    setFormData((prev) => ({ ...prev, email }))
    
    if (email.includes('@') && email.split('@')[1]?.includes('.')) {
      setIsDetecting(true)
      try {
        const result = await apiService.detectProvider(email)
        if (result.mode === 'preset' && result.settings) {
          const s = result.settings
          setFormData((prev) => ({
            ...prev,
            provider: result.provider,
            settings: {
              smtp_host: s.smtp_host,
              smtp_port: s.smtp_port,
              smtp_security: s.smtp_security as 'ssl' | 'starttls',
              imap_host: s.imap_host,
              imap_port: s.imap_port,
              imap_security: s.imap_security as 'ssl' | 'starttls',
              protocol: s.notes?.toLowerCase().includes('pop3') ? 'pop3' : 'imap',
            },
          }))
          toast.success(`Detected ${result.provider} - settings auto-filled!`)
        } else {
          setFormData((prev) => ({
            ...prev,
            provider: 'Custom',
          }))
          setShowAdvanced(true)
          toast(`Unknown provider - please enter settings manually`, { icon: '⚙️' })
        }
      } catch (error) {
        console.error('Provider detection failed:', error)
      } finally {
        setIsDetecting(false)
      }
    }
  }

  // Test connections
  const handleTestConnection = async () => {
    if (!formData.email || !formData.password) {
      toast.error('Please enter email and password first')
      return
    }

    setIsTesting(true)
    setTestResults({ imap: null, smtp: null })

    const config = {
      host: formData.settings.imap_host,
      port: formData.settings.imap_port,
      security: formData.settings.imap_security,
      username: formData.email,
      password: formData.password,
    }

    // Test incoming (IMAP or POP3)
    try {
      let incomingResult
      if (formData.settings.protocol === 'pop3') {
        incomingResult = await apiService.testPop3Connection({
          ...config,
          host: formData.settings.imap_host,
          port: formData.settings.imap_port,
        })
      } else {
        incomingResult = await apiService.testImapConnection(config)
      }
      setTestResults((prev) => ({ ...prev, imap: incomingResult.status === 'ok' ? 'success' : 'failed' }))
      if (incomingResult.status === 'ok') {
        toast.success(`${formData.settings.protocol.toUpperCase()} connection successful!`)
      }
    } catch (error: any) {
      setTestResults((prev) => ({ ...prev, imap: 'failed' }))
      toast.error(`${formData.settings.protocol.toUpperCase()} test failed: ${error.response?.data?.detail || error.message}`)
    }

    // Test SMTP
    try {
      const smtpResult = await apiService.testSmtpConnection({
        host: formData.settings.smtp_host,
        port: formData.settings.smtp_port,
        security: formData.settings.smtp_security,
        username: formData.email,
        password: formData.password,
      })
      setTestResults((prev) => ({ ...prev, smtp: smtpResult.status === 'ok' ? 'success' : 'failed' }))
      if (smtpResult.status === 'ok') {
        toast.success('SMTP connection successful!')
      }
    } catch (error: any) {
      setTestResults((prev) => ({ ...prev, smtp: 'failed' }))
      toast.error(`SMTP test failed: ${error.response?.data?.detail || error.message}`)
    }

    // If IMAP succeeded, try to list folders
    if (formData.settings.protocol === 'imap') {
      try {
        const foldersResult = await apiService.listImapFolders(config)
        if (foldersResult.folders) {
          setAvailableFolders(foldersResult.folders)
        }
      } catch (error) {
        console.error('Failed to list folders:', error)
      }
    }

    setIsTesting(false)
  }

  // Add account
  const handleAddAccount = () => {
    if (!formData.email || !formData.password) {
      toast.error('Email and password are required')
      return
    }

    if (testResults.imap !== 'success' || testResults.smtp !== 'success') {
      toast.error('Please test connections first')
      return
    }

    // Generate account ID upfront
    const accountId = `acc_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`

    // Store password securely (with the SAME ID that will be used for the account)
    storePassword(accountId, formData.password)

    // Add account with pre-generated ID so password lookup works
    const newAccount = addAccount({
      id: accountId,  // Pass the same ID so password can be found
      email: formData.email,
      displayName: formData.displayName || formData.email.split('@')[0],
      provider: formData.provider,
      settings: formData.settings,
      isActive: true,
      isVerified: true,
      foldersToSync: formData.foldersToSync,
    })

    // Start email sync for the new account (fetches initial 30 emails)
    toast.success(`Account ${formData.email} added! Syncing emails...`)
    
    console.log(`📧 Account added with ID: ${newAccount.id}, starting sync...`)
    
    // Start sync immediately since we have the account ID
    emailSyncService.startSync(newAccount.id)

    setFormData(initialFormData)
    setShowAddForm(false)
    setTestResults({ imap: null, smtp: null })
    setAvailableFolders([])
  }

  // Toggle folder sync
  const toggleFolderSync = (folder: string) => {
    setFormData((prev) => ({
      ...prev,
      foldersToSync: prev.foldersToSync.includes(folder)
        ? prev.foldersToSync.filter((f) => f !== folder)
        : [...prev.foldersToSync, folder],
    }))
  }

  return (
    <div className="bg-gray-900/50 backdrop-blur-xl rounded-2xl border border-gray-700/50 p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl">
            <Mail className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white">Email Accounts</h2>
            <p className="text-sm text-gray-400">Manage your email accounts for QuMail</p>
          </div>
        </div>
        <button
          onClick={() => setShowAddForm(true)}
          className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg hover:opacity-90 transition-opacity"
        >
          <Plus className="w-4 h-4" />
          Add Account
        </button>
      </div>

      {/* Account List */}
      <div className="space-y-4">
        {accounts.length === 0 ? (
          <div className="text-center py-12 text-gray-400">
            <Mail className="w-16 h-16 mx-auto mb-4 opacity-50" />
            <p>No email accounts configured</p>
            <p className="text-sm mt-2">Add an account to start sending and receiving encrypted emails</p>
          </div>
        ) : (
          accounts.map((account) => (
            <motion.div
              key={account.id}
              layout
              className={`p-4 rounded-xl border transition-colors ${
                account.id === activeAccountId
                  ? 'bg-blue-500/10 border-blue-500/50'
                  : 'bg-gray-800/50 border-gray-700/50 hover:border-gray-600/50'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                    account.id === activeAccountId ? 'bg-blue-500' : 'bg-gray-700'
                  }`}>
                    <Mail className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-white">{account.email}</span>
                      {account.isVerified && (
                        <CheckCircle className="w-4 h-4 text-green-400" />
                      )}
                      {account.id === activeAccountId && (
                        <span className="text-xs px-2 py-0.5 bg-blue-500/20 text-blue-400 rounded-full">
                          Active
                        </span>
                      )}
                    </div>
                    <span className="text-sm text-gray-400">{account.provider}</span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {account.id !== activeAccountId && (
                    <button
                      onClick={() => setActiveAccount(account.id)}
                      className="px-3 py-1.5 text-sm bg-blue-500/20 text-blue-400 rounded-lg hover:bg-blue-500/30 transition-colors"
                    >
                      Set Active
                    </button>
                  )}
                  <button
                    onClick={() => setExpandedAccount(expandedAccount === account.id ? null : account.id)}
                    className="p-2 text-gray-400 hover:text-white transition-colors"
                  >
                    {expandedAccount === account.id ? (
                      <ChevronUp className="w-4 h-4" />
                    ) : (
                      <ChevronDown className="w-4 h-4" />
                    )}
                  </button>
                  <button
                    onClick={() => {
                      if (confirm(`Remove account ${account.email}?`)) {
                        removePassword(account.id)  // Remove stored password
                        removeAccount(account.id)
                        toast.success('Account removed')
                      }
                    }}
                    className="p-2 text-red-400 hover:text-red-300 transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Expanded Details */}
              <AnimatePresence>
                {expandedAccount === account.id && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="mt-4 pt-4 border-t border-gray-700/50 overflow-hidden"
                  >
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-gray-400">Incoming ({account.settings.protocol.toUpperCase()}):</span>
                        <p className="text-white">{account.settings.imap_host}:{account.settings.imap_port}</p>
                      </div>
                      <div>
                        <span className="text-gray-400">Outgoing (SMTP):</span>
                        <p className="text-white">{account.settings.smtp_host}:{account.settings.smtp_port}</p>
                      </div>
                      <div>
                        <span className="text-gray-400">Folders to Sync:</span>
                        <p className="text-white">{account.foldersToSync.join(', ')}</p>
                      </div>
                      <div>
                        <span className="text-gray-400">Added:</span>
                        <p className="text-white">{new Date(account.createdAt).toLocaleDateString()}</p>
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          ))
        )}
      </div>

      {/* Add Account Modal */}
      <AnimatePresence>
        {showAddForm && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4"
            onClick={(e) => e.target === e.currentTarget && setShowAddForm(false)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-gray-900 rounded-2xl border border-gray-700 w-full max-w-lg max-h-[90vh] overflow-y-auto"
            >
              <div className="p-6 border-b border-gray-700">
                <div className="flex items-center justify-between">
                  <h3 className="text-xl font-bold text-white">Add Email Account</h3>
                  <button
                    onClick={() => setShowAddForm(false)}
                    className="p-2 text-gray-400 hover:text-white transition-colors"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
              </div>

              <div className="p-6 space-y-4">
                {/* Email */}
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Email Address
                  </label>
                  <div className="relative">
                    <input
                      type="email"
                      value={formData.email}
                      onChange={(e) => handleEmailChange(e.target.value)}
                      placeholder="you@rediffmail.com"
                      className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
                    />
                    {isDetecting && (
                      <Loader2 className="absolute right-3 top-3 w-5 h-5 text-blue-400 animate-spin" />
                    )}
                  </div>
                  {formData.provider && (
                    <p className="mt-2 text-sm text-green-400">
                      ✓ Detected: {formData.provider}
                    </p>
                  )}
                </div>

                {/* Password */}
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Password
                  </label>
                  <input
                    type="password"
                    value={formData.password}
                    onChange={(e) => setFormData((prev) => ({ ...prev, password: e.target.value }))}
                    placeholder="Your email password"
                    className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
                  />
                  <p className="mt-1 text-xs text-gray-500">
                    For Gmail/Yahoo/Outlook, you may need an app-specific password
                  </p>
                </div>

                {/* Display Name */}
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Display Name (optional)
                  </label>
                  <input
                    type="text"
                    value={formData.displayName}
                    onChange={(e) => setFormData((prev) => ({ ...prev, displayName: e.target.value }))}
                    placeholder="Your Name"
                    className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
                  />
                </div>

                {/* Advanced Settings Toggle */}
                <button
                  onClick={() => setShowAdvanced(!showAdvanced)}
                  className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors"
                >
                  <Settings className="w-4 h-4" />
                  {showAdvanced ? 'Hide' : 'Show'} Advanced Settings
                  {showAdvanced ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                </button>

                {/* Advanced Settings */}
                <AnimatePresence>
                  {showAdvanced && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      className="space-y-4 overflow-hidden"
                    >
                      {/* Protocol */}
                      <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                          Incoming Protocol
                        </label>
                        <div className="flex gap-4">
                          <label className="flex items-center gap-2">
                            <input
                              type="radio"
                              checked={formData.settings.protocol === 'imap'}
                              onChange={() => setFormData((prev) => ({
                                ...prev,
                                settings: { ...prev.settings, protocol: 'imap' },
                              }))}
                              className="text-blue-500"
                            />
                            <span className="text-gray-300">IMAP</span>
                          </label>
                          <label className="flex items-center gap-2">
                            <input
                              type="radio"
                              checked={formData.settings.protocol === 'pop3'}
                              onChange={() => setFormData((prev) => ({
                                ...prev,
                                settings: { ...prev.settings, protocol: 'pop3' },
                              }))}
                              className="text-blue-500"
                            />
                            <span className="text-gray-300">POP3</span>
                          </label>
                        </div>
                      </div>

                      {/* Incoming Server */}
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-300 mb-2">
                            {formData.settings.protocol.toUpperCase()} Server
                          </label>
                          <input
                            type="text"
                            value={formData.settings.imap_host}
                            onChange={(e) => setFormData((prev) => ({
                              ...prev,
                              settings: { ...prev.settings, imap_host: e.target.value },
                            }))}
                            placeholder={`${formData.settings.protocol}.example.com`}
                            className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-300 mb-2">
                            Port
                          </label>
                          <input
                            type="number"
                            value={formData.settings.imap_port}
                            onChange={(e) => setFormData((prev) => ({
                              ...prev,
                              settings: { ...prev.settings, imap_port: parseInt(e.target.value) },
                            }))}
                            className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm"
                          />
                        </div>
                      </div>

                      {/* SMTP Server */}
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-300 mb-2">
                            SMTP Server
                          </label>
                          <input
                            type="text"
                            value={formData.settings.smtp_host}
                            onChange={(e) => setFormData((prev) => ({
                              ...prev,
                              settings: { ...prev.settings, smtp_host: e.target.value },
                            }))}
                            placeholder="smtp.example.com"
                            className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-300 mb-2">
                            Port
                          </label>
                          <input
                            type="number"
                            value={formData.settings.smtp_port}
                            onChange={(e) => setFormData((prev) => ({
                              ...prev,
                              settings: { ...prev.settings, smtp_port: parseInt(e.target.value) },
                            }))}
                            className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm"
                          />
                        </div>
                      </div>

                      {/* Security */}
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-300 mb-2">
                            Incoming Security
                          </label>
                          <select
                            value={formData.settings.imap_security}
                            onChange={(e) => setFormData((prev) => ({
                              ...prev,
                              settings: { ...prev.settings, imap_security: e.target.value as 'ssl' | 'starttls' },
                            }))}
                            className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm"
                          >
                            <option value="ssl">SSL/TLS</option>
                            <option value="starttls">STARTTLS</option>
                          </select>
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-300 mb-2">
                            SMTP Security
                          </label>
                          <select
                            value={formData.settings.smtp_security}
                            onChange={(e) => setFormData((prev) => ({
                              ...prev,
                              settings: { ...prev.settings, smtp_security: e.target.value as 'ssl' | 'starttls' },
                            }))}
                            className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm"
                          >
                            <option value="ssl">SSL/TLS</option>
                            <option value="starttls">STARTTLS</option>
                          </select>
                        </div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* Test Connection */}
                <div className="pt-4 border-t border-gray-700">
                  <button
                    onClick={handleTestConnection}
                    disabled={isTesting || !formData.email || !formData.password}
                    className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-gray-800 text-white rounded-xl hover:bg-gray-700 transition-colors disabled:opacity-50"
                  >
                    {isTesting ? (
                      <>
                        <Loader2 className="w-5 h-5 animate-spin" />
                        Testing Connections...
                      </>
                    ) : (
                      <>
                        <RefreshCw className="w-5 h-5" />
                        Test Connection
                      </>
                    )}
                  </button>

                  {/* Test Results */}
                  {(testResults.imap || testResults.smtp) && (
                    <div className="mt-4 grid grid-cols-2 gap-4">
                      <div className={`p-3 rounded-lg ${
                        testResults.imap === 'success' ? 'bg-green-500/20 text-green-400' :
                        testResults.imap === 'failed' ? 'bg-red-500/20 text-red-400' :
                        'bg-gray-800 text-gray-400'
                      }`}>
                        <div className="flex items-center gap-2">
                          {testResults.imap === 'success' ? (
                            <CheckCircle className="w-4 h-4" />
                          ) : testResults.imap === 'failed' ? (
                            <AlertCircle className="w-4 h-4" />
                          ) : null}
                          {formData.settings.protocol.toUpperCase()}: {testResults.imap || 'Not tested'}
                        </div>
                      </div>
                      <div className={`p-3 rounded-lg ${
                        testResults.smtp === 'success' ? 'bg-green-500/20 text-green-400' :
                        testResults.smtp === 'failed' ? 'bg-red-500/20 text-red-400' :
                        'bg-gray-800 text-gray-400'
                      }`}>
                        <div className="flex items-center gap-2">
                          {testResults.smtp === 'success' ? (
                            <CheckCircle className="w-4 h-4" />
                          ) : testResults.smtp === 'failed' ? (
                            <AlertCircle className="w-4 h-4" />
                          ) : null}
                          SMTP: {testResults.smtp || 'Not tested'}
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                {/* Folders to Sync */}
                {availableFolders.length > 0 && (
                  <div className="pt-4 border-t border-gray-700">
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      <Folder className="w-4 h-4 inline mr-2" />
                      Folders to Sync
                    </label>
                    <div className="flex flex-wrap gap-2">
                      {availableFolders.map((folder) => (
                        <button
                          key={folder}
                          onClick={() => toggleFolderSync(folder)}
                          className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
                            formData.foldersToSync.includes(folder)
                              ? 'bg-blue-500/20 text-blue-400 border border-blue-500/50'
                              : 'bg-gray-800 text-gray-400 border border-gray-700 hover:border-gray-600'
                          }`}
                        >
                          {formData.foldersToSync.includes(folder) && (
                            <Check className="w-3 h-3 inline mr-1" />
                          )}
                          {folder}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Footer */}
              <div className="p-6 border-t border-gray-700 flex gap-4">
                <button
                  onClick={() => setShowAddForm(false)}
                  className="flex-1 px-4 py-3 bg-gray-800 text-gray-300 rounded-xl hover:bg-gray-700 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleAddAccount}
                  disabled={testResults.imap !== 'success' || testResults.smtp !== 'success'}
                  className="flex-1 px-4 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-xl hover:opacity-90 transition-opacity disabled:opacity-50"
                >
                  Add Account
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default EmailAccountsSettings
