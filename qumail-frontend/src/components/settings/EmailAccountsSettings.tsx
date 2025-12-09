import React, { useState, useEffect } from 'react'
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
  Key,
  ExternalLink,
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
  const [reauthAccountId, setReauthAccountId] = useState<string | null>(null)
  const [reauthPassword, setReauthPassword] = useState('')
  const [isReauthenticating, setIsReauthenticating] = useState(false)
  const [isMicrosoftOAuthConfigured, setIsMicrosoftOAuthConfigured] = useState(false)
  const [isMicrosoftAuthLoading, setIsMicrosoftAuthLoading] = useState(false)

  // Check if Microsoft OAuth is configured
  useEffect(() => {
    const checkMicrosoftOAuth = async () => {
      try {
        const response = await apiService.checkMicrosoftOAuthStatus()
        setIsMicrosoftOAuthConfigured(response.configured)
      } catch (error) {
        console.error('Failed to check Microsoft OAuth status:', error)
        setIsMicrosoftOAuthConfigured(false)
      }
    }
    checkMicrosoftOAuth()
  }, [])

  // Handle Microsoft/Outlook OAuth login
  const handleMicrosoftLogin = async () => {
    setIsMicrosoftAuthLoading(true)
    try {
      const response = await apiService.getMicrosoftAuthUrl()
      if (response.authorization_url) {
        // Store state for CSRF validation
        sessionStorage.setItem('microsoft_oauth_state', response.state)
        // Redirect to Microsoft OAuth
        window.location.href = response.authorization_url
      } else {
        toast.error('Failed to get Microsoft authorization URL')
      }
    } catch (error: any) {
      console.error('Microsoft OAuth error:', error)
      toast.error(error.response?.data?.detail || 'Failed to start Microsoft login')
    } finally {
      setIsMicrosoftAuthLoading(false)
    }
  }

  // Re-authenticate account with new password
  const handleReauthenticate = async (accountId: string) => {
    const account = accounts.find(a => a.id === accountId)
    if (!account || !reauthPassword) {
      toast.error('Please enter your password')
      return
    }

    setIsReauthenticating(true)

    try {
      // Test the connection first
      const config = {
        host: account.settings.imap_host,
        port: account.settings.imap_port,
        security: account.settings.imap_security,
        username: account.email,
        password: reauthPassword,
      }

      if (account.settings.protocol === 'pop3') {
        await apiService.testPop3Connection(config)
      } else {
        await apiService.testImapConnection(config)
      }

      // If test passes, store the password
      storePassword(accountId, reauthPassword)
      
      // Start syncing
      await emailSyncService.startSync(accountId)
      
      toast.success(`${account.email} re-authenticated successfully!`)
      setReauthAccountId(null)
      setReauthPassword('')
    } catch (error: any) {
      toast.error(`Authentication failed: ${error.response?.data?.detail || error.message}`)
    } finally {
      setIsReauthenticating(false)
    }
  }

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
      const errorMsg = error.response?.data?.detail || error.message
      // Add helpful guidance based on provider
      let guidance = ''
      const provider = formData.provider.toLowerCase()
      if (errorMsg.toLowerCase().includes('authentication') || errorMsg.toLowerCase().includes('login')) {
        if (provider.includes('outlook') || provider.includes('hotmail')) {
          guidance = '\n\n💡 For Outlook/Hotmail: Go to account.microsoft.com → Security → App passwords → Create new app password'
        } else if (provider.includes('yahoo')) {
          guidance = '\n\n💡 For Yahoo: Go to Account Security → Generate app password → Select "Other App"'
        } else if (provider.includes('gmail')) {
          guidance = '\n\n💡 For Gmail: Go to myaccount.google.com → Security → App passwords → Create new'
        } else if (provider.includes('rediff')) {
          guidance = '\n\n💡 For Rediffmail: Enable POP3 in Settings → Mail Settings → POP Access'
        }
      }
      toast.error(`${formData.settings.protocol.toUpperCase()} test failed: ${errorMsg}${guidance}`, { duration: 8000 })
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
      const errorMsg = error.response?.data?.detail || error.message
      // Add helpful guidance based on provider
      let guidance = ''
      const provider = formData.provider.toLowerCase()
      if (errorMsg.toLowerCase().includes('authentication') || errorMsg.toLowerCase().includes('login')) {
        if (provider.includes('outlook') || provider.includes('hotmail')) {
          guidance = '\n\n💡 For Outlook: Use App Password from account.microsoft.com → Security'
        } else if (provider.includes('yahoo')) {
          guidance = '\n\n💡 For Yahoo: Use App Password from Account Security settings'
        }
      }
      toast.error(`SMTP test failed: ${errorMsg}${guidance}`, { duration: 8000 })
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
    <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-indigo-100 dark:bg-indigo-900/30 rounded-lg flex items-center justify-center">
              <Mail className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Email Accounts</h2>
              <p className="text-sm text-gray-500 dark:text-gray-400">Manage your connected email accounts</p>
            </div>
          </div>
          <button
            onClick={() => setShowAddForm(true)}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-lg transition-colors"
          >
            <Plus className="w-4 h-4" />
            Add Account
          </button>
        </div>
      </div>

      {/* Account List */}
      <div className="p-6 space-y-3">
        {accounts.length === 0 ? (
          <div className="text-center py-12">
            <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center">
              <Mail className="w-8 h-8 text-gray-400 dark:text-gray-500" />
            </div>
            <p className="text-gray-900 dark:text-white font-medium">No email accounts configured</p>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Add an account to start sending and receiving encrypted emails</p>
          </div>
        ) : (
          accounts.map((account) => (
            <motion.div
              key={account.id}
              layout
              className={`p-4 rounded-lg border transition-colors ${
                account.id === activeAccountId
                  ? 'bg-indigo-50 dark:bg-indigo-900/20 border-indigo-200 dark:border-indigo-700'
                  : 'bg-gray-50 dark:bg-gray-900/50 border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                    account.id === activeAccountId 
                      ? 'bg-indigo-100 dark:bg-indigo-900/30' 
                      : 'bg-gray-200 dark:bg-gray-700'
                  }`}>
                    <Mail className={`w-5 h-5 ${
                      account.id === activeAccountId 
                        ? 'text-indigo-600 dark:text-indigo-400' 
                        : 'text-gray-600 dark:text-gray-400'
                    }`} />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-gray-900 dark:text-white">{account.email}</span>
                      {account.isVerified && (
                        <CheckCircle className="w-4 h-4 text-green-500" />
                      )}
                      {account.id === activeAccountId && (
                        <span className="text-xs px-2 py-0.5 bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 rounded-full font-medium">
                          Active
                        </span>
                      )}
                    </div>
                    <span className="text-sm text-gray-500 dark:text-gray-400">{account.provider}</span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {account.id !== activeAccountId && (
                    <button
                      onClick={() => setActiveAccount(account.id)}
                      className="px-3 py-1.5 text-sm bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 font-medium rounded-lg hover:bg-indigo-200 dark:hover:bg-indigo-900/50 transition-colors"
                    >
                      Set Active
                    </button>
                  )}
                  <button
                    onClick={() => setExpandedAccount(expandedAccount === account.id ? null : account.id)}
                    className="p-2 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-white transition-colors"
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
                    className="p-2 text-red-500 hover:text-red-600 dark:text-red-400 dark:hover:text-red-300 transition-colors"
                  >n                    <Trash2 className="w-4 h-4" />
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
                    className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700 overflow-hidden"
                  >
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">Incoming ({account.settings.protocol.toUpperCase()})</span>
                        <p className="text-gray-900 dark:text-white mt-1">{account.settings.imap_host}:{account.settings.imap_port}</p>
                      </div>
                      <div>
                        <span className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">Outgoing (SMTP)</span>
                        <p className="text-gray-900 dark:text-white mt-1">{account.settings.smtp_host}:{account.settings.smtp_port}</p>
                      </div>
                      <div>
                        <span className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">Folders to Sync</span>
                        <p className="text-gray-900 dark:text-white mt-1">{account.foldersToSync.join(', ')}</p>
                      </div>
                      <div>
                        <span className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">Added</span>
                        <p className="text-gray-900 dark:text-white mt-1">{new Date(account.createdAt).toLocaleDateString()}</p>
                      </div>
                    </div>
                    
                    {/* Re-authenticate Section */}
                    <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                      {reauthAccountId === account.id ? (
                        <div className="space-y-3">
                          <div className="flex items-center gap-2 text-amber-600 dark:text-amber-400 text-sm mb-2">
                            <Key className="w-4 h-4" />
                            <span>Re-enter your password to sync emails</span>
                          </div>
                          <input
                            type="password"
                            value={reauthPassword}
                            onChange={(e) => setReauthPassword(e.target.value)}
                            placeholder="Enter your password"
                            className="w-full px-3 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                          />
                          <div className="flex gap-2">
                            <button
                              onClick={() => handleReauthenticate(account.id)}
                              disabled={isReauthenticating || !reauthPassword}
                              className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors"
                            >
                              {isReauthenticating ? (
                                <>
                                  <Loader2 className="w-4 h-4 animate-spin" />
                                  Verifying...
                                </>
                              ) : (
                                <>
                                  <Check className="w-4 h-4" />
                                  Authenticate
                                </>
                              )}
                            </button>
                            <button
                              onClick={() => {
                                setReauthAccountId(null)
                                setReauthPassword('')
                              }}
                              className="px-3 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                            >
                              Cancel
                            </button>
                          </div>
                        </div>
                      ) : (
                        <button
                          onClick={() => setReauthAccountId(account.id)}
                          className="flex items-center gap-2 px-3 py-2 bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 rounded-lg hover:bg-amber-200 dark:hover:bg-amber-900/50 transition-colors text-sm font-medium"
                        >
                          <Key className="w-4 h-4" />
                          Re-enter Password (Sync Emails)
                        </button>
                      )}
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
            className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4"
            onClick={(e) => e.target === e.currentTarget && setShowAddForm(false)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto"
            >
              <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Add Email Account</h3>
                  <button
                    onClick={() => setShowAddForm(false)}
                    className="p-2 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-white transition-colors rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
              </div>

              <div className="p-6 space-y-4">
                {/* OAuth Login Options */}
                {isMicrosoftOAuthConfigured && (
                  <div className="space-y-3">
                    <div className="text-sm font-medium text-gray-700 dark:text-gray-300">
                      Quick Sign In (Recommended)
                    </div>
                    <button
                      onClick={handleMicrosoftLogin}
                      disabled={isMicrosoftAuthLoading}
                      className="w-full flex items-center justify-center gap-3 px-4 py-3 bg-[#2F2F2F] hover:bg-[#444444] text-white rounded-lg transition-colors disabled:opacity-50"
                    >
                      {isMicrosoftAuthLoading ? (
                        <Loader2 className="w-5 h-5 animate-spin" />
                      ) : (
                        <svg className="w-5 h-5" viewBox="0 0 21 21" fill="none">
                          <path d="M0 0h10v10H0V0z" fill="#F25022"/>
                          <path d="M11 0h10v10H11V0z" fill="#7FBA00"/>
                          <path d="M0 11h10v10H0V11z" fill="#00A4EF"/>
                          <path d="M11 11h10v10H11V11z" fill="#FFB900"/>
                        </svg>
                      )}
                      <span className="font-medium">Continue with Microsoft (Outlook)</span>
                    </button>
                    <div className="relative">
                      <div className="absolute inset-0 flex items-center">
                        <div className="w-full border-t border-gray-300 dark:border-gray-600"></div>
                      </div>
                      <div className="relative flex justify-center text-sm">
                        <span className="px-2 bg-white dark:bg-gray-800 text-gray-500 dark:text-gray-400">or add manually</span>
                      </div>
                    </div>
                  </div>
                )}

                {/* Email */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Email Address
                  </label>
                  <div className="relative">
                    <input
                      type="email"
                      value={formData.email}
                      onChange={(e) => handleEmailChange(e.target.value)}
                      placeholder="you@rediffmail.com"
                      className="w-full px-4 py-2.5 bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    />
                    {isDetecting && (
                      <Loader2 className="absolute right-3 top-2.5 w-5 h-5 text-indigo-500 animate-spin" />
                    )}
                  </div>
                  {formData.provider && (
                    <p className="mt-2 text-sm text-green-600 dark:text-green-400">
                      ✓ Detected: {formData.provider}
                    </p>
                  )}
                </div>

                {/* Password */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Password
                  </label>
                  <input
                    type="password"
                    value={formData.password}
                    onChange={(e) => setFormData((prev) => ({ ...prev, password: e.target.value }))}
                    placeholder="Your email password or app password"
                    className="w-full px-4 py-2.5 bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  />
                </div>

                {/* App Password Help Box */}
                {formData.provider && ['Yahoo', 'Outlook', 'Gmail', 'Rediffmail'].some(p => formData.provider.includes(p)) && (
                  <div className="p-3 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg">
                    <div className="flex items-start gap-2">
                      <Key className="w-4 h-4 text-amber-600 dark:text-amber-400 mt-0.5 flex-shrink-0" />
                      <div className="text-xs text-amber-800 dark:text-amber-300">
                        <strong>Important:</strong> {formData.provider} likely requires an <strong>App Password</strong> instead of your regular password.
                        {formData.provider.includes('Outlook') && (
                          <div className="mt-1">
                            → Go to <a href="https://account.microsoft.com/security" target="_blank" rel="noopener noreferrer" className="underline">account.microsoft.com/security</a> → App passwords
                          </div>
                        )}
                        {formData.provider.includes('Yahoo') && (
                          <div className="mt-1">
                            → Go to Yahoo Account Security → Generate app password
                          </div>
                        )}
                        {formData.provider.includes('Gmail') && (
                          <div className="mt-1">
                            → Go to <a href="https://myaccount.google.com/apppasswords" target="_blank" rel="noopener noreferrer" className="underline">myaccount.google.com/apppasswords</a>
                          </div>
                        )}
                        {formData.provider.includes('Rediff') && (
                          <div className="mt-1">
                            → Enable POP3 in Rediffmail Settings → Mail Settings → POP Access
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}

                {/* Display Name */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Display Name (optional)
                  </label>
                  <input
                    type="text"
                    value={formData.displayName}
                    onChange={(e) => setFormData((prev) => ({ ...prev, displayName: e.target.value }))}
                    placeholder="Your Name"
                    className="w-full px-4 py-2.5 bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  />
                </div>

                {/* Advanced Settings Toggle */}
                <button
                  onClick={() => setShowAdvanced(!showAdvanced)}
                  className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
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
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          Incoming Protocol
                        </label>
                        <div className="flex gap-4">
                          <label className="flex items-center gap-2 cursor-pointer">
                            <input
                              type="radio"
                              checked={formData.settings.protocol === 'imap'}
                              onChange={() => setFormData((prev) => ({
                                ...prev,
                                settings: { ...prev.settings, protocol: 'imap' },
                              }))}
                              className="text-indigo-600 focus:ring-indigo-500"
                            />
                            <span className="text-gray-700 dark:text-gray-300">IMAP</span>
                          </label>
                          <label className="flex items-center gap-2 cursor-pointer">
                            <input
                              type="radio"
                              checked={formData.settings.protocol === 'pop3'}
                              onChange={() => setFormData((prev) => ({
                                ...prev,
                                settings: { ...prev.settings, protocol: 'pop3' },
                              }))}
                              className="text-indigo-600 focus:ring-indigo-500"
                            />
                            <span className="text-gray-700 dark:text-gray-300">POP3</span>
                          </label>
                        </div>
                      </div>

                      {/* Incoming Server */}
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
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
                            className="w-full px-3 py-2 bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            Port
                          </label>
                          <input
                            type="number"
                            value={formData.settings.imap_port}
                            onChange={(e) => setFormData((prev) => ({
                              ...prev,
                              settings: { ...prev.settings, imap_port: parseInt(e.target.value) },
                            }))}
                            className="w-full px-3 py-2 bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                          />
                        </div>
                      </div>

                      {/* SMTP Server */}
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
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
                            className="w-full px-3 py-2 bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            Port
                          </label>
                          <input
                            type="number"
                            value={formData.settings.smtp_port}
                            onChange={(e) => setFormData((prev) => ({
                              ...prev,
                              settings: { ...prev.settings, smtp_port: parseInt(e.target.value) },
                            }))}
                            className="w-full px-3 py-2 bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                          />
                        </div>
                      </div>

                      {/* Security */}
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            Incoming Security
                          </label>
                          <select
                            value={formData.settings.imap_security}
                            onChange={(e) => setFormData((prev) => ({
                              ...prev,
                              settings: { ...prev.settings, imap_security: e.target.value as 'ssl' | 'starttls' },
                            }))}
                            className="w-full px-3 py-2 bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                          >
                            <option value="ssl">SSL/TLS</option>
                            <option value="starttls">STARTTLS</option>
                          </select>
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            SMTP Security
                          </label>
                          <select
                            value={formData.settings.smtp_security}
                            onChange={(e) => setFormData((prev) => ({
                              ...prev,
                              settings: { ...prev.settings, smtp_security: e.target.value as 'ssl' | 'starttls' },
                            }))}
                            className="w-full px-3 py-2 bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
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
                <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                  <button
                    onClick={handleTestConnection}
                    disabled={isTesting || !formData.email || !formData.password}
                    className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-white font-medium rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors disabled:opacity-50"
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
                      <div className={`p-3 rounded-lg text-sm font-medium ${
                        testResults.imap === 'success' ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400' :
                        testResults.imap === 'failed' ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400' :
                        'bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400'
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
                      <div className={`p-3 rounded-lg text-sm font-medium ${
                        testResults.smtp === 'success' ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400' :
                        testResults.smtp === 'failed' ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400' :
                        'bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400'
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
                  <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      <Folder className="w-4 h-4 inline mr-2" />
                      Folders to Sync
                    </label>
                    <div className="flex flex-wrap gap-2">
                      {availableFolders.map((folder) => (
                        <button
                          key={folder}
                          onClick={() => toggleFolderSync(folder)}
                          className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                            formData.foldersToSync.includes(folder)
                              ? 'bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-400 border border-indigo-200 dark:border-indigo-700'
                              : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 border border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500'
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
              <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-700 flex gap-3 bg-gray-50 dark:bg-gray-900/50">
                <button
                  onClick={() => setShowAddForm(false)}
                  className="flex-1 px-4 py-2.5 bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-600 font-medium transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleAddAccount}
                  disabled={testResults.imap !== 'success' || testResults.smtp !== 'success'}
                  className="flex-1 px-4 py-2.5 bg-indigo-600 text-white font-medium rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
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
